"""Data models for Stuffr."""

import datetime
import flask_security
import sqlalchemy

from database import db

# TODO: Increment this once the database layout settles down
DATABASE_VERSION = 0


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


class Inventory(BaseModel):
    """Model for a collection of things."""

    name = db.Column(db.Unicode(length=128), nullable=False)
    date_created = db.Column(db.DateTime, nullable=False,
                             default=datetime.datetime.utcnow)
    # Relationships
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    things = db.relationship('Thing', backref='inventory', lazy='dynamic')

    def __repr__(self):
        """Basic Inventory data as a string."""
        return "<Inventory name='{}'>".format(self.name)


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

    def as_dict(self):
        """Fix datetime columns before creating dict."""
        # SQLite does not keep timezone information, assume UTC
        if self.date_created.tzinfo is None:
            self.date_created = self.date_created.replace(
                tzinfo=datetime.timezone.utc)
        if self.date_modified.tzinfo is None:
            self.date_modified = self.date_modified.replace(
                tzinfo=datetime.timezone.utc)
        return BaseModel.as_dict(self)

    def __repr__(self):
        """Basic Thing data as a string."""
        return "<Thing name='{}'>".format(self.name)
