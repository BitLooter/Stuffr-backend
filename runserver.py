#!/usr/bin/env python3
"""Flask debug server for the Stuffr backend."""

from stuffrbackend import app

if __name__ == "__main__":
    app.run(app.config['SERVER_DEBUG_HOST'], app.config['SERVER_DEBUG_PORT'])
