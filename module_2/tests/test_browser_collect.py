"""Offline tests for the optional normal-browser capture helper."""

from unittest.mock import Mock, patch

import pytest

from browser_collect import (
    BrowserPage,
    _require_anonymous_public_page,
    _same_page,
    main,
)
from scrape import ScrapingStopped


def test_survey_slash_redirect_preserves_cursor_identity():
    assert _same_page(
        "https://www.thegradcafe.com/survey",
        "https://www.thegradcafe.com/survey/",
    )
    assert not _same_page(
        "https://www.thegradcafe.com/survey?cursor=old",
        "https://www.thegradcafe.com/survey?cursor=new",
    )
    with pytest.raises(ScrapingStopped):
        _same_page(
            "https://example.org/survey", "https://www.thegradcafe.com/survey"
        )


def test_new_page_waits_for_both_cursor_and_fresh_table():
    page = BrowserPage.__new__(BrowserPage)
    page.command = Mock(return_value={})
    url = "https://www.thegradcafe.com/survey?cursor=new"
    page.snapshot = Mock(
        side_effect=[
            {"ready": "complete", "url": url, "first": "/result/old"},
            {"ready": "complete", "url": url, "first": "/result/new"},
        ]
    )
    with patch("browser_collect.time.sleep"):
        assert page.navigate(url, "/result/old")["first"] == "/result/new"
    assert page.snapshot.call_count == 2
    assert page.command.call_count == 1


def test_browser_challenge_stops_before_capture():
    page = BrowserPage.__new__(BrowserPage)
    page.rejection = None
    page.evaluate = Mock(return_value={"title": "Just a moment..."})
    with pytest.raises(ScrapingStopped, match="challenge"):
        page.snapshot()


def test_document_rate_limit_is_recorded_without_retry():
    page = BrowserPage.__new__(BrowserPage)
    page.command_id = 0
    page.rejection = None
    page.socket = Mock()
    page.socket.recv.side_effect = [
        '{"method":"Network.responseReceived","params":{"type":"Document","response":{"status":429,"url":"https://www.thegradcafe.com/survey"}}}',
        '{"id":1,"result":{}}',
    ]
    page.command("Runtime.evaluate")
    assert page.rejection.startswith("HTTP 429")
    assert page.socket.send.call_count == 1


@pytest.mark.parametrize(
    "state",
    [
        {"url": "https://www.thegradcafe.com/login"},
        {"url": "https://www.thegradcafe.com/survey", "login_form": True},
        {
            "url": "https://www.thegradcafe.com/survey",
            "headings": ["Sign in to continue"],
        },
        {
            "url": "https://www.thegradcafe.com/survey",
            "account_controls": [{"text": "Sign Out", "target": ""}],
        },
        {
            "url": "https://www.thegradcafe.com/survey",
            "account_controls": [{"text": "", "target": "/logout"}],
        },
        {
            "url": "https://www.thegradcafe.com/survey",
            "authenticated_marker": True,
        },
    ],
)
def test_explicit_login_or_account_state_is_rejected(state):
    with pytest.raises(ScrapingStopped):
        _require_anonymous_public_page(state)


def test_optional_sign_in_navigation_is_not_a_login_gate():
    _require_anonymous_public_page(
        {
            "url": "https://www.thegradcafe.com/survey",
            "account_controls": [{"text": "Sign In", "target": "/login"}],
            "headings": ["Admissions Results"],
        }
    )


def test_persisted_stop_prevents_browser_launch_attach_and_prompt(tmp_path):
    from scrape import GradCafeScraper

    output, raw = tmp_path / "out.json", tmp_path / "raw"
    collector = GradCafeScraper(output, raw)
    collector.record_stop("HTTP 429 prior block")
    before = collector.state_path.read_bytes()
    with (
        patch(
            "sys.argv",
            [
                "browser_collect.py",
                "--output",
                str(output),
                "--raw-dir",
                str(raw),
            ],
        ),
        patch("browser_collect.subprocess.Popen") as launch,
        patch("browser_collect._find_page") as attach,
        patch("builtins.input") as prompt,
    ):
        assert main() == 1
    launch.assert_not_called()
    attach.assert_not_called()
    prompt.assert_not_called()
    assert collector.state_path.read_bytes() == before


def test_robots_policy_is_checked_before_any_survey_navigation(tmp_path):
    output, raw = tmp_path / "out.json", tmp_path / "raw"
    page = Mock()
    page.snapshot.return_value = {
        "url": "https://www.thegradcafe.com/robots.txt",
        "text": "User-agent: *\nDisallow: /survey\n",
    }
    with (
        patch(
            "sys.argv",
            [
                "browser_collect.py",
                "--attach",
                "--output",
                str(output),
                "--raw-dir",
                str(raw),
            ],
        ),
        patch("browser_collect._find_page", return_value=page),
        patch("builtins.input", return_value=""),
    ):
        assert main() == 1
    page.navigate.assert_not_called()
    assert not output.exists()


def test_new_browser_starts_at_robots_not_results(tmp_path):
    with (
        patch(
            "sys.argv",
            [
                "browser_collect.py",
                "--browser-path",
                "edge.exe",
                "--output",
                str(tmp_path / "out.json"),
                "--raw-dir",
                str(tmp_path / "raw"),
            ],
        ),
        patch("browser_collect.socket.create_connection", side_effect=OSError),
        patch("browser_collect.subprocess.Popen") as launch,
        patch("builtins.input", side_effect=KeyboardInterrupt),
    ):
        assert main() == 130
    arguments = launch.call_args.args[0]
    assert arguments[-1] == "https://www.thegradcafe.com/robots.txt"
    assert all("survey" not in argument for argument in arguments)
