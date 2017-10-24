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
