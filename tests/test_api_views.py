"""Test cases for Stuffr views."""

import datetime
from http import HTTPStatus
import json
import pytest
from flask import url_for

from database import db
from stuffrapp.api import models
from stuffrapp import user_store

TEST_TIME = datetime.datetime(2011, 11, 11, 11, 11, 11,
                              tzinfo=datetime.timezone.utc)
# Generate test data
TEST_DATA = []
for u in range(2):
    user_data = {'name_first': 'User u{}'.format(u),
                 'name_last': 'User U{}'.format(u),
                 'email': 'email{}@example.com'.format(u),
                 'password': 'testing',
                 'inventories': []}
    for i in range(2):
        inventory_data = {'name': 'Test Inventory U{}I{}'.format(u, i), 'things': []}
        for t in range(2):
            ident = 'T{}'.format(t)
            thing_data = {'name': 'Test Thing U{}I{}{}'.format(u, i, ident),
                          'date_created': TEST_TIME,
                          'date_modified': TEST_TIME,
                          'location': '{} location'.format(ident),
                          'details': '{} details'.format(ident)}
            inventory_data['things'].append(thing_data)
        user_data['inventories'].append(inventory_data)
    TEST_DATA.append(user_data)
TEST_USER_ID = None
TEST_INVENTORY_ID = None
TEST_THING_ID = None


def post_as_json(request_func, path, data, method='POST'):
    """Convert an object to JSON data and post to path."""
    json_data = json.dumps(data)
    return request_func(path,
                        headers={'Content-Type': 'application/json'},
                        data=json_data)


@pytest.fixture(autouse=True)
def setupdb():
    """Prepare the test database before use."""
    db.create_all()
    # Create test database from generated test data
    for user_data in TEST_DATA:
        user_filtered = {k: user_data[k] for k in user_data
                         if k != 'inventories'}
        user = user_store.create_user(**user_filtered)
        for inventory_data in user_data['inventories']:
            inventory_filtered = {k: inventory_data[k] for k in inventory_data
                                  if k != 'things'}
            inventory = models.Inventory(user=user, **inventory_filtered)
            db.session.add(inventory)
            for thing_data in inventory_data['things']:
                thing = models.Thing(inventory=inventory, **thing_data)
                db.session.add(thing)
    db.session.commit()
    # Set up variables to be used in tests
    # Select the last item in each group to detect bugs involving query.first()
    global TEST_USER_ID
    TEST_USER_ID = models.User.query.order_by(models.User.id.desc()).first().id
    global TEST_INVENTORY_ID
    TEST_INVENTORY_ID = models.Inventory.query. \
        order_by(models.Inventory.id.desc()). \
        filter_by(user_id=TEST_USER_ID).first().id
    global TEST_THING_ID
    TEST_THING_ID = models.Thing.query. \
        order_by(models.Thing.id.desc()). \
        filter_by(inventory_id=TEST_INVENTORY_ID).first().id
    yield
    db.session.remove()
    db.drop_all()


@pytest.fixture
def authenticated_client(client):
    """Rewrite client requests to include an authentication token."""
    client.user = models.User.query.get(TEST_USER_ID)
    login_url = url_for('security.login')
    credentials = {
        'email': client.user.email,
        'password': client.user.password}
    response = post_as_json(client.post, login_url, credentials)
    token = response.json['response']['user']['authentication_token']

    # Proxy client to automatically insert authentication header
    def open_proxy(*args, **kwargs):
        if 'headers' not in kwargs:
            kwargs['headers'] = {}
        kwargs['headers']['Authentication-Token'] = token
        return client._open(*args, **kwargs)
    client._open = client.open
    client.open = open_proxy

    return client


# The tests
#############

class CommonTests:
    """Base class with tests common to all views."""

    view_params = {}

    def test_unauthenticated(self, client):
        """Test that view requires user to be logged in."""
        url = url_for(self.view_name, **self.view_params)
        request_func = getattr(client, self.method)
        response = request_func(url)
        assert response.status_code == HTTPStatus.UNAUTHORIZED
        assert response.headers['Content-Type'] == 'application/json'


