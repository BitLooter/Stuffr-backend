#!/usr/bin/env python3
"""Manager for Flask-Script, containing backend-related commands."""

import sys
import os
from flask import render_template
from flask_debugtoolbar import DebugToolbarExtension
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager

from stuffrapp import create_app
from database import db

# Manager setup
################

if not os.environ['STUFFR_SETTINGS']:
    print('Set the STUFFR_SETTINGS environment variable before using this tool.')
    sys.exit(1)

# Manager is given a different app from runserver that doesn't touch
# the database during initialization
manager_app = create_app(config_override={
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
    debug_app = create_app()
    DebugToolbarExtension(debug_app)

    @debug_app.route('/')
    def debug_root():
        """Serve index.html when using the debug server."""
        # Using render_template so flask_debugtoolbar can do its thing
        return render_template('index.html')

    debug_app.run(debug_app.config['STUFFR_DEBUG_HOST'],
                  debug_app.config['STUFFR_DEBUG_PORT'])


@manager.command
def listroutes():
    """List all views defined by the app."""
    for rule in sorted(manager_app.url_map.iter_rules(),
                       key=lambda r: r.endpoint):
        endpoint = rule.endpoint
        methods = ', '.join(r for r in rule.methods if r not in ['OPTIONS', 'HEAD'])
        path = rule.rule
        print(f'{endpoint}: ({methods}) {path}')


if __name__ == "__main__":
    manager.run()
