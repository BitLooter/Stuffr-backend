"""REST views for stuffr."""

import datetime
from http import HTTPStatus
import json
from typing import Any, Dict, Tuple
from flask import request, Blueprint
from flask_security import current_user
from flask_security.decorators import auth_token_required

from . import models

bp = Blueprint('stuffrapi', __name__, template_folder='templates')

ViewReturnType = Tuple[str, int, Dict[str, str]]


# Helper functions
##################

@bp.errorhandler(HTTPStatus.BAD_REQUEST)
def defaulthandler(e: Exception) -> ViewReturnType:
    """Default exception handler to return JSON instead of HTML."""
    json_data = {'message': '{}: {}'.format(e.name, e.description)}
    return json_response(json_data, status_code=e.code)


def serialize_object(obj: Any) -> str:
    """Convert unserializable types for JSON encoding."""
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    else:
        raise TypeError("JSON: Cannot serialize {}".format(type(obj)))


def json_response(data: Any, status_code: int=HTTPStatus.OK) -> ViewReturnType:
    """Create a response object suitable for JSON data."""
    json_data = json.dumps(data, default=serialize_object)
    if status_code == HTTPStatus.UNAUTHORIZED:
        headers = {'Content-Type': 'application/json',
                   'WWW-Authenticate': 'FormBased'}
    else:
        headers = {'Content-Type': 'application/json'}
    return json_data, status_code, headers


def error_response(message: str, status_code: int=HTTPStatus.BAD_REQUEST) -> ViewReturnType:
    """Create a response object for errors."""
    return json_response({'message': message}, status_code=status_code)


def api_unauthorized() -> ViewReturnType:
    """Response handler for unauthenticated requests to protected API calls."""
    # TODO: Fix logging
    # logger.warning('Unauthenticated request')
    return error_response('You must be logged in to access this resource',
                          status_code=HTTPStatus.UNAUTHORIZED)


# Constants
###########

NO_CONTENT = ('', HTTPStatus.NO_CONTENT)
# These fields are handled by the server and not passed in from the client.
THING_MANAGED_FIELDS = models.Thing.CLIENT_FIELDS - models.Thing.USER_FIELDS
INVENTORY_MANAGED_FIELDS = models.Inventory.CLIENT_FIELDS - models.Inventory.USER_FIELDS


# Routes
#########

# TODO: Default 404 error view

@bp.route('/userinfo')
@auth_token_required
def get_userinfo() -> ViewReturnType:
    """Provide information about the current user."""
    user_dict = current_user.as_dict()
    filtered_user = {k: user_dict[k] for k in user_dict
                     if k in models.User.CLIENT_FIELDS}
    return json_response(filtered_user)


@bp.route('/inventories')
@auth_token_required
def get_inventories() -> ViewReturnType:
    """Provide a list of inventories from the database."""
    inventories = models.Inventory.get_user_inventories(current_user.id)
    return json_response(inventories)


@bp.route('/inventories', methods=['POST'])
@auth_token_required
def post_inventory() -> ViewReturnType:
    """POST an inventory to the database."""
    request_data = request.get_json()
    # TODO: Error handling - what if database is down?
    inventory = models.Inventory.create_new_inventory(request_data, current_user)
    initialized_data = {k: v for (k, v) in inventory.as_dict().items()
                        if k in INVENTORY_MANAGED_FIELDS}
    return json_response(initialized_data, HTTPStatus.CREATED)


@bp.route('/inventories/<int:inventory_id>/things')
@auth_token_required
def get_things(inventory_id: int=None) -> ViewReturnType:
    """Provide a list of things from the database."""
    # Check that current user owns inventory
    if current_user != models.Inventory.query.get(inventory_id).user:
        return error_response('Inventory does not belong to user',
                              status_code=HTTPStatus.FORBIDDEN)

    things = models.Thing.get_things_for_inventory(inventory_id)
    return json_response(things)


@bp.route('/inventories/<int:inventory_id>/things', methods=['POST'])
@auth_token_required
def post_thing(inventory_id: int) -> ViewReturnType:
    """POST a thing to the database."""
    request_data = request.get_json()

    # TODO: Error handling - what if database is down?
    thing = models.Thing.create_new_thing(request_data, inventory_id, current_user.id)
    initialized_data = {k: v for (k, v) in thing.as_dict().items()
                        if k in THING_MANAGED_FIELDS}
    return json_response(initialized_data, HTTPStatus.CREATED)


@bp.route('/things/<int:thing_id>', methods=['PUT'])
@bp.route('/inventories/<int:inventory_id>/things/<int:thing_id>', methods=['PUT'])
@auth_token_required
def update_thing(thing_id: int, inventory_id: int=None) -> ViewReturnType:
    """PUT (update) a thing in the database.

    inventory_id is ignored, only thing_id is needed.
    """
    request_data = request.get_json()
    modified_data = models.Thing.update_thing(thing_id, request_data, current_user.id)
    return json_response(modified_data)


@bp.route('/things/<int:thing_id>', methods=['DELETE'])
@bp.route('/inventories/<int:inventory_id>/things/<int:thing_id>', methods=['DELETE'])
@auth_token_required
def delete_thing(thing_id: int, inventory_id: int=None) -> ViewReturnType:
    """DELETE a thing in the database.

    inventory_id is ignored, only thing_id is needed.
    """
    models.Thing.delete_thing(thing_id, current_user.id)
    return NO_CONTENT
