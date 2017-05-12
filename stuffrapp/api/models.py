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

import datetime
from typing import Dict, Mapping, Sequence, Set
import flask_security
import sqlalchemy

from database import db
from . import errors

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

    @classmethod
    def id_exists(cls, item_id) -> bool:
        """Check that a row with the specified ID exists in the database."""
        return db.session.query(db.exists().where(cls.id == item_id)).scalar()

    @classmethod
    def get_client_entities(cls) -> Set:
        """Return SQLAlchemy entities used by clients."""
        # TODO: Set comprehension?
        entities = set()
        for field in cls.CLIENT_FIELDS:
            entities.add(getattr(cls, field))
        return entities

    def as_dict(self) -> Mapping:
        """Return fields as a dict."""
        return {c.key: getattr(self, c.key)
                for c in sqlalchemy.inspect(self).mapper.column_attrs}

    @classmethod
    def filter_user_input_dict(cls, data) -> Mapping:
        """Take a dict with model object data and remove non-user fields."""
        if type(data) is not dict:
            error = 'Provided data has type {}, should be a dict'.format(type(data))
            raise errors.InvalidDataError(error)
        return {k: v for (k, v) in data.items() if k in cls.USER_FIELDS}


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

    CLIENT_FIELDS = {'id', 'email', 'name_first', 'name_last'}

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

    def __repr__(self) -> str:
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

    # Columns
    name = db.Column(db.Unicode(length=128), nullable=False)
    date_created = db.Column(db.DateTime, nullable=False,
                             default=datetime.datetime.utcnow)
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
    def get_user_inventories(cls, user_id: int) -> Sequence:
        """Return all inventories belonging to specified user."""
        inventories = cls.query. \
            with_entities(*cls.get_client_entities()). \
            filter_by(user_id=user_id).all()
        # SQLite does not keep timezone information, assume UTC if not present
        fixed_inventories = []
        for inventory in inventories:
            # TODO: probably using wrong _asdict
            fixed_inventories.append(fix_dict_datetimes(inventory._asdict()))
        return fixed_inventories

    @classmethod
    def create_new_inventory(cls, inventory_data: Mapping, user_id: int) -> 'Inventory':
        """Create a new inventory based on inventory_data."""
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
    # Other data
    CLIENT_FIELDS = {
        'id', 'name',
        'date_created', 'date_modified', 'date_deleted',
        'location', 'details'}
    USER_FIELDS = {'name', 'location', 'details'}
    REQUIRED_FIELDS = {'name'}

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
    def get_things_for_inventory(cls, inventory_id: int, user_id: int) -> Sequence:
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
        things = cls.query.with_entities(*cls.get_client_entities()). \
            filter_by(date_deleted=None, inventory_id=inventory_id).all()
        fixed_things = []
        for thing in things:
            # SQLite does not keep timezone information, assume UTC
            # TODO: see if as_dict is doing redundant timezone fixing
            # TODO: am i even calling the right damn _asdict/as_dict?
            fixed_things.append(fix_dict_datetimes(thing._asdict()))
        return fixed_things

    @classmethod
    def get_thing_details(cls, thing_id: int) -> Mapping:
        """Return all information for specified thing."""
        # TODO: Find a cleaner way to do this. get() errors with with_entities
        thing = cls.query.with_entities(*cls.get_client_entities()). \
            filter_by(id=thing_id).all()[0]
        fixed_thing = fix_dict_datetimes(thing._asdict())
        return fixed_thing

    @classmethod
    def create_new_thing(cls, thing_data: Mapping, inventory_id: int, user_id: int) -> 'Thing':
        """Create a new thing."""
        # Sanity check of input
        if not Inventory.id_exists(inventory_id):
            raise errors.ItemNotFoundError('No Inventory with id {}'.format(inventory_id))
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
    def update_thing(cls, thing_id: int, update_data: Mapping, user_id: int) -> Mapping:
        """Update thing with new data.

        Afer updating, returns data that changed (including server-managed
        fields such as date_updated).
        """
        thing = cls.query.get(thing_id)
        if thing is None:
            error = 'Thing #{} does not exist'.format(thing_id)
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
        # TODO: handle thing does not exist
        thing = cls.query.get(thing_id)
        if thing is None:
            error = 'Thing #{} does not exist'.format(thing_id)
            raise errors.ItemNotFoundError(error)
        elif thing.inventory.user_id != user_id:
            error = 'User #{} does not have permission to delete Thing #{}'.format(
                user_id, thing_id)
            raise errors.UserPermissionError(error)
        thing.date_deleted = datetime.datetime.utcnow()
        db.session.commit()
