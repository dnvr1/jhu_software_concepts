"""Shared deterministic doubles for the Module 4 test suite."""

from decimal import Decimal

import pytest

from app import create_app


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
