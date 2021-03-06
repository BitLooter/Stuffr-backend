"""Test cases for Stuffr views' helper functions."""

import datetime
from http import HTTPStatus
import pytest

from stuffrapp.api import views_common
from tests.conftest import TEST_TIME


def test_serialize_object():
    """Test the function used to serialize objects for JSON transport."""
    serialized_time = views_common.serialize_object(TEST_TIME)
    assert serialized_time == TEST_TIME.isoformat()
    with pytest.raises(TypeError):
        # Functions are not serializable
        views_common.serialize_object(test_serialize_object)


def test_json_response():
    """Test function used to prepare an HTTP response for JSON data."""
    # Basic test
    data, status, headers = views_common.json_response(1)
    assert data == '1'
    assert status == HTTPStatus.OK
    assert headers == {'Content-Type': 'application/json'}
    # Special object serialization
    the_time = datetime.datetime.now()
    data, status, headers = views_common.json_response(the_time)
    assert data == '"{}"'.format(the_time.isoformat())
    # Custom status code
    data, status, headers = views_common.json_response('STATUS CODE TEST',
                                                       status_code=HTTPStatus.CREATED)
    assert status == HTTPStatus.CREATED
    # Unserializable ojbects given
    with pytest.raises(TypeError):
        views_common.json_response(test_json_response)
