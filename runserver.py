#!/usr/bin/env python3
"""Flask debug server for the Stuffr backend."""

from flask import Flask, send_from_directory

from stuffrbackend import bp as stuffr_bp


app = Flask('stuffrdebugserver',
            instance_relative_config=True,
            static_url_path='')
app.config.from_object('stuffrbackend.defaultconfig')
app.config.from_pyfile('debugconfig.py', silent=True)
app.register_blueprint(stuffr_bp, url_prefix='/api')


@app.route('/')
def debug_root():
    """Serve index.html when using the debug server."""
    return send_from_directory('static', 'index.html')


if __name__ == "__main__":
    app.run(app.config['SERVER_DEBUG_HOST'], app.config['SERVER_DEBUG_PORT'])
