"""Data models for Stuffr.

Some things to note:

* "Client entities" are database fields the client uses (e.g. creation dates).
* "User entities" are database columns the client can modify (e.g. item names).
* "Managed entities" are database columns the client cannot modify (e.g. row IDs).

Typically client entities used to filter data sent to the client, and user
entities are to verify data modification requests from the client. Managed
entities are simply any entities that are not User entities.

I made these names up. If it turns out there are already established names for
these concepts these names should be refactored to  match standard industry
practice.
"""

import datetime
from typing import Dict, Mapping, Sequence, Set
import flask_security
import sqlalchemy

from database import db

# TODO: Increment this once the database layout settles down
DATABASE_VERSION = 0


def fix_dict_datetimes(the_dict: Mapping) -> Dict:
    """Ensure datetimes have timezones in a dict from SQLAlchemy.

    Necessary because some databases (e.g. SQLite) do not store timezone
    information. Stuffr uses UTC in the database, so this just adds the UTC
    timezone to the datetime fields.
    """
    for k, v in the_dict.items():
        if type(v) is datetime.datetime and v.tzinfo is None:
            the_dict[k] = v.replace(tzinfo=datetime.timezone.utc)
    return the_dict


# Models
#########

# Models for authentication/authorization

class BaseModel(db.Model):
    """Base class for all models."""

    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)

    def as_dict(self):
        """Return fields as a dict."""
        return {c.key: getattr(self, c.key)
                for c in sqlalchemy.inspect(self).mapper.column_attrs}


class DatabaseInfo(BaseModel):
    """Model for database metadata."""

    creator_name = db.Column(db.Unicode(length=32), nullable=False)
    creator_version = db.Column(db.Unicode(length=32), nullable=False)
    date_created = db.Column(db.DateTime, nullable=False,
                             default=datetime.datetime.utcnow)
    # Database schema version - value incremented when a breaking change is made
    database_version = db.Column(db.Integer, nullable=False,
                                 default=DATABASE_VERSION)

    def __repr__(self):
        """Basic DatabaseInfo data as a string."""
        return "<DatabaseInfo creator_name='{}'>".format(self.creator_name)


roles_users = db.Table(
    'roles_users',
    db.Column('user_id', db.Integer(), db.ForeignKey('user.id'), nullable=False),
    db.Column('role_id', db.Integer(), db.ForeignKey('role.id'), nullable=False))


class User(BaseModel, flask_security.UserMixin):
    """Model for user data."""

    # Email is used for the username
    email = db.Column(db.Unicode(length=256), nullable=False)
    password = db.Column(db.Unicode(length=128), nullable=False)
    name_first = db.Column(db.Unicode(length=128), nullable=False)
    name_last = db.Column(db.Unicode(length=128), nullable=False)
    date_created = db.Column(db.DateTime, nullable=False,
                             default=datetime.datetime.utcnow)
    active = db.Column(db.Boolean)
    confirmed_at = db.Column(db.DateTime)
    last_login_at = db.Column(db.DateTime)
    current_login_at = db.Column(db.DateTime)
    last_login_ip = db.Column(db.Unicode(length=45))
    current_login_ip = db.Column(db.Unicode(length=45))
    login_count = db.Column(db.Integer)
    # Relationships
    inventories = db.relationship('Inventory', backref='user', lazy='dynamic')
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))

    def __repr__(self):
        """Basic User data as a string."""
        return "<User email='{}'>".format(self.email)


class Role(BaseModel, flask_security.RoleMixin):
    """Role for a user."""

    name = db.Column(db.Unicode(length=32), nullable=False)
    description = db.Column(db.Unicode(length=256))

    def __repr__(self):
        """Basic Role data as a string."""
        return "<Role name='{}'>".format(self.email)


# Stuffr data models

