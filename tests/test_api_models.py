"""Test cases for Stuffr models."""

from collections import abc
import pytest

from stuffrapp.api import models
from stuffrapp.api.errors import InvalidDataError, ItemNotFoundError, \
    UserPermissionError
from tests import conftest


pytestmark = pytest.mark.api_models

# The tests
#############


@pytest.mark.usefixtures('setupdb')
class ModelTestBase:
    """Base class for all model test classes."""

    item_id = None
    item_bad_id = None

    def test_check_id_exists(self):
        """Test that a thing with a given ID exists in the database."""
        item_exists = self.model.id_exists(self.item_id)
        assert item_exists
        bad_item_exists = self.model.id_exists(self.item_bad_id)
        assert not bad_item_exists

    def test_get_client_entities(self):
        """Test that it properly filters client entities."""
        entity_names = {e.key for e in self.model.get_client_entities()}
        assert entity_names == self.model.CLIENT_FIELDS

    def test_filter_user_input_dict(self):
        """Test that it properly filters input from the user."""
        correct_data = {k: None for k in self.model.USER_FIELDS}
        filtered_correct_data = self.model.filter_user_input_dict(correct_data)
        assert set(filtered_correct_data.keys()) == self.model.USER_FIELDS

        extra_data = correct_data.copy()
        extra_data['_filter_me_'] = None
        filtered_extra_data = self.model.filter_user_input_dict(extra_data)
        assert set(filtered_extra_data.keys()) == self.model.USER_FIELDS

        if len(self.model.USER_FIELDS) > 0:
            missing_data = correct_data.copy()
            # Doesn't matter which item is deleted, just use the first one Python grabs
            del missing_data[list(missing_data.keys())[0]]
            filtered_missing_data = self.model.filter_user_input_dict(missing_data)
            assert set(filtered_missing_data.keys()) < self.model.USER_FIELDS

    def test_total_count(self):
        """Test that it properly determines the total number of rows."""
        query_count = len(self.model.query.all())
        model_count = self.model.total_count()
        assert query_count == model_count


class TestUserModel(ModelTestBase):
    """Test cases for Users."""

    model = models.User

    @pytest.fixture(autouse=True)
    def set_ids(self, setupdb):
        """Set IDs used in common tests."""
        self.item_id = setupdb.test_user_id
        self.item_bad_id = setupdb.test_user_bad_id


class TestInventoryModel(ModelTestBase):
    """Test cases for Inventories."""

    model = models.Inventory

    @pytest.fixture(autouse=True)
    def set_ids(self, setupdb):
        """Set IDs used in common tests."""
        self.item_id = setupdb.test_inventory_id
        self.item_bad_id = setupdb.test_inventory_bad_id

    def test_get_user_inventories(self):
        """Check that all inventories for a user are returned."""
        expected_inventories = conftest.TEST_DATA[-1]['inventories']
        expected_inventory_names = [i['name'] for i in expected_inventories]
        expected_user_email = conftest.TEST_DATA[-1]['email']
        test_user_id = models.User.query.filter_by(email=expected_user_email).one().id
        user_inventories = self.model.get_user_inventories(test_user_id)
        assert isinstance(user_inventories, list)
        assert all(isinstance(i, self.model) for i in user_inventories)
        user_inventory_names = [i.name for i in user_inventories]
        assert user_inventory_names == expected_inventory_names

    def test_create_new_inventory(self, setupdb):
        """Check creating a new inventory."""
        new_data = {'name': 'NEW_INVENTORY'}
        new_inventory = self.model.create_new_inventory(new_data, setupdb.test_user_id)
        assert new_inventory.name == 'NEW_INVENTORY'

        with pytest.raises(InvalidDataError):
            missing_data = {}
            self.model.create_new_inventory(missing_data, setupdb.test_user_id)

        with pytest.raises(ItemNotFoundError):
            self.model.create_new_inventory(new_data, setupdb.test_user_bad_id)


