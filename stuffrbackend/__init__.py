"""Main file for Stuffr's backend."""

from flask import Blueprint

bp = Blueprint('stuffrbackend', __name__)

import stuffrbackend.views  # NOQA - imported so views has access to bp object
