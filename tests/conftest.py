"""Common code for pytest."""

import pytest
from sqlalchemy.engine.url import URL

from stuffrapp import create_app


@pytest.fixture
def app(scope='session'):
    """Fixture to set up Flask tests."""
    test_config = {
        'SECRET_KEY': 'TEST',
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': URL(drivername='sqlite'),
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'STUFFR_CREATE_TABLES': False,
        'STUFFR_INITIALIZE_DATABASE': False
    }
    app = create_app(config_override=test_config)
    return app
