"""Views for presenting data as simple static HTML.

Normal default view is a JavaScript/React/Redux/etc SPA. For those that prefer
a traditional HTML-only multipage interface (e.g. for performance or
accessibility reasons) this provides an alternative.

Views should be static HTML & CSS generated server-side, with little or no
JavaScript used. If JavaScript does get used for anything, it shall not be
required for any functionality.
"""

from http import HTTPStatus
from flask import Blueprint, render_template, abort
from flask_security import current_user
from flask_security.decorators import login_required

from stuffrapp.api import models
from stuffrapp.api.errors import ItemNotFoundError, UserPermissionError

bp = Blueprint('simple_interface', __name__, template_folder='templates')


@bp.route('/')
@login_required
def main_view():
    """Home page for the simple interface."""
    return render_template('simple/main.html')


@bp.route('/inventories/')
@login_required
def list_inventories():
    """Display all available inventories."""
    inventories = models.Inventory.get_user_inventories(current_user.id)
    return render_template('simple/inventories.html', inventories=inventories)


@bp.route('/inventories/<int:inventory_id>/')
@login_required
def list_things(inventory_id: int):
    """Display things part of given inventory."""
    try:
        things = models.Thing.get_things_for_inventory(inventory_id, current_user.id)
    except (ItemNotFoundError, UserPermissionError) as e:
        abort(HTTPStatus.FORBIDDEN)
    return render_template('simple/things.html', things=things)


@bp.route('/inventories/<int:inventory_id>/<int:thing_id>/')
@login_required
def thing_details(inventory_id: int, thing_id: int):
    """Display details for specified thing."""
    try:
        thing = models.Thing.get_thing(thing_id, current_user.id)
    except (ItemNotFoundError, UserPermissionError) as e:
        abort(HTTPStatus.FORBIDDEN)
    # If the thing ID is correct but the inventory ID is not, something is screwy
    if inventory_id != thing.inventory_id:
        abort(HTTPStatus.BAD_REQUEST)
    return render_template('simple/thing_details.html', thing=thing.as_client_dict())
