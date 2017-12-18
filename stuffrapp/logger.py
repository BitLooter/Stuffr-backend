"""Code for working with application logger."""

import logging

# Throw away logging messages until otherwise set up
null_logger = logging.getLogger('__NULL_LOGGER__')
null_logger.setLevel(logging.CRITICAL + 1)
null_logger.handlers = [logging.NullHandler()]
logger = null_logger


def set_logger(new_logger):
    """Set the active logger."""
    global logger  # pylint: disable=global-statement
    logger = new_logger
