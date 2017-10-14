"""Test cases for Stuffr's simple HTML views."""

from http import HTTPStatus
import pytest
from flask import url_for

from stuffrapp.api import models
from tests.conftest import login_session


pytestmark = pytest.mark.simple_views

# Views that do not take arguments
views_generic = [
    ('simple_interface.main_view', {}),
    ('simple_interface.list_inventories', {})
]
# Views that take arguements (e.g. ID of a thing)
views_parameters = [
    ('simple_interface.list_things', {'inventory_id': 'test_inventory_id'}),
    ('simple_interface.thing_details', {'inventory_id': 'test_inventory_id',
                                        'thing_id': 'test_thing_id'})
]
# All views combined
views = views_generic + views_parameters


# The tests
#############

@pytest.mark.parametrize('view_name, param_names', views)
def test_all_authenticated(session_client, setupdb, view_name, param_names):
    """Test all views are OK."""
    view_params = {k: getattr(setupdb, v) for k, v in param_names.items()}
    url = url_for(view_name, **view_params)
    response = session_client.get(url)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize('view_name, param_names', views)
def test_all_unauthenticated(setupdb, client, view_name, param_names):
    """Test all views while not authenticated."""
    view_params = {k: getattr(setupdb, v) for k, v in param_names.items()}
    url = url_for(view_name, **view_params)
    auth_url = url_for('security.login')
    response = client.get(url)
    # Unauthenticated requests should be redirected to the login page
    assert response.status_code == HTTPStatus.FOUND
    assert auth_url in response.location


@pytest.mark.parametrize('view_name, param_names', views_parameters)
def test_incorrect_user_access(setupdb, client, view_name, param_names):
    """Test views that show specified items restrict access to correct user."""
    user = models.User.query.get(setupdb.test_alt_user_id)
    login_session(client, user.email, user.password)
    view_params = {k: getattr(setupdb, v) for k, v in param_names.items()}
    url = url_for(view_name, **view_params)
    response = client.get(url)
    assert response.status_code == HTTPStatus.FORBIDDEN


def test_show_invalid_inventory_contents(session_client, setupdb):
    """Test nonexistant inventories access is forbidden."""
    url = url_for('simple_interface.list_things',
                  inventory_id=setupdb.test_inventory_bad_id)
    response = session_client.get(url)
    assert response.status_code == HTTPStatus.FORBIDDEN


def test_show_invalid_thing(session_client, setupdb):
    """Test nonexistant thing access is forbidden."""
    # Correct inventory, invalid thing
    url = url_for('simple_interface.thing_details',
                  inventory_id=setupdb.test_inventory_id,
                  thing_id=setupdb.test_thing_bad_id)
    response = session_client.get(url)
    assert response.status_code == HTTPStatus.FORBIDDEN
    # Invalid inventory, correct thing
    url = url_for('simple_interface.thing_details',
                  inventory_id=setupdb.test_inventory_bad_id,
                  thing_id=setupdb.test_thing_id)
    response = session_client.get(url)
    assert response.status_code == HTTPStatus.BAD_REQUEST
