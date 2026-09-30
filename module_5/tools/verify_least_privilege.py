"""Provision and verify a restricted role in a disposable *_test database.

Run after pytest in a fresh CI PostgreSQL service. Never targets the home DB.
The random password is process-local and is never printed or persisted.
"""

import os
import secrets

import psycopg
from psycopg import sql
from sqlalchemy.engine import make_url


def main():
    admin_url = make_url(os.environ["DATABASE_URL"])
    if not (admin_url.database or "").endswith("_test"):
        raise RuntimeError("Only a disposable *_test database is allowed")
    role = "gradcafe_app"
    password = secrets.token_urlsafe(32)
    admin_dsn = admin_url.set(drivername="postgresql").render_as_string(
        hide_password=False
    )
    with psycopg.connect(admin_dsn, autocommit=True) as connection:
        connection.execute(
            sql.SQL("CREATE ROLE {} LOGIN PASSWORD {} NOSUPERUSER NOCREATEDB "
                    "NOCREATEROLE NOREPLICATION NOBYPASSRLS").format(
                sql.Identifier(role), sql.Literal(password)
            )
        )
        connection.execute(
            sql.SQL("GRANT CONNECT ON DATABASE {} TO {}").format(
                sql.Identifier(admin_url.database), sql.Identifier(role)
            )
        )
        connection.execute("GRANT USAGE ON SCHEMA public TO gradcafe_app")
        connection.execute("GRANT SELECT, INSERT ON public.applicants TO gradcafe_app")
        connection.execute("GRANT USAGE ON SEQUENCE public.applicants_p_id_seq TO gradcafe_app")

    app_url = admin_url.set(username=role, password=password)
    app_dsn = app_url.set(drivername="postgresql").render_as_string(hide_password=False)
    os.environ["DATABASE_URL"] = app_url.render_as_string(hide_password=False)
    from app import create_app
    from query_data import lookup_applicants
    from scrape_refresh import insert_new_records

    with psycopg.connect(app_dsn, autocommit=True) as connection:
        attrs = connection.execute(
            "SELECT rolsuper, rolcreatedb, rolcreaterole, rolreplication, rolbypassrls "
            "FROM pg_roles WHERE rolname = current_user LIMIT 1"
        ).fetchone()
        assert attrs == (False,) * 5, attrs
        owner = connection.execute(
            "SELECT pg_has_role(current_user, relowner, 'MEMBER') "
            "FROM pg_class WHERE oid = 'public.applicants'::regclass LIMIT 1"
        ).fetchone()[0]
        assert owner is False
        with connection.cursor() as cursor:
            assert lookup_applicants(cursor, "status", "Accepted' OR 1=1 --", 999999) == []
            assert len(lookup_applicants(cursor, "status", "Accepted", 1)) <= 1
        for statement in (
            "CREATE TABLE public.forbidden_table (id integer)",
            "ALTER TABLE public.applicants ADD COLUMN forbidden integer",
            "DROP TABLE public.applicants",
            "UPDATE public.applicants SET status = status WHERE false",
            "DELETE FROM public.applicants WHERE false",
            "TRUNCATE public.applicants",
        ):
            try:
                # Roll back even if an unexpectedly permitted action succeeds.
                with connection.transaction(force_rollback=True):
                    connection.execute(statement)
            except psycopg.errors.InsufficientPrivilege:
                print("DENIED as expected:", statement.split()[0])
            else:
                raise AssertionError("Unexpected permission: " + statement)

    record = {"program": "Security Test, Example University",
              "date_added": "Sep 30, 2026", "url": "https://example.test/least-privilege",
              "status": "Accepted", "term": "Fall 2026", "degree": "Masters"}
    assert insert_new_records([record]) == (1, 0)
    assert insert_new_records([record]) == (0, 0)
    client = create_app({"TESTING": True}).test_client()
    assert client.get("/analysis").status_code == 200
    assert client.get("/analysis?updated=1%27%20OR%201=1--").status_code == 200
    assert client.post("/update-analysis").status_code == 200
    print("PASS: gradcafe_app is non-superuser, has no owner membership, and cannot perform DDL or destructive writes.")
    print("PASS: SELECT, INSERT, sequence usage, duplicate handling, bound malicious input, and Flask analysis/update work.")
    print("Scope: disposable CI/test database only; the home gradcafe database was not changed.")


if __name__ == "__main__":
    main()
