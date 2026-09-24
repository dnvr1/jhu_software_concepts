"""Deterministic tests for command and network boundaries."""

import argparse
import json
from pathlib import Path
from types import SimpleNamespace
from urllib.error import HTTPError, URLError
from unittest.mock import Mock

import pytest

import clean
import load_data
import run_flask
import scrape
import storage
from bs4 import BeautifulSoup


pytestmark = [pytest.mark.integration, pytest.mark.db]


@pytest.fixture
def isolated_scraper(tmp_path):
    policy = tmp_path / "policy.txt"
    policy.write_text("User-agent: *\nAllow: /\n", encoding="utf-8")
    collector = scrape.GradCafeScraper(
        tmp_path / "applicant_data.json", tmp_path / "raw"
    )
    collector.check_robots(policy)
    return collector


def _llm_fixture(tmp_path, records=None):
    package = tmp_path / "llm_hosting"
    package.mkdir()
    (package / "app.py").write_text("# test package", encoding="utf-8")
    source = tmp_path / "input.json"
    storage.save_data(
        records
        if records is not None
        else [{"program": "Math", "url": "https://example/1"}],
        source,
    )
    return package, source, tmp_path / "output.json"


def _candidate(**changes):
    value = {
        "program": "Math",
        "url": "https://example/1",
        "llm-generated-program": "Mathematics",
        "llm-generated-university": "Example University",
    }
    value.update(changes)
    return value


def test_clean_validation_and_output_formats(monkeypatch, tmp_path):
    assert clean.text_value(None) is None
    package, source, output = _llm_fixture(tmp_path)

    with pytest.raises(ValueError, match="batch_size"):
        clean.extend_with_llm(source, output, package, batch_size=0)

    storage.save_data([], source)
    with pytest.raises(ValueError, match="No applicant records"):
        clean.extend_with_llm(source, output, package)

    storage.save_data([{"program": "Math", "url": "https://example/1"}], source)
    responses = [
        SimpleNamespace(returncode=3, stdout="", stderr="model failed"),
        SimpleNamespace(returncode=0, stdout=json.dumps(_candidate()), stderr=""),
        SimpleNamespace(returncode=0, stdout=json.dumps(_candidate()) + "\n", stderr=""),
    ]
    monkeypatch.setattr(clean.subprocess, "run", lambda *a, **k: responses.pop(0))
    with pytest.raises(RuntimeError, match="model failed"):
        clean.extend_with_llm(source, output, package)

    assert clean.extend_with_llm(source, output, package) == 1
    # Change the package hash so the next call does not reuse the cached batch.
    (package / "config.txt").write_text("changed", encoding="utf-8")
    assert clean.extend_with_llm(source, output, package) == 1


@pytest.mark.parametrize(
    ("stdout", "message"),
    [
        ("not json", "must print JSON"),
        ("[]", "number of records"),
        (json.dumps(["not a mapping"]), "original program"),
        (json.dumps([_candidate(**{"llm-generated-program": 7})]), "valid llm-generated-program"),
    ],
)
def test_clean_rejects_invalid_model_output(monkeypatch, tmp_path, stdout, message):
    package, source, output = _llm_fixture(tmp_path)
    result = SimpleNamespace(returncode=0, stdout=stdout, stderr="")
    monkeypatch.setattr(clean.subprocess, "run", lambda *a, **k: result)

    with pytest.raises(ValueError, match=message):
        clean.extend_with_llm(source, output, package)


def test_clean_command_success_and_failure(monkeypatch, capsys):
    args = argparse.Namespace(
        file=Path("input.json"),
        output=Path("output.json"),
        llm_dir=Path("llm_hosting"),
        batch_size=1,
        python="python",
    )
    monkeypatch.setattr(clean.argparse.ArgumentParser, "parse_args", lambda self: args)
    monkeypatch.setattr(clean, "extend_with_llm", lambda *a: 2)
    assert clean.main() == 0
    assert "Saved 2" in capsys.readouterr().out

    monkeypatch.setattr(
        clean,
        "extend_with_llm",
        lambda *a: (_ for _ in ()).throw(ValueError("invalid model output")),
    )
    assert clean.main() == 1
    assert "invalid model output" in capsys.readouterr().err


def test_load_interactive_password(monkeypatch):
    final = object()
    maintenance = Mock()
    maintenance.__enter__ = Mock(return_value=maintenance)
    maintenance.__exit__ = Mock(return_value=False)
    cursor = Mock()
    cursor.__enter__ = Mock(return_value=cursor)
    cursor.__exit__ = Mock(return_value=False)
    cursor.fetchone.return_value = (1,)
    maintenance.cursor.return_value = cursor

    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("PGPASSWORD", raising=False)
    monkeypatch.setattr(load_data.sys, "stdin", SimpleNamespace(isatty=lambda: True))
    monkeypatch.setattr(load_data.getpass, "getpass", lambda prompt: "typed")
    monkeypatch.setattr(
        load_data.psycopg,
        "connect",
        lambda *a, **k: maintenance if k.get("autocommit") else final,
    )
    assert load_data.connect_database() is final


