"""Initialize the Flask application."""

import flask

from app.pages import blueprint


def create_app() -> flask.Flask:
    """Create and configure the Flask application."""
    app = flask.Flask(__name__)
    app.register_blueprint(blueprint)
    return app