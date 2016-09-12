"""Test cases for Stuffr views' helper functions."""

import datetime
from http import HTTPStatus
import pytest

from stuffrbackend import views

TEST_TIME = datetime.datetime(2011, 11, 11, 11, 11, 11,
                              tzinfo=datetime.timezone.utc)


def test_serialize_object():
    """Test the function used to serialize objects for JSON transport."""
    serialized_time = views.serialize_object(TEST_TIME)
    assert serialized_time == TEST_TIME.isoformat()
    with pytest.raises(TypeError):
        # Functions are not serializable
        views.serialize_object(test_serialize_object)


def test_json_response():
    """Test function used to prepare an HTTP response for JSON data."""
    # Basic test
    data, status, headers = views.json_response(1)
    assert data == '1'
    assert status == HTTPStatus.OK
    assert headers == {'Content-Type': 'application/json'}
    # Special object serialization
    the_time = datetime.datetime.now()
    data, status, headers = views.json_response(the_time)
    assert data == '"{}"'.format(the_time.isoformat())
    # Custom status code
    data, status, headers = views.json_response('STATUS CODE TEST',
                                                status_code=HTTPStatus.CREATED)
    assert status == HTTPStatus.CREATED
    # Unserializable ojbects given
    with pytest.raises(TypeError):
        views.json_response(test_json_response)