def test_storage_exhausts_permission_retries(monkeypatch, tmp_path):
    monkeypatch.setattr(storage, "REPLACE_ATTEMPTS", 2)
    monkeypatch.setattr(storage.time, "sleep", lambda delay: None)
    monkeypatch.setattr(
        storage.os,
        "replace",
        lambda source, destination: (_ for _ in ()).throw(PermissionError("locked")),
    )
    with pytest.raises(PermissionError, match="locked"):
        storage._replace_with_retry(tmp_path / "a", tmp_path / "b")


def test_scrape_url_policy_redirect_and_constructor(tmp_path):
    with pytest.raises(ValueError, match="start at 1"):
        scrape.result_url(0)
    with pytest.raises(scrape.ScrapingStopped, match="non-results"):
        scrape.validate_public_url("https://www.thegradcafe.com/account")
    with pytest.raises(ValueError, match="delay"):
        scrape.GradCafeScraper(tmp_path / "out.json", tmp_path / "raw", delay=1)

    allowed = Mock()
    redirect = scrape._CheckedRedirect(allowed)
    with pytest.raises(Exception):
        redirect.redirect_request(None, None, 302, "Found", {}, "https://www.thegradcafe.com/survey")
    allowed.assert_called_once()


class _Headers:
    def __init__(self, content_type):
        self.content_type = content_type

    def get_content_type(self):
        return self.content_type


class _Response:
    def __init__(self, content_type="text/html"):
        self.url = "https://www.thegradcafe.com/survey/"
        self.headers = _Headers(content_type)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return b"page"


def test_scrape_request_success_and_failures(monkeypatch, tmp_path):
    collector = scrape.GradCafeScraper(tmp_path / "out.json", tmp_path / "raw")
    monkeypatch.setattr(collector, "ensure_live_allowed", lambda: None)
    monkeypatch.setattr(collector, "_allowed", lambda url: None)
    monkeypatch.setattr(scrape.time, "monotonic", lambda: 100.0)

    opener = Mock()
    opener.open.return_value = _Response()
    monkeypatch.setattr(scrape, "build_opener", lambda *a: opener)
    assert collector._request("https://www.thegradcafe.com/survey/") == (
        b"page",
        "https://www.thegradcafe.com/survey/",
    )

    opener.open.return_value = _Response("application/json")
    with pytest.raises(scrape.ScrapingStopped, match="content type"):
        collector._request("https://www.thegradcafe.com/survey/")

    opener.open.side_effect = HTTPError("url", 429, "rate", {}, None)
    with pytest.raises(scrape.ScrapingStopped, match="HTTP 429"):
        collector._request("https://www.thegradcafe.com/survey/")

    opener.open.side_effect = URLError("offline")
    with pytest.raises(scrape.ScrapingStopped, match="Request failed"):
        collector._request("https://www.thegradcafe.com/survey/")


def test_scrape_wrapper_and_command_paths(monkeypatch, tmp_path, capsys):
    class FakeScraper:
        instances = []

        def __init__(self, output=None, raw_dir=None, delay=6):
            self.output = output
            self.raw_dir = raw_dir
            self.records = []
            self.state = {"next_url": "https://www.thegradcafe.com/survey/"}
            self.instances.append(self)

        def scrape_data(self, target=30000, max_pages=5000):
            self.records = [{"url": "one"}]
            return self.records

        def check_robots(self, path):
            return None

        def ingest(self, payload, page, source_url, method):
            self.records.append({"url": str(page)})
            return 1

    monkeypatch.setattr(scrape, "GradCafeScraper", FakeScraper)
    assert scrape.scrape_data(target=1) == [{"url": "one"}]

    args = argparse.Namespace(
        output=tmp_path / "out.json",
        raw_dir=tmp_path / "raw",
        target=1,
        max_pages=1,
        delay=6,
        html_dir=None,
        robots_file=None,
    )
    monkeypatch.setattr(scrape.argparse.ArgumentParser, "parse_args", lambda self: args)
    assert scrape.main() == 0
    assert "Saved 1" in capsys.readouterr().out

    args.target = 2
    assert scrape.main() == 2
    assert "INCOMPLETE" in capsys.readouterr().err

    args.target = 0
    assert scrape.main() == 1
    assert "must be positive" in capsys.readouterr().err