class ThingPostMixin:
    """Mixin to perform common tests for POST/PUT of things."""

    def test_malformed_json(self, authenticated_client):
        """Test response to an invalid JSON string."""
        url = url_for(self.view_name, **self.view_params)
        request_func = getattr(authenticated_client, self.method)
        response = request_func(url,
                                headers={'Content-Type': 'application/json'},
                                data='{Bad JSON')
        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_null_data(self, authenticated_client):
        """Test None/NULL passed as data."""
        url = url_for(self.view_name, **self.view_params)
        request_func = getattr(authenticated_client, self.method)
        null_thing = None
        response = post_as_json(request_func, url, null_thing,
                                method=self.method)
        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_list_thing(self, authenticated_client):
        """Thing is a list instead of an object."""
        url = url_for(self.view_name, **self.view_params)
        request_func = getattr(authenticated_client, self.method)
        list_thing = []
        response = post_as_json(request_func, url, list_thing,
                                method=self.method)
        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_null_value(self, authenticated_client):
        """Non-nullable field is null."""
        url = url_for(self.view_name, **self.view_params)
        request_func = getattr(authenticated_client, self.method)
        null_field_thing = {
            'name': None
        }
        response = post_as_json(request_func, url, null_field_thing,
                                method=self.method)
        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_ignore_nonuser_fields(self, authenticated_client):
        """Check that a view does not modify non-user data."""
        url = url_for(self.view_name, **self.view_params)
        server_field_thing = {
            'name': 'Ignore other field',
            'date_deleted': TEST_TIME.isoformat()
        }
        request_func = getattr(authenticated_client, self.method)
        response = post_as_json(request_func, url, server_field_thing)
        assert response.status_code < 300

        thing_id = TEST_THING_ID
        if response.status_code != HTTPStatus.NO_CONTENT:
            if 'id' in response.json:
                thing_id = response.json['id']

        modified_thing = models.Thing.query.get(thing_id)
        assert modified_thing.date_deleted is None


class TestGetUserInfo(CommonTests):
    """Tests for getting user info."""

    view_name = 'stuffrapi.get_userinfo'
    method = 'get'

    def test_get_userinfo(self, authenticated_client):
        """Test GETing UserInfo."""
        # Prepare test data
        for user_data in TEST_DATA:
            if user_data['email'] == authenticated_client.user.email:
                expected_response = user_data.copy()
                del expected_response['password']
                del expected_response['inventories']
                expected_response['id'] = authenticated_client.user.id
        url = url_for(self.view_name)

        response = authenticated_client.get(url)
        assert response.status_code == HTTPStatus.OK
        assert response.headers['Content-Type'] == 'application/json'

        response_data = response.json
        assert isinstance(response_data, dict)
        assert response_data == expected_response


class TestGetInventories(CommonTests):
    """Tests for getting inventories."""

    view_name = 'stuffrapi.get_inventories'
    method = 'get'

    def test_get_inventories(self, authenticated_client):
        """Test GETing Inventories."""
        # Prepare test data
        for user_data in TEST_DATA:
            if user_data['email'] == authenticated_client.user.email:
                test_data = user_data['inventories']
        expected_response = []
        for inventory in user_data['inventories']:
            expected_inventory = inventory.copy()
            del expected_inventory['things']
            expected_response.append(expected_inventory)
        url = url_for(self.view_name)

        response = authenticated_client.get(url)
        assert response.status_code == HTTPStatus.OK
        assert response.headers['Content-Type'] == 'application/json'

        response_data = response.json
        assert isinstance(response_data, list)
        assert len(response_data) == len(test_data)
        # Verify the test data and only the test data is returned
        for response_inventory in response_data:
            # Remove generated data
            del response_inventory['id']
            del response_inventory['date_created']
            assert response_inventory in expected_response
            expected_response.remove(response_inventory)
        assert expected_response == [], "Unknown inventories in database"


