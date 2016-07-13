"""REST views for stuffr."""

from http import HTTPStatus
import json
from flask import request

from stuffrbackend import bp
import stuffrbackend.models as models
from database import db


def json_response(data, status_code=HTTPStatus.OK):
    """Create a response object suitable for JSON data."""
    return data, status_code, {'Content-Type': 'application/json'}


@bp.route('/things')
def get_things():
    """Provide a list of things from the database."""
    things = db.session.query(models.Thing).all()
    things_list = [t.as_dict() for t in things]
    return json_response(json.dumps(things_list))


@bp.route('/things', methods=['POST'])
def post_thing():
    """POST a thing to the database."""
    thing = models.Thing(name=request.get_json()['name'])
    db.session.add(thing)
    db.session.commit()
    # TODO: Error handling
    return json_response(json.dumps(thing.as_dict()), HTTPStatus.CREATED)
