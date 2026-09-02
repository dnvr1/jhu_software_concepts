"""Define the pages blueprint."""

import flask


blueprint = flask.Blueprint("pages", __name__)


@blueprint.route("/")
def home() -> str:
    """Display the homepage."""
    return flask.render_template("home.html")


@blueprint.route("/projects")
def projects() -> str:
    """Display the projects page."""
    return flask.render_template("projects.html")


@blueprint.route("/contact")
def contact() -> str:
    """Display the contact page."""
    return flask.render_template("contact.html")