class TestPostInventory(CommonTests, ThingPostMixin):
    """Tests for adding inventories."""

    view_name = 'stuffrapi.post_inventory'
    method = 'post'
    new_inventory_data = {
        'name': 'NEWINVENTORY'}
    response_fields = {'id', 'date_created'}

    def test_post_inventory(self, authenticated_client):
        """Test POSTing inventories."""
        url = url_for(self.view_name, **self.view_params)
        # Fields added by the backend
        server_fields = {'user_id'}

        response = post_as_json(authenticated_client.post, url, self.new_inventory_data)
        assert response.status_code == HTTPStatus.CREATED
        assert response.headers['Content-Type'] == 'application/json'

        new_inventory_response = response.json
        assert isinstance(new_inventory_response, dict)
        assert set(new_inventory_response) == self.response_fields

        created_inventory = models.Inventory.query.get(new_inventory_response['id'])
        assert created_inventory is not None
        created_inventory_dict = created_inventory.as_dict()
        # Remove fields added by backend
        created_inventory_dict = {k: created_inventory_dict[k] for k in created_inventory_dict
                                  if k not in self.response_fields.union(server_fields)}
        assert self.new_inventory_data == created_inventory_dict

    def test_post_inventory_with_extra_data(self, authenticated_client):
        """Test POSTing inventories with nonexistant or non-user-editable fields."""
        url = url_for(self.view_name, **self.view_params)
        # Fields added by the backend
        server_fields = {'user_id'}

        extra_inventory_data = self.new_inventory_data.copy()
        extra_inventory_data['not_a_real_field'] = 'Will be removed from input'
        extra_inventory_data['date_created'] = TEST_TIME.isoformat()

        response = post_as_json(authenticated_client.post, url, extra_inventory_data)
        assert response.status_code == HTTPStatus.CREATED
        assert response.headers['Content-Type'] == 'application/json'

        new_inventory_response = response.json
        assert isinstance(new_inventory_response, dict)
        assert set(new_inventory_response) == self.response_fields

        created_inventory = models.Inventory.query.get(new_inventory_response['id'])
        assert created_inventory is not None
        # Time specified above should have been ignored
        assert created_inventory.date_created != TEST_TIME
        created_inventory_dict = created_inventory.as_dict()
        # Remove fields added by backend
        created_inventory_dict = {k: created_inventory_dict[k] for k in created_inventory_dict
                                  if k not in self.response_fields.union(server_fields)}
        assert self.new_inventory_data == created_inventory_dict

    def test_post_empty_object(self, authenticated_client):
        """Test posting an empty object."""
        url = url_for(self.view_name, **self.view_params)
        no_fields_inventory = {}
        response = post_as_json(authenticated_client.post, url, no_fields_inventory)
        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_required_field_missing(self, authenticated_client):
        """Test posting with a missing required field."""
        url = url_for(self.view_name, **self.view_params)
        # Required field missing
        missing_field_inventory = {
            'description': "Missing name"
        }
        response = post_as_json(authenticated_client.post, url, missing_field_inventory)
        assert response.status_code == HTTPStatus.BAD_REQUEST


class TestGetThings(CommonTests):
    """Tests for getting things."""

    view_name = 'stuffrapi.get_things'
    method = 'get'

    def setup_method(self):
        """Specify inventory ID.

        Params must be specified here as they are unknown until the setup_db
        fixture is run.
        """
        self.view_params = {'inventory_id': TEST_INVENTORY_ID}

    def test_get_things(self, authenticated_client):
        """Test GETing Things."""
        # Prepare test data
        url = url_for(self.view_name, **self.view_params)
        expected_response = []
        things = models.Thing.query. \
            filter_by(inventory_id=TEST_INVENTORY_ID).all()
        for thing in things:
            if thing.date_created.tzinfo is None:
                thing.date_created = thing.date_created.replace(
                    tzinfo=datetime.timezone.utc)
            if thing.date_modified.tzinfo is None:
                thing.date_modified = thing.date_modified.replace(
                    tzinfo=datetime.timezone.utc)
            if thing.date_deleted is not None:
                if thing.date_deleted.tzinfo is None:
                    thing.date_deleted = thing.date_deleted.replace(
                        tzinfo=datetime.timezone.utc)
            expected_thing = thing.as_dict()
            expected_thing['date_created'] = \
                expected_thing['date_created'].isoformat()
            expected_thing['date_modified'] = \
                expected_thing['date_modified'].isoformat()
            del expected_thing['inventory_id']
            expected_response.append(expected_thing)

        response = authenticated_client.get(url)
        assert response.status_code == HTTPStatus.OK
        assert response.headers['Content-Type'] == 'application/json'

        response_data = response.json
        assert isinstance(response_data, list)
        assert len(response_data) == len(expected_response)
        # Verify the test data and only the test data is returned
        for response_thing in response_data:
            assert response_thing in expected_response
            expected_response.remove(response_thing)
        assert expected_response == [], "Unknown things in database"

    def test_get_from_nonexistant_inventory(self, authenticated_client):
        """Test getting the things from an inventory that doesn't exist."""
        invalid_id = db.session.query(
            db.func.max(models.Inventory.id)).scalar() + 1
        url = url_for(self.view_name, inventory_id=invalid_id)
        response = authenticated_client.get(url)
        assert response.status_code == HTTPStatus.NOT_FOUND
        assert response.headers['Content-Type'] == 'application/json'

    def test_wrong_user(self, authenticated_client):
        """Test that getting an inventory's things as the wrong user fails."""
        # Find an inventory that does not belong to the logged-in user
        for inventory in models.Inventory.query.all():
            if inventory.user_id != TEST_USER_ID:
                unowned_id = inventory.id
                break
        url = url_for(self.view_name, inventory_id=unowned_id)

        response = authenticated_client.get(url)
        assert response.status_code == HTTPStatus.FORBIDDEN


