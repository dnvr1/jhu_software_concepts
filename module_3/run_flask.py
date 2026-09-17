"""Start the Flask application after securely configuring PostgreSQL."""

from __future__ import annotations

import os

import models
from orm_queries import runtime_password


def main() -> None:
    """Configure the shared Engine and run the local development server."""
    models.configure_database(runtime_password())

    from app import app

    app.run(
        host=os.getenv("FLASK_HOST", "127.0.0.1"),
        port=int(os.getenv("FLASK_PORT", "5000")),
        debug=False,
        use_reloader=False,
    )


if __name__ == "__main__":
    main()
