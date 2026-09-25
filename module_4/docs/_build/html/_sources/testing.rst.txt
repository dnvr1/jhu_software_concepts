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
factory, analysis runner, scraper, and loader with deterministic doubles.
Tests never depend on the live GradCafe site and use events instead of
arbitrary sleeps for background-job coordination.

Coverage and PostgreSQL
-----------------------

``pytest.ini`` applies ``pytest-cov`` to all code under ``src`` and fails the
run below 100 percent. The PostgreSQL integration test activates only when
``DATABASE_URL`` names a database ending in ``_test``. GitHub Actions provides
``gradcafe_test``, starts from an empty table, inserts two records, repeats the
same pull, and verifies the required fields and URL uniqueness policy.
