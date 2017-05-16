"""Common code for pytest."""

import datetime
import pytest
from sqlalchemy.engine.url import URL

from stuffrapp import create_app

from database import db
from stuffrapp import user_store
from stuffrapp.api import models


# Test data
############
TEST_TIME = datetime.datetime(2011, 11, 11, 11, 11, 11,
                              tzinfo=datetime.timezone.utc)
TEST_TIME_COMPARE = datetime.datetime(2012, 12, 12, 12, 12, 12,
                                      tzinfo=datetime.timezone.utc)
# These are set in setupdb after the database is generated
TEST_USER_ID = None
TEST_INVENTORY_ID = None
TEST_INVENTORY_BAD_ID = None
TEST_THING_ID = None
TEST_THING_BAD_ID = None
# Generate test database
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


# Test fixtures
################

@pytest.fixture
def app(scope='session'):
    """Fixture to set up Flask tests."""
    test_config = {
        'SECRET_KEY': 'TEST',
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': URL(drivername='sqlite'),
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'STUFFR_CREATE_TABLES': False,
        'STUFFR_INITIALIZE_DATABASE': False
    }
    app = create_app(config_override=test_config)
    return app


@pytest.fixture
def setupdb(app):
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
    global TEST_INVENTORY_BAD_ID
    TEST_INVENTORY_BAD_ID = db.session.query(db.func.max(models.Inventory.id)).scalar() + 1
    global TEST_THING_ID
    TEST_THING_ID = models.Thing.query. \
        order_by(models.Thing.id.desc()). \
        filter_by(inventory_id=TEST_INVENTORY_ID).first().id
    global TEST_THING_BAD_ID
    TEST_THING_BAD_ID = db.session.query(db.func.max(models.Thing.id)).scalar() + 1
    yield
    db.session.remove()
    db.drop_all()
