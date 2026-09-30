"""Start the Flask application after securely configuring PostgreSQL."""

from __future__ import annotations

import os

import models
from orm_queries import runtime_password


def main() -> None:
    """Configure the shared Engine and run the local development server.

    Reads FLASK_HOST and FLASK_PORT, defaulting to loopback on port 5000.
    This development entry point blocks until the server stops. Debugging
    and the automatic reloader remain disabled to avoid duplicate workers.

    Raises:
        ValueError: A configured database or Flask port is not an integer.
    """
    models.configure_database(runtime_password())

    # Import after configuration: create_app captures the current session
    # factory, so an earlier import would retain the old database binding.
    from app import app  # pylint: disable=import-outside-toplevel

    app.run(
        host=os.getenv("FLASK_HOST", "127.0.0.1"),
        port=int(os.getenv("FLASK_PORT", "5000")),
        debug=False,
        use_reloader=False,
    )


if __name__ == "__main__":  # pragma: no cover - module execution bootstrap
    main()
