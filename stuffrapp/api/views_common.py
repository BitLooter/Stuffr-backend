"""Common code for API views."""

import datetime
from http import HTTPStatus
import json
from typing import Any

from ..logger import logger
from ..typing import ViewReturnType


# Constants
############
NO_CONTENT = ('', HTTPStatus.NO_CONTENT)


# Functions
############

def serialize_object(obj: Any) -> str:
    """Convert unserializable types for JSON encoding."""
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    else:
        raise TypeError("JSON: Cannot serialize {}".format(type(obj)))


def json_response(data: Any, status_code: int = HTTPStatus.OK) -> ViewReturnType:
    """Create a response object suitable for JSON data."""
    json_data = json.dumps(data, default=serialize_object)
    if status_code == HTTPStatus.UNAUTHORIZED:
        headers = {'Content-Type': 'application/json',
                   'WWW-Authenticate': 'FormBased'}
    else:
        headers = {'Content-Type': 'application/json'}
    return json_data, status_code, headers


def error_response(message: str, status_code: int = HTTPStatus.BAD_REQUEST) -> ViewReturnType:
    """Create a response object for errors."""
    return json_response({'message': message}, status_code=status_code)


def api_unauthenticated_handler() -> ViewReturnType:
    """Response handler for unauthenticated requests to protected API calls."""
    logger.warning('Unauthenticated request')
    return error_response('You must be logged in to access this resource',
                          status_code=HTTPStatus.UNAUTHORIZED)
