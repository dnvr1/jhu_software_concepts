"""Exercise pull, busy rejection, persistence, update, and rendering in SQL."""

import threading
from unittest import mock

import pytest
import sqlalchemy

import app
import models
import orm_queries
import scrape_refresh


pytestmark = [pytest.mark.db, pytest.mark.integration]


def test_pull_update_render_and_overlapping_pull_are_consistent(
    postgres_engine, postgres_records
):
    """Use real routes, worker, loader, PostgreSQL, and ORM analysis.

    Args:
        postgres_engine: Guarded disposable PostgreSQL engine.
        postgres_records: Fixed records replacing only network collection.
    """
    entered = threading.Event()
    release = threading.Event()

    def collect():
        """Hold the worker at a deterministic boundary until released."""
        entered.set()
        assert release.wait(timeout=10), "Collector was not released"
        return postgres_records

    collector = mock.Mock(side_effect=collect)
    manager = scrape_refresh.ScrapeJobManager(collector=collector)
    analyzer = mock.Mock(wraps=orm_queries.run_complete_analysis)
    sessions = mock.Mock(wraps=models.SessionLocal)
    client = app.create_app({
        "TESTING": True, "SCRAPE_MANAGER": manager,
        "SESSION_FACTORY": sessions, "ANALYSIS_RUNNER": analyzer,
    }).test_client()

    def stored_count():
        """Read committed storage independently of the HTTP request."""
        with postgres_engine.connect() as connection:
            return connection.scalar(sqlalchemy.text(
                "SELECT count(*) FROM applicants LIMIT 1"
            ))

    assert stored_count() == 0
    try:
        assert client.post("/pull-data").status_code == 202
        assert entered.wait(timeout=10), "Worker never started"
        before = manager.snapshot()
        for path in ("/pull-data", "/update-analysis"):
            response = client.post(path)
            assert response.status_code == 409
            assert response.get_json()["busy"] is True
        # Prove absence of side effects, not just an HTTP error code.
        analyzer.assert_not_called()
        sessions.assert_not_called()
        collector.assert_called_once_with()
        assert manager.snapshot() == before
        assert stored_count() == 0
    finally:
        release.set()
        assert manager.wait(timeout=10), "Worker did not finish"

    assert manager.snapshot()["status"] == "succeeded", manager.snapshot()
    assert manager.snapshot()["records_inserted"] == 2
    assert stored_count() == 2
    update = client.post("/update-analysis")
    assert update.status_code == 200
    result = update.get_json()["analysis"]
    assert result["database_rows"] == "2"
    assert result["question_1"] == "2"
    assert result["question_2"] == "50.00%"
    assert result["question_3"]["gpa"] == "3.70"
    assert analyzer.call_count == 1
    assert sessions.call_count == 1

    page = client.get("/analysis")
    assert page.status_code == 200
    html = page.get_data(as_text=True)
    for expected in ("Answer: 2", "50.00%", "3.70", "Example University"):
        assert expected in html
    assert analyzer.call_count == 2
    assert client.post("/pull-data").status_code == 202
    assert manager.wait(timeout=10)
    assert manager.snapshot()["status"] == "succeeded", manager.snapshot()
    assert manager.snapshot()["records_inserted"] == 0
    assert stored_count() == 2
