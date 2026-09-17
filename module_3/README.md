# Module 3: Database Queries

Student: Denver Clarke (`dclar106`)

Course: EN.605.256, Modern Software Concepts in Python

Repository: `git@github.com:dnvr1/jhu_software_concepts.git`

## Part 1: Load Data into PostgreSQL

`load_data.py` loads the 30,000 cleaned GradCafe records from
`llm_extend_applicant_data.json` into the required PostgreSQL `applicants`
table. The table uses an identity primary key and a unique constraint on each
GradCafe result URL. Running the loader again skips rows already present.

The Module 2 `citizenship` field maps to `us_or_international`. The source
`gre` field maps to GRE Quantitative; the loader uses the separately parsed
`gre_quantitative` value when `gre` is missing. Hyphenated LLM output keys map
to the underscore-separated database column names required by the assignment.

### Setup on Windows

PostgreSQL 17 runs locally on port 5432. The course database is named
`gradcafe`, and the default database user is `postgres`. When `gradcafe` does
not exist, the loader creates it through PostgreSQL's `postgres` maintenance
database. The configured user must have permission to create a database.

Create and activate a virtual environment, then install the dependency:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Run the loader from the `module_3` directory:

```powershell
python load_data.py
```

The program securely prompts for the PostgreSQL password when `PGPASSWORD` is
not set. It does not write the password to disk. Standard PostgreSQL variables
can override the defaults:

- `PGHOST` (default `localhost`)
- `PGPORT` (default `5432`)
- `PGDATABASE` (default `gradcafe`)
- `PGUSER` (default `postgres`)
- `PGPASSWORD`

`DATABASE_URL` is also supported. Never commit passwords, connection URLs,
API keys, or `.env` files containing credentials.

### Table schema

The `applicants` table contains `p_id`, `program`, `comments`, `date_added`,
`url`, `status`, `term`, `us_or_international`, `gpa`, `gre`, `gre_v`,
`gre_aw`, `degree`, `llm_generated_program`, and
`llm_generated_university`.

Run the focused loader checks with:

```powershell
python -m pytest tests/test_load_data.py -q
```

## Part 2: Raw SQL Query Analysis

`query_data.py` answers required Questions 1-9 and two original questions
using PostgreSQL SQL executed through psycopg. All filtering, counting,
percentages, grouping, and averages are expressed in SQL. Text comparisons
normalize capitalization, individual averages rely on SQL's per-column `NULL`
handling, and percentages protect against a zero denominator.

Run the analysis with:

```powershell
python query_data.py
```

On Windows, `run_query_data.cmd` runs the same command and keeps the console
open for review. The verified output is recorded in `RAW_SQL_RESULTS.md`.

Run the Part 1 and Part 2 unit checks with:

```powershell
python -m pytest tests/test_load_data.py tests/test_query_data.py -q
```

## Part 4: SQL Analysis PDF

`query_results.pdf` contains all 11 analysis questions, their verified
results, the executable SQL, and a short explanation of each query. Rebuild it
from the query constants and recorded results with:

```powershell
python build_query_results_pdf.py
```

The report uses letter-sized pages, one question per page, and consistent
headers, result panels, SQL formatting, and page numbers.

## Part 5: SQLAlchemy Applicant Model

`models.py` defines a SQLAlchemy 2.x `Applicant` model for the existing
PostgreSQL `applicants` table. It maps all 15 required columns, uses `p_id` as
the primary key, and configures a PostgreSQL psycopg Engine and reusable
`SessionLocal` factory. It does not create a second table or duplicate the
applicant data.

Connection settings use `DATABASE_URL` or the standard PostgreSQL environment
variables documented above. Validate the mapping against the live database
with:

```powershell
python validate_models.py
```

On Windows, `run_model_validation.cmd` runs the same check and keeps the
console open. The validation confirms the live columns and primary key, counts
the existing rows through an ORM Session, and retrieves an `Applicant` object.

## Part 6: SQLAlchemy ORM Queries

`orm_queries.py` repeats Questions 1, 4, 5, 8, 9, and original Question 10
with SQLAlchemy 2.x expressions and `Session` objects. It does not import
psycopg, call a database cursor, use `text()`, or contain handwritten SQL.

Run the ORM analysis with:

```powershell
python orm_queries.py
```

On Windows, `run_orm_queries.cmd` runs the same analysis and keeps the console
open for review. The verified ORM results match the corresponding raw-SQL
results exactly. `analysis_format.py` provides the shared count, percentage,
average, and signed-difference formatting used by both implementations.

## Part 7: Raw SQL and SQLAlchemy Comparison

Question 4 asks for the average GPA of American applicants who applied for
Fall 2026. Both implementations return **3.79**.

Raw SQL:

```sql
SELECT AVG(gpa)
FROM applicants
WHERE LOWER(BTRIM(term)) = 'fall 2026'
  AND LOWER(BTRIM(us_or_international)) = 'american'
  AND gpa IS NOT NULL;
```

SQLAlchemy:

```python
statement = select(func.avg(Applicant.gpa)).where(
    func.lower(func.btrim(Applicant.term)) == "fall 2026",
    func.lower(func.btrim(Applicant.us_or_international)) == "american",
    Applicant.gpa.is_not(None),
)

with SessionLocal() as session:
    average_gpa = session.scalar(statement)
```

