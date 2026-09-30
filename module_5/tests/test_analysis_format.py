"""Required labels and exact percentage-formatting checks."""

import re

import pytest


pytestmark = pytest.mark.analysis


def test_answers_are_labeled_and_percentages_have_two_decimals(client):
    page = client.get("/analysis").get_data(as_text=True)
    percentages = re.findall(r"\b\d+\.\d+%", page)

    assert "Answer:" in page
    assert "39.28%" in percentages
    assert percentages
    assert all(re.fullmatch(r"\d+\.\d{2}%", value) for value in percentages)
