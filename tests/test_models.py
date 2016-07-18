"""Test cases for Stuffr models."""

from flask import Flask
from flask_testing import TestCase

from database import db

from stuffrbackend import models


class TestStuffrModels(TestCase):
    """Test Stuffr models module."""

    def create_app(self):
        """Create the Flask app used by Flask-Testing."""
        app = Flask('Stuffr-testing')
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        db.init_app(app)
        return app

    def setUp(self):
        """Prepare test database."""
        db.create_all()

    def tearDown(self):
        """Tear down test database."""
        db.session.remove()
        db.drop_all()

    def test_thing(self):
        """Test Thing model."""
        thing = models.Thing(name='hello')
        self.assertIsInstance(thing, models.Thing)
        self.assertEqual(thing.name, 'hello')