def test_saved_html_command_paths(monkeypatch, tmp_path, capsys):
    html_dir = tmp_path / "captures"
    html_dir.mkdir()
    page = html_dir / "page-000001.html"
    page.write_text("<html></html>", encoding="utf-8")
    page.with_suffix(".meta.json").write_text(
        json.dumps({"source_url": "https://www.thegradcafe.com/survey/"}),
        encoding="utf-8",
    )

    class SavedScraper:
        def __init__(self, *args):
            self.records = []
            self.state = {"next_url": None}

        def check_robots(self, path):
            return None

        def ingest(self, *args, **kwargs):
            self.records.append({"url": "one"})
            return 1

    args = argparse.Namespace(
        output=tmp_path / "out.json",
        raw_dir=tmp_path / "raw",
        target=1,
        max_pages=1,
        delay=6,
        html_dir=html_dir,
        robots_file=tmp_path / "robots.txt",
    )
    monkeypatch.setattr(scrape, "GradCafeScraper", SavedScraper)
    monkeypatch.setattr(scrape.argparse.ArgumentParser, "parse_args", lambda self: args)
    assert scrape.main() == 0
    assert "Page 1" in capsys.readouterr().out

    args.robots_file = None
    assert scrape.main() == 1

    args.robots_file = tmp_path / "robots.txt"
    page.unlink()
    page.with_suffix(".meta.json").unlink()
    assert scrape.main() == 1


def test_run_flask_configures_and_runs(monkeypatch):
    calls = []
    monkeypatch.setattr(run_flask, "runtime_password", lambda: "pw")
    monkeypatch.setattr(run_flask.models, "configure_database", lambda value: calls.append(value))

    import app

    monkeypatch.setattr(app.app, "run", lambda **kwargs: calls.append(kwargs))
    monkeypatch.setenv("FLASK_HOST", "0.0.0.0")
    monkeypatch.setenv("FLASK_PORT", "5050")
    run_flask.main()

    assert calls == [
        "pw",
        {"host": "0.0.0.0", "port": 5050, "debug": False, "use_reloader": False},
    ]


