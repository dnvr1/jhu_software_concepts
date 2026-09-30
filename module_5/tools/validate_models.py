"""Validate the SQLAlchemy model against the live applicants table."""

from __future__ import annotations

import getpass
import os
import sys

from sqlalchemy import func, inspect, select
from sqlalchemy.exc import SQLAlchemyError

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


def runtime_password() -> str | None:
    """Use the environment or request a password without echoing it."""
    if os.getenv("DATABASE_URL"):
        return None
    password = os.getenv("PGPASSWORD")
    if password is not None:
        return password
    return getpass.getpass(
        f"Password for PostgreSQL user {os.getenv('PGUSER', 'postgres')}: "
    )


def validate() -> None:
    """Compare mapped metadata to PostgreSQL and query through a Session."""
    engine, session_factory = models.configure_database(runtime_password())
    inspector = inspect(engine)

    live_columns = [
        column["name"] for column in inspector.get_columns("applicants")
    ]
    if live_columns != EXPECTED_COLUMNS:
        raise RuntimeError(
            "Applicant model columns do not match the live applicants table"
        )

    primary_key = inspector.get_pk_constraint("applicants")[
        "constrained_columns"
    ]
    if primary_key != ["p_id"]:
        raise RuntimeError("The live applicants primary key is not p_id")

    with session_factory() as session:
        row_count = session.scalar(
            select(func.count(models.Applicant.p_id))
        )
        sample = session.scalar(
            select(models.Applicant).order_by(models.Applicant.p_id).limit(1)
        )

    if row_count < 30_000:
        raise RuntimeError(
            f"Expected at least 30,000 applicants, found {row_count}"
        )
    if not isinstance(sample, models.Applicant):
        raise RuntimeError("The ORM did not return an Applicant object")

    print("SQLAlchemy model validation: passed")
    print(f"Engine dialect and driver: {engine.dialect.name}+{engine.driver}")
    print(f"Mapped table: {models.Applicant.__tablename__}")
    print(f"Mapped columns: {len(models.Applicant.__table__.columns)}")
    print(f"Primary key: {primary_key[0]}")
    print(f"Applicant rows through ORM Session: {row_count:,}")
    print(f"Sample object type: {type(sample).__name__}")


def main() -> int:
    """Run live validation with a concise failure message."""
    try:
        validate()
    except (RuntimeError, ValueError, SQLAlchemyError) as error:
        print(f"Model validation failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
