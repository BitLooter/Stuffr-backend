#!/usr/bin/env python3
"""Main file for Stuffr's backend."""

from http import HTTPStatus
import json
import sqlalchemy, sqlalchemy.ext.declarative, sqlalchemy.orm
from flask import Flask, send_from_directory, request

import models

# Set up database
engine = sqlalchemy.create_engine('sqlite:///stuffr.db')
Session = sqlalchemy.orm.sessionmaker(bind=engine)
models.DeclarativeBase.metadata.create_all(engine)

# Set up Flask
app = Flask('stuffr-backend', static_url_path='')


@app.route('/')
def debug_root():
    """Serve index.html when using the debug server."""
    # TODO: Check that debug mode is on first
    return send_from_directory('static', 'index.html')


@app.route('/api/things', methods=['GET', 'POST'])
def get_things():
    """Provide a list of things from the database."""
    if request.method == 'GET':
        session = Session()
        things = session.query(models.Thing).all()
        things_list = [t.as_dict() for t in things]
        return json.dumps(things_list)
    elif request.method == 'POST':
        session = Session()
        thing = models.Thing(name=request.get_json()['name'])
        session.add(thing)
        session.commit()
        return json.dumps({'id': thing.id, 'name': thing.name}), HTTPStatus.CREATED


if __name__ == "__main__":
    # TODO: load config from file
    app.run(debug=True, host='0.0.0.0', port=8080)
