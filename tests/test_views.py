"""Test cases for Stuffr views."""

import datetime
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

    def assertDictEqualWithoutId(self, dict_a, dict_b):
        """Check that both dicts are identical after removing IDs."""
        del dict_a


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
        test_time = datetime.datetime(2011, 11, 11, 11, 11, 11,
                                      tzinfo=datetime.timezone.utc)
        self.thing_data = [
            {'name': 'thing1', 'date_created': test_time},
            {'name': 'thing2', 'date_created': test_time}
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

        response_data = response.json
        self.assertIsInstance(response_data, list,
                              "Things GET response is not a list")
        self.assertEqual(len(response_data), len(self.thing_data),
                         "Things GET response did not return correct number of items")

        # Prepare test data
        expected_response = []
        for thing in self.thing_data.copy():
            thing['date_created'] = thing['date_created'].isoformat()
            expected_response.append(thing)
        # Verify the test data and only the test data is returned
        for response_thing in response_data:
            thing_copy = response_thing.copy()
            del thing_copy['id']
            with self.subTest("Match test", thing=thing_copy):
                self.assertIn(thing_copy, self.thing_data)
                expected_response.remove(thing_copy)
        self.assertListEqual(expected_response, [],
                             "Unknown things in database")

    def test_post_thing(self):
        """Test POSTing Things."""
        new_thing = {'name': 'newthing'}
        response_fields = {'id', 'date_created'}
        response = self.post_json('/things', new_thing)
        self.assertStatusCreated(response)
        self.assertJsonHeader(response)

        new_thing_response = response.json
        self.assertIsInstance(new_thing_response, dict,
                              "Thing POST response is not a dict")
        self.assertSetEqual(set(new_thing_response), response_fields,
                            "Thing POST response does not match required fields")
        # TODO: When getting specific items is implemented get and check this one
