"""Data models for Stuffr.

Some things to note:

* "Client" entities are database columns the client uses (e.g. creation dates).
* "User" entities are database columns the client can modify (e.g. item names).
* "Managed" entities are database columns the client cannot modify (e.g. row IDs).
* "Required" fields are columns that require data during creation.

Typically client entities used to filter data sent to the client, and user
entities are to verify data modification requests from the client. Managed
entities are simply any entities that are not User entities.

I made these names up. If it turns out there are already established names for
these concepts these names should be refactored to  match standard industry
practice.
"""

from collections import abc
import datetime
from typing import List, Mapping, Sequence, Set
import flask_security
import sqlalchemy
from sqlalchemy_utc import UtcDateTime

from database import db
from . import errors

# TODO: Increment this once the database layout settles down
DATABASE_VERSION = 0


def get_entity_names(entities: Sequence) -> Set:
    """Return the column names of all given entities."""
    return {c.key for c in entities}


# Models
#########

# Models for authentication/authorization

class BaseModel(db.Model):
    """Base class for all models.

    Subclasses should define CLIENT_FIELDS as a set with the field names as
    strings.
    """

    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)

    CLIENT_FIELDS = set()
    USER_FIELDS = set()
    REQUIRED_FIELDS = set()

    def _asdict(self) -> Mapping:
        """Return fields as a dict.

        Named as _asdict to match SQLAlchemy query results.
        """
        return {c.key: getattr(self, c.key)
                for c in sqlalchemy.inspect(self).mapper.column_attrs}

    def as_client_dict(self) -> Mapping:
        """Return fields as a dict, filtered for clients."""
        return {k: v for k, v in self._asdict().items() if k in self.CLIENT_FIELDS}

    @classmethod
    def id_exists(cls, item_id: int) -> bool:
        """Check that a row with the specified ID exists in the database."""
        return db.session.query(db.exists().where(cls.id == item_id)).scalar()

    @classmethod
    def get_client_entities(cls) -> Set:
        """Return SQLAlchemy entities used by clients."""
        return {getattr(cls, f) for f in cls.CLIENT_FIELDS}

    @classmethod
    def filter_user_input_dict(cls, data: Mapping) -> dict:
        """Take a dict with model object data and remove non-user fields."""
        if not isinstance(data, abc.Mapping):
            error = f'Provided data has type {type(data)}, should be a dict'
            raise errors.InvalidDataError(error)
        return {k: v for (k, v) in data.items() if k in cls.USER_FIELDS}

    @classmethod
    def total_count(cls):
        """Return the total number of this model in the database."""
        return cls.query.count()


class DatabaseInfo(BaseModel):
    """Model for database metadata."""

    creator_name = db.Column(db.Unicode(length=32), nullable=False)
    creator_version = db.Column(db.Unicode(length=32), nullable=False)
    date_created = db.Column(UtcDateTime, nullable=False,
                             default=datetime.datetime.now(datetime.timezone.utc))
    # Database schema version - value incremented when a breaking change is made
    database_version = db.Column(db.Integer, nullable=False,
                                 default=DATABASE_VERSION)

    def __repr__(self) -> str:
        """Basic DatabaseInfo data as a string."""
        return "<DatabaseInfo creator_name='{}'>".format(self.creator_name)


roles_users = db.Table(
    'roles_users',
    db.Column('user_id', db.Integer(), db.ForeignKey('user.id'), nullable=False),
    db.Column('role_id', db.Integer(), db.ForeignKey('role.id'), nullable=False))


class User(BaseModel, flask_security.UserMixin):
    """Model for user data.

    Note that this model is managed by Flask-Security, so there is not much
    need for data access methods.
    """

    CLIENT_FIELDS = {'id', 'email', 'name_first', 'name_last'}

    # Email is used for the username
    email = db.Column(db.Unicode(length=256), nullable=False)
    password = db.Column(db.Unicode(length=128), nullable=False)
    name_first = db.Column(db.Unicode(length=128), nullable=False)
    name_last = db.Column(db.Unicode(length=128), nullable=False)
    date_created = db.Column(UtcDateTime, nullable=False,
                             default=datetime.datetime.now(datetime.timezone.utc))
    active = db.Column(db.Boolean)
    confirmed_at = db.Column(UtcDateTime)
    last_login_at = db.Column(UtcDateTime)
    current_login_at = db.Column(UtcDateTime)
    last_login_ip = db.Column(db.Unicode(length=45))
    current_login_ip = db.Column(db.Unicode(length=45))
    login_count = db.Column(db.Integer)
    # Relationships
    inventories = db.relationship('Inventory', backref='user', lazy='dynamic')
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))

    def __repr__(self) -> str:
        """Basic User data as a string."""
        return "<User email='{}'>".format(self.email)

    @classmethod
    def get_user_list(cls) -> List['User']:
        """Return of list of all users in database."""
        # TODO: Don't load ALL user data for a simple listing
        users = cls.query.all()
        return users