class TestPostThing(CommonTests, ThingPostMixin):
    """Tests for adding things."""

    view_name = 'stuffrapi.post_thing'
    method = 'post'
    new_thing_data = {
        'name': 'NEWTHING',
        'location': "Test new location",
        'details': "Test new details"}
    response_fields = {'id', 'date_created', 'date_modified', 'date_deleted'}

    def setup_method(self):
        """Specify inventory ID."""
        self.view_params = {'inventory_id': TEST_INVENTORY_ID}

    def test_post_thing(self, authenticated_client):
        """Test POSTing Things."""
        url = url_for(self.view_name, **self.view_params)
        # Fields part of the full thing data but not returned
        server_fields = {'date_deleted', 'inventory_id'}

        response = post_as_json(authenticated_client.post, url, self.new_thing_data)
        assert response.status_code == HTTPStatus.CREATED
        assert response.headers['Content-Type'] == 'application/json'

        new_thing_response = response.json
        assert isinstance(new_thing_response, dict)
        assert set(new_thing_response) == self.response_fields

        created_thing = models.Thing.query.get(new_thing_response['id'])
        assert created_thing is not None
        created_thing_dict = created_thing.as_dict()
        # Remove fields added by database
        created_thing_dict = {k: created_thing_dict[k] for k in created_thing_dict
                              if k not in self.response_fields.union(server_fields)}
        assert self.new_thing_data == created_thing_dict

    def test_post_thing_with_extra_data(self, authenticated_client):
        """Test POSTing Things with nonexistant or non-user-editable fields."""
        url = url_for(self.view_name, **self.view_params)
        # Fields part of the full thing data but not returned
        server_fields = {'date_deleted', 'inventory_id'}

        extra_thing_data = self.new_thing_data.copy()
        extra_thing_data['not_a_real_field'] = 'Will be removed from input'
        extra_thing_data['date_created'] = TEST_TIME.isoformat()

        response = post_as_json(authenticated_client.post, url, extra_thing_data)
        assert response.status_code == HTTPStatus.CREATED
        assert response.headers['Content-Type'] == 'application/json'

        new_thing_response = response.json
        assert isinstance(new_thing_response, dict)
        assert set(new_thing_response) == self.response_fields

        created_thing = models.Thing.query.get(new_thing_response['id'])
        assert created_thing is not None
        # Time specified above should have been ignored
        assert created_thing.date_created != TEST_TIME
        created_thing_dict = created_thing.as_dict()
        # Remove fields added by database
        created_thing_dict = {k: created_thing_dict[k] for k in created_thing_dict
                              if k not in self.response_fields.union(server_fields)}
        assert self.new_thing_data == created_thing_dict

    def test_post_empty_object(self, authenticated_client):
        """Test posting an empty object."""
        url = url_for(self.view_name, **self.view_params)
        no_fields_thing = {}
        response = post_as_json(authenticated_client.post, url, no_fields_thing)
        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_required_field_missing(self, authenticated_client):
        """Test posting with a missing required field."""
        url = url_for(self.view_name, **self.view_params)
        # Required field missing
        missing_field_thing = {
            'description': "Missing name"
        }
        response = post_as_json(authenticated_client.post, url, missing_field_thing)
        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_nonexistant_inventory(self, authenticated_client):
        """Test posting to an inventory that doesn't exist."""
        # Nonexistant inventory
        invalid_id = db.session.query(
            db.func.max(models.Inventory.id)).scalar() + 1
        invalid_url = url_for('stuffrapi.post_thing', inventory_id=invalid_id)
        response = post_as_json(authenticated_client.post, invalid_url, self.new_thing_data)
        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_unowned_inventory(self, authenticated_client):
        """Test posting to an inventory owned by another user."""
        # Find an inventory that does not belong to the logged-in user
        for inventory in models.Inventory.query.all():
            if inventory.user_id != TEST_USER_ID:
                unowned_id = inventory.id
                break
        url = url_for(self.view_name, inventory_id=unowned_id)

        response = post_as_json(authenticated_client.post, url, self.new_thing_data)
        assert response.status_code == HTTPStatus.FORBIDDEN


