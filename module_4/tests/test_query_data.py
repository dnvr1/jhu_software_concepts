"""Unit tests for required raw-SQL output formatting."""

from decimal import Decimal
from contextlib import nullcontext

import pytest

from analysis_format import format_count, format_decimal, format_difference
import query_data


pytestmark = [pytest.mark.analysis, pytest.mark.db]


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


class QueryCursor:
    def __init__(self, one_rows=None, all_rows=None):
        self.one_rows = list(one_rows or [])
        self.all_rows = list(all_rows or [])
        self.queries = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute(self, query):
        self.queries.append(query)

    def fetchone(self):
        return self.one_rows.pop(0)

    def fetchall(self):
        return self.all_rows.pop(0)


class QueryConnection:
    def __init__(self, cursor):
        self._cursor = cursor
        self.read_only = False

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def cursor(self):
        return self._cursor


def complete_raw_results():
    return {
        "question_1": 12,
        "question_2": Decimal("39.28"),
        "question_3": (Decimal("3.8"), 165, 159, Decimal("4.5")),
        "question_4": Decimal("3.7"),
        "question_5": Decimal("50"),
        "question_6": Decimal("3.9"),
        "question_7": 2,
        "question_8": 3,
        "question_9": 4,
        "question_10": [("American", 2, Decimal("50"))],
        "question_11": [("Example University", 2, Decimal("50"))],
    }


def test_raw_query_helpers_and_complete_execution():
    expected = complete_raw_results()
    cursor = QueryCursor(
        one_rows=[
            (expected["question_1"],),
            (expected["question_2"],),
            expected["question_3"],
            (expected["question_4"],),
            (expected["question_5"],),
            (expected["question_6"],),
            (expected["question_7"],),
            (expected["question_8"],),
            (expected["question_9"],),
        ],
        all_rows=[expected["question_10"], expected["question_11"]],
    )
    connection = QueryConnection(cursor)

    assert query_data.run_analysis(connection) == expected
    assert connection.read_only is True
    assert len(cursor.queries) == 11


def test_fetch_one_rejects_missing_result():
    cursor = QueryCursor(one_rows=[None])
    with pytest.raises(RuntimeError, match="no result row"):
        query_data.fetch_one(cursor, "SELECT 1")


def test_raw_analysis_printing_and_main_paths(monkeypatch, capsys):
    results = complete_raw_results()
    query_data.print_analysis(results)
    output = capsys.readouterr().out
    assert "Question 11" in output
    assert "39.28%" in output
    assert "Difference: +1" in output

    connection = QueryConnection(QueryCursor())
    monkeypatch.setattr(query_data, "connect_database", lambda: connection)
    monkeypatch.setattr(query_data, "run_analysis", lambda value: results)
    assert query_data.main() == 0

    def fail():
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(query_data, "connect_database", fail)
    assert query_data.main() == 1
    assert "database unavailable" in capsys.readouterr().err
