"""Main file for Stuffr's backend."""

from flask import Flask

from database import db
from .api.views import bp as blueprint_api


def create_app(config_override={}):
    """Create the flask app for the debug server.

    Parameters:
        config_override:
            Dict containing custom configuration to apply after loading the
            normal config. Useful for testing.
    """
    app = Flask('stuffrdebugserver',
                instance_relative_config=True,
                static_url_path='',
                template_folder='static')
    app.config.from_object('defaultconfig')
    app.config.from_pyfile('debugconfig.py', silent=True)
    app.config.from_mapping(config_override)

    db.init_app(app)

    app.register_blueprint(blueprint_api, url_prefix='/api')

    return app
