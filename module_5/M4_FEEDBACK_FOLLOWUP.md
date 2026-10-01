# Module 4 feedback addressed in Module 5

Verified October 1, 2026. These changes improve the Module 5 submission;
they do not change a previously submitted Module 4 archive or its grade.

## 1. Busy requests must cause no update

`tests/test_buttons.py` now asserts that both busy button endpoints return
HTTP 409 without calling the analysis runner or session factory and without
changing the manager snapshot. The real PostgreSQL end-to-end test additionally
pauses the collector using threading events, checks there is only one collector
call, and confirms the committed row count remains zero during rejected requests.
It releases the worker in a finally block, not with arbitrary sleeps.

## 2. Inserts must enter through POST /pull-data

`tests/test_postgres_integration.py` now POSTs to the actual Flask endpoint with
the real ScrapeJobManager and default insert_new_records loader. Only network
collection is replaced with fixed source data. It waits for completion and
asserts the job succeeded, reads committed rows through another connection,
checks exact URLs/programs/dates, and verifies a repeated POST inserts no duplicates.
The test no longer calls the insert helper directly.

## 3. End-to-end storage must be PostgreSQL

`tests/test_integration_end_to_end.py` no longer uses InMemoryPullManager or
synthetic analysis results. It uses real PostgreSQL, the real worker/loader,
and the real ORM analysis runner. Wrapping spies observe calls without replacing
their implementations. The flow covers POST pull, busy rejection, committed
rows, POST update, rendered GET analysis, and a repeated idempotent pull.

## Database safety and mandatory CI execution

Both tests use the shared postgres_engine fixture in conftest.py. The URL must
select PostgreSQL and a database ending in `_test`; unsafe targets fail before
any connection or write. The fixture resets the applicants table, so the test
database must be disposable. Missing DATABASE_URL may skip a local test run;
CI sets REQUIRE_POSTGRES_TESTS=1 so it fails instead. Connection errors also fail.
The home database was not used or changed.

## Verification evidence

- Local complete suite: 132 passed, 4 skipped, 100% coverage over 1,166 statements.
  Two skips need optional llama_cpp; two need the disposable PostgreSQL service.
- Local Pylint: 10.00/10. Sphinx warning-as-error build succeeded.
- Negative checks: missing required URL failed instead of skipping; a non-test
  database name was rejected before connection/writes.
- [GitHub Actions run 36932699860](https://github.com/dnvr1/jhu_software_concepts/actions/runs/36932699860)
  verified code commit `386ba72`: all four jobs succeeded.
- The pytest job's full suite, dedicated **Required HTTP-to-PostgreSQL integration
  evidence** step, and restricted-role verification all succeeded. The dedicated
  step executes both database test files and uploads `module-5-postgres-integration`
  containing JUnit XML. Neither database test has an internal skip path when
  REQUIRE_POSTGRES_TESTS=1.

Historical PDF/screenshots retain their original run identities. This document
records the newer feedback-specific evidence; it does not relabel old screenshots.
