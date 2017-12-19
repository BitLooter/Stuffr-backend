"""Test cases for Stuffr views."""

from http import HTTPStatus
import pytest
from flask import url_for

from tests import conftest


pytestmark = pytest.mark.api_views


# The tests
############

class TestGetAdminStats(conftest.CommonViewTests):
    """Tests for getting stats about the database."""

    view_name = 'stuffrapi_admin.admin_stats'
    method = 'get'

    def test_get_stats(self, authenticated_client):
        """Test GETing stats."""
        # Prepare test data
        num_users = 0
        num_inventories = 0
        num_things = 0
        for user_data in conftest.TEST_DATA:
            num_users += 1
            for inventory in user_data['inventories']:
                num_inventories += 1
                num_things += len(inventory['things'])
        url = url_for(self.view_name)

        response = authenticated_client.get(url)
        assert response.status_code == HTTPStatus.OK
        assert response.headers['Content-Type'] == 'application/json'

        response_data = response.json
        assert isinstance(response_data, dict)
        assert response_data['numUsers'] == num_users


class TestGetAdminUsers(conftest.CommonViewTests):
    """Tests for getting stats about the database."""

    view_name = 'stuffrapi_admin.admin_users'
    method = 'get'

    def test_get_users(self, authenticated_client):
        """Test GETing users."""
        # Prepare test data
        num_users = len(conftest.TEST_DATA)
        url = url_for(self.view_name)

        response = authenticated_client.get(url)
        assert response.status_code == HTTPStatus.OK
        assert response.headers['Content-Type'] == 'application/json'

        response_data = response.json
        assert isinstance(response_data, list)
        assert len(response_data) == num_users


def test_admin_root_error(client):
    """Sanity check that root behaves as expected."""
    url = url_for('stuffrapi_admin.root')
    response = client.get(url)
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.headers['Content-Type'] == 'application/json'
