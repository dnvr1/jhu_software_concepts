"""SQLAlchemy 2.x mapping for the existing PostgreSQL applicants table."""

from __future__ import annotations

from datetime import date
import os

from sqlalchemy import Date, Float, Integer, Text, URL, create_engine
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    sessionmaker,
)


class Base(DeclarativeBase):
    """Declarative base for Module 3 database models."""


class Applicant(Base):
    """One GradCafe applicant entry in the existing applicants table.

    Attributes:
        p_id: Database-generated integer primary key.
        program: Original combined program and university text.
        comments: Optional applicant narrative.
        date_added: Source publication date, without time information.
        url: Required unique source URL used for deduplication.
        status: Source decision classification.
        term: Application term, such as Fall 2026.
        us_or_international: Reported nationality classification.
        gpa: Reported GPA; no scale conversion is performed.
        gre: Imported GRE field under the assignment's schema mapping.
        gre_v: Reported verbal GRE score.
        gre_aw: Reported analytical-writing GRE score.
        degree: Reported degree name.
        llm_generated_program: Optional locally standardized program name.
        llm_generated_university: Optional standardized university name.
    """

    __tablename__ = "applicants"

    p_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    program: Mapped[str | None] = mapped_column(Text)
    comments: Mapped[str | None] = mapped_column(Text)
    date_added: Mapped[date | None] = mapped_column(Date)
    url: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    status: Mapped[str | None] = mapped_column(Text)
    term: Mapped[str | None] = mapped_column(Text)
    us_or_international: Mapped[str | None] = mapped_column(Text)
    gpa: Mapped[float | None] = mapped_column(Float)
    gre: Mapped[float | None] = mapped_column(Float)
    gre_v: Mapped[float | None] = mapped_column(Float)
    gre_aw: Mapped[float | None] = mapped_column(Float)
    degree: Mapped[str | None] = mapped_column(Text)
    llm_generated_program: Mapped[str | None] = mapped_column(Text)
    llm_generated_university: Mapped[str | None] = mapped_column(Text)

    def __repr__(self) -> str:
        """Return a concise identifier useful during debugging."""
        return (
            f"Applicant(p_id={self.p_id!r}, "
            f"program={self.program!r}, status={self.status!r})"
        )


def database_url(password: str | None = None) -> URL:
    """Build a SQLAlchemy URL without hardcoding credentials.

    Args:
        password: Runtime password override for DB_*/PG* configuration.
            Ignored when DATABASE_URL is set.

    Returns:
        A URL using DATABASE_URL first, otherwise DB_* with PG* fallbacks.
        A plain postgresql driver name is upgraded to postgresql+psycopg.
        The returned object contains credentials and must not be logged.

    Raises:
        ValueError: The configured port is not an integer.
        sqlalchemy.exc.ArgumentError: DATABASE_URL cannot be parsed.
    """
    configured_url = os.getenv("DATABASE_URL")
    if configured_url:
        url = make_url(configured_url)
        if url.drivername == "postgresql":
            url = url.set(drivername="postgresql+psycopg")
        return url

    configured_password = (
        password
        if password is not None
        else os.getenv("DB_PASSWORD", os.getenv("PGPASSWORD"))
    )
    return URL.create(
        drivername="postgresql+psycopg",
        username=os.getenv("DB_USER", os.getenv("PGUSER", "gradcafe_app")),
        password=configured_password,
        host=os.getenv("DB_HOST", os.getenv("PGHOST", "localhost")),
        port=int(os.getenv("DB_PORT", os.getenv("PGPORT", "5432"))),
        database=os.getenv("DB_NAME", os.getenv("PGDATABASE", "gradcafe")),
    )


def make_engine(password: str | None = None) -> Engine:
    """Create a lazy Engine for the configured PostgreSQL database.

    Args:
        password: Optional runtime password forwarded to database_url.

    Returns:
        An Engine with pool_pre_ping enabled to detect stale connections.
        Construction alone does not authenticate or open a DB connection.
    """
    return create_engine(
        database_url(password),
        pool_pre_ping=True,
    )


engine = make_engine()
SessionLocal = sessionmaker(  # pylint: disable=invalid-name
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


def configure_database(
    password: str | None = None,
) -> tuple[Engine, sessionmaker]:
    """Reconfigure globals after securely obtaining runtime credentials.

    Call during startup, before creating the Flask app or serving requests;
    consumers holding the old session factory are not updated automatically.

    Args:
        password: Optional runtime password forwarded to make_engine.

    Returns:
        The replacement Engine and session factory, also assigned to the
        module globals after disposing of the previous connection pool.
    """
    global engine, SessionLocal  # pylint: disable=global-statement

    engine.dispose()
    engine = make_engine(password)
    SessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )
    return engine, SessionLocal
