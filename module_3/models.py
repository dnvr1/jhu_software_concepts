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
    """One GradCafe applicant entry in the existing applicants table."""

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
    """Build a SQLAlchemy URL without exposing credentials in source code."""
    configured_url = os.getenv("DATABASE_URL")
    if configured_url:
        url = make_url(configured_url)
        if url.drivername == "postgresql":
            url = url.set(drivername="postgresql+psycopg")
        return url

    configured_password = (
        password if password is not None else os.getenv("PGPASSWORD")
    )
    return URL.create(
        drivername="postgresql+psycopg",
        username=os.getenv("PGUSER", "postgres"),
        password=configured_password,
        host=os.getenv("PGHOST", "localhost"),
        port=int(os.getenv("PGPORT", "5432")),
        database=os.getenv("PGDATABASE", "gradcafe"),
    )


def make_engine(password: str | None = None) -> Engine:
    """Create a production-style Engine for the configured PostgreSQL DB."""
    return create_engine(
        database_url(password),
        pool_pre_ping=True,
    )


engine = make_engine()
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


def configure_database(
    password: str | None = None,
) -> tuple[Engine, sessionmaker]:
    """Reconfigure globals after securely obtaining runtime credentials."""
    global engine, SessionLocal

    engine.dispose()
    engine = make_engine(password)
    SessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )
    return engine, SessionLocal
