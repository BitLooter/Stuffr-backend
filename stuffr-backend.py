#!/usr/bin/env python3
"""Main file for Stuffr's backend."""

import json
from flask import Flask, send_from_directory

app = Flask('stuffr-backend', static_url_path='')


@app.route('/')
def debug_root():
    """Serve index.html when using the debug server."""
    # TODO: Check that debug mode is on first
    return send_from_directory('static', 'index.html')


@app.route('/api/things')
def get_things():
    """Provide a list of things from the database."""
    things = [
        {'id': 0, 'name': 'First thing'},
        {'id': 1, 'name': 'Second thing'}
    ]
    return json.dumps(things)


if __name__ == "__main__":
    # TODO: load config from file
    app.run(debug=True, host='0.0.0.0', port=8080)
