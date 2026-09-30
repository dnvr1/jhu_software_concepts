"""Deterministic pull-to-update-to-render integration test."""

from decimal import Decimal

import pytest

from app import create_app
from conftest import DummySession


pytestmark = pytest.mark.integration


class InMemoryPullManager:
    """Fake scraper/loader boundary with URL-based idempotency."""

    def __init__(self, rows):
        self.source_rows = rows
        self.rows = {}
        self.status = "idle"

    def snapshot(self):
        return {
            "status": self.status,
            "message": "Integration pull complete.",
            "records_inserted": len(self.rows),
        }

    def start(self):
        if self.status == "running":
            return False, self.snapshot()
        self.status = "running"
        self.rows.update({row["url"]: row for row in self.source_rows})
        self.status = "succeeded"
        return True, self.snapshot()


def test_pull_update_render_and_overlapping_pull_are_consistent():
    records = [
        {"url": "one", "status": "Accepted"},
        {"url": "two", "status": "Rejected"},
    ]
    manager = InMemoryPullManager(records)

    def analyze(session):
        total = len(manager.rows)
        return {
            "total_rows": total,
            "question_1": total,
            "question_2": Decimal("50.00"),
            "question_3": (None, None, None, None),
            "question_4": None,
            "question_5": Decimal("50.00"),
            "question_6": None,
            "question_7": 0,
            "question_8": 0,
            "question_9": 0,
            "question_10": [("American", 1, Decimal("50.00"))],
            "question_11": [("Example University", 1, Decimal("50.00"))],
        }

    application = create_app(
        {
            "TESTING": True,
            "SESSION_FACTORY": DummySession,
            "ANALYSIS_RUNNER": analyze,
            "SCRAPE_MANAGER": manager,
        }
    )
    client = application.test_client()

    assert client.post("/pull-data").status_code == 202
    assert client.post("/pull-data").status_code == 202
    assert len(manager.rows) == 2
    assert client.post("/update-analysis").status_code == 200
    page = client.get("/analysis").get_data(as_text=True)
    assert "Answer: 2" in page
    assert "50.00%" in page
