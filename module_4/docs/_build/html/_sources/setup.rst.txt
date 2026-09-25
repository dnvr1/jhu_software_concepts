Setup and local development
===========================

Install Python 3.10 or newer, PostgreSQL, and the dependencies in
``requirements.txt``. From ``module_4`` run:

.. code-block:: powershell

   python -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   $env:DATABASE_URL = "postgresql+psycopg://postgres:password@localhost:5432/gradcafe"
   .\.venv\Scripts\python.exe src\run_flask.py

The application is available at ``http://127.0.0.1:5000/analysis``.

Configuration
-------------

``DATABASE_URL`` is preferred. The data layer also accepts ``PGHOST``,
``PGPORT``, ``PGDATABASE``, ``PGUSER``, and ``PGPASSWORD``. Optional scrape
settings include ``SCRAPE_DELAY``, ``SCRAPE_MAX_PAGES``, and
``SCRAPE_RUN_ROOT``. Never commit credentials.

Build these docs with:

.. code-block:: powershell

   .\.venv\Scripts\python.exe -m sphinx -W --keep-going -b html docs docs\_build\html

Read the Docs uses the repository-level ``.readthedocs.yaml`` file and this
same requirements file and Sphinx configuration.
