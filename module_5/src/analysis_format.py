"""Shared numeric formatting for SQL, ORM, PDF, and Flask output."""

from __future__ import annotations

from decimal import Decimal


def format_count(value: object) -> str:
    """Format a required whole-number count.

    Args:
        value: Nonmissing value accepted by int, normally a SQL count.

    Returns:
        A decimal integer string with thousands separators.

    Raises:
        TypeError: The value cannot be converted to an integer.
        ValueError: The value has an invalid numeric representation.
        OverflowError: The value is infinite.
    """
    return f"{int(value):,}"


def format_decimal(value: object, suffix: str = "") -> str:
    """Format an average or percentage to exactly two decimal places.

    Args:
        value: Numeric value, numeric string, or None for a missing average.
        suffix: Text appended after a number, such as a percent sign.

    Returns:
        A two-decimal string with suffix, or N/A without suffix for None.

    Raises:
        decimal.InvalidOperation: The value is not a valid decimal string.
    """
    if value is None:
        return "N/A"
    return f"{Decimal(str(value)):.2f}{suffix}"


def format_difference(value: int) -> str:
    """Format a comparison difference with an explicit sign.

    Args:
        value: Signed integer difference between two applicant counts.

    Returns:
        A thousands-separated integer prefixed with + or -.
    """
    return f"{value:+,}"
