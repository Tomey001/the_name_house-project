# models.py
from datetime import datetime, date

# Import shared db to avoid circular imports
from extensions import db

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


# ============================================================
# TABLE 1: ROOMS
# ============================================================
class Room(db.Model):
    __tablename__ = 'rooms'

    id = db.Column(db.Integer, primary_key=True)
    room_name = db.Column(db.String(100), nullable=False, unique=True)
    room_type = db.Column(db.String(50), nullable=False)
    is_occupied = db.Column(db.Boolean, default=False, nullable=False)

    # One room connects to one tenant
    tenant = db.relationship('Tenant', backref='room', uselist=False)

    def __repr__(self):
        return f'<Room {self.room_name}>'


# ============================================================
# TABLE 2: TENANTS
# ============================================================
class Tenant(db.Model):
    __tablename__ = 'tenants'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(150), nullable=True)
    emergency_contact = db.Column(db.String(150), nullable=True)
    emergency_phone = db.Column(db.String(20), nullable=True)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    date_registered = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    # One tenant connects to many payments
    payments = db.relationship('Payment', backref='tenant', lazy=True)

    def __repr__(self):
        return f'<Tenant {self.full_name}>'


# ============================================================
# TABLE 3: PAYMENTS
# ============================================================
class Payment(db.Model):
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.Date, nullable=False)
    expiry_date = db.Column(db.Date, nullable=False)
    notes = db.Column(db.String(255), nullable=True)
    date_recorded = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Payment {self.tenant_id} - {self.payment_date}>'

    @property
    def status(self):
        today = date.today()
        days_left = (self.expiry_date - today).days
        if days_left < 0:
            return 'EXPIRED'
        elif days_left <= 30:
            return 'EXPIRING SOON'
        else:
            return 'ACTIVE'

    @property
    def days_remaining(self):
        today = date.today()
        return (self.expiry_date - today).days


# ============================================================
# TABLE 4: ADMIN
# ============================================================
class Admin(UserMixin, db.Model):
    __tablename__ = 'admin'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<Admin {self.username}>'