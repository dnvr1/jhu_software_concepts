"""Shared deterministic doubles for the Module 4 test suite."""

from decimal import Decimal
import os

import pytest
import sqlalchemy
from sqlalchemy import orm

from app import create_app
import load_data
import models


REQUIRED_MARKERS = {"web", "buttons", "analysis", "db", "integration"}


def pytest_collection_modifyitems(items):
    """Fail collection when an assignment test has no approved marker."""
    unmarked = [
        item.nodeid
        for item in items
        if not REQUIRED_MARKERS.intersection(
            marker.name for marker in item.iter_markers()
        )
    ]
    if unmarked:
        raise pytest.UsageError(
            "Every test needs an assignment marker: " + ", ".join(unmarked)
        )


class DummySession:
    """Small context manager standing in for a SQLAlchemy session."""

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False


class FakeManager:
    """Observable pull manager used without threads or network access."""

    def __init__(self, status="idle", start_result=True):
        self.status = status
        self.start_result = start_result
        self.start_calls = 0

    def snapshot(self):
        return {
            "status": self.status,
            "message": "Deterministic test status.",
            "records_inserted": 0,
        }

    def start(self):
        self.start_calls += 1
        if not self.start_result or self.status == "running":
            return False, self.snapshot()
        self.status = "running"
        return True, self.snapshot()


@pytest.fixture
def analysis_results():
    """Representative results covering every template field."""
    return {
        "total_rows": 4,
        "question_1": 3,
        "question_2": Decimal("39.28"),
        "question_3": (
            Decimal("3.80"),
            Decimal("168.00"),
            Decimal("160.00"),
            Decimal("4.50"),
        ),
        "question_4": Decimal("3.75"),
        "question_5": Decimal("50.00"),
        "question_6": Decimal("3.70"),
        "question_7": 1,
        "question_8": 2,
        "question_9": 3,
        "question_10": [("American", 2, Decimal("50.00"))],
        "question_11": [("Johns Hopkins University", 1, Decimal("25.00"))],
    }


@pytest.fixture
def manager():
    return FakeManager()


@pytest.fixture
def flask_app(analysis_results, manager):
    """Create an app whose external boundaries are fully injected."""
    return create_app(
        {
            "TESTING": True,
            "SESSION_FACTORY": DummySession,
            "ANALYSIS_RUNNER": lambda session: analysis_results,
            "SCRAPE_MANAGER": manager,
        }
    )


@pytest.fixture
def client(flask_app):
    return flask_app.test_client()


@pytest.fixture
def postgres_engine(monkeypatch):
    """Provide real storage only in a disposable PostgreSQL test database.

    Args:
        monkeypatch: Fixture restoring original model bindings afterward.

    Yields:
        An engine with an empty applicants table. Missing CI configuration
        fails rather than skipping the required database tests.
    """
    if not os.getenv("DATABASE_URL"):
        if os.getenv("REQUIRE_POSTGRES_TESTS") == "1":
            pytest.fail("Required PostgreSQL tests need DATABASE_URL")
        pytest.skip("Set DATABASE_URL to a disposable PostgreSQL *_test DB")
    url = models.database_url()
    if url.get_backend_name() != "postgresql" or not (
        url.database or ""
    ).endswith("_test"):
        pytest.fail("Refusing writes outside a PostgreSQL *_test database")
    engine = sqlalchemy.create_engine(url)
    factory = orm.sessionmaker(bind=engine, expire_on_commit=False)
    monkeypatch.setattr(models, "engine", engine)
    monkeypatch.setattr(models, "SessionLocal", factory)
    try:
        with engine.begin() as connection:
            connection.execute(sqlalchemy.text(load_data.CREATE_TABLE_SQL))
            connection.execute(sqlalchemy.text(
                "TRUNCATE TABLE applicants RESTART IDENTITY"
            ))
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def postgres_records():
    """Replace only network collection with fixed applicant source data."""
    return [
        {
            "program": "Computer Science, Example University",
            "date_added": "Sep 22, 2026",
            "url": "https://example.test/result/1",
            "status": "Accepted", "term": "Fall 2026",
            "citizenship": "International", "degree": "PhD", "gpa": 3.8,
            "llm_generated_university": "Example University",
        },
        {
            "program": "Mathematics, Example University",
            "date_added": "Sep 22, 2026",
            "url": "https://example.test/result/2",
            "status": "Rejected", "term": "Fall 2026",
            "citizenship": "American", "degree": "Masters", "gpa": 3.6,
            "llm_generated_university": "Example University",
        },
    ]
