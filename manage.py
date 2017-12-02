#!/usr/bin/env python3
"""Manager for Flask-Script, containing backend-related commands."""

import sys
import os
import asyncore
from smtpd import SMTPServer
from flask import render_template
from flask_debugtoolbar import DebugToolbarExtension
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager
from flask_mail import email_dispatched

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

    # Display emails sent by flask
    def report_email(message, **_):
        """Take an outgoing message and print it to the screen."""
        print(f"===== Email sent by Stuffr =====")
        print(f"From: {message.sender}")
        print(f"To: {','.join(message.recipients)}")
        print(f"Subject: {message.subject}")
        print(f"Body:\n{message.body.strip()}")
    email_dispatched.connect(report_email)

    @debug_app.route('/')
    def debug_root():  # pylint: disable=unused-variable
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


class DummySMTP(SMTPServer):
    """Simple SMTP Server that prints messages to screen.

    No bells or whistles, just prints email straight to the terminal. Use a
    proper email dev server if you need anything fancier.

    smtpd is considered deprecated by the Python docs. Nevertheless, it's far
    more than enough for what we're doing here, and doesn't require additional
    dependencies.
    """
    def process_message(self, peer, mailfrom, rcpttos, data, **_):
        """Take an incoming message and print it to the screen."""
        print(f"===== Message from {peer[0]} =====")
        print(f"From: {mailfrom}")
        print(f"To: {','.join(rcpttos)}")
        print(f"Body:\n{data.decode()}")


@manager.command
def emailsrv():
    """Simple SMTP server that prints messages to stdout.

    Normally this is not needed, as a default development config will suppress
    sending of emails and print them to stdout instead. However, if you wish
    to develop or test with an actual SMTP server, this will work as a very
    bare-bones server. Anything more complicated than simply printing emails
    to the screen will need a proper server.
    """
    host = manager_app.config['MAIL_SERVER']
    port = manager_app.config['MAIL_PORT']
    DummySMTP((host, port), None)
    print(f"Starting email test server on port {port}...")
    print("Press Ctrl-C to exit")
    try:
        asyncore.loop()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    manager.run()