class TestPutThing(CommonTests, ThingPostMixin):
    """Tests for updating things."""

    view_name = 'stuffrapi.update_thing'
    method = 'put'

    def setup_method(self, method):
        """Specify inventory ID."""
        self.view_params = {'thing_id': TEST_THING_ID}

    def test_update_thing(self, authenticated_client):
        """Test PUT (updating) a thing."""
        url = url_for(self.view_name, **self.view_params)
        original_thing = models.Thing.query.get(TEST_THING_ID)
        expected_data = original_thing.as_dict()
        update_data = {'name': 'CHANGED NAME',
                       'location': 'CHANGED LOCATION',
                       'details': 'CHANGED DETAILS'}
        expected_data.update(update_data)

        response = post_as_json(authenticated_client.put, url, update_data)
        assert response.status_code == HTTPStatus.OK

        modified_data = models.Thing.query.get(TEST_THING_ID).as_dict()
        # Check modification date changed but don't bother comparing
        assert modified_data['date_modified'] > TEST_TIME
        del modified_data['date_modified'], expected_data['date_modified']
        assert modified_data == expected_data

    def test_update_nonexistant_thing(self, authenticated_client):
        """Test updating a nonexistant thing."""
        invalid_id = db.session.query(db.func.max(models.Thing.id)).scalar() + 1
        invalid_url = url_for('stuffrapi.update_thing', thing_id=invalid_id)
        invalid_id_thing = {'name': 'Should fail'}
        response = post_as_json(authenticated_client.put, invalid_url, invalid_id_thing)
        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_update_nonint_id(self, authenticated_client):
        """Test updating with an invalid noninteger ID."""
        # Build manually because url_for checks type
        # TODO: base off url_for('stuffrapi.search_things')
        notint_url = '/api/things/not_id'
        bad_id_thing = {'name': 'Should fail'}
        response = post_as_json(authenticated_client.put, notint_url, bad_id_thing)
        # Flask view looks for an int after /things, no view is set up for str
        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED

    def test_unowned_thing(self, authenticated_client):
        """Test updating a thing owned by another user."""
        # Find an inventory that does not belong to the logged-in user
        for inventory in models.Inventory.query.all():
            if inventory.user_id != TEST_USER_ID:
                test_thing = inventory.things[0]
                break
        url = url_for(self.view_name, thing_id=test_thing.id)

        response = post_as_json(authenticated_client.put, url,
                                {'name': 'Should be forbidden'})
        assert response.status_code == HTTPStatus.FORBIDDEN


class TestDeleteThing(CommonTests):
    """Tests for deleting things."""

    view_name = 'stuffrapi.delete_thing'
    method = 'delete'

    def setup_method(self):
        """Specify URL params."""
        self.view_params = {'thing_id': TEST_THING_ID}

    def test_delete_thing(self, authenticated_client):
        """Test DELETE a thing."""
        url = url_for(self.view_name, **self.view_params)
        thing_to_delete = models.Thing.query.get(TEST_THING_ID)

        response = authenticated_client.delete(url)
        assert response.status_code == HTTPStatus.NO_CONTENT
        assert thing_to_delete.date_deleted is not None

    def test_delete_nonexistant_item(self, authenticated_client):
        """Test deleting a thing not present in the database."""
        invalid_id = db.session.query(db.func.max(models.Thing.id)).scalar() + 1
        response = authenticated_client.delete(
            url_for('stuffrapi.delete_thing', thing_id=invalid_id))
        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_delete_nonint_id(self, authenticated_client):
        """Test deleting a thing using a non-integer ID."""
        # Build manually because url_for checks type
        # TODO: base off url_for('stuffrapi.search_things')
        notint_url = '/api/things/not_id'
        response = authenticated_client.delete(notint_url)
        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED

    def test_delete_post_data(self, authenticated_client):
        """Test deleting ignores data in request."""
        url = url_for(self.view_name, **self.view_params)
        response = authenticated_client.delete(
            url,
            headers={'Content-Type': 'application/json'},
            data='Data should be ignored')
        assert response.status_code == HTTPStatus.NO_CONTENT
        thing_to_delete = models.Thing.query.get(TEST_THING_ID)
        assert thing_to_delete.date_deleted is not None

    def test_unowned_thing(self, authenticated_client):
        """Test deleting a thing owned by another user."""
        # Find an inventory that does not belong to the logged-in user
        for inventory in models.Inventory.query.all():
            if inventory.user_id != TEST_USER_ID:
                test_thing = inventory.things[0]
                break
        url = url_for(self.view_name, thing_id=test_thing.id)

        response = authenticated_client.delete(url)
        assert response.status_code == HTTPStatus.FORBIDDEN
