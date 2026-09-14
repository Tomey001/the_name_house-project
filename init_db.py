# init_db.py
# This runs automatically to set up the database on Render

from app import app, db

with app.app_context():
    # Import all models
    from models import Room, Tenant, Payment, Admin

    # Create all tables
    db.create_all()

    # ── Seed rooms if empty ──────────────────────────────
    if Room.query.count() == 0:
        rooms = [
            Room(room_name='Chamber & Hall 1', room_type='Chamber and Hall'),
            Room(room_name='Chamber & Hall 2', room_type='Chamber and Hall'),
            Room(room_name='Chamber & Hall 3', room_type='Chamber and Hall'),
            Room(room_name='Single Room 1',    room_type='Single Room'),
            Room(room_name='Single Room 2',    room_type='Single Room'),
            Room(room_name='Single Room 3',    room_type='Single Room'),
            Room(room_name='Single Room 4',    room_type='Single Room'),
            Room(room_name='Store 1',          room_type='Store'),
            Room(room_name='Store 2',          room_type='Store'),
            Room(room_name='Store 3',          room_type='Store'),
        ]
        db.session.add_all(rooms)
        db.session.commit()
        print("✅ Rooms seeded successfully!")

    # ── Create admin if not exists ───────────────────────
    if Admin.query.count() == 0:
        admin = Admin(username='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("✅ Admin account created!")

    print("✅ Database ready!")