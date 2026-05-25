from flask_sqlalchemy import SQLAlchemy

# Shared SQLAlchemy instance to avoid circular imports between app.py and models.py
db = SQLAlchemy()

