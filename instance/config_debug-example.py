"""Example settings for debugging."""

from sqlalchemy.engine.url import URL

DEBUG = True
SECRET_KEY = 'DEBUG KEY DO NOT USE IN PRODUCTION'

# By default writes to a local SQLite database
SQLALCHEMY_DATABASE_URI = URL(drivername='sqlite', database='stuffr.db')
