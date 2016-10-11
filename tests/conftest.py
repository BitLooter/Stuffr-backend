"""Common code for pytest."""

import pytest

from stuffrapp import create_app


@pytest.fixture
def app(scope='session'):
    """Fixture to set up Flask tests."""
    test_config = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite://',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'CREATE_TABLES': False,
        'INITIALIZE_DATABASE': False
    }
    app = create_app(config_override=test_config)
    return app
