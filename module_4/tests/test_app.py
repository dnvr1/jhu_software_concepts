"""Flask page tests using deterministic ORM result fixtures."""

import ast
from decimal import Decimal
from pathlib import Path

import app as app_module
import pytest


pytestmark = [pytest.mark.web, pytest.mark.buttons, pytest.mark.analysis]


class DummySession:
    """Minimal context manager used in place of a database Session."""

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False


class DummyScrapeManager:
    """Deterministic status provider for Flask route tests."""

    def __init__(self, status="idle"):
        self.start_calls = 0
        self.status = status

    def snapshot(self):
        return {
            "status": self.status,
            "message": "Test scrape status.",
            "records_inserted": 0,
        }

    def start(self):
        self.start_calls += 1
        self.status = "running"
        return True, self.snapshot()


def sample_results():
    """Return the verified database values expected by the template."""
    return {
        "total_rows": 30_006,
        "question_1": 29_586,
        "question_2": Decimal("46.34"),
        "question_3": (
            Decimal("3.80"),
            Decimal("260.47"),
            Decimal("161.53"),
            Decimal("8.34"),
        ),
        "question_4": Decimal("3.79"),
        "question_5": Decimal("47.92"),
        "question_6": Decimal("3.79"),
        "question_7": 8,
        "question_8": 28,
        "question_9": 28,
        "question_10": [
            ("American", 15_449, Decimal("38.53")),
            ("International", 13_499, Decimal("34.59")),
        ],
        "question_11": [
            ("Stanford University", 718, Decimal("19.08")),
            (
                "University of California, Berkeley",
                615,
                Decimal("25.20"),
            ),
            ("Yale University", 573, Decimal("14.14")),
            ("Princeton University", 556, Decimal("20.86")),
            ("University of Washington", 547, Decimal("27.97")),
        ],
    }


def test_analysis_page_displays_all_required_results(monkeypatch):
    monkeypatch.setattr(app_module.models, "SessionLocal", DummySession)
    monkeypatch.setattr(
        app_module,
        "run_complete_analysis",
        lambda session: sample_results(),
    )
    monkeypatch.setattr(app_module, "scrape_manager", DummyScrapeManager())
    application = app_module.create_app({"TESTING": True})

    response = application.test_client().get("/")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    for expected in (
        "29,586",
        "46.34%",
        "260.47",
        "47.92%",
        "Original fields",
        "LLM-generated fields",
        "American",
        "International",
        "Stanford University",
        "University of Washington",
        "Pull Data",
        "newly submitted application results",
    ):
        assert expected in page


def test_flask_reads_do_not_use_raw_sql_or_psycopg():
    source = Path(app_module.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)

    imported_names = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    called_attributes = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }

    assert "psycopg" not in imported_names
    assert "text" not in imported_names
    assert "cursor" not in called_attributes
    assert "SessionLocal" in source
    assert "run_complete_analysis" in source


def test_pull_data_route_starts_one_background_job(monkeypatch):
    manager = DummyScrapeManager()
    monkeypatch.setattr(app_module, "scrape_manager", manager)
    application = app_module.create_app({"TESTING": True})

    response = application.test_client().post("/pull-data")

    assert response.status_code == 202
    assert response.get_json()["ok"] is True
    assert manager.start_calls == 1


def test_scrape_status_route_returns_current_state(monkeypatch):
    manager = DummyScrapeManager("succeeded")
    monkeypatch.setattr(app_module, "scrape_manager", manager)
    application = app_module.create_app({"TESTING": True})

    response = application.test_client().get("/scrape-status")

    assert response.status_code == 200
    assert response.get_json()["status"] == "succeeded"


def test_update_analysis_requeries_without_starting_scrape(monkeypatch):
    manager = DummyScrapeManager("idle")
    query_calls = []
    monkeypatch.setattr(app_module.models, "SessionLocal", DummySession)
    monkeypatch.setattr(app_module, "scrape_manager", manager)
    monkeypatch.setattr(
        app_module,
        "run_complete_analysis",
        lambda session: query_calls.append(session) or sample_results(),
    )
    application = app_module.create_app({"TESTING": True})

    response = application.test_client().get("/?updated=1")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert len(query_calls) == 1
    assert manager.start_calls == 0
    assert "latest records in PostgreSQL" in page
    assert "Update Analysis" in page


def test_update_analysis_reports_active_scrape_without_interrupting(monkeypatch):
    manager = DummyScrapeManager("running")
    monkeypatch.setattr(app_module.models, "SessionLocal", DummySession)
    monkeypatch.setattr(app_module, "scrape_manager", manager)
    monkeypatch.setattr(
        app_module,
        "run_complete_analysis",
        lambda session: sample_results(),
    )
    application = app_module.create_app({"TESTING": True})

    response = application.test_client().get("/?updated=1")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert manager.start_calls == 0
    assert "New data is still being retrieved" in page
    assert "Pulling data" in page
    assert 'data-active-scrape="true"' in page


def test_analysis_and_update_return_service_unavailable_on_query_error():
    manager = DummyScrapeManager("idle")

    def fail(_session):
        raise RuntimeError("synthetic database failure")

    application = app_module.create_app(
        {
            "TESTING": True,
            "SESSION_FACTORY": DummySession,
            "ANALYSIS_RUNNER": fail,
            "SCRAPE_MANAGER": manager,
        }
    )
    client = application.test_client()

    page_response = client.get("/analysis")
    update_response = client.post("/update-analysis")

    assert page_response.status_code == 503
    assert "could not be loaded" in page_response.get_data(as_text=True)
    assert update_response.status_code == 503
    assert update_response.get_json() == {"busy": False, "ok": False}
