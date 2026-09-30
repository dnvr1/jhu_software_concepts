"""Shared numeric formatting for SQL, ORM, PDF, and Flask output."""

from __future__ import annotations

from decimal import Decimal


def format_count(value: object) -> str:
    """Format a required whole-number count."""
    return f"{int(value):,}"


def format_decimal(value: object, suffix: str = "") -> str:
    """Format an average or percentage to exactly two decimal places."""
    if value is None:
        return "N/A"
    return f"{Decimal(str(value)):.2f}{suffix}"


def format_difference(value: int) -> str:
    """Format a comparison difference with an explicit sign."""
    return f"{value:+,}"