Both versions express the same filters and average the same non-NULL GPA
values. The ORM version uses mapped Python attributes, which makes the query
composable and easier to reuse alongside the rest of the application's model
logic. The raw SQL version is shorter and exposes the database operation
directly, which can make debugging and query tuning more straightforward. For
application code, SQLAlchemy provides useful abstraction and integration,
while raw SQL provides concise syntax and precise control over the statement.

## Part 8: Dynamic Flask Analysis Page

`app.py` defines a Flask application whose `/` route opens `SessionLocal`,
runs all 11 analyses with SQLAlchemy expressions, and renders the current
PostgreSQL results. The route does not use psycopg, database cursors,
handwritten SQL, or hard-coded result values. `templates/analysis.html` and
`static/style.css` provide an accessible, responsive presentation for the
analysis.

On Windows, start the application from the `module_3` directory with:

```powershell
.\run_flask.cmd
```

Enter the PostgreSQL password when prompted, leave the terminal open, and
visit `http://127.0.0.1:5000`. The page refreshes its analysis from the shared
`gradcafe.applicants` table on every request. Stop the local development server
with `Ctrl+C` in its terminal.

The Flask tests use a temporary test client and mocked ORM results so they do
not require credentials:

```powershell
python -m pytest tests/test_app.py -q
```

Live browser validation was completed at desktop and mobile widths with no
console errors. The desktop evidence is saved at
`output/playwright/flask_analysis_desktop.png`; mobile evidence is saved at
`output/playwright/flask_analysis_mobile.png`.

## Part 9: Pull Data

The **Pull Data** button starts one background refresh and returns control to
the webpage immediately. `scrape_refresh.py` reuses the Module 2
`GradCafeScraper` to check the newest public results page, normalizes the
records with the same loader rules, and inserts them through SQLAlchemy. The
PostgreSQL insert uses the unique `url` column with `ON CONFLICT DO NOTHING`,
so existing rows are retained and repeated entries are skipped.

While collection is active, the button is disabled and a live status message
explains that retrieval may take some time. The application refuses another
Pull Data job until the first job finishes. Success messages report checked,
inserted, skipped, and unusable-record counts; collection or database errors
are also displayed to the user. Each scrape's checkpoint artifacts are stored
under the ignored `runtime/pull_data` directory.

The default refresh checks one current GradCafe results page using the Module
2 scraper's six-second request delay, robots policy check, URL restrictions,
and stop-on-rejection behavior. These optional environment variables adjust
the collection settings:

- `SCRAPE_DELAY` (default `6`, minimum `2`)
- `SCRAPE_MAX_PAGES` (default `1`)
- `SCRAPE_RUN_ROOT` (default `runtime/pull_data`)

Live validation checked 20 records, inserted 6 unseen URLs, skipped 14 URLs
already in PostgreSQL, and increased the database from 30,000 to 30,006 rows.
The result is shown in
`output/playwright/flask_pull_data_updated.png`.

## Part 10: Update Analysis

The **Update Analysis** button appears at the top-right of the page. It sends a
GET request that re-runs all 11 SQLAlchemy analyses against the current
PostgreSQL rows; it never starts, stops, or waits for a Pull Data job. When no
scrape is active, the page confirms that the latest database records were
used.

If Pull Data is running, Update Analysis still renders the rows that have
already committed and reports that new data is being retrieved. The scraper
continues independently. When retrieval finishes, the live status tells the
user to select Update Analysis again so any newly inserted rows are included
in the displayed results.

Browser evidence for the active and completed states is saved in
`output/playwright/flask_update_active_scrape.png` and
`output/playwright/flask_update_finished.png`.

## Part 11: Written Reflection

`limitations.pdf` contains the required two-paragraph reflection on the limits
of analyzing anonymous, self-submitted GradCafe data. It discusses selection
and self-reporting bias, missing values, inconsistent information,
representativeness, and the difference between a correct database calculation
and a defensible real-world conclusion.

The reflection connects those limitations to the live 30,006-row analysis,
including the 38.53% American and 34.59% international acceptance percentages
and the questionable 260.47 GRE Quantitative average. Rebuild the PDF with:

```powershell
python build_limitations_pdf.py
```

## Submission Evidence

The `screenshots` directory contains the three rubric-required images:

- `screenshots/raw_sql_output.png` shows Questions 1-11 executed with raw
  PostgreSQL SQL.
- `screenshots/sqlalchemy_orm_output.png` shows Questions 1, 4, 5, 8, 9, and
  the original Question 10 executed with SQLAlchemy ORM expressions.
- `screenshots/flask_webpage.png` shows the running, dynamically populated
  Flask analysis page.

To refresh the two console screenshots after the database changes, start from
the `module_3` directory and run:

```powershell
python capture_submission_evidence.py
```

The script prompts for the PostgreSQL password once and reads the actual
database through both required query implementations. The Flask screenshot is
captured separately from `http://127.0.0.1:5000` while the application is
running.

## Final Archive Verification

Create the Canvas archive from the repository root so it contains exactly the
committed `module_3` folder:

```powershell
git archive --format=zip --output=module_3.zip HEAD module_3
python module_3/verify_submission.py
```

`verify_submission.py` checks the archive CRC, compares its complete file
manifest with the current Git commit, confirms the required deliverables are
present, rejects generated or sensitive directories, and prints the archive's
SHA-256 digest.
