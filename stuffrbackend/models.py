"""Data models for Stuffr."""

import sqlalchemy
import sqlalchemy.ext.declarative
from sqlalchemy import Column, Integer, String

DeclarativeBase = sqlalchemy.ext.declarative.declarative_base()


class Base(DeclarativeBase):
    """Base class for all models."""

    __abstract__ = True

    id = Column(Integer, primary_key=True)

    def as_dict(self):
        """Return fields as a dict."""
        return {c.key: getattr(self, c.key)
                for c in sqlalchemy.inspect(self).mapper.column_attrs}


class Thing(Base):
    """Model for generic thing data."""

    __tablename__ = 'things'
    name = Column(String)

    def __repr__(self):
        """Basic Thing data as a string."""
        return "<Thing name='{}'>".format(self.name)
