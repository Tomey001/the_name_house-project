# routes.py
from flask import render_template, redirect, url_for, request, flash
from flask_login import (
    login_user, logout_user,
    login_required, current_user
)
from app import app, db
from datetime import date, datetime


# ============================================================
# CONTEXT PROCESSOR
# ============================================================
@app.context_processor
def inject_globals():
    def get_all_rooms():
        try:
            from models import Room
            return Room.query.all()
        except Exception:
            return []

    def get_expired_count():
        try:
            from models import Payment
            all_payments = Payment.query.all()
            return sum(
                1 for p in all_payments
                if p.status == 'EXPIRED'
            )
        except Exception:
            return 0

    return dict(
        get_all_rooms=get_all_rooms,
        expired_count=get_expired_count()
    )


# ============================================================
# HOME
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
        admin    = Admin.query.filter_by(
            username=username
        ).first()
        if admin and admin.check_password(password):
            login_user(admin)
            flash('✅ Welcome back!', 'success')
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
    occupied_rooms = Room.query.filter_by(
        is_occupied=True
    ).count()
    vacant_rooms   = total_rooms - occupied_rooms
    total_tenants  = Tenant.query.filter_by(
        is_active=True
    ).count()
    all_payments   = Payment.query.all()
    expiring_soon  = sum(
        1 for p in all_payments
        if p.status == 'EXPIRING SOON'
    )
    expired = sum(
        1 for p in all_payments
        if p.status == 'EXPIRED'
    )
    return render_template('dashboard.html',
        total_rooms=total_rooms,
        occupied_rooms=occupied_rooms,
        vacant_rooms=vacant_rooms,
        total_tenants=total_tenants,
        expiring_soon=expiring_soon,
        expired=expired
    )


# ============================================================
# TENANTS
# ============================================================
@app.route('/tenants')
@login_required
def tenants():
    from models import Tenant
    search = request.args.get('search', '')
    if search:
        all_tenants = Tenant.query.filter(
            Tenant.is_active == True,
            db.or_(
                Tenant.full_name.ilike(f'%{search}%'),
                Tenant.phone.ilike(f'%{search}%')
            )
        ).all()
    else:
        all_tenants = Tenant.query.filter_by(
            is_active=True
        ).all()
    return render_template('tenants.html',
        tenants=all_tenants,
        search=search
    )


# ============================================================
# ADD TENANT
# ============================================================
@app.route('/add-tenant', methods=['GET', 'POST'])
@login_required
def add_tenant():
    from models import Room, Tenant, Payment
    vacant_rooms = Room.query.filter_by(
        is_occupied=False
    ).all()

    if request.method == 'POST':
        full_name         = request.form.get('full_name')
        phone             = request.form.get('phone')
        email             = request.form.get('email')
        emergency_contact = request.form.get('emergency_contact')
        emergency_phone   = request.form.get('emergency_phone')
        room_id           = request.form.get('room_id')
        payment_amount    = request.form.get('payment_amount')
        payment_date_str  = request.form.get('payment_date')

        if not full_name or not phone or not room_id:
            flash(
                '❌ Full name, phone and room are required.',
                'danger'
            )
            return render_template(
                'add_tenant.html', rooms=vacant_rooms
            )

        room = Room.query.get(int(room_id))
        if not room:
            flash('❌ Selected room does not exist.', 'danger')
            return render_template(
                'add_tenant.html', rooms=vacant_rooms
            )

        if room.is_occupied:
            flash(
                f'❌ {room.room_name} is already occupied.',
                'danger'
            )
            return render_template(
                'add_tenant.html', rooms=vacant_rooms
            )

        new_tenant = Tenant(
            full_name=full_name,
            phone=phone,
            email=email,
            emergency_contact=emergency_contact,
            emergency_phone=emergency_phone,
            room_id=int(room_id)
        )
        db.session.add(new_tenant)
        room.is_occupied = True

        if payment_amount and payment_date_str:
            payment_date = datetime.strptime(
                payment_date_str, '%Y-%m-%d'
            ).date()
            expiry_date = payment_date.replace(
                year=payment_date.year + 1
            )
            new_payment = Payment(
                tenant=new_tenant,
                amount=float(payment_amount),
                payment_date=payment_date,
                expiry_date=expiry_date
            )
            db.session.add(new_payment)

        db.session.commit()
        flash(
            f'✅ Tenant "{full_name}" registered!',
            'success'
        )
        return redirect(url_for('tenants'))

    return render_template('add_tenant.html', rooms=vacant_rooms)


# ============================================================
# TENANT DETAIL
# ============================================================
@app.route('/tenant/<int:tenant_id>')
@login_required
def tenant_detail(tenant_id):
    from models import Tenant
    tenant = Tenant.query.get_or_404(tenant_id)
    return render_template('tenant_detail.html', tenant=tenant)


# ============================================================
# EDIT TENANT
# ============================================================
@app.route('/edit-tenant/<int:tenant_id>',
           methods=['GET', 'POST'])
