#!/usr/bin/env python3
"""Flask debug server for the Stuffr backend."""

from flask import Flask, render_template
from flask_debugtoolbar import DebugToolbarExtension

from database import db


def create_app():
    """Create the flask app for the debug server."""
    app = Flask('stuffrdebugserver',
                instance_relative_config=True,
                static_url_path='',
                template_folder='static')
    app.config.from_object('defaultconfig')
    app.config.from_pyfile('debugconfig.py', silent=True)

    db.init_app(app)

    from stuffrbackend import bp as stuffr_bp
    app.register_blueprint(stuffr_bp, url_prefix='/api')

    return app


if __name__ == "__main__":
    app = create_app()
    DebugToolbarExtension(app)

    @app.route('/')
    def debug_root():
        """Serve index.html when using the debug server."""
        # Using render_template so flask_debugtoolbar can do its thing
        return render_template('index.html')

    app.run(app.config['SERVER_DEBUG_HOST'], app.config['SERVER_DEBUG_PORT'])
