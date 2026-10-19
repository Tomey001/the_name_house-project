# config.py
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or \
        'thenamehouse2025supersecretkey'

    DATABASE_URL = os.environ.get('DATABASE_URL', '')

    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace(
            'postgres://', 'postgresql://', 1
        )

    SQLALCHEMY_DATABASE_URI = DATABASE_URL if DATABASE_URL \
        else 'sqlite:///' + os.path.join(
            BASE_DIR, 'instance', 'tenancy.db'
        )

    SQLALCHEMY_TRACK_MODIFICATIONS = False