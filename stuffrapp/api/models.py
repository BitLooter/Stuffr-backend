"""Data models for Stuffr."""

import datetime
import sqlalchemy

from database import db


class Base(db.Model):
    """Base class for all models."""

    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)

    def as_dict(self):
        """Return fields as a dict."""
        return {c.key: getattr(self, c.key)
                for c in sqlalchemy.inspect(self).mapper.column_attrs}


class StuffrInfo(Base):
    """Model for database metadata."""

    creator_name = db.Column(db.Unicode, nullable=False)

    def __repr__(self):
        """Basic StuffrInfo data as a string."""
        return "<StuffrInfo creator_name='{}'>".format(self.creator_name)


class Thing(Base):
    """Model for generic thing data."""

    __tablename__ = 'things'
    name = db.Column(db.String, nullable=False)
    date_created = db.Column(db.DateTime, nullable=False,
                             default=datetime.datetime.utcnow)
    date_modified = db.Column(db.DateTime, nullable=False,
                              default=datetime.datetime.utcnow,
                              onupdate=datetime.datetime.utcnow)
    date_deleted = db.Column(db.DateTime)
    description = db.Column(db.UnicodeText)
    notes = db.Column(db.UnicodeText)

    def as_dict(self):
        """Fix datetime columns before creating dict."""
        # SQLite does not keep timezone information, assume UTC
        if self.date_created.tzinfo is None:
            self.date_created = self.date_created.replace(tzinfo=datetime.timezone.utc)
        if self.date_modified.tzinfo is None:
            self.date_modified = self.date_modified.replace(tzinfo=datetime.timezone.utc)
        return Base.as_dict(self)

    def __repr__(self):
        """Basic Thing data as a string."""
        return "<Thing name='{}'>".format(self.name)