class Inventory(BaseModel):
    """Model for a collection of things."""

    name = db.Column(db.Unicode(length=128), nullable=False)
    date_created = db.Column(db.DateTime, nullable=False,
                             default=datetime.datetime.utcnow)
    # Relationships
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    things = db.relationship('Thing', backref='inventory', lazy='dynamic')

    def __repr__(self) -> str:
        """Basic Inventory data as a string."""
        return "<Inventory name='{}'>".format(self.name)

    @classmethod
    def _get_client_entities(cls) -> Set:
        """Return SQLAlchemy entities used by clients."""
        return {cls.id, cls.name, cls.date_created}

    @classmethod
    def get_user_inventories(cls, user_id: int) -> Sequence:
        """Return all inventories belonging to specified user."""
        inventories = cls.query. \
            with_entities(*(cls._get_client_entities())). \
            filter_by(user_id=user_id).all()
        # SQLite does not keep timezone information, assume UTC if not present
        fixed_inventories = []
        for inventory in inventories:
            fixed_inventories.append(fix_dict_datetimes(inventory._asdict()))
        return fixed_inventories

    @classmethod
    def get_user_things(cls, user_id: int, inventory_id: int) -> Sequence:
        """Return all things belonging to specified user."""
        inventories = Thing.query. \
            with_entities(*(Thing._get_client_entities())). \
            filter_by(user_id=user_id).all()
        # SQLite does not keep timezone information, assume UTC if not present
        fixed_inventories = []
        for inventory in inventories:
            fixed_inventories.append(fix_dict_datetimes(inventory._asdict()))
        return fixed_inventories


class Thing(BaseModel):
    """Model for generic thing data."""

    name = db.Column(db.Unicode(length=128), nullable=False)
    date_created = db.Column(db.DateTime, nullable=False,
                             default=datetime.datetime.utcnow)
    date_modified = db.Column(db.DateTime, nullable=False,
                              default=datetime.datetime.utcnow,
                              onupdate=datetime.datetime.utcnow)
    date_deleted = db.Column(db.DateTime)
    location = db.Column(db.Unicode(length=128))
    details = db.Column(db.UnicodeText)
    # Relationships
    inventory_id = db.Column(db.Integer, db.ForeignKey('inventory.id'),
                             nullable=False)

    def as_dict(self) -> Mapping:
        """Fix datetime columns before creating dict."""
        # SQLite does not keep timezone information, assume UTC
        if self.date_created.tzinfo is None:
            self.date_created = self.date_created.replace(
                tzinfo=datetime.timezone.utc)
        if self.date_modified.tzinfo is None:
            self.date_modified = self.date_modified.replace(
                tzinfo=datetime.timezone.utc)
        return BaseModel.as_dict(self)

    def __repr__(self) -> str:
        """Basic Thing data as a string."""
        return "<Thing name='{}'>".format(self.name)

    @classmethod
    def _get_client_entities(cls) -> Set:
        """Return SQLAlchemy entities used by clients."""
        return {
            cls.id, cls.name,
            cls.date_created, cls.date_modified, cls.date_deleted,
            cls.location, cls.details,
            cls.inventory_id}

    @classmethod
    def get_inventory_things(cls, inventory_id: int) -> Sequence:
        """Return all things belonging to specified inventory."""
        things = cls.query.with_entities(*cls._get_client_entities()). \
            filter_by(date_deleted=None, inventory_id=inventory_id).all()
        fixed_things = []
        for thing in things:
            # SQLite does not keep timezone information, assume UTC
            # TODO: see if _as_dict is doing redundant timezone fixing
            fixed_things.append(fix_dict_datetimes(thing._asdict()))
        return fixed_things

    @classmethod
    def get_thing_details(cls, thing_id: int) -> Mapping:
        """Return all information for specified thing."""
        # TODO: Find a cleaner way to do this. get() errors with with_entities
        thing = cls.query.with_entities(*cls._get_client_entities()). \
            filter_by(id=thing_id).all()[0]
        fixed_thing = fix_dict_datetimes(thing._asdict())
        return fixed_thing
