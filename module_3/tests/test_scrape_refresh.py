"""Tests for safe scraper reuse, inserts, and single-job coordination."""

from threading import Event
import time

from scrape_refresh import ScrapeJobManager, prepare_mappings


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
    for _ in range(100):
        result = manager.snapshot()
        if result["status"] != "running":
            break
        time.sleep(0.01)
    assert result["status"] == "succeeded"
    assert result["records_inserted"] == 1


def test_manager_exposes_collection_errors_to_the_user():
    def collector():
        raise RuntimeError("public site unavailable")

    manager = ScrapeJobManager(collector, lambda records: (0, 0))
    manager.start()
    for _ in range(100):
        result = manager.snapshot()
        if result["status"] != "running":
            break
        time.sleep(0.01)
    assert result["status"] == "failed"
    assert "public site unavailable" in result["message"]
