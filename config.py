# config.py
# This file contains all the settings for our Flask application

import os  # os helps us work with file paths and environment variables

# This is the base directory of our project
BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # SECRET_KEY is used to protect forms and sessions
    # Think of it as a password for your app's security system
    SECRET_KEY = 'thenamevilla-secret-key-2025'

    # This tells Flask where to find the SQLite database file
    # It will be created automatically inside an 'instance' folder
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'instance', 'tenancy.db')

    # This turns off a feature we don't need (saves memory)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

