"""Views for presenting data as simple static HTML.

Normal default view is a JavaScript/React/Redux/etc SPA. For those that prefer
a traditional HTML-only multipage interface (e.g. for performance or
accessibility reasons) this provides an alternative.

Views should be static HTML & CSS generated server-side, with little or no
JavaScript used. If JavaScript does get used for anything, it shall not be
required for any functionality.
"""

from flask import Blueprint, render_template
from flask_security import current_user
from flask_security.decorators import login_required

from stuffrapp.api import models

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
    # TODO: Verify user owns inventory
    things = models.Thing.get_inventory_things(inventory_id)
    return render_template('simple/things.html', things=things)


@bp.route('/inventories/<int:inventory_id>/<int:thing_id>/')
@login_required
def thing_details(inventory_id: int, thing_id: int):
    """Display details for specified thing."""
    # TODO: Verify user owns thing
    thing = models.Thing.get_thing_details(thing_id)
    return render_template('simple/thing_details.html', thing=thing)
