"""Test cases for Stuffr models."""

import datetime

from stuffrapp.api import models
from .sample_data import TEST_TIME


def test_flask_stuff():
    """Test Thing model."""
    # FIXME: this test isn't really necessary, i should be testing the class methods
    thing = models.Thing(name='hello', location='loc', details='dets')
    assert thing.name == 'hello'
    assert thing.location == 'loc'
    assert thing.details == 'dets'


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
    fixed_thing = models.fix_dict_datetimes(test_dict)
    assert fixed_thing['normal_time'].tzinfo == datetime.timezone.utc
    assert fixed_thing['pst_time'].tzinfo == datetime.timezone(
        datetime.timedelta(hours=PST_OFFSET))
    assert fixed_thing['notz_time'].tzinfo == datetime.timezone.utc
    assert fixed_thing['not_datetime'] == 4
