"""Required endpoint and observable busy-state tests."""

import pytest


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

    response = flask_app.test_client().post(path)

    assert response.status_code == 409
    assert response.get_json()["busy"] is True