def test_checkpoint_recovery_guardrails(tmp_path):
    output = tmp_path / "out.json"
    raw = tmp_path / "raw"
    policy = tmp_path / "robots.txt"
    policy.write_text("User-agent: *\nAllow: /\n", encoding="utf-8")
    collector = scrape.GradCafeScraper(output, raw)
    collector.check_robots(policy)
    html = """<table><tr><td>Example U</td><td><span>Math</span></td>
    <td>Sep 22, 2026</td><td>Accepted</td>
    <td><a href='/result/1'>View</a></td></tr></table>"""
    collector.ingest(html.encode(), 1)

    journal_path = raw / "page-000001.json"
    journal = json.loads(journal_path.read_text(encoding="utf-8"))
    journal["parser_schema_version"] = 1
    journal_path.write_text(json.dumps(journal), encoding="utf-8")
    with pytest.raises(ValueError, match="Incompatible parser schema"):
        scrape.GradCafeScraper(output, raw)

    empty_raw = tmp_path / "empty-raw"
    empty_raw.mkdir()
    (empty_raw / "checkpoint.json").write_text(
        json.dumps(
            {
                "parser_schema_version": scrape.PARSER_SCHEMA_VERSION,
                "completed_pages": {"1": {"next_url": None}},
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="records/journals are missing"):
        scrape.GradCafeScraper(tmp_path / "missing.json", empty_raw)


def test_atomic_recovery_requires_evidence(isolated_scraper):
    isolated_scraper.record_stop(
        "[WinError 5] Access is denied: '.applicant_data.json.x.tmp' -> 'applicant_data.json'"
    )
    with pytest.raises(ValueError, match="review evidence"):
        isolated_scraper.resolve_atomic_save_stop(" ")


def test_live_robots_fetch_rate_and_invalid_policy(monkeypatch, tmp_path):
    collector = scrape.GradCafeScraper(tmp_path / "out.json", tmp_path / "raw")
    policy = (
        b"User-agent: *\nAllow: /\nCrawl-delay: 7\nRequest-rate: 1/10\n"
    )
    monkeypatch.setattr(
        collector,
        "_request",
        lambda url: (policy, "https://www.thegradcafe.com/robots.txt"),
    )
    collector.check_robots()
    assert collector.delay == 10

    invalid = scrape.GradCafeScraper(
        tmp_path / "bad.json", tmp_path / "bad-raw"
    )
    monkeypatch.setattr(
        invalid,
        "_request",
        lambda url: (b"<html>challenge</html>", url),
    )
    with pytest.raises(scrape.ScrapingStopped, match="not a readable"):
        invalid.check_robots()


def test_parser_layout_degree_and_pagination_edges():
    missing_link = BeautifulSoup(
        "<tr><td>Example</td><td>Math</td><td>Date</td><td>Accepted</td></tr>",
        "html.parser",
    ).tr
    with pytest.raises(ValueError, match="stable result link"):
        scrape.GradCafeScraper._parse_entry(missing_link, [], scrape.result_url(1))

    bad_layout = BeautifulSoup(
        "<tr><td>Example</td><td><a href='/result/1'>View</a></td></tr>",
        "html.parser",
    ).tr
    with pytest.raises(ValueError, match="Unrecognized applicant row"):
        scrape.GradCafeScraper._parse_entry(bad_layout, [], scrape.result_url(1))

    degree_row = BeautifulSoup(
        """<tr><td>Example University</td><td><span>Physics PhD</span></td>
        <td>Sep 22, 2026</td><td>Accepted</td>
        <td><a href='/result/2'>View</a></td></tr>""",
        "html.parser",
    ).tr
    parsed = scrape.GradCafeScraper._parse_entry(
        degree_row, [], scrape.result_url(1)
    )
    assert parsed["degree"].lower() == "phd"

    collector = object.__new__(scrape.GradCafeScraper)
    unrelated = """<a rel='next' href='/result/3'>Next</a>"""
    assert collector.next_url(unrelated, scrape.result_url(1)) is None
    stuck = """<a rel='next' href='/survey/?page=1'>Next</a>"""
    with pytest.raises(scrape.ScrapingStopped, match="pagination is stuck"):
        collector.next_url(stuck, scrape.result_url(1))


def test_ingest_rejects_changed_existing_page(isolated_scraper):
    from test_scrape_pipeline import listing

    isolated_scraper.ingest(listing().encode(), 1)
    with pytest.raises(scrape.ScrapingStopped, match="differs"):
        isolated_scraper.ingest(listing(2).encode(), 1)


def test_scrape_loop_reads_archive_skips_completed_and_stops(monkeypatch, tmp_path):
    collector = scrape.GradCafeScraper(tmp_path / "out.json", tmp_path / "raw")
    collector.raw_dir.mkdir()
    (collector.raw_dir / "page-000001.html").write_bytes(b"saved")
    monkeypatch.setattr(collector, "check_robots", lambda: None)
    monkeypatch.setattr(collector, "ensure_live_allowed", lambda: None)

    def ingest(payload, page, url):
        assert payload == b"saved"
        collector.records.append({"url": "one"})
        collector.state["next_url"] = None
        return 1

    monkeypatch.setattr(collector, "ingest", ingest)
    assert collector.scrape_data(target=2, max_pages=3) == [{"url": "one"}]

    collector.records.clear()
    collector.state["completed_pages"] = {"1": {"next_url": None}}
    collector.state["next_url"] = None
    assert collector.scrape_data(target=2, max_pages=2) == []

    collector.records[:] = [{"url": "already-complete"}]
    collector.state["completed_pages"] = {}
    collector.state["next_url"] = "https://www.thegradcafe.com/survey/"
    assert collector.scrape_data(target=1, max_pages=1) == [
        {"url": "already-complete"}
    ]

    live = scrape.GradCafeScraper(
        tmp_path / "live.json", tmp_path / "live-raw"
    )
    monkeypatch.setattr(live, "check_robots", lambda: None)
    monkeypatch.setattr(live, "ensure_live_allowed", lambda: None)
    monkeypatch.setattr(
        live,
        "_request",
        lambda url: (b"live", "https://www.thegradcafe.com/survey/"),
    )

    def ingest_live(payload, page, url):
        live.records.append({"url": "live"})
        return 1

    monkeypatch.setattr(live, "ingest", ingest_live)
    assert live.scrape_data(target=1, max_pages=1) == [{"url": "live"}]


def test_saved_html_break_and_missing_source(monkeypatch, tmp_path):
    html_dir = tmp_path / "captures"
    html_dir.mkdir()
    for number in (1, 2):
        (html_dir / f"page-{number:06d}.html").write_text(
            "<html></html>", encoding="utf-8"
        )

    class SavedScraper:
        def __init__(self, *args):
            self.records = []
            self.state = {"next_url": "https://www.thegradcafe.com/survey/"}

        def check_robots(self, path):
            return None

        def ingest(self, payload, page, source_url, method):
            self.records.append({"url": str(page)})
            return 1

    args = argparse.Namespace(
        output=tmp_path / "out.json",
        raw_dir=tmp_path / "raw",
        target=1,
        max_pages=2,
        delay=6,
        html_dir=html_dir,
        robots_file=tmp_path / "robots.txt",
    )
    monkeypatch.setattr(scrape, "GradCafeScraper", SavedScraper)
    monkeypatch.setattr(scrape.argparse.ArgumentParser, "parse_args", lambda self: args)
    assert scrape.main() == 0

    class MissingSource(SavedScraper):
        def __init__(self, *args):
            super().__init__(*args)
            self.state["next_url"] = None

    monkeypatch.setattr(scrape, "GradCafeScraper", MissingSource)
    args.target = 2
    assert scrape.main() == 1
