"""Main file for Stuffr's backend."""

import sqlalchemy, sqlalchemy.ext.declarative, sqlalchemy.orm
from flask import Blueprint

import stuffrbackend.models as models

# Static files are served at url root for debug server
bp = Blueprint('stuffrbackend', __name__)

# Set up database
engine = sqlalchemy.create_engine('sqlite:///stuffr.db')
models.DeclarativeBase.metadata.create_all(engine)
Session = sqlalchemy.orm.sessionmaker(bind=engine)
import stuffrbackend.views  # NOQA - imported so views has access to bp object
