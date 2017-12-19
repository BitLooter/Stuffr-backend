"""Test cases for Stuffr's simple HTML views."""

import pytest
from flask_security import user_registered
from flask_security.registerable import register_user

from tests.conftest import TEST_NEW_USER


pytestmark = pytest.mark.auth


# The tests
#############

@pytest.mark.appsettings(SECURITY_SEND_REGISTER_EMAIL=False)
@pytest.mark.usefixtures('setupdb')
def test_new_user_setup():
    """Test new user creation initial setup.

    New user setup is handled with a signal handler, running when
    Flask-Security flashes a user_registered signal.
    """
    assert user_registered.receivers
    user = register_user(**TEST_NEW_USER)
    # New users get a default inventory
    assert user.inventories.count() == 1
