#!/usr/bin/env python3
"""Main file for Stuffr's backend."""

import json
import sqlalchemy, sqlalchemy.ext.declarative, sqlalchemy.orm
from sqlalchemy import Column, Integer, String
from flask import Flask, send_from_directory, request

# Set up database
engine = sqlalchemy.create_engine('sqlite:///stuffr.db')
Session = sqlalchemy.orm.sessionmaker(bind=engine)
Base = sqlalchemy.ext.declarative.declarative_base()


class Thing(Base):
    """Model for generic thing data."""

    __tablename__ = 'things'
    id = Column(Integer, primary_key=True)
    name = Column(String)

    def as_dict(self):
        """Return fields as a dict."""
        # TODO: find out if there's a way to do this built into SQLAlchemy
        return {'id': self.id, 'name': self.name}

    def __repr__(self):
        """Basic Thing data as a string."""
        return "<Thing name='{}'>".format(self.name)

Base.metadata.create_all(engine)

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
        things = session.query(Thing).all()
        things_list = [t.as_dict() for t in things]
        return json.dumps(things_list)
    elif request.method == 'POST':
        session = Session()
        thing = Thing(name=request.get_json()['name'])
        session.add(thing)
        session.commit()
        return json.dumps({'id': thing.id, 'name': thing.name})


if __name__ == "__main__":
    # TODO: load config from file
    app.run(debug=True, host='0.0.0.0', port=8080)
