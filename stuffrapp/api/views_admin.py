"""REST views for Stuffr admin."""
# Class-based views means this test causes false positives
# pylint: disable=no-self-use

from flask import Blueprint
from flask_restplus import Api, Resource
from flask_security.decorators import auth_token_required

from . import models
from ..typing import ViewReturnType


bp = Blueprint('stuffrapi_admin', __name__, template_folder='templates')
api = Api(bp)


# Routes
#########

# TODO: Route for root and admin root

# TODO: Check user role
@api.route('/stats')
class AdminStats(Resource):
    """Handler for database information and statistics."""

    @auth_token_required
    def get(self) -> ViewReturnType:
        """Returns database stats."""
        users_count = models.User.total_count()
        inventories_count = models.Inventory.total_count()
        thing_count = models.Thing.total_count()
        return {
            'numUsers': users_count,
            'numInventories': inventories_count,
            'numThings': thing_count
        }
