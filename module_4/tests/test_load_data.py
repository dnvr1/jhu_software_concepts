"""Focused tests for the Part 1 data-to-table mapping."""

from datetime import date, datetime
import json
from types import SimpleNamespace

import pytest

import load_data
from load_data import normalize_record, prepare_rows


pytestmark = pytest.mark.db


def source_record(**overrides):
    """Return the smallest representative cleaned source object."""
    record = {
        "program": "Computer Science, Example University",
        "comments": " ",
        "date_added": "Feb 12, 2026",
        "url": "https://www.thegradcafe.com/result/1",
        "status": "Accepted",
        "term": "Fall 2026",
        "citizenship": "International",
        "gpa": None,
        "gre": None,
        "gre_quantitative": 165,
        "gre_v": "159",
        "gre_aw": 4,
        "degree": "PhD",
        "llm-generated-program": "Computer Science",
        "llm-generated-university": "Example University",
    }
    record.update(overrides)
    return record


def test_normalize_record_maps_module_2_fields():
    """Hyphenated LLM keys and citizenship map to the SQL schema."""
    row = normalize_record(source_record())

    assert row == (
        "Computer Science, Example University",
        None,
        date(2026, 2, 12),
        "https://www.thegradcafe.com/result/1",
        "Accepted",
        "Fall 2026",
        "International",
        None,
        165.0,
        159.0,
        4.0,
        "PhD",
        "Computer Science",
        "Example University",
    )


def test_prepare_rows_deduplicates_by_url():
    """Repeated loader input cannot create repeated applicants."""
    records = [source_record(), source_record(status="Rejected")]

    rows, duplicate_count = prepare_rows(records)

    assert len(rows) == 1
    assert duplicate_count == 1


def test_missing_optional_scores_are_allowed():
    """An applicant need not supply any score fields."""
    row = normalize_record(
        source_record(
            gre_quantitative=None,
            gre_v=None,
            gre_aw=None,
        )
    )

    assert row[7:11] == (None, None, None, None)


def test_missing_url_is_rejected():
    """A stable URL is required for safe duplicate prevention."""
    with pytest.raises(ValueError, match="url is required"):
        normalize_record(source_record(url=None))


def test_scalar_normalizers_cover_dates_numbers_and_aliases():
    assert load_data.optional_text("  value  ") == "value"
    assert load_data.optional_text(" ") is None
    assert load_data.optional_date(datetime(2026, 2, 12, 9, 30)) == date(2026, 2, 12)
    assert load_data.optional_date(date(2026, 2, 12)) == date(2026, 2, 12)
    assert load_data.optional_date("2026-02-12") == date(2026, 2, 12)
    assert load_data.optional_date("") is None
    assert load_data.first_present({"a": " ", "b": 0}, "a", "b") == 0
    assert load_data.first_present({}, "missing") is None

    with pytest.raises(ValueError, match="must be numeric"):
        load_data.optional_float("unknown", "gpa")
    with pytest.raises(ValueError, match="must be finite"):
        load_data.optional_float(float("inf"), "gpa")
    with pytest.raises(ValueError, match="unsupported format"):
        load_data.optional_date("yesterday")


def test_read_records_and_positioned_validation_errors(tmp_path):
    source = tmp_path / "records.json"
    source.write_text(json.dumps([source_record()]), encoding="utf-8")
    assert load_data.read_records(source)[0]["status"] == "Accepted"

    source.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="JSON array"):
        load_data.read_records(source)

    with pytest.raises(ValueError, match="Record 1"):
        prepare_rows([source_record(gpa="not numeric")])


def test_connection_arguments_and_bounded_batches(monkeypatch):
    monkeypatch.setenv("PGHOST", "db.test")
    monkeypatch.setenv("PGPORT", "5433")
    monkeypatch.setenv("PGDATABASE", "course")
    monkeypatch.setenv("PGUSER", "student")

    assert load_data.connection_arguments() == {
        "host": "db.test",
        "port": 5433,
        "dbname": "course",
        "user": "student",
    }
    assert list(load_data.batches([(1,), (2,), (3,)], 2)) == [
        [(1,), (2,)],
        [(3,)],
    ]


class FakeCursor:
    def __init__(self, fetchall_values=None, fetchone_values=None):
        self.fetchall_values = list(fetchall_values or [])
        self.fetchone_values = list(fetchone_values or [])
        self.executed = []
        self.many = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute(self, query, parameters=None):
        self.executed.append((query, parameters))

    def executemany(self, query, rows):
        self.many.append((query, list(rows)))

    def fetchall(self):
        return self.fetchall_values.pop(0)

    def fetchone(self):
        return self.fetchone_values.pop(0)


