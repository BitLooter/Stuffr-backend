"""Test cases for Stuffr models."""

import pytest

from stuffrapp.api import models
from tests import conftest


pytestmark = pytest.mark.api_models

# The tests
#############


@pytest.mark.usefixtures('setupdb')
class ModelTestBase:
    """Base class for all model test classes."""

    def test_check_id_exists(self):
        """Test that a thing with a given ID exists in the database."""
        item_exists = self.model.id_exists(self.item_id)
        assert item_exists
        bad_item_exists = self.model.id_exists(self.item_bad_id)
        assert not bad_item_exists


class TestUserModel(ModelTestBase):
    """Test cases for Users."""

    model = models.User
    item_id = property(lambda _: conftest.TEST_USER_ID)
    item_bad_id = property(lambda _: conftest.TEST_USER_BAD_ID)


class TestInventoryModel(ModelTestBase):
    """Test cases for Inventories."""

    model = models.Inventory
    item_id = property(lambda _: conftest.TEST_INVENTORY_ID)
    item_bad_id = property(lambda _: conftest.TEST_INVENTORY_BAD_ID)

    def test_get_user_inventories(self):
        """Check that all inventories for a user are returned."""
        expected_inventories = conftest.TEST_DATA[-1]['inventories']
        expected_inventory_names = [i['name'] for i in expected_inventories]
        expected_user_email = conftest.TEST_DATA[-1]['email']
        test_user_id = models.User.query.filter_by(email=expected_user_email).one().id
        user_inventories = self.model.get_user_inventories(test_user_id)
        assert type(user_inventories) == list
        assert all(isinstance(i, self.model) for i in user_inventories)
        user_inventory_names = [i.name for i in user_inventories]
        assert user_inventory_names == expected_inventory_names


class TestThingModel(ModelTestBase):
    """Test cases for Things."""

    model = models.Thing
    item_id = property(lambda _: conftest.TEST_THING_ID)
    item_bad_id = property(lambda _: conftest.TEST_THING_BAD_ID)
