# Phase 5: SQLAlchemy Model Validation

Validated on September 15, 2026 against the existing PostgreSQL 17
`gradcafe` database.

```text
SQLAlchemy model validation: passed
Engine dialect and driver: postgresql+psycopg
Mapped table: applicants
Mapped columns: 15
Primary key: p_id
Applicant rows through ORM Session: 30,000
Sample object type: Applicant
```

The declarative metadata contains only the `applicants` table. The validation
does not call `create_all()` or create a second copy of the data. It inspects
the live table structure and retrieves the existing rows through the
SQLAlchemy `Applicant` model and `SessionLocal` configuration.

Automated model tests verify the table name, column order, SQLAlchemy types,
primary key, URL constraint metadata, PostgreSQL psycopg driver, and Session
settings without requiring a database connection during import.
