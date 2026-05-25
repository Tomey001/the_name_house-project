# app.py
from flask import Flask
from flask_login import LoginManager
from config import Config
from extensions import db
import os

# Create Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Bind shared db to app (avoids circular imports)
db.init_app(app)


# Create login manager
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please login to access this page.'
login_manager.login_message_category = 'warning'

# Make sure instance folder exists
os.makedirs(os.path.join(app.root_path, 'instance'), exist_ok=True)

# This runs AFTER app and db are fully ready
with app.app_context():
    # Import models HERE (inside app context)
    from models import Room, Tenant, Payment, Admin

    # Create all tables
    db.create_all()
    print("✅ Database tables ready!")

    # Tell login manager how to load admin
    @login_manager.user_loader
    def load_user(user_id):
        return Admin.query.get(int(user_id))

# Import routes AFTER everything is set up
from routes import *

if __name__ == '__main__':
    app.run(debug=True)