"""Test cases for Stuffr's simple HTML views."""

from http import HTTPStatus
import pytest
from flask import url_for

from tests import conftest
from stuffrapp.api import models


pytestmark = pytest.mark.simple_views

# Views that do not take arguments
views_generic = [
    ('simple_interface.main_view', {}),
    ('simple_interface.list_inventories', {})
]
# Views that take arguements (e.g. ID of a thing)
views_parameters = [
    ('simple_interface.list_things', {'inventory_id': 'TEST_INVENTORY_ID'}),
    ('simple_interface.thing_details', {'inventory_id': 'TEST_INVENTORY_ID',
                                        'thing_id': 'TEST_THING_ID'})
]
# All views combined
views = views_generic + views_parameters


# Fixtures and helper functions
################################

def login_client(client, email, password):
    """Logs in a client with the given email and password as credentials."""
    login_url = url_for('security.login')
    client.post(login_url, data={'email': email, 'password': password})


@pytest.fixture
def session_client(client, setupdb):
    """Log in before using client."""
    user = models.User.query.get(conftest.TEST_USER_ID)
    login_client(client, user.email, user.password)
    return client


# The tests
#############

@pytest.mark.parametrize('view_name, param_names', views)
def test_all_authenticated(session_client, view_name, param_names):
    """Test all views are OK."""
    view_params = {k: getattr(conftest, v) for k, v in param_names.items()}
    url = url_for(view_name, **view_params)
    response = session_client.get(url)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize('view_name, param_names', views)
def test_all_unauthenticated(setupdb, client, view_name, param_names):
    """Test all views while not authenticated."""
    view_params = {k: getattr(conftest, v) for k, v in param_names.items()}
    url = url_for(view_name, **view_params)
    auth_url = url_for('security.login')
    response = client.get(url)
    # Unauthenticated requests should be redirected to the login page
    assert response.status_code == HTTPStatus.FOUND
    assert auth_url in response.location


@pytest.mark.parametrize('view_name, param_names', views_parameters)
def test_incorrect_user_access(setupdb, client, view_name, param_names):
    """Test views that show specified items restrict access to correct user."""
    user = models.User.query.get(conftest.TEST_ALT_USER_ID)
    login_client(client, user.email, user.password)
    view_params = {k: getattr(conftest, v) for k, v in param_names.items()}
    url = url_for(view_name, **view_params)
    response = client.get(url)
    assert response.status_code == HTTPStatus.FORBIDDEN


def test_show_invalid_inventory_contents(session_client):
    url = url_for('simple_interface.list_things',
                  inventory_id=conftest.TEST_INVENTORY_BAD_ID)
    response = session_client.get(url)
    assert response.status_code == HTTPStatus.FORBIDDEN


def test_show_invalid_thing(session_client):
    # Correct inventory, invalid thing
    url = url_for('simple_interface.thing_details',
                  inventory_id=conftest.TEST_INVENTORY_ID,
                  thing_id=conftest.TEST_THING_BAD_ID)
    response = session_client.get(url)
    assert response.status_code == HTTPStatus.FORBIDDEN
    # Invalid inventory, correct thing
    url = url_for('simple_interface.thing_details',
                  inventory_id=conftest.TEST_INVENTORY_BAD_ID,
                  thing_id=conftest.TEST_THING_ID)
    response = session_client.get(url)
    assert response.status_code == HTTPStatus.BAD_REQUEST
