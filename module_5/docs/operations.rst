Operational notes
=================

Busy-state policy
-----------------

Only one pull may run at a time. A pull or update request made during an active
pull receives HTTP 409 and ``{"busy": true}``. The status endpoint exposes the
current state without changing it.

Idempotency
-----------

The canonical GradCafe result URL is unique. PostgreSQL inserts use
``ON CONFLICT DO NOTHING`` so overlapping pulls preserve one row per result.

Troubleshooting
---------------

An HTTP 503 from the analysis routes usually means PostgreSQL is unavailable
or ``DATABASE_URL`` is invalid. Import failures generally mean dependencies
were installed outside the active virtual environment. CI database failures
should be checked against the PostgreSQL service health check and connection
URL in the workflow.
