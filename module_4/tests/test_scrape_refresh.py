"""Tests for safe scraper reuse, inserts, and single-job coordination."""

from threading import Event

import pytest

import scrape_refresh
from scrape_refresh import ScrapeJobManager, prepare_mappings


pytestmark = [pytest.mark.buttons, pytest.mark.db]


def applicant(url="https://www.thegradcafe.com/result/123"):
    """Return a minimal usable Module 2 record."""
    return {
        "url": url,
        "program": "Example University Computer Science",
        "date_added": "Sep 17, 2026",
        "status": "Accepted",
        "term": "Fall 2027",
        "citizenship": "American",
        "degree": "PhD",
    }


def test_prepare_mappings_skips_duplicate_and_unusable_records():
    mappings, rejected = prepare_mappings(
        [applicant(), applicant(), {"program": "Missing URL"}]
    )

    assert len(mappings) == 1
    assert mappings[0]["url"].endswith("/123")
    assert mappings[0]["us_or_international"] == "American"
    assert mappings[0]["llm_generated_program"] is None
    assert rejected == 2


def test_manager_refuses_overlapping_jobs_and_reports_success():
    collector_started = Event()
    allow_finish = Event()

    def collector():
        collector_started.set()
        assert allow_finish.wait(timeout=2)
        return [applicant()]

    manager = ScrapeJobManager(collector, lambda records: (1, 0))
    started, first = manager.start()
    assert started is True
    assert collector_started.wait(timeout=2)
    duplicate_started, duplicate = manager.start()
    assert duplicate_started is False
    assert first["status"] == duplicate["status"] == "running"

    allow_finish.set()
    assert manager.wait(timeout=2)
    result = manager.snapshot()
    assert result["status"] == "succeeded"
    assert result["records_inserted"] == 1


def test_manager_exposes_collection_errors_to_the_user():
    def collector():
        raise RuntimeError("public site unavailable")

    manager = ScrapeJobManager(collector, lambda records: (0, 0))
    manager.start()
    assert manager.wait(timeout=2)
    result = manager.snapshot()
    assert result["status"] == "failed"
    assert "public site unavailable" in result["message"]


def test_collection_uses_isolated_runtime_and_validates_pages(monkeypatch, tmp_path):
    calls = {}

    class FakeScraper:
        def __init__(self, output, raw_directory, delay):
            calls["init"] = (output, raw_directory, delay)

        def scrape_data(self, **kwargs):
            calls["scrape"] = kwargs
            return [applicant()]

    monkeypatch.setenv("SCRAPE_RUN_ROOT", str(tmp_path))
    monkeypatch.setenv("SCRAPE_DELAY", "0")
    monkeypatch.setenv("SCRAPE_MAX_PAGES", "2")
    monkeypatch.setattr(scrape_refresh, "GradCafeScraper", FakeScraper)

    assert scrape_refresh.collect_current_entries() == [applicant()]
    assert calls["init"][0].name == "applicant_data.json"
    assert calls["scrape"] == {"target": 1, "max_pages": 2}

    monkeypatch.setenv("SCRAPE_MAX_PAGES", "0")
    with pytest.raises(ValueError, match="at least 1"):
        scrape_refresh.collect_current_entries()


def test_insert_new_records_empty_and_postgres_insert(monkeypatch):
    assert scrape_refresh.insert_new_records([{"program": "missing URL"}]) == (
        0,
        1,
    )

    class ScalarResult:
        def all(self):
            return [1]

    class Session:
        def scalars(self, statement):
            return ScalarResult()

    class Begin:
        def __enter__(self):
            return Session()

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(scrape_refresh.models.SessionLocal, "begin", lambda: Begin())
    inserted, rejected = scrape_refresh.insert_new_records([applicant()])
    assert (inserted, rejected) == (1, 0)


def test_success_message_reports_duplicates_and_rejections():
    manager = ScrapeJobManager(
        lambda: [applicant("one"), applicant("two"), applicant("three")],
        lambda records: (1, 1),
    )
    manager.start()
    assert manager.wait(timeout=2)
    result = manager.snapshot()
    assert "1 existing records skipped" in result["message"]
    assert "1 unusable records" in result["message"]
