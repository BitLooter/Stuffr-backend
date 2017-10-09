"""Common startup code for API blueprints."""

from http import HTTPStatus

from .views import bp as blueprint_api
from .views_admin import bp as blueprint_apiadmin
from .views_common import json_response
from ..typing import ViewReturnType


# One error handler for all blueprints
@blueprint_api.errorhandler(HTTPStatus.BAD_REQUEST)
@blueprint_apiadmin.errorhandler(HTTPStatus.BAD_REQUEST)
def defaulthandler(e: Exception) -> ViewReturnType:
    """Default exception handler to return JSON instead of HTML."""
    json_data = {'message': '{}: {}'.format(e.name, e.description)}
    return json_response(json_data, status_code=e.code)
