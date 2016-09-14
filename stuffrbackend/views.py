"""REST views for stuffr."""

import datetime
from http import HTTPStatus
import json
from flask import request

from stuffrbackend import bp
import stuffrbackend.models as models
from database import db

NO_CONTENT = ('', HTTPStatus.NO_CONTENT)
# These fields are created by the server, not passed in from the client.
SERVER_CREATED_FIELDS = ('id', 'date_created', 'date_modified')


def serialize_object(obj):
    """Convert unserializable types for JSON encoding."""
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    else:
        raise TypeError("JSON: Cannot serialize {}".format(type(obj)))


def json_response(data, status_code=HTTPStatus.OK):
    """Create a response object suitable for JSON data."""
    json_data = json.dumps(data, default=serialize_object)
    return json_data, status_code, {'Content-Type': 'application/json'}


@bp.route('/things')
def get_things():
    """Provide a list of things from the database."""
    things = models.Thing.query.all()
    things_list = [t.as_dict() for t in things]
    return json_response(things_list)


@bp.route('/things', methods=['POST'])
def post_thing():
    """POST a thing to the database."""
    thing = models.Thing(name=request.get_json()['name'])
    db.session.add(thing)
    db.session.commit()
    # TODO: Error handling
    # TODO: Prevent setting backend-managed columns such as id, date_created, etc.
    initializedData = {k: thing.as_dict()[k] for k in SERVER_CREATED_FIELDS}
    return json_response(initializedData, HTTPStatus.CREATED)


@bp.route('/things/<int:thing_id>', methods=['PUT'])
def update_thing(thing_id):
    """PUT (update) a thing in the database."""
    thing = models.Thing.query.get(thing_id)
    thing.name = request.get_json()['name']
    db.session.commit()
    # TODO: Error handling
    # TODO: Handle updating a nonexistant item (error?)
    return NO_CONTENT


@bp.route('/things/<int:thing_id>', methods=['DELETE'])
def delete_thing(thing_id):
    """DELETE a thing in the database."""
    models.Thing.query.filter_by(id=thing_id).delete()
    db.session.commit()
    # TODO: Error handling
    # TODO: Handle updating a nonexistant item (error?)
    return NO_CONTENT
