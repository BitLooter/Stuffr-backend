"""REST views for stuffr."""

from http import HTTPStatus
import json
from flask import request

from stuffrbackend import bp, Session
import stuffrbackend.models as models


@bp.route('/things')
def get_things():
    """Provide a list of things from the database."""
    session = Session()
    things = session.query(models.Thing).all()
    things_list = [t.as_dict() for t in things]
    return json.dumps(things_list)


@bp.route('/things', methods=['POST'])
def post_thing():
    """POST a thing to the database."""
    session = Session()
    thing = models.Thing(name=request.get_json()['name'])
    session.add(thing)
    session.commit()
    return json.dumps(thing.as_dict()), HTTPStatus.CREATED
