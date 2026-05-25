# seed_rooms.py
# This file creates all 10 rooms in the database
# We only need to run this ONCE

from app import app, db
from models import Room

def seed_rooms():
    with app.app_context():

        # Check if rooms already exist
        # We don't want to add them twice
        existing = Room.query.count()
        if existing > 0:
            print(f"⚠️  Rooms already exist ({existing} rooms found). Skipping.")
            return

        # Define all 10 rooms
        rooms = [
            # 3 Chamber and Hall rooms
            Room(room_name='Chamber & Hall 1', room_type='Chamber and Hall'),
            Room(room_name='Chamber & Hall 2', room_type='Chamber and Hall'),
            Room(room_name='Chamber & Hall 3', room_type='Chamber and Hall'),

            # 4 Single Rooms
            Room(room_name='Single Room 1', room_type='Single Room'),
            Room(room_name='Single Room 2', room_type='Single Room'),
            Room(room_name='Single Room 3', room_type='Single Room'),
            Room(room_name='Single Room 4', room_type='Single Room'),

            # 3 Stores
            Room(room_name='Store 1', room_type='Store'),
            Room(room_name='Store 2', room_type='Store'),
            Room(room_name='Store 3', room_type='Store'),
        ]

        # Add all rooms to the database
        db.session.add_all(rooms)
        db.session.commit()  # Save to database

        print("✅ All 10 rooms added to the database successfully!")
        print("\nRooms created:")
        for room in rooms:
            print(f"  - {room.room_name} ({room.room_type})")

# Run the seeder
if __name__ == '__main__':
    seed_rooms()