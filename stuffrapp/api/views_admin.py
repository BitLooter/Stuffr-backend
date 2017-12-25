"""REST views for Stuffr admin."""
# Class-based views means this test causes false positives
# pylint: disable=no-self-use

from http import HTTPStatus
from flask_restplus import Namespace, Resource, fields
from flask_security.decorators import auth_token_required

from . import models
from ..typing import ViewReturnType


ns = Namespace('admin', description='Admin interface API')


# View models
##############

stats = ns.model('Stats', {
    'numUsers': fields.Integer(
        required=True, example=23,
        description='Total number of users'),
    'numInventories': fields.Integer(
        required=True, example=85,
        description='Total inventories across all users'),
    'numThings': fields.Integer(
        required=True, example=4295,
        description='Total inventories across all users')
})

user_model = ns.model('User', {
    'id': fields.Integer(required=True, example=253),
    'email': fields.String(required=True, example='email@example.com'),
    'name_first': fields.String(required=True, example='Boaty'),
    'name_last': fields.String(required=True, example='McBoatface'),
    'date_created': fields.DateTime(
        required=True, example='2012-12-21T04:07:45.503547+00:00'),
    'active': fields.Boolean(
        required=True, example=True,
        description='False if user is currently disabled')
})


# Views
########

# TODO: Check user role
@ns.route('/stats')
@ns.response(HTTPStatus.UNAUTHORIZED, "Requires admin login")
class Stats(Resource):
    """Handler for database information and statistics."""

    @auth_token_required
    @ns.marshal_with(stats, code=HTTPStatus.OK, description="Success")
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


@ns.route('/users')
@ns.response(HTTPStatus.UNAUTHORIZED, "Requires admin login")
class Users(Resource):
    """Handler for requesting info on users."""

    @auth_token_required
    @ns.marshal_with(user_model, envelope='users',
                     code=HTTPStatus.OK, description="Success")
    def get(self) -> ViewReturnType:
        """Returns list of all users."""
        return models.User.get_user_list()


@ns.route('/')
@ns.response(HTTPStatus.NOT_FOUND, "Nothing at root")
class Root(Resource):
    """Handler for admin root."""

    def get(self):
        """Dummy endpoint for admin root, nothing there."""
        return 'Nothing here', HTTPStatus.NOT_FOUND
