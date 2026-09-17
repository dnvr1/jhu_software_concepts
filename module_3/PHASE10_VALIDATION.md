# Part 10 Validation: Update Analysis

Validated on September 17, 2026 against the 30,006-row PostgreSQL database.

## Required behavior

- **Update Analysis** is positioned at the page's top-right.
- The control performs a GET request and re-runs all 11 SQLAlchemy ORM
  analyses.
- It does not call the scraper start method.
- While Pull Data is idle, the page confirms that it used the latest
  PostgreSQL records.
- While Pull Data is active, the update completes from committed rows and
  reports that new data is still being retrieved.
- The running scraper remains active and its duplicate protections remain in
  effect.
- When the scrape finishes, the page prompts the user to update once more if
  new rows were added.

## Verification

- Full automated suite: `24 passed`
- Idle and active-scrape update paths: passed
- A live repeat scrape checked 20 records, inserted 0 duplicates, and skipped
  all 20 existing URLs.
- Browser console: zero errors and zero warnings
- Active-scrape evidence: `output/playwright/flask_update_active_scrape.png`
- Completion-prompt evidence: `output/playwright/flask_update_finished.png`
