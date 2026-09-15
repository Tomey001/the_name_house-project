# init_db.py
# Runs on every Render startup to ensure database is ready

from app import app, db

with app.app_context():
    from models import Room, Tenant, Payment, Admin

    # Create all tables if they don't exist
    db.create_all()
    print("✅ Database tables ready!")

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
        print("✅ All 10 rooms created!")
    else:
        print(f"ℹ️  Rooms already exist. Skipping.")

    # ── Create admin if not exists ───────────────────────
    existing_admin = Admin.query.filter_by(username='admin').first()
    if not existing_admin:
        admin = Admin(username='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("✅ Admin account created!")
        print("   Username : admin")
        print("   Password : admin123")
    else:
        print("ℹ️  Admin already exists. Skipping.")

    print("✅ All done — app is ready!")