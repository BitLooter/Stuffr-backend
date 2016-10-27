"""REST views for stuffr."""

import datetime
from http import HTTPStatus
import json
from typing import Dict, Tuple
from flask import request, Blueprint
from sqlalchemy import exists

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
    return {k: original_thing[k] for k in original_thing
            if k in THING_USER_FIELDS}


def fix_dict_datetimes(the_dict):
    """Ensure datetimes have timezones in a dict from SQLAlchemy.

    Necessary because some databases (e.g. SQLite) do not store timezone
    information. Stuffr uses UTC in the database, so this just adds the UTC
    timezone to the datetime fields.
    """
    for k, v in the_dict.items():
        if type(v) is datetime.datetime and v.tzinfo is None:
            the_dict[k] = v.replace(tzinfo=datetime.timezone.utc)
    return the_dict


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
               if f in THING_REQUIRED_FIELDS):
        null_fields = [f for f in request_data if request_data[f] is None]
        return error_response(
            "Field(s) cannot be NULL: {}".format(', '.join(null_fields))
        )
    return message


def check_inventory_exists(inventory_id: int) -> bool:
    """Check that inventory_id is an actual inventory in the database."""
    inventory_exists = db.session.query(
        exists().where(models.Inventory.id == inventory_id)).scalar()
    if not inventory_exists:
        return 'No inventory with id {}'.format(inventory_id)


NO_CONTENT = ('', HTTPStatus.NO_CONTENT)
# Fields sent to the client
THING_CLIENT_ENTITIES = {
    models.Thing.id, models.Thing.name,
    models.Thing.date_created, models.Thing.date_modified,
    models.Thing.date_deleted,
    models.Thing.description, models.Thing.notes,
    models.Thing.inventory_id}
INVENTORY_CLIENT_ENTITIES = {
    models.Inventory.id, models.Inventory.name, models.Inventory.user_id,
    models.Inventory.date_created}
# Fields client is allowed to modify
THING_USER_ENTITIES = {
    models.Thing.name,
    models.Thing.description, models.Thing.notes}
THING_USER_FIELDS = get_entity_names(THING_USER_ENTITIES)
# These fields are handled by the server and not passed in from the client.
THING_MANAGED_ENTITIES = {
    models.Thing.id, models.Thing.date_created, models.Thing.date_modified}
THING_MANAGED_FIELDS = get_entity_names(THING_MANAGED_ENTITIES)
# Fields that must have data
THING_REQUIRED_FIELDS = {
    e.key for e in THING_USER_ENTITIES
    if models.Thing.__table__.columns[e.key].nullable is False and
    e.key not in ('inventory_id')}

ViewReturnType = Tuple[str, int, Dict[str, str]]


# Routes
#########


@bp.route('/inventories')
def get_inventories() -> ViewReturnType:
    """Provide a list of inventories from the database."""
    # TODO: user filtering
    user = models.User.query.first()
    inventories = models.Inventory.query. \
        with_entities(*INVENTORY_CLIENT_ENTITIES). \
        filter_by(user_id=user.id).all()
    # SQLite does not keep timezone information, assume UTC
    fixed_inventories = []
    for inventory in inventories:
        fixed_inventories.append(fix_dict_datetimes(inventory._asdict()))
    return json_response(fixed_inventories)


@bp.route('/inventories/<int:inventory_id>/things')
def get_things(inventory_id: int=None) -> ViewReturnType:
    """Provide a list of things from the database."""
    # TODO: check user ID
    error_message = check_inventory_exists(inventory_id)
    if error_message:
        return error_response(error_message, status_code=HTTPStatus.NOT_FOUND)
    things = models.Thing.query.with_entities(*THING_CLIENT_ENTITIES). \
        filter_by(date_deleted=None, inventory_id=inventory_id).all()
    fixed_things = []
    for thing in things:
        # SQLite does not keep timezone information, assume UTC
        fixed_things.append(fix_dict_datetimes(thing._asdict()))
    return json_response(fixed_things)


@bp.route('/inventories/<int:inventory_id>/things', methods=['POST'])
def post_thing(inventory_id: int) -> ViewReturnType:
    """POST a thing to the database."""
    request_data = request.get_json()

    # Sanity check of data
    # TODO: check user owns inventory
    error_message = check_inventory_exists(inventory_id)
    if error_message:
        return error_response(error_message, status_code=HTTPStatus.NOT_FOUND)
    error_message = check_thing_request(request_data)
    if error_message:
        return error_response(error_message)
    # New things require certain fields
    if not THING_REQUIRED_FIELDS.issubset(request_data):
        missing_fields = [f for f in THING_REQUIRED_FIELDS
                          if f not in request_data]
        return error_response(
            "Required field(s) missing: {}".format(', '.join(missing_fields))
        )
    # Filter only desired fields
    new_thing_data = filter_user_fields(request_data)

    thing = models.Thing(inventory_id=inventory_id, **new_thing_data)
    # TODO: Inventory will be specified by client
    inventory = models.Inventory.query.first()
    thing.inventory = inventory
    db.session.add(thing)
    db.session.commit()
    # TODO: Error handling - what if database is down?
    initializedData = {k: thing.as_dict()[k] for k in THING_MANAGED_FIELDS}
    return json_response(initializedData, HTTPStatus.CREATED)


@bp.route('/things/<int:thing_id>', methods=['PUT'])
@bp.route('/inventories/<int:inventory_id>/things/<int:thing_id>', methods=['PUT'])
def update_thing(thing_id: int, inventory_id: int=None) -> ViewReturnType:
    """PUT (update) a thing in the database.

    inventory_id is ignored, only thing_id is needed.
    """
    request_data = request.get_json()

    # Sanity check of data
    error_message = check_thing_request(request_data)
    if error_message:
        return error_response(error_message)
    # Filter only desired fields
    update_thing_data = filter_user_fields(request_data)

    thing = models.Thing.query.filter_by(id=thing_id)
    if thing.one_or_none() is None:
        return error_response(
            'No thing with id {}'.format(thing_id),
            status_code=HTTPStatus.NOT_FOUND
        )
    thing.update(update_thing_data)
    db.session.commit()
    return NO_CONTENT


@bp.route('/things/<int:thing_id>', methods=['DELETE'])
@bp.route('/inventories/<int:inventory_id>/things/<int:thing_id>', methods=['DELETE'])
def delete_thing(thing_id: int, inventory_id: int=None) -> ViewReturnType:
    """DELETE a thing in the database.

    inventory_id is ignored, only thing_id is needed.
    """
    thing = models.Thing.query.get(thing_id)
    if thing is None:
        return error_response(
            'No thing with id {}'.format(thing_id),
            status_code=HTTPStatus.NOT_FOUND
        )
    thing.date_deleted = datetime.datetime.utcnow()
    db.session.commit()
    return NO_CONTENT
