# config.py

import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # Secret key for session security
    SECRET_KEY = os.environ.get('SECRET_KEY')

    if not SECRET_KEY:
        SECRET_KEY = 'dev-only-change-this-secret-key'

    # SQLite database configuration
    # Set SQLITE_DB_PATH in Render to your persistent disk path.
    SQLITE_DB_PATH = os.environ.get(
        'SQLITE_DB_PATH',
        os.path.join(BASE_DIR, 'instance', 'tenancy.db')
    )

    # Ensure the directory containing the database exists.
    os.makedirs(os.path.dirname(SQLITE_DB_PATH), exist_ok=True)

    # SQLAlchemy database connection
    SQLALCHEMY_DATABASE_URI = (
        'sqlite:///' + SQLITE_DB_PATH.replace('\\', '/')
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # SQLite settings
    SQLALCHEMY_ENGINE_OPTIONS = {
        'connect_args': {
            'timeout': 30
        }
    }