class Role(BaseModel, flask_security.RoleMixin):
    """Role for a user."""

    name = db.Column(db.Unicode(length=32), nullable=False)
    description = db.Column(db.Unicode(length=256))

    def __repr__(self) -> str:
        """Basic Role data as a string."""
        return "<Role name='{}'>".format(self.email)


# Stuffr data models

class Inventory(BaseModel):
    """Model for a collection of things."""

    # Columns
    name = db.Column(db.Unicode(length=128), nullable=False)
    date_created = db.Column(UtcDateTime, nullable=False,
                             default=datetime.datetime.now(datetime.timezone.utc))
    # Relationships
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    things = db.relationship('Thing', backref='inventory', lazy='dynamic')
    # Other data
    CLIENT_FIELDS = {'id', 'name', 'date_created'}
    USER_FIELDS = {'name'}
    REQUIRED_FIELDS = {'name'}

    def __repr__(self) -> str:
        """Basic Inventory data as a string."""
        return "<Inventory name='{}'>".format(self.name)

    @classmethod
    def get_user_inventories(cls, user_id: int) -> List['Inventory']:
        """Return all inventories belonging to specified user."""
        if not db.session.query(sqlalchemy.sql.exists().where(User.id == user_id)).scalar():
            error = f'User #{user_id} does not exist'
            raise errors.ItemNotFoundError(error)
        inventories = cls.query.filter_by(user_id=user_id).all()
        return inventories

    @classmethod
    def create_new_inventory(cls, inventory_data: Mapping, user_id: int) -> 'Inventory':
        """Create a new inventory based on inventory_data."""
        if not db.session.query(sqlalchemy.sql.exists().where(User.id == user_id)).scalar():
            error = f'User #{user_id} does not exist'
            raise errors.ItemNotFoundError(error)
        clean_data = cls.filter_user_input_dict(inventory_data)
        if not cls.REQUIRED_FIELDS.issubset(clean_data):
            missing_fields = [f for f in cls.REQUIRED_FIELDS
                              if f not in inventory_data]
            error = "Required field(s) missing: {}".format(', '.join(missing_fields))
            raise errors.InvalidDataError(error)
        inventory = cls(user_id=user_id, **clean_data)
        db.session.add(inventory)
        try:
            db.session.commit()
        except sqlalchemy.exc.IntegrityError as e:
            error = 'Database error: {}'.format(e.orig)
            raise errors.InvalidDataError(error)
        return inventory


