"""Test cases for Stuffr views' helper functions."""

import datetime
from http import HTTPStatus
import pytest

from stuffrapp.api import views

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


def test_filter_user_fields():
    """Test function used to extract user fields from an input dict."""
    VALID_FIELDS = {'name'}
    server_field_thing = {
        'name': 'Should be in returned object',
        'date_created': 'Should not be in returned object'
    }
    cleaned_thing = views.filter_user_fields(server_field_thing)
    assert VALID_FIELDS == cleaned_thing.keys()

    bad_field_thing = {
        'name': 'Should be in returned object',
        'DOESNOTEXIST': 'Should not be in returned object'
    }
    cleaned_thing = views.filter_user_fields(bad_field_thing)
    assert VALID_FIELDS == cleaned_thing.keys()


def test_fix_dict_datetimes():
    """Test function that sets datetimes in a dict without offsets to UTC."""
    PST_OFFSET = -8
    PST_TIME = TEST_TIME.replace(tzinfo=datetime.timezone(
        datetime.timedelta(hours=PST_OFFSET)))
    NOTZ_TIME = TEST_TIME.replace(tzinfo=None)
    test_dict = {
        'normal_time': TEST_TIME,
        'pst_time': PST_TIME,
        'notz_time': NOTZ_TIME,
        'not_datetime': 4
    }
    fixed_thing = views.fix_dict_datetimes(test_dict)
    assert fixed_thing['normal_time'].tzinfo == datetime.timezone.utc
    assert fixed_thing['pst_time'].tzinfo == datetime.timezone(
        datetime.timedelta(hours=PST_OFFSET))
    assert fixed_thing['notz_time'].tzinfo == datetime.timezone.utc
    assert fixed_thing['not_datetime'] == 4


def test_check_thing_request():
    """Test function that does a sanity check of thing data input."""
    # Test normal function
    message = views.check_thing_request({'name': 'Test name'})
    assert message is None

    # Test empty dict
    message = views.check_thing_request({})
    assert message is None

    # Test not a dict
    message = views.check_thing_request([])
    assert message is not None

    # Test missing required fields
    message = views.check_thing_request({'name': None})
    assert message is not None
