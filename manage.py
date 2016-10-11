#!/usr/bin/env python3
"""Manager for Flask-Script, containing backend-related commands."""

from flask import render_template
from flask_debugtoolbar import DebugToolbarExtension
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager

from stuffrapp import create_app
from database import db

manager_app = create_app({
    'INITIALIZE_DATABASE': False,
    'CREATE_TABLES': False
})
manager = Manager(manager_app)

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

    debug_app.run(debug_app.config['SERVER_DEBUG_HOST'],
                   debug_app.config['SERVER_DEBUG_PORT'])


if __name__ == "__main__":
    manager.run()
