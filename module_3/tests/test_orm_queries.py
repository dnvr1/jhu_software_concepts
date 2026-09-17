"""Guardrails for the required SQLAlchemy-only query implementation."""

import ast
from pathlib import Path

from sqlalchemy.sql import Select

import orm_queries


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
