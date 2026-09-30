"""Required Flask application factory and page-rendering tests."""

import pytest


pytestmark = pytest.mark.web


def test_factory_registers_required_routes(flask_app):
    rules = {rule.rule for rule in flask_app.url_map.iter_rules()}

    assert {"/analysis", "/pull-data", "/update-analysis"} <= rules


def test_analysis_page_renders_required_components(client):
    response = client.get("/analysis")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Analysis" in page
    assert "Pull Data" in page
    assert "Update Analysis" in page
    assert "Answer:" in page
    assert 'data-testid="pull-data-btn"' in page
    assert 'data-testid="update-analysis-btn"' in page
