"""Tests for the SQLAlchemy Applicant mapping without a database connection."""

from sqlalchemy import Date, Float, Integer, Text
import pytest

import models


pytestmark = pytest.mark.db


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


def test_applicant_repr_and_database_url_sources(monkeypatch):
    applicant = models.Applicant(
        p_id=7,
        program="Computer Science",
        status="Accepted",
        url="https://example/7",
    )
    assert repr(applicant) == (
        "Applicant(p_id=7, program='Computer Science', status='Accepted')"
    )

    monkeypatch.setenv("DATABASE_URL", "postgresql://student:secret@db.test/course")
    assert models.database_url().drivername == "postgresql+psycopg"

    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://student:secret@db.test/course",
    )
    assert models.database_url().database == "course"

    monkeypatch.delenv("DATABASE_URL")
    monkeypatch.setenv("PGUSER", "student")
    monkeypatch.setenv("PGHOST", "db.test")
    monkeypatch.setenv("PGPORT", "5433")
    monkeypatch.setenv("PGDATABASE", "course")
    monkeypatch.setenv("PGPASSWORD", "from-env")
    url = models.database_url("explicit")
    assert (url.username, url.host, url.port, url.database) == (
        "student",
        "db.test",
        5433,
        "course",
    )
    assert url.password == "explicit"


def test_make_engine_and_reconfiguration(monkeypatch):
    created = object()
    calls = []

    def create_engine(url, **options):
        calls.append((url, options))
        return created

    monkeypatch.setattr(models, "create_engine", create_engine)
    assert models.make_engine("pw") is created
    assert calls[0][1] == {"pool_pre_ping": True}

    class OldEngine:
        def __init__(self):
            self.disposed = False

        def dispose(self):
            self.disposed = True

    old = OldEngine()
    replacement = object()
    monkeypatch.setattr(models, "engine", old)
    monkeypatch.setattr(models, "make_engine", lambda password=None: replacement)
    engine, factory = models.configure_database("pw")

    assert old.disposed is True
    assert engine is replacement
    assert factory.kw["bind"] is replacement