class TestThingModel(ModelTestBase):
    """Test cases for Things."""

    model = models.Thing

    @pytest.fixture(autouse=True)
    def set_ids(self, setupdb):
        """Set IDs used in common tests."""
        self.item_id = setupdb.test_thing_id
        self.item_bad_id = setupdb.test_thing_bad_id

    def test_get_things_for_inventory(self, setupdb):
        """Test getting all things for a specific inventory."""
        num_test_things = self.model.query. \
            filter_by(inventory_id=setupdb.test_inventory_id, date_deleted=None). \
            count()
        things = self.model.get_things_for_inventory(
            setupdb.test_inventory_id,
            setupdb.test_user_id)
        assert isinstance(things, abc.Sequence)
        assert len(things) == num_test_things
        assert all(isinstance(t, self.model) for t in things)

    def test_get_thing(self, setupdb):
        """Test that thing details are retreived."""
        thing = self.model.get_thing(setupdb.test_thing_id, setupdb.test_user_id)
        assert isinstance(thing, self.model)
        assert thing.id == setupdb.test_thing_id

        # Invalid thing
        with pytest.raises(ItemNotFoundError):
            self.model.get_thing(setupdb.test_thing_bad_id, setupdb.test_user_id)

        # Thing unowned
        with pytest.raises(UserPermissionError):
            self.model.get_thing(setupdb.test_thing_id, setupdb.test_alt_user_id)

    def test_create_new_thing(self, setupdb):
        """Test creating new things."""
        # Everything correct
        new_thing = self.model.create_new_thing(conftest.TEST_NEW_THING,
                                                setupdb.test_inventory_id,
                                                setupdb.test_user_id)
        assert isinstance(new_thing, self.model)

        # Missing a required field
        new_thing_missing = conftest.TEST_NEW_THING.copy()
        del new_thing_missing['name']
        with pytest.raises(InvalidDataError):
            self.model.create_new_thing(new_thing_missing,
                                        setupdb.test_inventory_id,
                                        setupdb.test_user_id)

        # Contains non-writable field

        # Empty object
        with pytest.raises(InvalidDataError):
            self.model.create_new_thing({},
                                        setupdb.test_inventory_id,
                                        setupdb.test_user_id)

        # None object
        with pytest.raises(InvalidDataError):
            self.model.create_new_thing(None,
                                        setupdb.test_inventory_id,
                                        setupdb.test_user_id)

        # List of things
        with pytest.raises(InvalidDataError):
            thing_data_list = [conftest.TEST_NEW_THING, conftest.TEST_NEW_THING]
            self.model.create_new_thing(thing_data_list,
                                        setupdb.test_inventory_id,
                                        setupdb.test_user_id)

        # Invalid inventory
        with pytest.raises(ItemNotFoundError):
            self.model.create_new_thing(new_thing_missing,
                                        setupdb.test_inventory_bad_id,
                                        setupdb.test_user_id)

        # Unowned inventory
        with pytest.raises(UserPermissionError):
            self.model.create_new_thing(new_thing_missing,
                                        setupdb.test_inventory_id,
                                        setupdb.test_alt_user_id)

        # Invalid user
        with pytest.raises(ItemNotFoundError):
            self.model.create_new_thing(new_thing_missing,
                                        setupdb.test_inventory_id,
                                        setupdb.test_user_bad_id)

    def test_update_thing(self, setupdb):
        """Test that thing data is updated."""
        # Everything correct
        new_thing = self.model.update_thing(setupdb.test_thing_id,
                                            conftest.TEST_UPDATE_THING,
                                            setupdb.test_user_id)
        assert isinstance(new_thing, dict)

        # Contains non-writable field

        # Empty object
        empty_update_results = self.model.update_thing(setupdb.test_thing_id,
                                                       {},
                                                       setupdb.test_user_id)
        assert list(empty_update_results.keys()) == ['date_modified']

        # None object
        with pytest.raises(InvalidDataError):
            self.model.update_thing(setupdb.test_thing_id,
                                    None,
                                    setupdb.test_user_id)

        # List of things
        with pytest.raises(InvalidDataError):
            thing_data_list = [conftest.TEST_NEW_THING, conftest.TEST_NEW_THING]
            self.model.update_thing(setupdb.test_thing_id,
                                    thing_data_list,
                                    setupdb.test_user_id)

        # Invalid thing
        with pytest.raises(ItemNotFoundError):
            self.model.update_thing(setupdb.test_thing_bad_id,
                                    conftest.TEST_UPDATE_THING,
                                    setupdb.test_user_id)

        # Unowned thing
        with pytest.raises(UserPermissionError):
            self.model.update_thing(setupdb.test_thing_id,
                                    conftest.TEST_UPDATE_THING,
                                    setupdb.test_alt_user_id)

        # Invalid user
        with pytest.raises(ItemNotFoundError):
            self.model.update_thing(setupdb.test_thing_id,
                                    conftest.TEST_UPDATE_THING,
                                    setupdb.test_user_bad_id)

    def test_delete_thing(self, setupdb):
        """Test that things are deleted."""
        # Correct data
        self.model.delete_thing(setupdb.test_thing_id, setupdb.test_user_id)
        deleted_thing = self.model.query.get(setupdb.test_thing_id)
        assert deleted_thing.date_deleted is not None

        # Invalid thing
        with pytest.raises(ItemNotFoundError):
            self.model.delete_thing(setupdb.test_thing_bad_id,
                                    setupdb.test_user_id)

        # Unowned thing
        with pytest.raises(UserPermissionError):
            self.model.delete_thing(setupdb.test_thing_id,
                                    setupdb.test_alt_user_id)
