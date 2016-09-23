"""Test cases for Stuffr models."""

from stuffrapp.api import models


def test_flask_stuff():
    """Test Thing model."""
    thing = models.Thing(name='hello')
    assert thing.name == 'hello'
