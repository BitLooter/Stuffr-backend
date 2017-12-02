"""Example settings for debugging."""

from sqlalchemy.engine.url import URL

DEBUG = True
SECRET_KEY = 'DEBUG KEY DO NOT USE IN PRODUCTION'

# By default writes to a local SQLite database
SQLALCHEMY_DATABASE_URI = URL(drivername='sqlite', database='stuffr.db')

# Email settings
# By default emails are not sent on a development server, but are printed to
# stdout instead.
MAIL_SUPPRESS_SEND = True
# If you want to use an actual email server, remove previous line and
# set SMTP server parameters.
# MAIL_SERVER = 'localhost'
# MAIL_PORT = 1025
