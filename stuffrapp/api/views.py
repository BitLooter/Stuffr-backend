"""Main module managing views."""

# from flask import Blueprint
from flask_restplus import Api

from .views_admin import ns as ns_admin
# from .views_core import ns as ns_core
from .views_core import bp


authorizations = {
    'ApiKey': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'authentication-token'
    }
}
# bp = Blueprint('stuffrapi', __name__, template_folder='templates')
api = Api(bp, authorizations=authorizations, security='ApiKey')
# api.add_namespace(ns_core)
api.add_namespace(ns_admin)
