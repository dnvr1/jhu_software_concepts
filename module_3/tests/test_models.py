"""Tests for the SQLAlchemy Applicant mapping without a database connection."""

from sqlalchemy import Date, Float, Integer, Text

import models


EXPECTED_COLUMNS = [
    "p_id",
    "program",
    "comments",
    "date_added",
    "url",
    "status",
    "term",
    "us_or_international",
    "gpa",
    "gre",
    "gre_v",
    "gre_aw",
    "degree",
    "llm_generated_program",
    "llm_generated_university",
]


def test_applicant_maps_the_required_existing_table():
    assert models.Applicant.__tablename__ == "applicants"
    assert list(models.Applicant.__table__.columns.keys()) == EXPECTED_COLUMNS
    assert list(models.Base.metadata.tables) == ["applicants"]


def test_applicant_uses_the_required_primary_key_and_types():
    table = models.Applicant.__table__

    assert [column.name for column in table.primary_key] == ["p_id"]
    assert isinstance(table.c.p_id.type, Integer)
    assert isinstance(table.c.program.type, Text)
    assert isinstance(table.c.comments.type, Text)
    assert isinstance(table.c.date_added.type, Date)
    assert isinstance(table.c.url.type, Text)
    assert isinstance(table.c.gpa.type, Float)
    assert isinstance(table.c.gre.type, Float)
    assert isinstance(table.c.gre_v.type, Float)
    assert isinstance(table.c.gre_aw.type, Float)


def test_url_is_required_and_unique_in_the_mapping():
    url_column = models.Applicant.__table__.c.url

    assert url_column.nullable is False
    assert url_column.unique is True


def test_engine_and_session_use_postgresql_psycopg():
    assert models.engine.url.drivername == "postgresql+psycopg"
    assert models.SessionLocal.kw["bind"] is models.engine
    assert models.SessionLocal.kw["autoflush"] is False
    assert models.SessionLocal.kw["expire_on_commit"] is False
