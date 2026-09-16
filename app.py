# app.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config
import os

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please login to access this page.'
login_manager.login_message_category = 'warning'

os.makedirs(
    os.path.join(app.root_path, 'instance'),
    exist_ok=True
)

@login_manager.user_loader
def load_user(user_id):
    with app.app_context():
        from models import Admin
        return db.session.get(Admin, int(user_id))

# ── Always create tables on startup ─────────────────────
# This runs every time gunicorn starts the app
# It is safe to run multiple times — skips if already exists
with app.app_context():
    from models import Room, Tenant, Payment, Admin

    # Create all tables if they don't exist
    db.create_all()
    print("✅ Tables ready!")

    # Create rooms if empty
    room_count = db.session.execute(
        db.select(db.func.count(Room.id))
    ).scalar()

    if room_count == 0:
        rooms = [
            Room(room_name='Chamber & Hall 1',
                 room_type='Chamber and Hall'),
            Room(room_name='Chamber & Hall 2',
                 room_type='Chamber and Hall'),
            Room(room_name='Chamber & Hall 3',
                 room_type='Chamber and Hall'),
            Room(room_name='Single Room 1',
                 room_type='Single Room'),
            Room(room_name='Single Room 2',
                 room_type='Single Room'),
            Room(room_name='Single Room 3',
                 room_type='Single Room'),
            Room(room_name='Single Room 4',
                 room_type='Single Room'),
            Room(room_name='Store 1',
                 room_type='Store'),
            Room(room_name='Store 2',
                 room_type='Store'),
            Room(room_name='Store 3',
                 room_type='Store'),
        ]
        db.session.add_all(rooms)
        db.session.commit()
        print("✅ 10 rooms created!")
    else:
        print("ℹ️  Rooms exist — skipping")

    # Create admin if not exists
    existing_admin = db.session.execute(
        db.select(Admin).where(Admin.username == 'admin')
    ).scalar_one_or_none()

    if not existing_admin:
        admin = Admin(username='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("✅ Admin created — username:admin password:admin123")
    else:
        print("ℹ️  Admin exists — skipping")

    print("✅ Database fully ready!")

# Import routes LAST — after everything is set up
from routes import *

if __name__ == '__main__':
    app.run(debug=True)