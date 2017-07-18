## Stuffr

Stuffr is a web-based appplication to manage your *things*. It makes it easy to manage a database of items and all their related data - keep track of receipts, photos, purchase dates, serial numbers, any sort of information you might need.

This repository contains the backend server code needed to get Stuffr to work. It mostly manages the database and provides a REST frontend to access it.


### Installation


1. Install dependencies:

    `pip install -r requirements.txt`

2. Set up the database:

    `./manage.py db upgrade`

3. Configure the server. Stuffr looks for an environment variable named `STUFFR_SETTINGS` set to the name of the configuration file to use. For development, create a directory named `instance` in the root of the Stuffr directory, copy `config_debug-example.py` to `instance/config_debug.py`, and set `STUFFR_SETTINGS` to `config_debug.py`. For more information see Flask's documentation on [instance folders](http://flask.pocoo.org/docs/0.12/config/#instance-folders).
