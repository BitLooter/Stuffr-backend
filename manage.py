#!/usr/bin/env python3
"""Manager for Flask-Script, containing backend-related commands."""

from flask import render_template
from flask_debugtoolbar import DebugToolbarExtension
from flask_script import Manager

from stuffrapp import create_app

stuffr_app = create_app()
manager = Manager(stuffr_app)


@manager.command
def runserver():
    """Run the Flask debug server."""
    DebugToolbarExtension(stuffr_app)

    @stuffr_app.route('/')
    def debug_root():
        """Serve index.html when using the debug server."""
        # Using render_template so flask_debugtoolbar can do its thing
        return render_template('index.html')

    stuffr_app.run(stuffr_app.config['SERVER_DEBUG_HOST'],
                   stuffr_app.config['SERVER_DEBUG_PORT'])


if __name__ == "__main__":
    manager.run()
