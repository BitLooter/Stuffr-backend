"""REST views for stuffr."""

import datetime
from http import HTTPStatus
import json
from flask import request, Blueprint

from . import models
from database import db

bp = Blueprint('stuffrapi', __name__)


@bp.errorhandler(HTTPStatus.BAD_REQUEST)
def defaulthandler(e):
    """Default exception handler to return JSON instead of HTML."""
    json_data = {'message': '{}: {}'.format(e.name, e.description)},
    return json_response(json_data, status_code=e.code)


def get_entity_names(entities):
    """Return a list containing the column names of all given entities."""
    return {c.key for c in entities}


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


def error_response(message, status_code=HTTPStatus.BAD_REQUEST):
    """Create a response object for errors."""
    return json_response({'message': message}, status_code=status_code)


def filter_user_fields(original_thing):
    """Return a dict that contains only the user fields from original_thing."""
    return {k: original_thing[k] for k in original_thing if k in USER_COLS}


def fix_thing_dict_times(thing):
    """Ensure datetimes have timezones in a Thing dict.

    Necessary because some databases (e.g. SQLite) do not store timezone
    information. Stuffr uses UTC in the database, so this just adds the UTC
    timezone to the datetime fields.
    """
    if thing['date_created'].tzinfo is None:
        thing['date_created'] = thing['date_created'].replace(
            tzinfo=datetime.timezone.utc)
    if thing['date_modified'].tzinfo is None:
        thing['date_modified'] = thing['date_modified'].replace(
            tzinfo=datetime.timezone.utc)
    return thing


def check_thing_request(request_data):
    """Perform common checks against thing request data."""
    message = None
    if type(request_data) != dict:
        if request_data is None:
            message = 'No data or NULL passed as data'
        else:
            message = 'Data in incorrect format, must be an object'
        return error_response(message)
    # Required fields are not Non-nullable
    if not all(request_data[f] is not None for f in request_data
               if f in REQUIRED_FIELDS):
        null_fields = [f for f in request_data if request_data[f] is None]
        return error_response(
            "Field(s) cannot be NULL: {}".format(', '.join(null_fields))
        )
    return message


NO_CONTENT = ('', HTTPStatus.NO_CONTENT)
# Fields sent to the client
CLIENT_ENTITIES = {models.Thing.id, models.Thing.name,
                   models.Thing.date_created, models.Thing.date_modified,
                   models.Thing.description, models.Thing.notes}
# Fields client is allowed to modify
USER_ENTITIES = {models.Thing.name,
                 models.Thing.description, models.Thing.notes}
USER_COLS = get_entity_names(USER_ENTITIES)
# These fields are initialized by the server, not passed in from the client.
SERVER_MANAGED_ENTITIES = {
    models.Thing.id, models.Thing.date_created, models.Thing.date_modified}
SERVER_MANAGED_COLS = get_entity_names(SERVER_MANAGED_ENTITIES)
# Fields that must have data
REQUIRED_FIELDS = {e.key for e in USER_ENTITIES if
                   models.Thing.__table__.columns[e.key].nullable is False}


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
        fixed_things.append(fix_thing_dict_times(thing._asdict()))
    return json_response(fixed_things)


@bp.route('/things', methods=['POST'])
def post_thing():
    """POST a thing to the database."""
    request_data = request.get_json()

    # Sanity check of data
    error_message = check_thing_request(request_data)
    if error_message:
        return error_response(error_message)
    # New things require certain fields
    if not REQUIRED_FIELDS.issubset(request_data):
        missing_fields = [f for f in REQUIRED_FIELDS
                          if f not in request_data]
        return error_response(
            "Required field(s) missing: {}".format(', '.join(missing_fields))
        )
    # Filter only desired fields
    new_thing_data = filter_user_fields(request_data)

    thing = models.Thing(**new_thing_data)
    db.session.add(thing)
    db.session.commit()
    # TODO: Error handling - what if database is down?
    initializedData = {k: thing.as_dict()[k] for k in SERVER_MANAGED_COLS}
    return json_response(initializedData, HTTPStatus.CREATED)


@bp.route('/things/<int:thing_id>', methods=['PUT'])
def update_thing(thing_id):
    """PUT (update) a thing in the database."""
    request_data = request.get_json()

    # Sanity check of data
    error_message = check_thing_request(request_data)
    if error_message:
        return error_response(error_message)
    # Filter only desired fields
    update_thing_data = filter_user_fields(request_data)

    models.Thing.query.filter_by(id=thing_id).update(update_thing_data)
    db.session.commit()
    # TODO: Handle updating a nonexistant item (error?)
    return NO_CONTENT


@bp.route('/things/<int:thing_id>', methods=['DELETE'])
def delete_thing(thing_id):
    """DELETE a thing in the database."""
    thing = models.Thing.query.get(thing_id)
    if thing is None:
        return error_response(
            'No thing with id {}'.format(thing_id),
            status_code=HTTPStatus.NOT_FOUND
        )
    thing.date_deleted = datetime.datetime.utcnow()
    db.session.commit()
    # TODO: Error handling
    # TODO: Handle updating a nonexistant item (error?)
    return NO_CONTENT
