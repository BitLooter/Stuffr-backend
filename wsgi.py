#!/usr/bin/env python3
"""Manager for Flask-Script, containing backend-related commands."""

import sys
import os
import asyncore
from smtpd import SMTPServer
from flask import render_template
from flask_debugtoolbar import DebugToolbarExtension
import flask_migrate
from flask_mail import email_dispatched
from sqlalchemy.orm.exc import MultipleResultsFound

from stuffrapp import create_app
from stuffrapp.api import models
from database import db

# Manager setup
################

if not os.environ['STUFFR_SETTINGS']:
    print('Set the STUFFR_SETTINGS environment variable before using this tool.')
    sys.exit(1)

app = create_app()

# Alembic/Flask-Migrate
flask_migrate.Migrate(app, db)


# Development server setup
###########################

# Display emails sent by flask
def report_email(message, **_):
    """Take an outgoing message and print it to the screen."""
    print(f"===== Email sent by Stuffr =====")
    print(f"From: {message.sender}")
    print(f"To: {','.join(message.recipients)}")
    print(f"Subject: {message.subject}")
    print(f"Body:\n{message.body.strip()}")


email_dispatched.connect(report_email)

# Debug toolbar
# TODO: Figure out why this stopped working
DebugToolbarExtension(app)


# Show root HTML with debug toolbar
@app.route('/')
def debug_root():
    """Serve index.html when using the debug server."""
    # Using render_template so flask_debugtoolbar can do its thing
    return render_template('index.html')


def db_created():
    """Return status of creation of database tables."""
    return db.engine.dialect.has_table(db.engine, 'database_info')


# CLI commands
###############

@app.cli.command()
def init():
    """Set up the database with default data."""
    if not db_created():
        print("Creating database tables...")
        # Using Alembic to manage database migration (via Flask-Migrate)
        flask_migrate.upgrade()

    try:
        db_info = models.DatabaseInfo.query.one_or_none()
    except MultipleResultsFound:
        print("Multiple DatabaseInfo entries found. This shouldn't happen.")
        return
    else:
        # If no DatabaseInfo table, database has not been initialized
        if db_info:
            print('Stuffr already initialized')
        else:
            print('Performing first-time database initialization...')
            info = models.DatabaseInfo(
                creator_name='Stuffr',
                creator_version='alpha')
            db.session.add(info)
            db.session.commit()


@app.cli.command()
def dbinfo():
    """Display information about database."""
    if not db_created():
        print("Database has not been created, run 'flask init'")
        return

    try:
        db_info = models.DatabaseInfo.query.one_or_none()
    except MultipleResultsFound:
        print("Multiple DatabaseInfo entries found. This shouldn't happen.")
    else:
        if db_info:
            print(f"Database version: {db_info.database_version}")
            print(f"Creation date: {db_info.date_created}")
            print(f"Creator name: {db_info.creator_name}")
            print(f"Creator version: {db_info.creator_version}")
        else:
            print("Database has not been initialized, run 'flask init'")


@app.cli.command()
def listroutes():
    """List all views defined by the app."""
    for rule in sorted(app.url_map.iter_rules(),
                       key=lambda r: r.endpoint):
        endpoint = rule.endpoint
        methods = ', '.join(r for r in rule.methods if r not in ['OPTIONS', 'HEAD'])
        path = rule.rule
        print(f'{endpoint}: ({methods}) {path}')


@app.cli.command()
def showconfig():
    """Output the current configuration."""
    for key in sorted(app.config):
        print(f"{key}: {app.config[key]}")


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


@app.cli.command()
def emailsrv():
    """Barebones development SMTP server.

    Normally this is not needed, as a default development config will suppress
    sending of emails and print them to stdout instead. However, if you wish
    to develop or test with an actual SMTP server, this will work as a very
    bare-bones server. Anything more complicated than simply printing emails
    to the screen will need a proper server.
    """
    if 'MAIL_SERVER' not in app.config:
        print("MAIL_SERVER must be configured to use email")
        return
    host = app.config['MAIL_SERVER']
    port = app.config.get('MAIL_PORT', 25)
    DummySMTP((host, port), None)
    print(f"Starting email test server on port {port}...")
    print("Press Ctrl-C to exit")
    try:
        asyncore.loop()
    except KeyboardInterrupt:
        pass
