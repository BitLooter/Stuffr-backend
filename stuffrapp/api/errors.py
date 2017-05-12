"""Exceptions that can be raised by Stuffer API code."""


class ItemNotFoundError(Exception):
    """Raised when an item is not found in the database.

    Used (for example) if a data access method is given a nonexistant ID.
    """

    pass


class UserPermissionError(Exception):
    """Raised when a user does not have permission to perform an action.

    Example: A user tries to delete an item they do not own.
    """

    pass


class InvalidDataError(Exception):
    """Raised when bad data is given to the database.

    Example: A non-nullable field is not given a value.
    """

    pass
