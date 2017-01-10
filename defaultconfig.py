"""
Config module for Stuffr's backend.

To override these settings, create a directory named 'instance' alongside the
package directory, copy this file there and name it 'debugconfig.py' or
'prodconfig.py', and change settings to what you need.
"""

# Will be used as the 'host'/'port' parameters for app.run
SERVER_DEBUG_HOST = 'localhost'
SERVER_DEBUG_PORT = 5000

# Default database information
SQLALCHEMY_DATABASE_URI = 'sqlite://'   # No path makes a memory database
SQLALCHEMY_TRACK_MODIFICATIONS = False
# Normally handled by Alembic
CREATE_TABLES = False
# Set False if you need to create app without seeding database, e.g. testing
INITIALIZE_DATABASE = True

# Flask-Security settings
SECURITY_URL_PREFIX = '/auth'
SECURITY_REGISTERABLE = True
