"""Test cases for Stuffr views."""

from http import HTTPStatus
import json

from flask import Flask
from flask_testing import TestCase

from database import db
from stuffrbackend import models


class CommonAssertions:
    """Assertions that will be used by most or all test classes in this module."""

    def assertStatusOk(self, response):
        """Check that an HTTP response is OK (200)."""
        if response.status_code != HTTPStatus.OK:
            raise AssertionError("Wrong status code (should be {} [OK]): {}".format(
                HTTPStatus.OK, response.status_code
            ))

    def assertStatusCreated(self, response):
        """Check that an HTTP response is CREATED (201)."""
        if response.status_code != HTTPStatus.CREATED:
            raise AssertionError("Wrong status code (should be {} [CREATED]): {}".format(
                HTTPStatus.CREATED, response.status_code
            ))

    def assertJsonHeader(self, response):
        """Check that a JSON response has the correct headers."""
        content_type = response.headers['Content-Type']
        if content_type != 'application/json':
            raise AssertionError("Wrong Content-Type for JSON: " + content_type)


class TestStuffrViews(TestCase, CommonAssertions):
    """Test Stuffr views module."""

    def create_app(self):
        """Create the Flask app used by Flask-Testing."""
        app = Flask('Stuffr-testing')
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        db.init_app(app)
        from stuffrbackend import bp as stuffr_bp
        app.register_blueprint(stuffr_bp)

        return app

    def setUp(self):
        """Prepare test database."""
        db.create_all()

        # Create some test data
        self.thing_data = [
            {'name': 'thing1'},
            {'name': 'thing2'}
        ]
        things = [models.Thing(**t) for t in self.thing_data]
        db.session.add_all(things)
        db.session.commit()

    def tearDown(self):
        """Tear down test database."""
        db.session.remove()
        db.drop_all()

    def post_json(self, path, data):
        """Convert an object to JSON data and post to path."""
        json_data = json.dumps(data)
        return self.client.post(path,
                                headers={'Content-Type': 'application/json'},
                                data=json_data)

    # The actual tests

    def test_get_things(self):
        """Test GETing Things."""
        response = self.client.get('/things')
        self.assertStatusOk(response)
        self.assertJsonHeader(response)

        data = response.json
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), len(self.thing_data))

    def test_post_things(self):
        """Test POSTing Things."""
        new_thing = {'name': 'newthing'}
        response = self.post_json('/things', new_thing)
        self.assertStatusCreated(response)
        self.assertJsonHeader(response)

        data = response.json
        # ID can not be determined ahead of time and will interfere with this test
        del data['id']
        self.assertIsInstance(data, dict)
        self.assertSetEqual(set(data), set(new_thing))
