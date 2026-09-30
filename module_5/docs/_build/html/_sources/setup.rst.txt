Setup and local development
===========================

Install Python 3.10 or newer, PostgreSQL, and the dependencies in
``requirements.txt``. From ``module_5`` run:

.. code-block:: powershell

   python -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   .\.venv\Scripts\python.exe -m pip install -e .
   # Set DB_HOST, DB_PORT, DB_NAME, DB_USER and DB_PASSWORD privately.
   # Use gradcafe_app, not postgres, for the running application.
   .\.venv\Scripts\python.exe src\run_flask.py

The application is available at ``http://127.0.0.1:5000/analysis``.

Configuration
-------------

``DATABASE_URL`` is preferred. See ``.env.example`` for the ``DB_*`` variables.
The data layer also accepts ``PGHOST``,
``PGPORT``, ``PGDATABASE``, ``PGUSER``, and ``PGPASSWORD``. Optional scrape
settings include ``SCRAPE_DELAY``, ``SCRAPE_MAX_PAGES``, and
``SCRAPE_RUN_ROOT``. Never commit credentials.

Build these docs with:

.. code-block:: powershell

   .\.venv\Scripts\python.exe -m sphinx -W --keep-going -b html docs docs\_build\html

The existing Read the Docs site continues to publish Module 4 using the
repository-level configuration. Module 5 documentation can be built locally
with the command above; its security setup is also documented in README.md.
