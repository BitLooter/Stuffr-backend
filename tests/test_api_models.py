"""Test cases for Stuffr models."""

from stuffrapp.api import models


def test_flask_stuff():
    """Test Thing model."""
    thing = models.Thing(name='hello', description='desc', notes='notes')
    assert thing.name == 'hello'
    assert thing.description == 'desc'
    assert thing.notes == 'notes'
