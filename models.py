"""Data models for Stuffr."""

import sqlalchemy.ext.declarative
from sqlalchemy import Column, Integer, String

Base = sqlalchemy.ext.declarative.declarative_base()


class Thing(Base):
    """Model for generic thing data."""

    __tablename__ = 'things'
    id = Column(Integer, primary_key=True)
    name = Column(String)

    def as_dict(self):
        """Return fields as a dict."""
        # TODO: find out if there's a way to do this built into SQLAlchemy
        return {'id': self.id, 'name': self.name}

    def __repr__(self):
        """Basic Thing data as a string."""
        return "<Thing name='{}'>".format(self.name)
