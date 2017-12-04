"""
Main file for Stuffr's backend.

Use create_app() to generate the Flask app to be used. Note that it expects an
environment variable named STUFFR_SETTINGS to contain the name of the file
containing the local configuration.
"""

from datetime import datetime
from typing import Mapping
from flask import Flask
from flask.json import JSONEncoder
from flask_security import Security, SQLAlchemyUserDatastore
from flask_security import user_registered
from flask_security.forms import ConfirmRegisterForm, StringField
from flask_mail import Mail

from database import db
from .api import models
from .api.views import bp as blueprint_api
from .api.views_admin import bp as blueprint_apiadmin
from .api.views_common import api_unauthenticated_handler
from .simple import bp as blueprint_simple

logger = None
user_store = SQLAlchemyUserDatastore(db, models.User, models.Role)


class StuffrRegisterForm(ConfirmRegisterForm):
    """Extended form for more fields during user registration."""

    # TODO: make required
    name_first = StringField('First name')
    name_last = StringField('Last name')


class StuffrJSONEncoder(JSONEncoder):
    """Handles custom JSON serialization."""

    def default(self, obj):
        """Convert unserializable types for JSON encoding."""
        if isinstance(obj, datetime):
            # Stuffr uses ISO dates
            return obj.isoformat()

        return JSONEncoder.default(self, obj)


def create_app(config_override: Mapping = None) -> Flask:
    """Create the flask app for the debug server.

    Parameters:
        config_override:
            Dict containing custom configuration to apply after loading the
            normal config. Useful for testing.
    """
    config_override = {} if config_override is None else config_override
    app = Flask('stuffrdebugserver',
                instance_relative_config=True,
                static_url_path='',
                template_folder='static')
    app.config.from_object('config.default')
    app.config.from_envvar('STUFFR_SETTINGS')
    app.config.from_mapping(config_override)
    app.json_encoder = StuffrJSONEncoder
    global logger   # pylint: disable=global-statement
    logger = app.logger

    db.init_app(app)
    security = Security(app, user_store, confirm_register_form=StuffrRegisterForm)
    security.unauthorized_handler(api_unauthenticated_handler)
    Mail(app)

    app.register_blueprint(blueprint_simple, url_prefix='/simple')
    app.register_blueprint(blueprint_api, url_prefix='/api')
    app.register_blueprint(blueprint_apiadmin, url_prefix='/api/admin')

    return app


@user_registered.connect
def setup_new_user(*_, user: models.User, **__):
    """Initial setup for a new user.

    Called via signal handler on user creation. The only parameter we need is
    the user instance.
    """
    logger.info('Initializing new user %s', user.email)
    default_inventory = models.Inventory(
        # TODO: Adapt for missing first name, possesive when ends with S
        name='{}\'s stuff'.format(user.name_first),
        user=user)
    db.session.add(default_inventory)
    db.session.commit()
