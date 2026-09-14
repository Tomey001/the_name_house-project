# config.py
# Configuration for both local development and production

import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Use environment variable on Render, fallback for local dev
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'thenamehouse-dev-key-2025'

    # Database path
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(BASE_DIR, 'instance', 'tenancy.db')

    SQLALCHEMY_TRACK_MODIFICATIONS = False