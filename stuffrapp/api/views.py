"""REST views for stuffr."""

import datetime
from http import HTTPStatus
import json
from flask import request, Blueprint

from . import models
from database import db

bp = Blueprint('stuffrapi', __name__)


def get_entity_names(entities):
    """Return a list containing the column names of all given entities."""
    return [c.property.key for c in entities]


NO_CONTENT = ('', HTTPStatus.NO_CONTENT)
# Fields sent to the client
CLIENT_ENTITIES = (models.Thing.id, models.Thing.name,
                   models.Thing.date_created, models.Thing.date_modified,
                   models.Thing.description, models.Thing.notes)
# Fields client is allowed to modify
USER_ENTITIES = (models.Thing.name,
                 models.Thing.description, models.Thing.notes)
USER_COLS = get_entity_names(USER_ENTITIES)
# These fields are initialized by the server, not passed in from the client.
SERVER_INITIALIZED_ENTITIES = (
    models.Thing.id, models.Thing.date_created, models.Thing.date_modified)
SERVER_INITIALIZED_COLS = get_entity_names(SERVER_INITIALIZED_ENTITIES)


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


# Routes
#########

@bp.route('/things')
def get_things():
    """Provide a list of things from the database."""
    things = models.Thing.query.with_entities(*CLIENT_ENTITIES). \
        filter(models.Thing.date_deleted == None).all()  # noqa: E711
    # SQLite does not keep timezone information, assume UTC
    fixed_things = []
    for thing in things:
        fixed_thing = thing._asdict()
        if fixed_thing['date_created'].tzinfo is None:
            fixed_thing['date_created'] = fixed_thing['date_created'].replace(tzinfo=datetime.timezone.utc)
        if fixed_thing['date_modified'].tzinfo is None:
            fixed_thing['date_modified'] = fixed_thing['date_modified'].replace(tzinfo=datetime.timezone.utc)
        fixed_things.append(fixed_thing)
    return json_response(fixed_things)


@bp.route('/things', methods=['POST'])
def post_thing():
    """POST a thing to the database."""
    request_data = request.get_json()
    # Filter only desired fields
    new_thing_data = {k: request_data[k] for k in request_data
                      if k in USER_COLS}
    thing = models.Thing(**new_thing_data)
    db.session.add(thing)
    db.session.commit()
    # TODO: Error handling
    initializedData = {k: thing.as_dict()[k] for k in SERVER_INITIALIZED_COLS}
    return json_response(initializedData, HTTPStatus.CREATED)


@bp.route('/things/<int:thing_id>', methods=['PUT'])
def update_thing(thing_id):
    """PUT (update) a thing in the database."""
    request_data = request.get_json()
    # Filter only desired fields
    thing = models.Thing.query.get(thing_id)
    for field in USER_COLS:
        if field in request_data:
            setattr(thing, field, request_data[field])
    db.session.commit()
    # TODO: Error handling
    # TODO: Handle updating a nonexistant item (error?)
    return NO_CONTENT


@bp.route('/things/<int:thing_id>', methods=['DELETE'])
def delete_thing(thing_id):
    """DELETE a thing in the database."""
    thing = models.Thing.query.get(thing_id)
    thing.date_deleted = datetime.datetime.utcnow()
    db.session.commit()
    # TODO: Error handling
    # TODO: Handle updating a nonexistant item (error?)
    return NO_CONTENT
