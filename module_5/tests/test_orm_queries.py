"""Guardrails for the required SQLAlchemy-only query implementation."""

import ast
from decimal import Decimal
from pathlib import Path

from sqlalchemy.sql import Select
import pytest

import orm_queries


pytestmark = [pytest.mark.analysis, pytest.mark.db]


def test_all_required_orm_statements_are_select_objects():
    statements = orm_queries.build_statements()

    assert set(statements) == {
        "question_1",
        "question_4",
        "question_5",
        "question_8",
        "question_9",
        "question_10",
    }
    assert all(isinstance(statement, Select) for statement in statements.values())


def test_orm_file_does_not_use_raw_sql_or_psycopg_cursors():
    source = Path(orm_queries.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)

    imported_names = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    called_names = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    called_attributes = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }

    assert "psycopg" not in imported_names
    assert "text" not in imported_names
    assert "text" not in called_names
    assert "cursor" not in called_attributes


def test_original_question_is_grouped_and_ordered():
    statement = orm_queries.question_10_statement()

    assert len(statement._group_by_clauses) == 1
    assert len(statement._order_by_clauses) == 1


class ResultRows:
    def __init__(self, rows):
        self.rows = rows

    def all(self):
        return self.rows

    def one(self):
        return self.rows


class FakeSession:
    def __init__(self):
        self.scalar_values = iter([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        self.execute_values = iter(
            [
                ResultRows([("American", 1, Decimal("50"))]),
                ResultRows((Decimal("3.8"), 165, 159, Decimal("4.5"))),
                ResultRows([("Example University", 1, Decimal("50"))]),
            ]
        )

    def scalar(self, statement):
        return next(self.scalar_values)

    def execute(self, statement):
        return next(self.execute_values)


def test_all_complete_statements_and_execution_paths():
    statements = orm_queries.build_complete_statements()
    assert set(statements) == {f"question_{number}" for number in range(1, 12)}

    results = orm_queries.run_complete_analysis(FakeSession())
    assert results["question_1"] == 1
    assert results["question_10"][0][0] == "American"
    assert results["question_3"][0] == Decimal("3.8")
    assert results["total_rows"] == 9


def test_runtime_password_printing_and_main(monkeypatch, capsys):
    monkeypatch.setenv("DATABASE_URL", "postgresql://configured")
    assert orm_queries.runtime_password() is None

    monkeypatch.delenv("DATABASE_URL")
    monkeypatch.setenv("PGPASSWORD", "secret")
    assert orm_queries.runtime_password() == "secret"

    monkeypatch.delenv("PGPASSWORD")
    monkeypatch.setattr(orm_queries.getpass, "getpass", lambda prompt: "typed")
    assert orm_queries.runtime_password() == "typed"

    results = {
        "question_1": 1,
        "question_4": Decimal("3.7"),
        "question_5": Decimal("50"),
        "question_8": 2,
        "question_9": 3,
        "question_10": [("American", 2, Decimal("50"))],
    }
    orm_queries.print_analysis(results)
    assert "Difference: +1" in capsys.readouterr().out

    class SessionContext:
        def __enter__(self):
            return object()

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(
        orm_queries.models,
        "configure_database",
        lambda password: (object(), SessionContext),
    )
    monkeypatch.setattr(orm_queries, "run_analysis", lambda session: results)
    assert orm_queries.main() == 0

    monkeypatch.setattr(
        orm_queries.models,
        "configure_database",
        lambda password: (_ for _ in ()).throw(RuntimeError("offline")),
    )
    assert orm_queries.main() == 1
    assert "offline" in capsys.readouterr().err
