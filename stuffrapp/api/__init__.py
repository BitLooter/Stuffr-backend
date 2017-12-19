"""Common startup code for API blueprints."""

from flask_security import user_registered

from database import db
from ..logger import logger
from . import models


@user_registered.connect
def setup_new_user(*_, user: models.User, **__):
    """Initial setup for a new user.

    Called via signal handler on user creation. The only parameter we need is
    the user instance.
    """
    logger.info('Initializing new user %s', user.email)
    default_inventory = models.Inventory(
        # TODO: Adapt for missing first name, possesive when ends with S
        name='{}\'s stuff'.format(user.name_first),
        user=user)
    db.session.add(default_inventory)
    db.session.commit()
