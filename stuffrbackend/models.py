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


class Thing(Base):
    """Model for generic thing data."""

    __tablename__ = 'things'
    name = db.Column(db.String, nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.datetime.utcnow, nullable=False)
    date_updated = db.Column(db.DateTime, default=datetime.datetime.utcnow, nullable=False)

    def as_dict(self):
        """Fix datetime columns before creating dict."""
        # SQLite does not keep timezone information, assume UTC
        if self.date_created.tzinfo is None:
            self.date_created = self.date_created.replace(tzinfo=datetime.timezone.utc)
        return Base.as_dict(self)

    # TODO: Fix this property code
    # @property
    # @sqlalchemy.ext.declarative.synonym_for('_date_created')
    # def date_created(self):
    #     """Fix date before returning value."""
    #     # SQLite does not keep timezone information, assume utcnow
    #     if self._date_created.tzinfo is None:
    #         self._date_created.tzinfo = datetime.timezone.utc
    #     return self._date_created
    #
    # @date_created.setter
    # def date_created(self, created):
    #     """Set creation date."""
    #     self._date_created = created

    def __repr__(self):
        """Basic Thing data as a string."""
        return "<Thing name='{}'>".format(self.name)
