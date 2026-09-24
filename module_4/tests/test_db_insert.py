"""Required mapping, uniqueness, and query-contract tests."""

import pytest

from scrape_refresh import prepare_mappings


pytestmark = pytest.mark.db


def _record(url):
    return {
        "url": url,
        "program": "Computer Science, Johns Hopkins University",
        "date_added": "Sep 22, 2026",
        "status": "Accepted",
        "term": "Fall 2027",
        "citizenship": "American",
        "degree": "PhD",
    }


def test_required_fields_are_mapped_and_duplicate_urls_are_rejected():
    mappings, rejected = prepare_mappings(
        [_record("https://example.test/result/1"), _record("https://example.test/result/1")]
    )

    assert len(mappings) == 1
    assert rejected == 1
    assert all(mappings[0][key] is not None for key in ("url", "program", "date_added"))


def test_analysis_query_contract_contains_template_keys(analysis_results):
    expected = {"total_rows", *(f"question_{number}" for number in range(1, 12))}

    assert expected <= analysis_results.keys()
