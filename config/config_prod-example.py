"""Example settings for production."""

from sqlalchemy.engine.url import URL

# Value must be set
SECRET_KEY =

# Default database information
# https://docs.sqlalchemy.org/en/latest/core/engines.html#sqlalchemy.engine.url.URL
SQLALCHEMY_DATABASE_URI = URL(
    drivername='',
    host='',
    username='',
    password='',
    database=''
)
