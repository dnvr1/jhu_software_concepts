# Part 8 Validation: Dynamic Flask Analysis Page

Validated on September 17, 2026 against the local PostgreSQL `gradcafe`
database.

## Architecture checks

- `app.py` opens the SQLAlchemy `SessionLocal` factory configured in
  `models.py`.
- `orm_queries.run_complete_analysis()` retrieves all 11 results from the
  existing `applicants` table using SQLAlchemy expressions.
- The Flask layer contains no psycopg import, cursor call, `text()` call,
  handwritten SQL, or hard-coded analysis result.
- Database failures return a readable error page with HTTP status 503.

## Live results

The page loaded 30,000 rows and displayed values matching the verified raw SQL
analysis, including 29,585 Fall 2026 entries, 46.34% international entries,
47.92% Fall 2025 acceptances, and 28 qualifying records for both Question 8
and Question 9.

## Automated and browser checks

- Full suite: `17 passed`
- Python compilation: passed for `orm_queries.py`, `app.py`, and
  `run_flask.py`
- Desktop browser: 1440 by 1100 pixels, no console errors or warnings
- Mobile browser: 390 by 844 pixels, no console errors or warnings
- Desktop screenshot: `output/playwright/flask_analysis_desktop.png`
- Mobile screenshot: `output/playwright/flask_analysis_mobile.png`
