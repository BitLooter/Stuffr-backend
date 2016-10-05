"""Test cases for Stuffr views."""

import datetime
from http import HTTPStatus
import json
from flask import url_for
import pytest

from database import db
from stuffrapp.api import models

TEST_TIME = datetime.datetime(2011, 11, 11, 11, 11, 11,
                              tzinfo=datetime.timezone.utc)
THING_DATA = [
    {'name': 'thing1', 'date_created': TEST_TIME, 'date_modified': TEST_TIME,
     'description': "Test Thing 1", 'notes': "For unit testing"},
    {'name': 'thing2', 'date_created': TEST_TIME, 'date_modified': TEST_TIME,
     'description': "Test Thing 2", 'notes': "For unit testing"}
]


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


def post_as_json(request_func, path, data, method='POST'):
    """Convert an object to JSON data and post to path."""
    json_data = json.dumps(data)
    return request_func(path,
                        headers={'Content-Type': 'application/json'},
                        data=json_data)


def check_common_thing_errors(request_func, url, method, thing_id=None):
    """Check errors common to many views relating to thing objects."""
    # Malformed JSON
    response = request_func(url,
                            headers={'Content-Type': 'application/json'},
                            data='{Bad JSON')
    assert response.status_code == HTTPStatus.BAD_REQUEST

    # Null/None passed as data
    null_thing = None
    response = post_as_json(request_func, url, null_thing, method=method)
    assert response.status_code == HTTPStatus.BAD_REQUEST

    # Thing is a list instead of an object
    list_thing = []
    response = post_as_json(request_func, url, list_thing, method=method)
    assert response.status_code == HTTPStatus.BAD_REQUEST

    # Non-nullable field is null
    null_field_thing = {
        'name': None
    }
    response = post_as_json(request_func, url, null_field_thing, method=method)
    assert response.status_code == HTTPStatus.BAD_REQUEST


def check_ignore_nonuser_fields(request_func, url, thing_id, expected_status):
    """Check that a view does not modify non-user data."""
    server_field_thing = {
        'name': 'Ignore other field',
        'date_deleted': TEST_TIME.isoformat()
    }
    response = post_as_json(request_func, url, server_field_thing)
    if thing_id is None:
        thing_id = response.json['id']
    modified_thing = models.Thing.query.get(thing_id)
    assert modified_thing.date_deleted is None
    assert response.status_code == expected_status


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
    url = url_for('stuffrapi.get_things')

    response = client.get(url)
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
    new_thing_data = {
        'name': 'NEWTHING',
        'description': "Test new description",
        'notes': "Test new notes"}
    response_fields = {'id', 'date_created', 'date_modified'}
    server_fields = {'date_deleted'}
    things_url = url_for('stuffrapi.post_thing')

    response = post_as_json(client.post, things_url, new_thing_data)
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
                          if k not in response_fields.union(server_fields)}
    assert new_thing_data == created_thing_dict

    # Test error conditions
    #######################
    check_common_thing_errors(client.post, things_url, 'POST')
    check_ignore_nonuser_fields(client.post, things_url, None,
                                HTTPStatus.CREATED)

    # Empty object
    no_fields_thing = {}
    response = post_as_json(client.post, things_url, no_fields_thing)
    assert response.status_code == HTTPStatus.BAD_REQUEST

    # Required field missing
    missing_field_thing = {
        'description': "Missing name"
    }
    response = post_as_json(client.post, things_url, missing_field_thing)
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_update_thing(client):
    """Test PUT (updating) a thing."""
    original_thing = models.Thing.query.first()
    expected_data = original_thing.as_dict()
    expected_data['name'] = 'MODIFIED_NAME'
    expected_data['description'] = 'MODIFIED_DESC'
    expected_data['notes'] = 'MODIFIED_NOTES'
    thing_id = original_thing.id
    thing_url = url_for('stuffrapi.update_thing', thing_id=thing_id)
    modified_fields = {'name': expected_data['name'],
                       'description': expected_data['description'],
                       'notes': expected_data['notes']}

    response = post_as_json(client.put,
                            thing_url,
                            modified_fields)
    assert response.status_code == HTTPStatus.NO_CONTENT

    modified_data = models.Thing.query.get(thing_id).as_dict()
    # Do not compare modification date
    del modified_data['date_modified'], expected_data['date_modified']
    assert modified_data == expected_data

    # Test error conditions
    #######################
    check_common_thing_errors(client.put, thing_url, 'PUT')
    check_ignore_nonuser_fields(client.put, thing_url, thing_id,
                                HTTPStatus.NO_CONTENT)

    # Update nonexistant thing
    invalid_id_thing = {'name': 'Should fail'}
    invalid_id = db.session.query(db.func.max(models.Thing.id)).scalar() + 1
    response = post_as_json(client.put,
                            url_for('stuffrapi.update_thing',
                                    thing_id=invalid_id),
                            invalid_id_thing)
    assert response.status_code == HTTPStatus.NOT_FOUND

    # Check updating something that isn't a numerical ID
    # Using get_things because url_for checks type
    bad_id_thing = {'name': 'Should fail'}
    response = post_as_json(client.put,
                            url_for('stuffrapi.get_things') + '/notanid',
                            bad_id_thing)
    # Flask view looks for an int after /things, no view is set up for str
    assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED


def test_delete_thing(client):
    """Test DELETE a thing."""
    id_list = models.Thing.query.with_entities(models.Thing.id).all()
    id_list = [i[0] for i in id_list]
    thing_id = id_list[0]
    thing_to_delete = models.Thing.query.get(thing_id)
    url = url_for('stuffrapi.delete_thing', thing_id=thing_id)

    response = client.delete(url)
    assert response.status_code == HTTPStatus.NO_CONTENT
    assert thing_to_delete.date_deleted is not None

    # Check deleting nonexistant item
    invalid_id = db.session.query(db.func.max(models.Thing.id)).scalar() + 1
    response = client.delete(url_for('stuffrapi.delete_thing',
                                     thing_id=invalid_id))
    assert response.status_code == HTTPStatus.NOT_FOUND

    # Check deleting something that isn't a numerical ID
    # Using get_things because url_for checks type
    response = client.delete(url_for('stuffrapi.get_things') + '/notanid')
    # Flask view looks for an int after /things, no view is set up for str
    assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED

    # Check putting data in request
    data_thing_id = id_list[1]
    response = client.delete(url_for('stuffrapi.delete_thing',
                                     thing_id=data_thing_id),
                             headers={'Content-Type': 'application/json'},
                             data='Data should be ignored')
    assert response.status_code == HTTPStatus.NO_CONTENT
    assert models.Thing.query.get(data_thing_id).date_deleted is not None
