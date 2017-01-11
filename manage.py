#!/usr/bin/env python3
"""Manager for Flask-Script, containing backend-related commands."""

from flask import render_template
from flask_debugtoolbar import DebugToolbarExtension
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager

from stuffrapp import create_app
from database import db

# Constants
############
DEBUG_CONFIG = 'config_debug.py'

# Manager setup
################

# Manager is given a different app from runserver that doesn't touch
# the database during initialization
manager_app = create_app(DEBUG_CONFIG, config_override={
    'STUFFR_INITIALIZE_DATABASE': False,
    'STUFFR_CREATE_TABLES': False
})
manager = Manager(manager_app)

# Alembic
migrate = Migrate(manager_app, db)
manager.add_command('db', MigrateCommand)


@manager.command
def runserver():
    """Run the Flask debug server."""
    # manager_app does not do database initialization
    debug_app = create_app(DEBUG_CONFIG)
    DebugToolbarExtension(debug_app)

    @debug_app.route('/')
    def debug_root():
        """Serve index.html when using the debug server."""
        # Using render_template so flask_debugtoolbar can do its thing
        return render_template('index.html')

    debug_app.run(debug_app.config['STUFFR_DEBUG_HOST'],
                  debug_app.config['STUFFR_DEBUG_PORT'])


if __name__ == "__main__":
    manager.run()
