"""Main file for Stuffr's backend."""

from flask import Flask
from sqlalchemy.orm.exc import MultipleResultsFound

from database import db
from .api.views import models
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
    try:
        db_info = models.StuffrInfo.query.one_or_none()
    except MultipleResultsFound as e:
        # TODO: Handle this error
        raise e

    # If `None` database had not been initialized
    if not db_info:
        info = models.StuffrInfo(creator_name='Stuffr')
        db.session.add(info)

        default_user = models.User(name='DEFAULT_USER')
        db.session.add(default_user)
        default_inventory = models.Inventory(
            name='DEFAULT_INVENTORY',
            owner=default_user)
        db.session.add(default_inventory)
        db.session.commit()
