"""Required endpoint and observable busy-state tests."""

import pytest
from unittest import mock


pytestmark = pytest.mark.buttons


def test_pull_data_starts_loader(client, manager):
    response = client.post("/pull-data")

    assert response.status_code == 202
    assert response.get_json()["ok"] is True
    assert manager.start_calls == 1


def test_update_analysis_succeeds_when_idle(client):
    response = client.post("/update-analysis")

    assert response.status_code == 200
    assert response.get_json()["ok"] is True


@pytest.mark.parametrize("path", ["/pull-data", "/update-analysis"])
def test_busy_state_rejects_button_requests(flask_app, manager, path):
    manager.status = "running"
    before = manager.snapshot()
    sessions = mock.Mock(side_effect=AssertionError("DB accessed"))
    analyzer = mock.Mock(side_effect=AssertionError("Analysis updated"))
    flask_app.config.update(
        SESSION_FACTORY=sessions, ANALYSIS_RUNNER=analyzer
    )

    response = flask_app.test_client().post(path)

    assert response.status_code == 409
    assert response.get_json()["busy"] is True
    sessions.assert_not_called()
    analyzer.assert_not_called()
    assert manager.snapshot() == before
    assert manager.start_calls == (1 if path == "/pull-data" else 0)
