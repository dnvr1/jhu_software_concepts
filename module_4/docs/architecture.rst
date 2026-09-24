Architecture
============

Web layer
---------

``app.py`` exposes the application factory and the analysis, pull, update, and
status routes. The factory accepts injected session, analysis, and scrape
dependencies so tests do not need a live network or database.

ETL layer
---------

``scrape.py`` collects public records, ``clean.py`` normalizes model-assisted
fields, and ``scrape_refresh.py`` coordinates one observable background pull.
Records are normalized before loading and malformed records are rejected.
One-off audit, evidence, and report-generation commands live in ``tools/`` and
are outside the deployed service surface.

Database and analysis layer
---------------------------

``load_data.py`` maps records to the required schema. ``models.py`` defines the
SQLAlchemy mapping, while ``query_data.py`` and ``orm_queries.py`` calculate
the values displayed by Flask. The source URL is the uniqueness key.
