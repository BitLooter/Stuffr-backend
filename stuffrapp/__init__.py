"""Main file for Stuffr's backend."""

from typing import Mapping
from http import HTTPStatus
from flask import Flask
from sqlalchemy.orm.exc import MultipleResultsFound
from flask_security import Security, SQLAlchemyUserDatastore

from database import db
from .api.views import models
from .api.views import bp as blueprint_api, error_response

logger = None
user_store = SQLAlchemyUserDatastore(db, models.User, models.Role)


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
    security = Security(app, user_store)
    security._state.unauthorized_handler(api_unauthorized)
    # TODO: Better initial setup
    with app.app_context():
        if app.config['CREATE_TABLES']:
            db.create_all()
        if app.config['INITIALIZE_DATABASE']:
            initialize_database()

    app.register_blueprint(blueprint_api, url_prefix='/api')

    return app


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

        create_new_user('default@example.com', 'password', 'DEFAULT', 'USER')
        create_new_user('default2@example.com', 'password', 'TEST', 'USER2')


def create_new_user(email: str, password: str, first_name: str, last_name: str):
    """Initial setup for a new user."""
    logger.info('Creating new user {}'.format(email))
    default_user = user_store.create_user(
        email=email, password=password,
        name_first=first_name, name_last=last_name)
    default_inventory = models.Inventory(
        # TODO: Adapt for missing first name, possesive when ends with S
        name='{}\'s stuff'.format(first_name),
        user=default_user)
    db.session.add(default_inventory)
    db.session.commit()
