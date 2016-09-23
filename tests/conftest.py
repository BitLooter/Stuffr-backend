"""Common code for pytest."""
#
import pytest
from flask import Flask

from database import db


@pytest.fixture
def app(scope='session'):
    """Fixture to set up Flask tests."""
    # TODO: Use actual app
    app = Flask('Stuffr-testing')
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    from stuffrapp.api.views import bp as stuffr_bp
    app.register_blueprint(stuffr_bp)
    return app
