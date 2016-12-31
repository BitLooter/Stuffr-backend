"""Settings for debugging."""

from sqlalchemy.engine.url import URL

DEBUG = True
SECRET_KEY = 'DEBUG KEY DO NOT USE IN PRODUCTION'

# Default database information
SQLALCHEMY_DATABASE_URI = str(URL(drivername='sqlite', database='stuffr.db'))
