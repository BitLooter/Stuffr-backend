"""Test cases for Stuffr views."""

import datetime
from http import HTTPStatus
import json
import pytest

from database import db
from stuffrbackend import models

TEST_TIME = datetime.datetime(2011, 11, 11, 11, 11, 11,
                              tzinfo=datetime.timezone.utc)
THING_DATA = [
    {'name': 'thing1', 'date_created': TEST_TIME},
    {'name': 'thing2', 'date_created': TEST_TIME}
]


def post_as_json(client, path, data):
    """Convert an object to JSON data and post to path."""
    json_data = json.dumps(data)
    return client.post(path,
                       headers={'Content-Type': 'application/json'},
                       data=json_data)


@pytest.fixture(autouse=True)
def setupdb():
    """Prepare the test database before use."""
    db.create_all()
    things = [models.Thing(**t) for t in THING_DATA]
    db.session.add_all(things)
    db.session.commit()
    yield
    db.session.remove()
    db.drop_all()


def test_get_things(app, client):
    """Test GETing Things."""
    response = client.get('/things')
    assert response.status_code == HTTPStatus.OK
    assert response.headers['Content-Type'] == 'application/json'

    response_data = response.json
    assert isinstance(response_data, list)
    assert len(response_data) == len(THING_DATA)

    # Prepare test data
    expected_response = []
    for thing in THING_DATA:
        expected_thing = thing.copy()
        expected_thing['date_created'] = thing['date_created'].isoformat()
        expected_response.append(expected_thing)
    # Verify the test data and only the test data is returned
    for response_thing in response_data:
        assert 'id' in response_thing
        del response_thing['id']
        assert response_thing in expected_response
        expected_response.remove(response_thing)
    assert expected_response == [], "Unknown things in database"


def test_post_thing(app, client):
    """Test POSTing Things."""
    new_thing = {'name': 'newthing'}
    response_fields = {'id', 'date_created'}

    response = post_as_json(client, '/things', new_thing)
    assert response.status_code == HTTPStatus.CREATED
    assert response.headers['Content-Type'] == 'application/json'

    new_thing_response = response.json
    assert isinstance(new_thing_response, dict)
    assert set(new_thing_response) == response_fields
    # TODO: When getting specific items is implemented get and check this one