@login_required
def edit_tenant(tenant_id):
    from models import Tenant, Room
    tenant    = Tenant.query.get_or_404(tenant_id)
    all_rooms = Room.query.all()
    available_rooms = [
        r for r in all_rooms
        if not r.is_occupied or r.id == tenant.room_id
    ]

    if request.method == 'POST':
        tenant.full_name         = request.form.get('full_name')
        tenant.phone             = request.form.get('phone')
        tenant.email             = request.form.get('email')
        tenant.emergency_contact = request.form.get(
            'emergency_contact'
        )
        tenant.emergency_phone   = request.form.get(
            'emergency_phone'
        )
        new_room_id = int(request.form.get('room_id'))

        if new_room_id != tenant.room_id:
            old_room = Room.query.get(tenant.room_id)
            if old_room:
                old_room.is_occupied = False
            new_room = Room.query.get(new_room_id)
            if new_room:
                new_room.is_occupied = True
            tenant.room_id = new_room_id

        db.session.commit()
        flash(
            f'✅ Tenant "{tenant.full_name}" updated!',
            'success'
        )
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
    room   = Room.query.get(tenant.room_id)
    if room:
        room.is_occupied = False
    Payment.query.filter_by(tenant_id=tenant_id).delete()
    db.session.delete(tenant)
    db.session.commit()
    flash(
        f'✅ Tenant "{tenant.full_name}" deleted.',
        'success'
    )
    return redirect(url_for('tenants'))


# ============================================================
# ROOMS
# ============================================================
@app.route('/rooms')
@login_required
def rooms():
    from models import Room
    all_rooms     = Room.query.all()
    chamber_rooms = [
        r for r in all_rooms
        if r.room_type == 'Chamber and Hall'
    ]
    single_rooms  = [
        r for r in all_rooms
        if r.room_type == 'Single Room'
    ]
    stores        = [
        r for r in all_rooms
        if r.room_type == 'Store'
    ]
    return render_template('rooms.html',
        all_rooms=all_rooms,
        chamber_rooms=chamber_rooms,
        single_rooms=single_rooms,
        stores=stores
    )


# ============================================================
# PAYMENTS
# ============================================================
@app.route('/payments')
@login_required
def payments():
    from models import Payment
    all_payments = Payment.query.order_by(
        Payment.payment_date.desc()
    ).all()
    return render_template('payments.html',
                           payments=all_payments)


# ============================================================
# ADD PAYMENT
# ============================================================
@app.route('/add-payment/<int:tenant_id>',
           methods=['GET', 'POST'])
@login_required
def add_payment(tenant_id):
    from models import Tenant, Payment
    tenant = Tenant.query.get_or_404(tenant_id)

    if request.method == 'POST':
        amount           = request.form.get('amount')
        payment_date_str = request.form.get('payment_date')
        notes            = request.form.get('notes')

        if not amount or not payment_date_str:
            flash('❌ Amount and date are required.', 'danger')
            return render_template(
                'add_payment.html', tenant=tenant
            )

        payment_date = datetime.strptime(
            payment_date_str, '%Y-%m-%d'
        ).date()
        expiry_date = payment_date.replace(
            year=payment_date.year + 1
        )
        new_payment = Payment(
            tenant_id=tenant_id,
            amount=float(amount),
            payment_date=payment_date,
            expiry_date=expiry_date,
            notes=notes
        )
        db.session.add(new_payment)
        db.session.commit()
        flash(
            f'✅ Payment recorded for "{tenant.full_name}".',
            'success'
        )
        return redirect(url_for('payments'))

    return render_template('add_payment.html', tenant=tenant)


# ============================================================
# EXPIRED
# ============================================================
@app.route('/expired')
@login_required
def expired():
    from models import Payment
    all_payments  = Payment.query.all()
    expired_list  = [
        p for p in all_payments if p.status == 'EXPIRED'
    ]
    expiring_list = [
        p for p in all_payments if p.status == 'EXPIRING SOON'
    ]
    return render_template('expired.html',
        expired_list=expired_list,
        expiring_list=expiring_list
    )


