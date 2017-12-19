"""
Main file for Stuffr's backend.

Use create_app() to generate the Flask app to be used. Note that it expects an
environment variable named STUFFR_SETTINGS to contain the name of the file
containing the local configuration.
"""

from datetime import datetime
from http import HTTPStatus
from typing import Mapping
from flask import Flask
from flask.json import JSONEncoder
from flask_security import Security, SQLAlchemyUserDatastore
from flask_security.forms import ConfirmRegisterForm, StringField, validators
from flask_mail import Mail

from database import db
from . import logger
from .api import models
from .api.views import bp as blueprint_api
from .api.views_admin import bp as blueprint_apiadmin
from .api.views_common import api_unauthenticated_handler, error_response
from .simple import bp as blueprint_simple

user_store = SQLAlchemyUserDatastore(db, models.User, models.Role)


class StuffrRegisterForm(ConfirmRegisterForm):
    """Extended form for more fields during user registration."""

    name_first = StringField('First name')
    name_last = StringField('Last name', [validators.DataRequired()])


class StuffrJSONEncoder(JSONEncoder):
    """Handles custom JSON serialization."""

    def default(self, o):  # pylint: disable=method-hidden
        """Convert unserializable types for JSON encoding."""
        if isinstance(o, datetime):
            # Stuffr uses ISO dates
            return o.isoformat()

        return JSONEncoder.default(self, o)


def create_app(config_override: Mapping = None) -> Flask:
    """Create the flask app for the debug server.

    Parameters:
        config_override:
            Dict containing custom configuration to apply after loading the
            normal config. Useful for testing.
    """
    config_override = {} if config_override is None else config_override
    # TODO: Rename app, no longer used only for debugging
    app = Flask('stuffrdebugserver',
                instance_relative_config=True,
                static_url_path='',
                template_folder='static')
    app.config.from_object('config.default')
    app.config.from_envvar('STUFFR_SETTINGS')
    app.config.from_mapping(config_override)
    app.json_encoder = StuffrJSONEncoder
    logger.set_logger(app.logger)

    db.init_app(app)
    security = Security(app, user_store, confirm_register_form=StuffrRegisterForm)
    security.unauthorized_handler(api_unauthenticated_handler)
    Mail(app)

    # In debug mode Swagger documentation is served at root
    if not app.config['DEBUG']:
        def api_root_view():
            """Provide a link to API documentation if root accessed."""
            return error_response(
                'TODO: Link to documentation here', HTTPStatus.NOT_FOUND)
        blueprint_api.add_url_rule('/', 'apiindex', api_root_view)

        def apiadmin_root():
            """Dummy view for API root."""
            # TODO: Clean up this view definition when main API switches
            # to Flask-Restplus
            return error_response('Nothing to see here', HTTPStatus.NOT_FOUND)
        blueprint_apiadmin.add_url_rule('/', 'apiadmin_root', apiadmin_root)

    app.register_blueprint(blueprint_simple, url_prefix='/simple')
    app.register_blueprint(blueprint_api, url_prefix='/api')
    app.register_blueprint(blueprint_apiadmin, url_prefix='/api/admin')

    def default404(e):
        """Default handler for 404."""
        # TODO: Conditional JSON/HTML response (for simple mode)
        return error_response(e.description, HTTPStatus.NOT_FOUND)
    app.register_error_handler(HTTPStatus.NOT_FOUND, default404)

    # TODO: Make friendlier error message (40x or 50x?)
    app.add_url_rule('/', 'index', lambda: "You probably shouldn't be here")

    return app
