# create_admin.py
# Run this file ONCE to create the admin account

from app import app, db
from models import Admin

def create_admin():
    with app.app_context():

        # Check if admin already exists
        existing = Admin.query.filter_by(username='admin').first()
        if existing:
            print("⚠️  Admin account already exists. Skipping.")
            return

        # Create the admin account
        admin = Admin(username='admin')
        admin.set_password('admin123')  # ← You can change this password

        db.session.add(admin)
        db.session.commit()

        print("✅ Admin account created successfully!")
        print("   Username: admin")
        print("   Password: admin123")
        print("\n⚠️  Remember to change this password later!")

if __name__ == '__main__':
    create_admin()