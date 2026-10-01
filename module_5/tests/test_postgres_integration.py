"""Verify HTTP-triggered insertion and idempotency in real PostgreSQL."""

import datetime

import pytest
import sqlalchemy

import app
import scrape_refresh


pytestmark = [pytest.mark.db, pytest.mark.integration]


def test_postgres_insert_required_fields_and_duplicate_policy(
    postgres_engine, postgres_records
):
    """POST twice through the real worker and inspect committed row contents.

    Args:
        postgres_engine: Guarded disposable PostgreSQL engine.
        postgres_records: Deterministic replacement for network collection.
    """
    manager = scrape_refresh.ScrapeJobManager(
        collector=lambda: postgres_records
    )
    client = app.create_app({
        "TESTING": True, "SCRAPE_MANAGER": manager
    }).test_client()
    for expected_inserted in (2, 0):
        assert client.post("/pull-data").status_code == 202
        assert manager.wait(timeout=10), "Background insertion timed out"
        state = manager.snapshot()
        assert state["status"] == "succeeded", state
        assert state["records_inserted"] == expected_inserted
        assert state["records_rejected"] == 0

    # A new connection observes committed rows, not worker-local state.
    with postgres_engine.connect() as connection:
        rows = connection.execute(sqlalchemy.text(
            "SELECT url, program, date_added FROM applicants "
            "ORDER BY url LIMIT 100"
        )).mappings().all()
    assert [dict(row) for row in rows] == [
        {
            "url": record["url"], "program": record["program"],
            "date_added": datetime.date(2026, 9, 22),
        }
        for record in postgres_records
    ]