# ============================================================
# SETUP ADMIN — Run once then remove
# ============================================================
@app.route('/setup-admin')
def setup_admin():
    from models import Admin, Room
    results = []
    db.create_all()
    results.append("✅ Tables ready")

    existing = Admin.query.filter_by(username='admin').first()
    if not existing:
        admin = Admin(username='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        results.append(
            "✅ Admin created — username: admin / password: admin123"
        )
    else:
        results.append("ℹ️ Admin already exists")

    if Room.query.count() == 0:
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
            Room(room_name='Store 1', room_type='Store'),
            Room(room_name='Store 2', room_type='Store'),
            Room(room_name='Store 3', room_type='Store'),
        ]
        db.session.add_all(rooms)
        db.session.commit()
        results.append("✅ All 10 rooms created")
    else:
        results.append("ℹ️ Rooms already exist")

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Setup</title>
        <style>
            body {{
                font-family:Arial;max-width:600px;
                margin:60px auto;padding:20px;
                background:#f0f2f5;
            }}
            .card {{
                background:white;padding:30px;
                border-radius:12px;
                box-shadow:0 4px 16px rgba(0,0,0,0.1);
            }}
            .item {{
                padding:10px 0;
                border-bottom:1px solid #eee;
            }}
            .btn {{
                display:inline-block;margin-top:20px;
                padding:12px 24px;background:#4361ee;
                color:white;text-decoration:none;
                border-radius:8px;font-weight:bold;
            }}
        </style>
    </head>
    <body>
        <div class="card">
            <h2>🏠 The Name House Setup</h2>
            {items}
            <a href="/login" class="btn">
                Go to Login →
            </a>
        </div>
    </body>
    </html>
    """.format(
        items=''.join(
            f'<div class="item">{r}</div>'
            for r in results
        )
    )
    return html


# ============================================================
# EXPORT — Get local data as JSON
# ============================================================
@app.route('/export-data')
@login_required
def export_data():
    from models import Tenant
    import json

    tenants = Tenant.query.all()
    data    = []

    for tenant in tenants:
        tenant_data = {
            'full_name':         tenant.full_name,
            'phone':             tenant.phone,
            'email':             tenant.email or '',
            'emergency_contact': tenant.emergency_contact or '',
            'emergency_phone':   tenant.emergency_phone or '',
            'room_name':         tenant.room.room_name,
            'payments':          []
        }
        for payment in tenant.payments:
            tenant_data['payments'].append({
                'amount':       payment.amount,
                'payment_date': payment.payment_date.strftime(
                    '%Y-%m-%d'
                ),
                'expiry_date':  payment.expiry_date.strftime(
                    '%Y-%m-%d'
                ),
                'notes': payment.notes or ''
            })
        data.append(tenant_data)

    return f'<pre>{json.dumps(data, indent=2)}</pre>'


# ============================================================
# IMPORT — Load exported data into database
# ============================================================
@app.route('/import-data', methods=['GET', 'POST'])
@login_required
def import_data():
    from models import Room, Tenant, Payment
    import json

    if request.method == 'POST':
        try:
            raw      = request.form.get('json_data')
            data     = json.loads(raw)
            imported = 0
            skipped  = 0

            for item in data:
                existing = Tenant.query.filter_by(
                    full_name=item['full_name'],
                    phone=item['phone']
                ).first()
                if existing:
                    skipped += 1
                    continue

                room = Room.query.filter_by(
                    room_name=item['room_name']
                ).first()
                if not room or room.is_occupied:
                    skipped += 1
                    continue

                tenant = Tenant(
                    full_name=item['full_name'],
                    phone=item['phone'],
                    email=item.get('email', ''),
                    emergency_contact=item.get(
                        'emergency_contact', ''
                    ),
                    emergency_phone=item.get(
                        'emergency_phone', ''
                    ),
                    room_id=room.id
                )
                db.session.add(tenant)
                room.is_occupied = True

                for p in item.get('payments', []):
                    payment = Payment(
                        tenant=tenant,
                        amount=float(p['amount']),
                        payment_date=datetime.strptime(
                            p['payment_date'], '%Y-%m-%d'
                        ).date(),
                        expiry_date=datetime.strptime(
                            p['expiry_date'], '%Y-%m-%d'
                        ).date(),
                        notes=p.get('notes', '')
                    )
                    db.session.add(payment)

                imported += 1

            db.session.commit()
            flash(
                f'✅ Done! {imported} imported, '
                f'{skipped} skipped.',
                'success'
            )
            return redirect(url_for('tenants'))

        except Exception as e:
            flash(f'❌ Import failed: {str(e)}', 'danger')

    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Import Data</title>
        <style>
            body {
                font-family:Arial;max-width:700px;
                margin:60px auto;padding:20px;
                background:#f0f2f5;
            }
            .card {
                background:white;padding:30px;
                border-radius:12px;
                box-shadow:0 4px 16px rgba(0,0,0,0.1);
            }
            textarea {
                width:100%;height:350px;padding:12px;
                border:1.5px solid #dee2e6;
                border-radius:8px;font-family:monospace;
                font-size:0.85rem;margin-bottom:16px;
                resize:vertical;box-sizing:border-box;
            }
            button {
                padding:12px 24px;background:#4361ee;
                color:white;border:none;
                border-radius:8px;font-size:1rem;
                font-weight:bold;cursor:pointer;width:100%;
            }
            .info {
                background:#e8f4fd;padding:12px;
                border-radius:8px;font-size:0.85rem;
                color:#0c5460;margin-bottom:20px;
                border-left:4px solid #4cc9f0;
            }
        </style>
    </head>
    <body>
        <div class="card">
            <h2>📥 Import Tenant Data</h2>
            <div class="info">
                ℹ️ Paste the JSON from your local
                /export-data page, then click Import.
            </div>
            <form method="POST">
                <textarea name="json_data"
                    placeholder="Paste JSON here...">
                </textarea>
                <button type="submit">Import Data</button>
            </form>
        </div>
    </body>
    </html>
    '''