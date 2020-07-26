"""
The `playwhat.web` module is responsible for exposing and implementing a web UI for managing
PlayingWHAT
"""

from flask import Flask

def create_app():
    """Creates the Flask app responsible for providing a web UI for PlayingWHAT."""
    # Create and configure the Flask application
    flask_app = Flask(__name__, instance_relative_config=True)

    # For now, we'll start with a basic "Hello World!" route.
    @flask_app.route("/")
    def index(): # pylint: disable=unused-variable
        return "Hello, World!"

    return flask_app

"""The app that can be used to run this Flask app under uWSGI"""
app = create_app() # pylint: disable=invalid-name
