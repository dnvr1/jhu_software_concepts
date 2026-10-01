Testing guide
=============

Run every assignment test with:

.. code-block:: powershell

   python -m pytest -m "web or buttons or analysis or db or integration"

Markers
-------

``web`` covers Flask routes and HTML structure. ``buttons`` covers pull,
update, and busy-state behavior. ``analysis`` covers labels and formatting.
``db`` covers schema, inserts, uniqueness, and queries. ``integration`` covers
pull-to-update-to-render flows.

Selectors and doubles
---------------------

The stable button selectors are ``data-testid="pull-data-btn"`` and
``data-testid="update-analysis-btn"``. Shared fixtures replace the session
factory, analysis runner, scraper, and loader in isolated unit tests only.
The PostgreSQL integration tests replace only network collection with fixed
records. They use the real worker, loader, database, and ORM analysis.
Tests never depend on the live GradCafe site and use events instead of
arbitrary sleeps for background-job coordination.

Coverage and PostgreSQL
-----------------------

``pytest.ini`` applies ``pytest-cov`` to all code under ``src`` and fails the
run below 100 percent. PostgreSQL integration tests require ``DATABASE_URL``
to name a disposable PostgreSQL database ending in ``_test``. Fixtures create
the applicants table if needed and truncate it before each test. Never point
these tests at a database containing valuable data.

GitHub Actions sets ``REQUIRE_POSTGRES_TESTS=1``: missing configuration fails
instead of skipping, and invalid database targets always fail before writes.
Local runs without a database skip these two tests; CI must execute them.
A dedicated CI step also runs both files verbosely and uploads JUnit evidence.

Both tests insert through ``POST /pull-data`` and wait for the real worker.
One checks exact committed fields and duplicate handling. The end-to-end test
checks busy rejection before releasing an event-controlled collector, proves
no analysis/session calls or stored-row changes occurred while busy, then
verifies persisted rows, real ORM update results, and rendered HTML. A repeated
pull verifies that the database unique-URL constraint prevents duplicates.