class FakeConnection:
    def __init__(self, cursor):
        self._cursor = cursor

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def cursor(self):
        return self._cursor


def schema_rows(identity="YES"):
    return [
        (name, data_type, identity if name == "p_id" else "NO")
        for name, data_type in load_data.EXPECTED_SCHEMA.items()
    ]


def test_verify_schema_accepts_required_shape_and_rejects_drift():
    valid = FakeCursor(
        fetchall_values=[schema_rows(), [("p_id",)]],
        fetchone_values=[(3, 3)],
    )
    assert load_data.verify_schema(valid) == 3

    bad_schema = FakeCursor(fetchall_values=[[]])
    with pytest.raises(RuntimeError, match="required schema"):
        load_data.verify_schema(bad_schema)

    bad_identity = FakeCursor(fetchall_values=[schema_rows("NO")])
    with pytest.raises(RuntimeError, match="identity"):
        load_data.verify_schema(bad_identity)

    bad_primary_key = FakeCursor(
        fetchall_values=[schema_rows(), [("url",)]],
    )
    with pytest.raises(RuntimeError, match="primary key"):
        load_data.verify_schema(bad_primary_key)

    duplicates = FakeCursor(
        fetchall_values=[schema_rows(), [("p_id",)]],
        fetchone_values=[(3, 2)],
    )
    with pytest.raises(RuntimeError, match="duplicate URLs"):
        load_data.verify_schema(duplicates)


def test_connect_database_url_noninteractive_and_database_creation(monkeypatch, capsys):
    direct = object()
    connect_calls = []

    def connect(*args, **kwargs):
        connect_calls.append((args, kwargs))
        return direct

    monkeypatch.setenv("DATABASE_URL", "postgresql://example")
    monkeypatch.setattr(load_data.psycopg, "connect", connect)
    assert load_data.connect_database() is direct
    assert connect_calls[0][0] == ("postgresql://example",)

    monkeypatch.delenv("DATABASE_URL")
    monkeypatch.delenv("PGPASSWORD", raising=False)
    monkeypatch.setattr(load_data.sys, "stdin", SimpleNamespace(isatty=lambda: False))
    with pytest.raises(RuntimeError, match="Set PGPASSWORD"):
        load_data.connect_database()

    maintenance_cursor = FakeCursor(fetchone_values=[None])
    maintenance = FakeConnection(maintenance_cursor)
    final = object()
    calls = []

    def create_connect(*args, **kwargs):
        calls.append((args, kwargs))
        return maintenance if kwargs.get("autocommit") else final

    monkeypatch.setenv("PGPASSWORD", "test-password")
    monkeypatch.setattr(load_data.psycopg, "connect", create_connect)
    assert load_data.connect_database() is final
    assert "Created PostgreSQL database" in capsys.readouterr().out
    assert len(maintenance_cursor.executed) == 2


def test_load_rows_and_command_paths(monkeypatch, tmp_path, capsys):
    cursor = FakeCursor(
        fetchall_values=[schema_rows(), [("p_id",)]],
        fetchone_values=[(1,), (3,), (3, 3)],
    )
    monkeypatch.setattr(
        load_data, "connect_database", lambda: FakeConnection(cursor)
    )
    rows = [normalize_record(source_record(url=f"https://example/{n}")) for n in range(2)]
    assert load_data.load_rows(rows, 1) == (1, 3, 3)
    assert len(cursor.many) == 2

    source = tmp_path / "records.json"
    source.write_text(json.dumps([source_record()]), encoding="utf-8")
    monkeypatch.setattr(
        load_data,
        "parse_args",
        lambda: SimpleNamespace(file=source, batch_size=10),
    )
    monkeypatch.setattr(load_data, "load_rows", lambda rows, size: (0, 1, 1))
    assert load_data.main() == 0
    assert "Rows inserted: 1" in capsys.readouterr().out

    monkeypatch.setattr(load_data, "read_records", lambda path: (_ for _ in ()).throw(ValueError("bad input")))
    assert load_data.main() == 1
    assert "Load failed: bad input" in capsys.readouterr().err


def test_parse_args_rejects_nonpositive_batch(monkeypatch):
    monkeypatch.setattr(load_data.sys, "argv", ["load_data.py", "--batch-size", "5"])
    assert load_data.parse_args().batch_size == 5

    monkeypatch.setattr(load_data.sys, "argv", ["load_data.py", "--batch-size", "0"])
    with pytest.raises(SystemExit):
        load_data.parse_args()
