"""REST views for stuffr."""

from http import HTTPStatus
from typing import Dict, Mapping, Sequence
from flask import request, Blueprint
from flask_security import current_user
from flask_security.decorators import auth_token_required

from . import models
from . import errors
from .views_common import json_response, error_response, NO_CONTENT
from ..typing import ViewReturnType


bp = Blueprint('stuffrapi', __name__, template_folder='templates')


# Helper functions
##################

def filter_dict(the_dict: Mapping, allowed_keys: Sequence) -> Dict:
    """Filter an input dict to only contain specified keys."""
    return {k: the_dict[k] for k in the_dict if k in allowed_keys}


# Constants
###########

# These fields are handled by the server and not passed in from the client.
THING_MANAGED_FIELDS = models.Thing.CLIENT_FIELDS - models.Thing.USER_FIELDS
INVENTORY_MANAGED_FIELDS = models.Inventory.CLIENT_FIELDS - models.Inventory.USER_FIELDS


# Routes
#########

# TODO: Default 404 error view

@bp.route('/serverinfo')
@auth_token_required
def get_serverinfo() -> ViewReturnType:
    """Provide information about the server."""
    # TODO: Centralized place to store version info
    return json_response({'version': '0.1.0'})


@bp.route('/userinfo')
@auth_token_required
def get_userinfo() -> ViewReturnType:
    """Provide information about the current user."""
    return json_response(filter_dict(current_user._asdict(), models.User.CLIENT_FIELDS))


@bp.route('/inventories')
@auth_token_required
def get_inventories() -> ViewReturnType:
    """Provide a list of inventories from the database."""
    inventories = models.Inventory.get_user_inventories(current_user.id)
    return json_response([filter_dict(i._asdict(), models.Inventory.CLIENT_FIELDS)
                          for i in inventories])


@bp.route('/inventories', methods=['POST'])
@auth_token_required
def post_inventory() -> ViewReturnType:
    """POST an inventory to the database."""
    request_data = request.get_json()
    # TODO: Error handling - what if database is down?
    try:
        inventory = models.Inventory.create_new_inventory(request_data, current_user.id)
    except errors.InvalidDataError as e:
        response = error_response(e.args, status_code=HTTPStatus.BAD_REQUEST)
    else:
        initialized_data = {k: v for (k, v) in inventory._asdict().items()
                            if k in INVENTORY_MANAGED_FIELDS}
        response = json_response(initialized_data, HTTPStatus.CREATED)
    return response


@bp.route('/inventories/<int:inventory_id>/things')
@auth_token_required
def get_things(inventory_id: int = None) -> ViewReturnType:
    """Provide a list of things from the database."""
    try:
        things = models.Thing.get_things_for_inventory(inventory_id, current_user.id)
    except errors.ItemNotFoundError as e:
        response = error_response(e.args, status_code=HTTPStatus.NOT_FOUND)
    except errors.UserPermissionError as e:
        response = error_response(e.args, status_code=HTTPStatus.FORBIDDEN)
    else:
        response = json_response([t.as_client_dict() for t in things])
    return response


@bp.route('/inventories/<int:inventory_id>/things', methods=['POST'])
@auth_token_required
def post_thing(inventory_id: int) -> ViewReturnType:
    """POST a thing to the database."""
    request_data = request.get_json()

    # TODO: Error handling - what if database is down?
    try:
        thing = models.Thing.create_new_thing(request_data, inventory_id, current_user.id)
    except errors.ItemNotFoundError as e:
        response = error_response(e.args, status_code=HTTPStatus.NOT_FOUND)
    except errors.UserPermissionError as e:
        response = error_response(e.args, status_code=HTTPStatus.FORBIDDEN)
    except errors.InvalidDataError as e:
        response = error_response(e.args, status_code=HTTPStatus.BAD_REQUEST)
    else:
        initialized_data = {k: v for (k, v) in thing._asdict().items()
                            if k in THING_MANAGED_FIELDS}
        response = json_response(initialized_data, HTTPStatus.CREATED)
    return response


@bp.route('/things/<int:thing_id>', methods=['PUT'])
@bp.route('/inventories/<int:_>/things/<int:thing_id>', methods=['PUT'])
@auth_token_required
def update_thing(thing_id: int, _: int = None) -> ViewReturnType:
    """PUT (update) a thing in the database.

    inventory_id (_) is ignored, only thing_id is needed.
    """
    request_data = request.get_json()
    try:
        modified_data = models.Thing.update_thing(thing_id, request_data, current_user.id)
    except errors.ItemNotFoundError as e:
        response = error_response(e.args, status_code=HTTPStatus.NOT_FOUND)
    except errors.UserPermissionError as e:
        response = error_response(e.args, status_code=HTTPStatus.FORBIDDEN)
    except errors.InvalidDataError as e:
        response = error_response(e.args, status_code=HTTPStatus.BAD_REQUEST)
    else:
        response = json_response(modified_data)
    return response


@bp.route('/things/<int:thing_id>', methods=['DELETE'])
@bp.route('/inventories/<int:_>/things/<int:thing_id>', methods=['DELETE'])
@auth_token_required
def delete_thing(thing_id: int, _: int = None) -> ViewReturnType:
    """DELETE a thing in the database.

    inventory_id (_) is ignored, only thing_id is needed.
    """
    response = NO_CONTENT
    try:
        models.Thing.delete_thing(thing_id, current_user.id)
    except errors.ItemNotFoundError as e:
        response = error_response(e.args, status_code=HTTPStatus.NOT_FOUND)
    except errors.UserPermissionError as e:
        response = error_response(e.args, status_code=HTTPStatus.FORBIDDEN)
    return response
