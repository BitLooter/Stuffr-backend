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
# Allow plaintext for testing. Also prevents bug that appears when 'argon2'
# is the only item in the list. Will remove this line when Flask-Security
# adds argon2 to the allowed hashes.
SECURITY_PASSWORD_SCHEMES = ['plaintext', 'argon2']
SECURITY_PASSWORD_HASH = 'argon2'
# Stuffr uses token-based security, CSRF is not a factor
# TODO: Now that there's a static HTML view this will need to be enabled
WTF_CSRF_ENABLED = False

MAIL_PORT = 25


# Settings specific to Stuffr
