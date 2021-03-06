"""Common code for pytest."""

from collections import namedtuple
import datetime
import json
from http import HTTPStatus
import pytest
from flask import url_for, session
from flask_security.utils import login_user
from sqlalchemy.engine.url import URL

from stuffrapp import create_app, user_store
from stuffrapp.api import models
from database import db


# Utility functions
####################

def _generate_test_data():
    """Dynamically generate data for testing."""
    test_data = []
    for user in range(2):
        user_data = {'name_first': 'User u{}'.format(user),
                     'name_last': 'User U{}'.format(user),
                     'email': 'email{}@example.com'.format(user),
                     'password': 'testing',
                     'inventories': []}
        for inventory in range(2):
            inventory_data = {'name': 'Test Inventory U{}I{}'.format(user, inventory),
                              'things': []}
            for thing in range(2):
                ident = 'T{}'.format(thing)
                thing_data = {'name': 'Test Thing U{}I{}{}'.format(user, inventory, ident),
                              'date_created': TEST_TIME,
                              'date_modified': TEST_TIME,
                              'location': '{} location'.format(ident),
                              'details': '{} details'.format(ident)}
                inventory_data['things'].append(thing_data)
            user_data['inventories'].append(inventory_data)
        test_data.append(user_data)
    return test_data


def post_as_json(request_func, path, data):
    """Convert an object to JSON data and post to path."""
    json_data = json.dumps(data)
    return request_func(path,
                        headers={'Content-Type': 'application/json'},
                        data=json_data)


def _login_session(test_app, client):
    """Logs in a client with the with the client's user.

    Expects client to have an attribute 'user' with the user object that will
    be logged in.

    Uses session-based authentication and intended to be used by the
    session_client fixture (cookie-based session management). For token-based
    AJAX authentication, use the authenticated_client fixture.
    """
    login_user(client.user)
    # Session will be lost for the actual test, manually add session cookie
    session_serializer = test_app.session_interface.get_signing_serializer(test_app)
    session_cookie = session_serializer.dumps(dict(session))
    client.set_cookie('localhost', 'session', session_cookie)


# Test data
############
TEST_TIME = datetime.datetime(2011, 11, 11, 11, 11, 11,
                              tzinfo=datetime.timezone.utc)
TEST_TIME_COMPARE = datetime.datetime(2012, 12, 12, 12, 12, 12,
                                      tzinfo=datetime.timezone.utc)
TEST_DATA = _generate_test_data()
TEST_NEW_USER = {
    'email': 'testnewuser@example.com',
    'password': 'hunter2',
    'name_first': 'TEST',
    'name_last': 'USER'
}
TEST_NEW_THING = {
    'name': 'Test NEW name',
    'location': 'Test NEW location',
    'details': 'Test NEW details'
}
TEST_UPDATE_THING = {
    'name': 'Test MODIFIED name',
    'location': 'Test MODIFIED location',
    'details': 'Test MODIFIED details'
}


# Test fixtures
################

@pytest.fixture(scope='session')
def app():
    """Fixture to set up Flask tests."""
    test_config = {
        'SECRET_KEY': 'TEST',
        'TESTING': True,
        'DEBUG': False,
        'SECURITY_PASSWORD_HASH': 'plaintext',
        'SQLALCHEMY_DATABASE_URI': URL(drivername='sqlite'),
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'MAIL_SUPPRESS_SEND': True
    }
    new_app = create_app(config_override=test_config)
    return new_app


@pytest.fixture
def setupdb(app):  # pylint: disable=redefined-outer-name,unused-argument
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

    # Set up test values
    test_user_id = models.User.query.order_by(models.User.id.desc()).first().id
    test_inventory_id = models.Inventory.query. \
        order_by(models.Inventory.id.desc()).filter_by(user_id=test_user_id).first().id
    test_values_dict = {
        'test_user_id': test_user_id,
        'test_alt_user_id': models.User.query.order_by(models.User.id.asc()).first().id,
        'test_user_bad_id': db.session.query(db.func.max(models.User.id)).scalar() + 1,
        'test_inventory_id': test_inventory_id,
        'test_inventory_bad_id': db.session.query(db.func.max(models.Inventory.id)).scalar() + 1,
        'test_thing_id': models.Thing.query.
                         order_by(models.Thing.id.desc()).
                         filter_by(inventory_id=test_inventory_id).first().id,
        'test_thing_bad_id': db.session.query(db.func.max(models.Thing.id)).scalar() + 1
    }
    test_values = namedtuple('TestData', test_values_dict.keys())(**test_values_dict)

    yield test_values
    db.session.remove()
    db.drop_all()


@pytest.fixture
def authenticated_client(request, client, setupdb):  # pylint: disable=redefined-outer-name
    """Rewrite client requests to include an authentication token."""
    user_id = None
    if 'use_alt_user' in request.keywords:
        print(f'authenticated_client: Using alternate user ID {setupdb.test_alt_user_id}')
        user_id = setupdb.test_alt_user_id
    else:
        print(f'authenticated_client: Using default user ID {setupdb.test_user_id}')
        user_id = setupdb.test_user_id
    client.user = models.User.query.get(user_id)

    login_user(client.user)
    token = client.user.get_auth_token()

    def open_proxy(*args, **kwargs):
        """Proxy client to automatically insert authentication header"""
        if 'headers' not in kwargs:
            kwargs['headers'] = {}
        kwargs['headers']['Authentication-Token'] = token
        return client.open_(*args, **kwargs)
    client.open_ = client.open
    client.open = open_proxy

    return client


@pytest.fixture
def session_client(request, app, client, setupdb):  # pylint: disable=redefined-outer-name
    """Log in using session-based authentication."""
    user_id = None
    if 'use_alt_user' in request.keywords:
        print(f'session_client: Using alternate user ID {setupdb.test_alt_user_id}')
        user_id = setupdb.test_alt_user_id
    else:
        print(f'session_client: Using default user ID {setupdb.test_user_id}')
        user_id = setupdb.test_user_id
    client.user = models.User.query.get(user_id)
    _login_session(app, client)
    return client


# Common test code
###################

class CommonViewTests:
    """Base class with tests common to all views."""

    item_id = None
    view_params = {}

    def test_unauthenticated(self, client):
        """Test that view requires user to be logged in."""
        url = url_for(self.view_name, **self.view_params)
        request_func = getattr(client, self.method)
        response = request_func(url)
        assert response.status_code == HTTPStatus.UNAUTHORIZED
        assert response.headers['Content-Type'] == 'application/json'
