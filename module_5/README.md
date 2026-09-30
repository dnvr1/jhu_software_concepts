# Module 5: Software Assurance and Secure SQL

Student: Denver Clarke (`dclar106`)

Course: EN.605.256, Modern Software Concepts in Python

Repository: `git@github.com:dnvr1/jhu_software_concepts.git`

This directory builds on Module 4's GradCafe analytics application. The
application code lives in `src/`, and the tests live in `tests/`.

## Fresh Install

Use Python 3.12 (the verified tooling/CI version) and PostgreSQL. Start in `module_5/`.
Choose either path below, then provide the database settings shown in
`.env.example`. The sample file contains placeholders only; `.env` is ignored
by Git. The application does not load `.env` automatically, so export the
values in your shell or use a private environment manager.

### pip and venv

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install -e .
```

### uv

```powershell
uv venv .venv
uv pip sync --python .venv\Scripts\python.exe requirements.txt
uv pip install --python .venv\Scripts\python.exe -e .
```

On macOS/Linux, replace `.venv\Scripts\python.exe` with `.venv/bin/python`.
An editable install keeps local imports consistent across the application,
tests, and CI. Runtime packages and the required Pylint/pydeps tools are in
`requirements.txt`.

## Database roles

Use a dedicated `gradcafe_app` role with `CONNECT`, schema `USAGE`, and
`SELECT` and `INSERT` on `public.applicants`, plus sequence `USAGE` for
generated primary keys. The example grants are in
`least_privilege.sql`; an administrator must apply them using psql, which
prompts privately for the role password. Pull Data inserts new rows, so `INSERT` is
required; schema creation and the initial data loader use a separate
administrator role. Do not run the Flask application as the PostgreSQL owner
or superuser. Configure `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, and
`DB_PASSWORD`, or provide `DATABASE_URL`. Legacy `PG*` variables still work.

From this folder, run these in your own PowerShell session:

```powershell
& 'C:\Program Files\PostgreSQL\17\bin\psql.exe' -h localhost -U postgres -d gradcafe -W -f least_privilege.sql
& 'C:\Program Files\PostgreSQL\17\bin\psql.exe' -h localhost -U postgres -d gradcafe -W -f verify_privileges.sql
```

The role must be new when applying the creation script. If it already exists,
inspect its privileges before changing it. The verification should show only
SELECT and INSERT table privileges and no owner-role membership.

## Security checks

```powershell
.\.venv\Scripts\python.exe -m pylint src --fail-under=10
.\.venv\Scripts\python.exe -m pytest -m "web or buttons or analysis or db or integration"
```

The raw analysis queries in `query_data.py` have explicit result limits.
`lookup_applicants` accepts only approved column names, quotes them using
`psycopg.sql.Identifier`, binds user values as parameters, and clamps the
requested limit to 1-100. The restricted role and live Flask analysis were
verified against PostgreSQL 17 in CI; see `database_privileges.txt`.
The home database has not been changed. For local deployment, run
`setup_database.cmd` as the database administrator and configure app credentials.
Snyk successfully tested 52 dependencies with zero issues; see
`snyk-analysis.txt`, `snyk-results.json`, and `snyk-analysis.png`.

## Extra credit: Snyk Code

Run `snyk code test --json-file-output=snyk-code-results.json` from this
folder after authenticating and enabling Snyk Code for your organization.
This uploads source code to Snyk for analysis. The completed scan initially
reported 26 findings; HTML escaping in the capture helper resolved one
medium XSS finding. The repeat scan reports 25 open findings: no high,
two medium and 23 low. Exit code 1 means findings were detected.
See `SNYK_CODE_REVIEW.md` and the original before/after text and JSON evidence.
The extra-credit scan is separate from the four required CI jobs.

## Dependency graph

Install Graphviz and add `dot` to `PATH`, then regenerate the graph with:

```powershell
.\.venv\Scripts\python.exe -m pydeps src/app.py --noshow -T svg -o dependency.svg
```

`dependency.svg` was generated from `src/app.py` with pydeps and Graphviz.
The `app` module defines Flask routes and asks `orm_queries` for the analysis
shown on the page. `orm_queries` uses `models` for the applicant mapping and
SQLAlchemy session access. `models` depends on SQLAlchemy and the PostgreSQL
dialect, which connect the Python model to PostgreSQL. `scrape_refresh` joins
the scraper, data loader, and model layer for the optional refresh action.
`analysis_format` turns database results into display strings. Flask and its
template helpers render the page, while the external SQLAlchemy and Flask
nodes account for most of the graph's complexity.

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

The Module 5 workflow is in `.github/workflows/ci.yml` at the repository root.
It has test coverage, lint, dependency graph, and Snyk jobs and runs on every
push/PR. All four passed in
[Module 5 run 36719680940](https://github.com/dnvr1/jhu_software_concepts/actions/runs/36719680940).
`ci_success.jpg` captures that run. Hosted tests passed 133 tests with two
optional model skips and 100% coverage. Snyk tested 50 dependencies on Linux
with zero issues (the local Windows scan tested 52).

The CI database check provisions a new `gradcafe_app` in the disposable
`gradcafe_test` service, with a random password kept in memory. It verifies
permitted reads/inserts, denied DDL/destructive writes, safe lookup input, and
HTTP 200 responses from analysis/update. No live GradCafe scraping is needed.

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
module_5/
|-- src/                 Flask, ETL, database, and analysis modules
|-- tests/               marked unit and integration tests
|-- docs/                Sphinx source
|-- tools/               one-off audit and evidence utilities
|-- coverage_summary.txt committed 100% coverage proof
|-- dependency.svg       pydeps and Graphviz output
|-- least_privilege.sql  example DB privilege grants
|-- setup.py             editable install metadata
|-- pytest.ini
|-- requirements.txt
`-- README.md
```

The hosted documentation remains Module 4 and is built automatically from
the repository's unchanged `.readthedocs.yaml` configuration. Module 5's own
documentation is included as locally built HTML.

## Submission archive

From the repository root, after committing all deliverables:

```powershell
module_5/.venv/Scripts/python.exe module_5/tools/build_submission.py
module_5/.venv/Scripts/python.exe module_5/tools/verify_submission.py
```

The builder creates `module_5/output/module_5_submission.zip` directly from
Git blobs, avoiding platform-specific line-ending conversion. The verifier
checks the ZIP's file list and every file's bytes against Git. The archive includes the root
workflow alongside `module_5/` and excludes environments, secrets and caches.
