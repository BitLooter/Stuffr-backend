"""Main file for Stuffr's backend."""

from flask import Flask

from database import db
from .api.views import bp as blueprint_api


def create_app():
    """Create the flask app for the debug server."""
    app = Flask('stuffrdebugserver',
                instance_relative_config=True,
                static_url_path='',
                template_folder='static')
    app.config.from_object('defaultconfig')
    app.config.from_pyfile('debugconfig.py', silent=True)

    db.init_app(app)

    app.register_blueprint(blueprint_api, url_prefix='/api')

    return app