class Thing(BaseModel):
    """Model for generic thing data."""

    # Columns
    name = db.Column(db.Unicode(length=128), nullable=False)
    date_created = db.Column(UtcDateTime, nullable=False,
                             default=datetime.datetime.now(datetime.timezone.utc))
    date_modified = db.Column(UtcDateTime, nullable=False,
                              default=datetime.datetime.now(datetime.timezone.utc),
                              onupdate=datetime.datetime.now(datetime.timezone.utc))
    date_deleted = db.Column(UtcDateTime)
    location = db.Column(db.Unicode(length=128))
    details = db.Column(db.UnicodeText)
    # Relationships
    inventory_id = db.Column(db.Integer, db.ForeignKey('inventory.id'),
                             nullable=False)
    # Other data
    CLIENT_FIELDS = {
        'id', 'name',
        'date_created', 'date_modified', 'date_deleted',
        'location', 'details'}
    USER_FIELDS = {'name', 'location', 'details'}
    REQUIRED_FIELDS = {'name'}

    def __repr__(self) -> str:
        """Basic Thing data as a string."""
        return "<Thing name='{}'>".format(self.name)

    @classmethod
    def get_things_for_inventory(cls, inventory_id: int, user_id: int) -> List['Thing']:
        """Return all things belonging to specified inventory."""
        if not Inventory.id_exists(inventory_id):
            error = 'Inventory #{} does not exist'.format(inventory_id)
            raise errors.ItemNotFoundError(error)
        inventory_user = Inventory.query.get(inventory_id).user
        if inventory_user is None:
            error = 'User #{} does not exist'.format(user_id)
            raise errors.ItemNotFoundError(error)
        elif inventory_user.id != user_id:
            error = 'User #{} does not have permission to get things from Inventory #{}'.format(
                user_id, inventory_id)
            raise errors.UserPermissionError(error)
        things = cls.query.filter_by(date_deleted=None, inventory_id=inventory_id).all()
        return things

    @classmethod
    def get_thing(cls, thing_id: int, user_id: int) -> 'Thing':
        """Return all information for specified thing."""
        thing = cls.query.get(thing_id)
        if thing is None:
            error = f'Thing #{thing_id} does not exist'
            raise errors.ItemNotFoundError(error)
        if not db.session.query(sqlalchemy.sql.exists().where(User.id == user_id)).scalar():
            error = f'User #{user_id} does not exist'
            raise errors.ItemNotFoundError(error)
        elif thing.inventory.user_id != user_id:
            error = f'User #{user_id} does not have permission to read Thing #{thing_id}'
            raise errors.UserPermissionError(error)
        return thing

    @classmethod
    def create_new_thing(cls, thing_data: Mapping, inventory_id: int, user_id: int) -> 'Thing':
        """Create a new thing."""
        # Sanity check of input
        if not Inventory.id_exists(inventory_id):
            raise errors.ItemNotFoundError('No Inventory with id {}'.format(inventory_id))
        if not db.session.query(sqlalchemy.sql.exists().where(User.id == user_id)).scalar():
            error = f'User #{user_id} does not exist'
            raise errors.ItemNotFoundError(error)
        if Inventory.query.get(inventory_id).user_id != user_id:
            raise errors.UserPermissionError('Inventory #{} does not belong to user #{}'.format(
                inventory_id, user_id))
        clean_data = cls.filter_user_input_dict(thing_data)
        if not cls.REQUIRED_FIELDS.issubset(clean_data):
            missing_fields = [f for f in cls.REQUIRED_FIELDS
                              if f not in thing_data]
            error = "Required field(s) missing: {}".format(', '.join(missing_fields))
            raise errors.InvalidDataError(error)

        # Create the thing
        thing = cls(inventory_id=inventory_id, **clean_data)
        db.session.add(thing)
        try:
            db.session.commit()
        except sqlalchemy.exc.IntegrityError as e:
            error = 'Database error: {}'.format(e.orig)
            raise errors.InvalidDataError(error)
        return thing

    @classmethod
    def update_thing(cls, thing_id: int, update_data: Mapping, user_id: int) -> dict:
        """Update thing with new data.

        Afer updating, returns data that changed (including server-managed
        fields such as date_updated).
        """
        thing = cls.query.get(thing_id)
        if thing is None:
            error = 'Thing #{} does not exist'.format(thing_id)
            raise errors.ItemNotFoundError(error)
        if not db.session.query(sqlalchemy.sql.exists().where(User.id == user_id)).scalar():
            error = f'User #{user_id} does not exist'
            raise errors.ItemNotFoundError(error)
        elif thing.inventory.user_id != user_id:
            error = 'User #{} does not have permission to modify Thing #{}'.format(
                user_id, thing_id)
            raise errors.UserPermissionError(error)

        # Filter only desired fields
        clean_data = cls.filter_user_input_dict(update_data)

        for field, value in clean_data.items():
            setattr(thing, field, value)
        try:
            db.session.commit()
        except sqlalchemy.exc.IntegrityError as e:
            error = 'Database error: {}'.format(e.orig)
            raise errors.InvalidDataError(error)

        # Get the modified data
        clean_data.update({'date_modified': thing.date_modified})
        return clean_data

    @classmethod
    def delete_thing(cls, thing_id: int, user_id: int) -> None:
        """Delete an existing thing."""
        thing = cls.query.get(thing_id)
        if thing is None:
            error = 'Thing #{} does not exist'.format(thing_id)
            raise errors.ItemNotFoundError(error)
        elif thing.inventory.user_id != user_id:
            error = 'User #{} does not have permission to delete Thing #{}'.format(
                user_id, thing_id)
            raise errors.UserPermissionError(error)
        thing.date_deleted = datetime.datetime.now(datetime.timezone.utc)
        db.session.commit()
