# Part 9 Validation: Pull Data

Validated on September 17, 2026 against the live GradCafe results page and the
local PostgreSQL `gradcafe` database.

## Required behavior

- The Flask page includes a clearly labeled **Pull Data** button and a short
  user-facing explanation.
- A click starts a daemon worker around the existing Module 2
  `GradCafeScraper`, leaving the Flask request responsive.
- A nonblocking job lock rejects overlapping Pull Data requests.
- The button is disabled while the worker runs and the page polls a read-only
  status endpoint for running, success, and failure messages.
- Records are normalized with the Part 1 loader rules and inserted through
  SQLAlchemy with a PostgreSQL URL conflict guard.
- Invalid records are ignored, existing rows are preserved, and runtime scrape
  files are isolated under a Git-ignored directory.

## Live result

The scrape checked the newest 20 public entries. Six unseen URLs were inserted
and 14 existing URLs were skipped. A fresh ORM analysis confirmed that the
database increased from 30,000 to 30,006 rows. Fall 2026 entries increased
from 29,585 to 29,586, demonstrating that the analysis reads the newly added
database records.

## Verification

- Full automated suite: `22 passed`
- Python compilation: passed
- Browser console: zero errors and zero warnings
- Success evidence: `output/playwright/flask_pull_data_updated.png`
