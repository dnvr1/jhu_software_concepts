"""Run the Flask application."""

from app import create_app


def main() -> None:
    """Start the Flask development server."""
    app = create_app()
    app.run(host="0.0.0.0", port=8080)


if __name__ == "__main__":
    main()