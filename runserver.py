#!/usr/bin/env python3
"""Flask debug server for the Stuffr backend."""

from stuffrbackend import app

if __name__ == "__main__":
    # TODO: load config from file
    app.run(debug=True, host='0.0.0.0', port=8080)
