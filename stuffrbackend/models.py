"""Data models for Stuffr."""

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


class Thing(Base):
    """Model for generic thing data."""

    __tablename__ = 'things'
    name = db.Column(db.String)

    def __repr__(self):
        """Basic Thing data as a string."""
        return "<Thing name='{}'>".format(self.name)
