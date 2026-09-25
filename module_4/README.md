# Module 4: Testing and Documentation

Student: Denver Clarke (`dclar106`)

Course: EN.605.256, Modern Software Concepts in Python

Repository: `git@github.com:dnvr1/jhu_software_concepts.git`

This directory extends the Module 3 GradCafe analytics application with a
deterministic Pytest suite, explicit Flask dependency injection, CI, and
Sphinx documentation. The application code lives in `src/`; all tests live in
`tests/`.

## Setup

Python 3.10 or newer and PostgreSQL are required.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:DATABASE_URL = "postgresql+psycopg://postgres:password@localhost:5432/gradcafe"
```

Do not commit database passwords or `.env` files. `DATABASE_URL` may be
replaced by `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, and `PGPASSWORD`.

## Run the application

```powershell
.\.venv\Scripts\python.exe src\run_flask.py
```

Open `http://127.0.0.1:5000/analysis`. The page includes stable
`data-testid="pull-data-btn"` and `data-testid="update-analysis-btn"`
selectors. Pulls are idempotent by source URL, and requests made while a pull
is active receive HTTP 409.

## Run tests

The tests use injected fakes at external boundaries and never scrape the live
site.

```powershell
.\.venv\Scripts\python.exe -m pytest -m "web or buttons or analysis or db or integration"
```

Coverage is enforced at 100% by `pytest.ini`. The committed terminal result is
recorded in `coverage_summary.txt`. When `DATABASE_URL` names a database ending
in `_test`, the suite also runs its PostgreSQL-backed insert and idempotency
test; GitHub Actions supplies this database automatically.

The workflow passed on commit `3af0dee`: [verified GitHub Actions run](https://github.com/dnvr1/jhu_software_concepts/actions/runs/36050953484).
The required green-run evidence is saved as `actions_success.png`.

## Build documentation

```powershell
.\.venv\Scripts\python.exe -m sphinx -W --keep-going -b html docs docs\_build\html
```

Open `docs/_build/html/index.html` locally. The generated HTML is committed
under `docs/_build/html/` as a submission artifact. The published Read the
Docs URL is
[dnvr1-gradcafe-module4.readthedocs.io](https://dnvr1-gradcafe-module4.readthedocs.io/en/latest/).

## Project layout

```text
module_4/
|-- src/                 Flask, ETL, database, and analysis modules
|-- tests/               marked unit and integration tests
|-- docs/                Sphinx source
|-- tools/               one-off audit and evidence utilities
|-- coverage_summary.txt committed 100% coverage proof
|-- pytest.ini
|-- requirements.txt
`-- README.md
```

The hosted documentation is built automatically from the repository's
`.readthedocs.yaml` configuration.
