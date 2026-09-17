"""Unit tests for required raw-SQL output formatting."""

from decimal import Decimal

from analysis_format import format_count, format_decimal, format_difference


def test_count_formatting_uses_whole_numbers():
    assert format_count(19290) == "19,290"


def test_decimal_formatting_uses_two_places():
    assert format_decimal(Decimal("50.086"), "%") == "50.09%"
    assert format_decimal(Decimal("3.7")) == "3.70"


def test_missing_average_is_readable():
    assert format_decimal(None) == "N/A"


def test_difference_includes_explicit_sign():
    assert format_difference(3) == "+3"
    assert format_difference(-2) == "-2"
