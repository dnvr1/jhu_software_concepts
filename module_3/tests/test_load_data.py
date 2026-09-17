"""Focused tests for the Part 1 data-to-table mapping."""

from datetime import date

import pytest

from load_data import normalize_record, prepare_rows


def source_record(**overrides):
    """Return the smallest representative cleaned source object."""
    record = {
        "program": "Computer Science, Example University",
        "comments": " ",
        "date_added": "Feb 12, 2026",
        "url": "https://www.thegradcafe.com/result/1",
        "status": "Accepted",
        "term": "Fall 2026",
        "citizenship": "International",
        "gpa": None,
        "gre": None,
        "gre_quantitative": 165,
        "gre_v": "159",
        "gre_aw": 4,
        "degree": "PhD",
        "llm-generated-program": "Computer Science",
        "llm-generated-university": "Example University",
    }
    record.update(overrides)
    return record


def test_normalize_record_maps_module_2_fields():
    """Hyphenated LLM keys and citizenship map to the SQL schema."""
    row = normalize_record(source_record())

    assert row == (
        "Computer Science, Example University",
        None,
        date(2026, 2, 12),
        "https://www.thegradcafe.com/result/1",
        "Accepted",
        "Fall 2026",
        "International",
        None,
        165.0,
        159.0,
        4.0,
        "PhD",
        "Computer Science",
        "Example University",
    )


def test_prepare_rows_deduplicates_by_url():
    """Repeated loader input cannot create repeated applicants."""
    records = [source_record(), source_record(status="Rejected")]

    rows, duplicate_count = prepare_rows(records)

    assert len(rows) == 1
    assert duplicate_count == 1


def test_missing_optional_scores_are_allowed():
    """An applicant need not supply any score fields."""
    row = normalize_record(
        source_record(
            gre_quantitative=None,
            gre_v=None,
            gre_aw=None,
        )
    )

    assert row[7:11] == (None, None, None, None)


def test_missing_url_is_rejected():
    """A stable URL is required for safe duplicate prevention."""
    with pytest.raises(ValueError, match="url is required"):
        normalize_record(source_record(url=None))
