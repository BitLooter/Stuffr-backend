"""Test cases for Stuffr models."""

import datetime
import pytest

from stuffrapp.api import models
from tests import conftest


pytestmark = pytest.mark.api_models

# The tests
#############


def test_fix_dict_datetimes():
    """Test function that sets datetimes in a dict without offsets to UTC."""
    PST_OFFSET = -8
    PST_TIME = conftest.TEST_TIME.replace(tzinfo=datetime.timezone(
        datetime.timedelta(hours=PST_OFFSET)))
    NOTZ_TIME = conftest.TEST_TIME.replace(tzinfo=None)
    test_dict = {
        'normal_time': conftest.TEST_TIME,
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


@pytest.mark.usefixtures('setupdb')
class ModelTestBase:
    """Base class for all model test classes."""

    pass


class TestCommonBase(ModelTestBase):
    """Tests for the models' common base class."""

    def test_check_id_exists(self):
        """Test that a thing with a given ID exists in the database."""
        thing_exists = models.Thing.id_exists(conftest.TEST_THING_ID)
        assert thing_exists
        bad_thing_exists = models.Thing.id_exists(conftest.TEST_THING_BAD_ID)
        assert not bad_thing_exists
