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
    {'name': 'thing1', 'date_created': TEST_TIME, 'date_modified': TEST_TIME},
    {'name': 'thing2', 'date_created': TEST_TIME, 'date_modified': TEST_TIME}
]


def post_as_json(client, path, data, method='POST'):
    """Convert an object to JSON data and post to path."""
    json_data = json.dumps(data)
    if method == 'POST':
        client_func = client.post
    elif method == 'PUT':
        client_func = client.put
    else:
        # TODO: Raise an error
        pass
    return client_func(path,
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

# The tests
#############


def test_get_things(client):
    """Test GETing Things."""
    # Prepare test data
    expected_response = []
    for thing in THING_DATA:
        expected_thing = thing.copy()
        expected_thing['date_created'] = thing['date_created'].isoformat()
        expected_thing['date_modified'] = thing['date_modified'].isoformat()
        expected_response.append(expected_thing)

    response = client.get('/things')
    assert response.status_code == HTTPStatus.OK
    assert response.headers['Content-Type'] == 'application/json'

    response_data = response.json
    assert isinstance(response_data, list)
    assert len(response_data) == len(THING_DATA)

    # Verify the test data and only the test data is returned
    for response_thing in response_data:
        assert response_thing['id'] is not None
        del response_thing['id']
        assert response_thing in expected_response
        expected_response.remove(response_thing)
    assert expected_response == [], "Unknown things in database"


def test_post_thing(client):
    """Test POSTing Things."""
    new_thing_data = {'name': 'NEWTHING'}
    response_fields = {'id', 'date_created', 'date_modified'}

    response = post_as_json(client, '/things', new_thing_data)
    assert response.status_code == HTTPStatus.CREATED
    assert response.headers['Content-Type'] == 'application/json'

    new_thing_response = response.json
    assert isinstance(new_thing_response, dict)
    assert set(new_thing_response) == response_fields

    created_thing = models.Thing.query.get(new_thing_response['id'])
    assert created_thing is not None
    created_thing_dict = created_thing.as_dict()
    # Remove fields added by database
    created_thing_dict = {k: created_thing_dict[k] for k in created_thing_dict
                          if k not in response_fields}
    assert new_thing_data == created_thing_dict


def test_update_thing(client):
    """Test PUT (updating) a thing."""
    original_thing = models.Thing.query.first()
    expected_thing = original_thing.as_dict()
    expected_thing['name'] = 'MODIFIED'
    thing_id = original_thing.id
    modified_fields = {'name': 'MODIFIED'}

    response = post_as_json(client,
                            '/things/{}'.format(thing_id),
                            modified_fields,
                            method='PUT')
    assert response.status_code == HTTPStatus.NO_CONTENT

    modified_thing = models.Thing.query.get(thing_id)
    assert modified_thing.name == original_thing.name
    assert modified_thing.name == expected_thing['name']


def test_delete_thing(client):
    """Test DELETE a thing."""
    original_thing = models.Thing.query.first()
    thing_id = original_thing.id
    original_count = models.Thing.query.count()
    expected_count = original_count - 1

    response = client.delete('/things/{}'.format(thing_id))
    assert response.status_code == HTTPStatus.NO_CONTENT
    modified_thing = models.Thing.query.get(thing_id)
    assert modified_thing is None
    assert models.Thing.query.count() == expected_count
