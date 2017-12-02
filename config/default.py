"""
Config module for Stuffr's backend.

To override these settings, create a file in the instance directory with your
desired settings. Then when you call create_app() set the local_config
parameter to the name of the file you just created (without the path). See
manage.py for an example of how the debug server handles it.

Flask instance documentation:
    http://flask.pocoo.org/docs/config/#instance-folders
"""

from sqlalchemy.engine.url import URL

# Database setup
# Recommended to use an URL object to specify database
# https://docs.sqlalchemy.org/en/latest/core/engines.html#sqlalchemy.engine.url.URL
SQLALCHEMY_DATABASE_URI = URL(drivername='sqlite')   # In-memory database
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Flask-Security settings
SECURITY_URL_PREFIX = '/auth'
SECURITY_POST_LOGOUT_VIEW = 'simple_interface.main_view'
SECURITY_REGISTERABLE = True
# Stuffr uses token-based security, CSRF is not a factor
# TODO: Now that there's a static HTML view this will need to be enabled
WTF_CSRF_ENABLED = False

MAIL_PORT = 25


# Settings specific to Stuffr

# Will be used as the 'host'/'port' parameters for app.run
STUFFR_DEBUG_HOST = 'localhost'
STUFFR_DEBUG_PORT = 5000
# Normally handled by Alembic
STUFFR_CREATE_TABLES = False
# Set False if you need to create app without seeding database, e.g. testing
STUFFR_INITIALIZE_DATABASE = True
