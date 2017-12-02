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

SECURITY_PASSWORD_HASH = 'bcrypt'

# Set these to your SMTP server. MAIL_PORT defaults to 25 if not set.
MAIL_SERVER =
# MAIL_PORT =
