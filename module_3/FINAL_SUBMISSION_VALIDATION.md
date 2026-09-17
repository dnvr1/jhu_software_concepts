# Final Submission Validation

Validated on September 17, 2026.

## Automated checks

- A new temporary Python virtual environment was created from
  `requirements.txt`.
- Both submission PDFs rebuilt successfully.
- The complete automated test suite passed: 24 tests passed.
- Python compilation completed without errors.
- The repository secret scan found no embedded database passwords, API keys,
  or private keys.

## Required evidence

- `query_results.pdf` contains 12 pages covering Questions 1-11 with results,
  executable SQL, and explanations.
- `limitations.pdf` contains the required two-paragraph reflection.
- `screenshots/raw_sql_output.png` contains the raw SQL output.
- `screenshots/sqlalchemy_orm_output.png` contains the ORM output.
- `screenshots/flask_webpage.png` contains the running Flask webpage.
- The final database snapshot contains 30,006 unique applicant rows.

## Repository and archive

- The private SSH repository URL in `github.txt` matches the configured Git
  remote.
- The final branch is `main`.
- The Canvas archive is generated directly from Git with `git archive`.
- `verify_submission.py` confirms that the archive has 76 committed files,
  passes its CRC check, includes every required deliverable, contains no
  generated environment directories, and matches the Git file manifest.
