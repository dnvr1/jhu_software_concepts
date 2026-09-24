"""PostgreSQL-backed insert verification for CI and test databases."""

import os

import pytest
from sqlalchemy import text

import load_data
import models
from scrape_refresh import insert_new_records


pytestmark = [pytest.mark.db, pytest.mark.integration]


def _postgres_test_url():
    url = os.getenv("DATABASE_URL")
    if not url:
        pytest.skip("DATABASE_URL is supplied by the PostgreSQL CI service")
    parsed = models.database_url()
    if not (parsed.database or "").endswith("_test"):
        pytest.skip("PostgreSQL integration only runs against a *_test database")
    return url


def test_postgres_insert_required_fields_and_duplicate_policy():
    """A repeated pull keeps one row per required, non-null source URL."""
    _postgres_test_url()
    engine, _ = models.configure_database()
    records = [
        {
            "program": "Computer Science, Example University",
            "date_added": "Sep 22, 2026",
            "url": "https://example.test/result/1",
            "status": "Accepted",
            "term": "Fall 2027",
            "citizenship": "International",
            "degree": "PhD",
        },
        {
            "program": "Mathematics, Example University",
            "date_added": "Sep 22, 2026",
            "url": "https://example.test/result/2",
            "status": "Rejected",
            "term": "Fall 2027",
            "citizenship": "American",
            "degree": "Masters",
        },
    ]

    with engine.begin() as connection:
        connection.execute(text(load_data.CREATE_TABLE_SQL))
        connection.execute(text("TRUNCATE TABLE applicants RESTART IDENTITY"))

    assert insert_new_records(records) == (2, 0)
    assert insert_new_records(records) == (0, 0)

    with engine.connect() as connection:
        rows = connection.execute(
            text(
                "SELECT url, program, date_added FROM applicants "
                "ORDER BY url"
            )
        ).mappings().all()

    assert len(rows) == 2
    assert [dict(row) for row in rows] == [
        {
            "url": "https://example.test/result/1",
            "program": "Computer Science, Example University",
            "date_added": rows[0]["date_added"],
        },
        {
            "url": "https://example.test/result/2",
            "program": "Mathematics, Example University",
            "date_added": rows[1]["date_added"],
        },
    ]
    assert all(row["date_added"] is not None for row in rows)
