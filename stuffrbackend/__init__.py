"""Main file for Stuffr's backend."""

import sqlalchemy, sqlalchemy.ext.declarative, sqlalchemy.orm
from flask import Flask, send_from_directory

import stuffrbackend.models as models
app = Flask('stuffr-backend', static_url_path='')
# Set up database
engine = sqlalchemy.create_engine('sqlite:///stuffr.db')
models.DeclarativeBase.metadata.create_all(engine)
Session = sqlalchemy.orm.sessionmaker(bind=engine)
import stuffrbackend.views  # NOQA - imported so views has access to app object


@app.route('/')
def debug_root():
    """Serve index.html when using the debug server."""
    # TODO: Check that debug mode is on first
    return send_from_directory('static', 'index.html')
