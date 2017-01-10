"""Main file for Stuffr's backend."""

from typing import Mapping
from http import HTTPStatus
from flask import Flask
from sqlalchemy.orm.exc import MultipleResultsFound
from flask_security import Security, SQLAlchemyUserDatastore
from flask_security import user_registered
from flask_security.forms import ConfirmRegisterForm, StringField

from database import db
from .api.views import models
from .api.views import bp as blueprint_api, error_response

logger = None
user_store = SQLAlchemyUserDatastore(db, models.User, models.Role)


class StuffrRegisterForm(ConfirmRegisterForm):
    """Extended form for more fields during user registration."""

    # TODO: make required
    name_first = StringField('First name')
    name_last = StringField('Last name')


def api_unauthorized():
    """Response handler for unauthenticated requests to protected API calls."""
    logger.warning('Unauthenticated request')
    return error_response('You must be logged in to access this resource',
                          status_code=HTTPStatus.UNAUTHORIZED)


def create_app(config_override: Mapping={}) -> Flask:
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
    global logger
    logger = app.logger

    db.init_app(app)
    security = Security(app, user_store, confirm_register_form=StuffrRegisterForm)
    security._state.unauthorized_handler(api_unauthorized)
    # TODO: Better initial setup
    with app.app_context():
        if app.config['CREATE_TABLES']:
            db.create_all()
        if app.config['INITIALIZE_DATABASE']:
            initialize_database()

    app.register_blueprint(blueprint_api, url_prefix='/api')

    # connect() doesn't work for some reason, but the decorator does. Should
    # remove this workaround if a solution is found.
    @user_registered.connect_via(app)
    def new_user_signal_handler(app, user=None, confirm_token=None, **extra):
        setup_new_user(user)

    return app


def setup_new_user(user):
    """Initial setup for a new user."""
    logger.info('Initializing new user {}'.format(user.email))
    default_inventory = models.Inventory(
        # TODO: Adapt for missing first name, possesive when ends with S
        name='{}\'s stuff'.format(user.name_first),
        user=user)
    db.session.add(default_inventory)
    db.session.commit()


def initialize_database():
    """Set up the database with default data."""
    # TODO: make sure you test this after you get the server working against
    try:
        db_info = models.DatabaseInfo.query.one_or_none()
    except MultipleResultsFound as e:
        logger.error(
            'Multiple DatabaseInfo entries found. This shouldn\'t happen.')
        # TODO: Handle this error
        raise e

    # If no DatabaseInfo table, database has not been initialized
    if not db_info:
        logger.info('Performing first-time database initialization...')
        info = models.DatabaseInfo(creator_name='Stuffr', creator_version='alpha')
        db.session.add(info)
        db.session.commit()
