"""Define the pages blueprint."""

import flask


blueprint = flask.Blueprint("pages", __name__)


@blueprint.route("/")
def home() -> str:
    """Display the homepage."""
    return flask.render_template("home.html")