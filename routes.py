# routes.py
# All URL routes for The Name Villa Tenancy System

from flask import render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db
from datetime import date, datetime, timedelta

# Template helper — makes get_all_rooms() available in all templates
from app import app, db

@app.context_processor
def inject_globals():
    from models import Room, Payment
    def get_all_rooms():
        return Room.query.all()
    # Count expired for sidebar badge
    all_payments  = Payment.query.all()
    expired_count = sum(1 for p in all_payments if p.status == 'EXPIRED')
    return dict(get_all_rooms=get_all_rooms, expired_count=expired_count)

# ============================================================
# HOME — Redirect to login
# ============================================================
@app.route('/')
def home():
    return redirect(url_for('login'))


# ============================================================
# LOGIN
# ============================================================
@app.route('/login', methods=['GET', 'POST'])
def login():
    from models import Admin

    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        admin = Admin.query.filter_by(username=username).first()

        if admin and admin.check_password(password):
            login_user(admin)
            flash('✅ Welcome back! You are now logged in.', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('❌ Invalid username or password.', 'danger')

    return render_template('login.html')


# ============================================================
# LOGOUT
# ============================================================
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('✅ You have been logged out.', 'info')
    return redirect(url_for('login'))

# ============================================================
# DASHBOARD
# ============================================================
@app.route('/dashboard')
@login_required
def dashboard():
    from models import Room, Tenant, Payment

    total_rooms    = Room.query.count()
    occupied_rooms = Room.query.filter_by(is_occupied=True).count()
    vacant_rooms   = total_rooms - occupied_rooms
    total_tenants  = Tenant.query.filter_by(is_active=True).count()

    all_payments   = Payment.query.all()
    expiring_soon  = sum(1 for p in all_payments if p.status == 'EXPIRING SOON')
    expired        = sum(1 for p in all_payments if p.status == 'EXPIRED')

    return render_template('dashboard.html',
        total_rooms=total_rooms,
        occupied_rooms=occupied_rooms,
        vacant_rooms=vacant_rooms,
        total_tenants=total_tenants,
        expiring_soon=expiring_soon,
        expired=expired
    )

# ============================================================
# VIEW ALL TENANTS
# ============================================================
@app.route('/tenants')
@login_required
def tenants():
    from models import Tenant

    # Get search query from URL if any
    # e.g. /tenants?search=John
    search = request.args.get('search', '')

    if search:
        # Search by name or phone number
        all_tenants = Tenant.query.filter(
            Tenant.is_active == True,
            db.or_(
                Tenant.full_name.ilike(f'%{search}%'),
                Tenant.phone.ilike(f'%{search}%')
            )
        ).all()
    else:
        # Get all active tenants
        all_tenants = Tenant.query.filter_by(is_active=True).all()

    return render_template('tenants.html',
        tenants=all_tenants,
        search=search
    )


# ============================================================
# ADD NEW TENANT
# ============================================================
@app.route('/add-tenant', methods=['GET', 'POST'])
@login_required
def add_tenant():
    from models import Room, Tenant, Payment

    # Get only VACANT rooms for the dropdown
    vacant_rooms = Room.query.filter_by(is_occupied=False).all()

    if request.method == 'POST':
        # Get all form data
        full_name        = request.form.get('full_name')
        phone            = request.form.get('phone')
        email            = request.form.get('email')
        emergency_contact = request.form.get('emergency_contact')
        emergency_phone  = request.form.get('emergency_phone')
        room_id          = request.form.get('room_id')
        payment_amount   = request.form.get('payment_amount')
        payment_date_str = request.form.get('payment_date')

        # ── Validation ──────────────────────────────────────
        if not full_name or not phone or not room_id:
            flash('❌ Full name, phone, and room are required.', 'danger')
            return render_template('add_tenant.html', rooms=vacant_rooms)

        # Check room is still vacant (safety check)
        room = Room.query.get(int(room_id))
        if not room:
            flash('❌ Selected room does not exist.', 'danger')
            return render_template('add_tenant.html', rooms=vacant_rooms)

        if room.is_occupied:
            flash(f'❌ {room.room_name} is already occupied.', 'danger')
            return render_template('add_tenant.html', rooms=vacant_rooms)

        # ── Create Tenant ────────────────────────────────────
        new_tenant = Tenant(
            full_name=full_name,
            phone=phone,
            email=email,
            emergency_contact=emergency_contact,
            emergency_phone=emergency_phone,
            room_id=int(room_id)
        )
        db.session.add(new_tenant)

        # Mark room as occupied
        room.is_occupied = True

        # ── Create Payment Record if provided ────────────────
        if payment_amount and payment_date_str:
            payment_date = datetime.strptime(payment_date_str, '%Y-%m-%d').date()

            # Rent expires exactly 1 year after payment date
            expiry_date = payment_date.replace(year=payment_date.year + 1)

            new_payment = Payment(
                tenant=new_tenant,
                amount=float(payment_amount),
                payment_date=payment_date,
                expiry_date=expiry_date
            )
            db.session.add(new_payment)

        # Save everything to database
        db.session.commit()

        flash(f'✅ Tenant "{full_name}" registered successfully!', 'success')
        return redirect(url_for('tenants'))

    return render_template('add_tenant.html', rooms=vacant_rooms)


# ============================================================
# VIEW SINGLE TENANT DETAIL
# ============================================================
@app.route('/tenant/<int:tenant_id>')
@login_required
def tenant_detail(tenant_id):
    from models import Tenant
    # Get tenant or show 404 if not found
    tenant = Tenant.query.get_or_404(tenant_id)
    return render_template('tenant_detail.html', tenant=tenant)


# ============================================================
# EDIT TENANT
# ============================================================
@app.route('/edit-tenant/<int:tenant_id>', methods=['GET', 'POST'])
@login_required
def edit_tenant(tenant_id):
    from models import Tenant, Room

    tenant = Tenant.query.get_or_404(tenant_id)

    # Get all rooms for dropdown
    # Include the tenant's current room + all vacant rooms
    all_rooms = Room.query.all()
    available_rooms = [
        r for r in all_rooms
        if not r.is_occupied or r.id == tenant.room_id
    ]

    if request.method == 'POST':
        # Get updated form data
        tenant.full_name         = request.form.get('full_name')
        tenant.phone             = request.form.get('phone')
        tenant.email             = request.form.get('email')
        tenant.emergency_contact = request.form.get('emergency_contact')
        tenant.emergency_phone   = request.form.get('emergency_phone')

        new_room_id = int(request.form.get('room_id'))

        # If room has changed, update room statuses
        if new_room_id != tenant.room_id:
            # Free up the old room
            old_room = Room.query.get(tenant.room_id)
            if old_room:
                old_room.is_occupied = False

            # Occupy the new room
            new_room = Room.query.get(new_room_id)
            if new_room:
                new_room.is_occupied = True

            tenant.room_id = new_room_id

        db.session.commit()
        flash(f'✅ Tenant "{tenant.full_name}" updated successfully!', 'success')
        return redirect(url_for('tenants'))

    return render_template('edit_tenant.html',
        tenant=tenant,
        rooms=available_rooms
    )


# ============================================================
# DELETE TENANT
# ============================================================
@app.route('/delete-tenant/<int:tenant_id>', methods=['POST'])
@login_required
def delete_tenant(tenant_id):
    from models import Tenant, Room, Payment

    tenant = Tenant.query.get_or_404(tenant_id)

    # Free up the room
    room = Room.query.get(tenant.room_id)
    if room:
        room.is_occupied = False

    # Delete all payments for this tenant
    Payment.query.filter_by(tenant_id=tenant_id).delete()

    # Delete the tenant
    db.session.delete(tenant)
    db.session.commit()

    flash(f'✅ Tenant "{tenant.full_name}" deleted successfully.', 'success')
    return redirect(url_for('tenants'))


# ============================================================
# ROOMS PAGE
# ============================================================
@app.route('/rooms')
@login_required
def rooms():
    from models import Room

    all_rooms = Room.query.all()

    # Separate rooms by type for display
    chamber_rooms = [r for r in all_rooms if r.room_type == 'Chamber and Hall']
    single_rooms  = [r for r in all_rooms if r.room_type == 'Single Room']
    stores        = [r for r in all_rooms if r.room_type == 'Store']

    return render_template('rooms.html',
        all_rooms=all_rooms,
        chamber_rooms=chamber_rooms,
        single_rooms=single_rooms,
        stores=stores
    )


# ============================================================
# PAYMENTS PAGE
# ============================================================
@app.route('/payments')
@login_required
def payments():
    from models import Payment
    all_payments = Payment.query.order_by(Payment.payment_date.desc()).all()
    return render_template('payments.html', payments=all_payments)


# ============================================================
# ADD PAYMENT FOR EXISTING TENANT
# ============================================================
@app.route('/add-payment/<int:tenant_id>', methods=['GET', 'POST'])
@login_required
def add_payment(tenant_id):
    from models import Tenant, Payment

    tenant = Tenant.query.get_or_404(tenant_id)

    if request.method == 'POST':
        amount           = request.form.get('amount')
        payment_date_str = request.form.get('payment_date')
        notes            = request.form.get('notes')

        if not amount or not payment_date_str:
            flash('❌ Amount and payment date are required.', 'danger')
            return render_template('add_payment.html', tenant=tenant)

        payment_date = datetime.strptime(payment_date_str, '%Y-%m-%d').date()
        expiry_date  = payment_date.replace(year=payment_date.year + 1)

        new_payment = Payment(
            tenant_id=tenant_id,
            amount=float(amount),
            payment_date=payment_date,
            expiry_date=expiry_date,
            notes=notes
        )
        db.session.add(new_payment)
        db.session.commit()

        flash(f'✅ Payment recorded for "{tenant.full_name}".', 'success')
        return redirect(url_for('payments'))

    return render_template('add_payment.html', tenant=tenant)


# ============================================================
# EXPIRED / EXPIRING SOON PAGE
# ============================================================
@app.route('/expired')
@login_required
def expired():
    from models import Payment

    all_payments = Payment.query.all()

    expired_list  = [p for p in all_payments if p.status == 'EXPIRED']
    expiring_list = [p for p in all_payments if p.status == 'EXPIRING SOON']

    return render_template('expired.html',
        expired_list=expired_list,
        expiring_list=expiring_list
    )
    
    # ============================================================
# SETUP ROUTE — Creates admin on first deployment
# Visit /setup-admin ONCE then remove this route
# ============================================================
@app.route('/setup-admin')
def setup_admin():
    from models import Admin, Room

    results = []

    # Create tables
    db.create_all()
    results.append("✅ Tables ready")

    # Create admin if not exists
    existing = Admin.query.filter_by(username='admin').first()
    if not existing:
        admin = Admin(username='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        results.append("✅ Admin created — username: admin / password: admin123")
    else:
        results.append("ℹ️ Admin already exists")

    # Seed rooms if empty
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
        results.append("✅ All 10 rooms created")
    else:
        results.append(f"ℹ️ Rooms already exist")

    # Show results as a simple page
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Setup — The Name House</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                max-width: 600px;
                margin: 60px auto;
                padding: 20px;
                background: #f0f2f5;
            }}
            .card {{
                background: white;
                padding: 30px;
                border-radius: 12px;
                box-shadow: 0 4px 16px rgba(0,0,0,0.1);
            }}
            h2 {{ color: #1a1a2e; }}
            .item {{
                padding: 10px 0;
                border-bottom: 1px solid #eee;
                font-size: 0.95rem;
            }}
            .btn {{
                display: inline-block;
                margin-top: 20px;
                padding: 12px 24px;
                background: #4361ee;
                color: white;
                text-decoration: none;
                border-radius: 8px;
                font-weight: bold;
            }}
            .warning {{
                margin-top: 20px;
                padding: 12px;
                background: #fff3cd;
                border-radius: 8px;
                font-size: 0.85rem;
                color: #856404;
            }}
        </style>
    </head>
    <body>
        <div class="card">
            <h2>🏠 The Name House — Setup</h2>
            {items}
            <a href="/login" class="btn">Go to Login →</a>
            <div class="warning">
                ⚠️ <strong>Important:</strong> Remove the /setup-admin
                route from routes.py after logging in successfully.
            </div>
        </div>
    </body>
    </html>
    """.format(
        items=''.join(f'<div class="item">{r}</div>' for r in results)
    )

    return html