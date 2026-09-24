import datetime
from decimal import Decimal
from flask import render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import login_required, current_user
from app.operator import operator_bp
from app.models import User, Farmer, ProcurementCentre, Slot, Booking, SMSLog, Payment, AuditLog
from app.extensions import db
from app.services.booking_service import booking_service, MSP_RATES
from app.services.aadhaar_service import mock_aadhaar_service
from app.services.sms_service import mock_sms_service

def operator_required(f):
    """Decorator to ensure current user is an operator, CSC agent, or admin."""
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if not current_user.can_assist():
            flash('Access restricted to Procurement Operators and CSC Assistants. (केवल ऑपरेटरों के लिए)', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return login_required(decorated_function)

@operator_bp.route('/dashboard')
@operator_required
def dashboard():
    today = datetime.date.today()
    
    # Overview counts
    today_bookings_count = Booking.query.join(Slot).filter(Slot.slot_date == today).count()
    total_farmers_count = Farmer.query.count()
    pending_verif_count = Farmer.query.filter_by(identity_status='Pending').count()
    
    # Available slots today
    available_slots_count = Slot.query.filter(
        Slot.slot_date == today,
        Slot.status == 'Available',
        Slot.booked_count < Slot.capacity
    ).count()

    # Active queue items today across centres
    active_queue = (
        Booking.query.join(Slot)
        .filter(
            Slot.slot_date == today,
            Booking.booking_status.in_(['Booked', 'Arrived', 'In Procurement'])
        )
        .order_by(Booking.token_number.asc())
        .limit(10)
        .all()
    )

    centres = ProcurementCentre.query.filter_by(is_active=True).all()

    return render_template(
        'operator/dashboard.html',
        today=today,
        today_bookings_count=today_bookings_count,
        total_farmers_count=total_farmers_count,
        pending_verif_count=pending_verif_count,
        available_slots_count=available_slots_count,
        active_queue=active_queue,
        centres=centres
    )

@operator_bp.route('/register-farmer', methods=['GET', 'POST'])
@operator_required
def register_farmer():
    """Assisted registration of walk-in farmers without digital devices."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        mobile = request.form.get('mobile', '').strip()
        email = request.form.get('email', '').strip().lower()
        village = request.form.get('village', '').strip()
        district = request.form.get('district', '').strip()
        state = request.form.get('state', '').strip()
        crop_type = request.form.get('crop_type', '').strip()
        land_area = request.form.get('land_area', '0').strip() or '0'
        auto_verify = bool(request.form.get('auto_verify'))

        if not (name and mobile and village and district and state and crop_type):
            flash('All mandatory fields are required. (सभी अनिवार्य फ़ील्ड भरें)', 'danger')
            return render_template('operator/register_farmer.html')

        if len(mobile) != 10 or not mobile.isdigit():
            flash('Please enter a valid 10-digit mobile number.', 'danger')
            return render_template('operator/register_farmer.html')

        if User.query.filter_by(mobile=mobile).first():
            flash('This mobile number is already registered in the system.', 'danger')
            return render_template('operator/register_farmer.html')

        if not email:
            email = f"assisted.{mobile}@kisansetu.local"

        try:
            # Create user
            user = User(
                name=name,
                mobile=mobile,
                email=email,
                role='farmer',
                is_active=True
            )
            # Default password for farmer
            user.set_password(f"Kisan@{mobile[-4:]}")
            db.session.add(user)
            db.session.flush()

            # Create farmer profile
            farmer = Farmer(
                user_id=user.id,
                village=village,
                district=district,
                state=state,
                crop_type=crop_type,
                land_area=Decimal(land_area),
                identity_status='Pending'
            )
            db.session.add(farmer)
            db.session.flush()

            # Optional immediate mock verification
            if auto_verify:
                mock_aadhaar_service.verify_identity(
                    farmer_id=farmer.id,
                    verified_by=current_user.id
                )

            audit = AuditLog(
                user_id=current_user.id,
                action='ASSISTED_FARMER_REGISTRATION',
                entity_type='Farmer',
                entity_id=farmer.id,
                description=f"Operator {current_user.name} registered farmer {name} ({mobile})."
            )
            db.session.add(audit)
            db.session.commit()

            flash(f"Farmer {name} registered successfully! (किसान सफलतापूर्वक पंजीकृत)", 'success')
            return redirect(url_for('operator.book_slot', farmer_id=farmer.id))

        except Exception as e:
            db.session.rollback()
            flash(f"Error registering farmer: {str(e)}", 'danger')

    return render_template('operator/register_farmer.html', crops=list(MSP_RATES.keys()))

@operator_bp.route('/search-farmer')
@operator_required
def search_farmer():
    query = request.args.get('q', '').strip()
    farmers = []
    if query:
        # Search by mobile or user name
        farmers = (
            Farmer.query.join(User)
            .filter(
                db.or_(
                    User.mobile.ilike(f"%{query}%"),
                    User.name.ilike(f"%{query}%"),
                    Farmer.village.ilike(f"%{query}%")
                )
            )
            .all()
        )
    return render_template('operator/search_farmer.html', query=query, farmers=farmers)

@operator_bp.route('/verify-farmer', methods=['POST'])
@operator_required
def verify_farmer():
    farmer_id = request.form.get('farmer_id', type=int)
    if not farmer_id:
        flash('Farmer ID required.', 'danger')
        return redirect(request.referrer or url_for('operator.search_farmer'))

    res = mock_aadhaar_service.verify_identity(
        farmer_id=farmer_id,
        verified_by=current_user.id
    )

    if res['success']:
        flash(f"{res['message']} (पहचान सत्यापन सफल)", 'success')
    else:
        flash(res['message'], 'danger')

    return redirect(request.referrer or url_for('operator.search_farmer'))

@operator_bp.route('/book-slot', methods=['GET', 'POST'])
@operator_required
def book_slot():
    farmer_id = request.args.get('farmer_id', type=int)
    preselected_farmer = Farmer.query.get(farmer_id) if farmer_id else None

    centres = ProcurementCentre.query.filter_by(is_active=True).all()
    crops = list(MSP_RATES.keys())

    if request.method == 'POST':
        target_farmer_id = request.form.get('farmer_id', type=int)
        slot_id = request.form.get('slot_id', type=int)
        crop_type = request.form.get('crop_type')
        quantity = request.form.get('estimated_quantity', type=float)

        if not target_farmer_id or not slot_id or not crop_type or not quantity:
            flash('Please specify all booking details.', 'danger')
            return redirect(url_for('operator.book_slot', farmer_id=target_farmer_id))

        result = booking_service.create_booking(
            farmer_id=target_farmer_id,
            slot_id=slot_id,
            crop_type=crop_type,
            estimated_quantity=quantity,
            booked_by_user_id=current_user.id
        )

        if result['success']:
            flash(result['message'], 'success')
            return redirect(url_for('operator.token_receipt', booking_id=result['booking'].id))
        else:
            flash(result['message'], 'danger')
            return redirect(url_for('operator.book_slot', farmer_id=target_farmer_id))

    return render_template(
        'operator/book_slot.html',
        preselected_farmer=preselected_farmer,
        centres=centres,
        crops=crops,
        msp_rates=MSP_RATES
    )

@operator_bp.route('/token-receipt/<int:booking_id>')
@operator_required
def token_receipt(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    return render_template('operator/token_receipt.html', booking=booking)

@operator_bp.route('/queue')
@operator_required
def queue():
    today = datetime.date.today()
    centre_id = request.args.get('centre_id', type=int)
    date_str = request.args.get('date')

    target_date = today
    if date_str:
        try:
            target_date = datetime.date.fromisoformat(date_str)
        except ValueError:
            target_date = today

    centres = ProcurementCentre.query.filter_by(is_active=True).all()
    selected_centre = None
    if centre_id:
        selected_centre = ProcurementCentre.query.get(centre_id)
    if not selected_centre and centres:
        selected_centre = centres[0]

    bookings_query = Booking.query.join(Slot).filter(Slot.slot_date == target_date)
    if selected_centre:
        bookings_query = bookings_query.filter(Booking.centre_id == selected_centre.id)

    all_bookings = bookings_query.order_by(Booking.token_number.asc()).all()

    # Categorize tokens for live queue board
    current_token = next((b for b in all_bookings if b.booking_status == 'In Procurement'), None)
    waiting_tokens = [b for b in all_bookings if b.booking_status in ('Booked', 'Arrived')]
    completed_tokens = [b for b in all_bookings if b.booking_status == 'Completed']
    other_tokens = [b for b in all_bookings if b.booking_status in ('Cancelled', 'No Show')]

    return render_template(
        'operator/queue.html',
        centres=centres,
        selected_centre=selected_centre,
        target_date=target_date,
        current_token=current_token,
        waiting_tokens=waiting_tokens,
        completed_tokens=completed_tokens,
        other_tokens=other_tokens,
        total_count=len(all_bookings)
    )

@operator_bp.route('/queue/call-next', methods=['POST'])
@operator_required
def call_next():
    centre_id = request.form.get('centre_id', type=int)
    date_str = request.form.get('date')

    target_date = datetime.date.today()
    if date_str:
        try:
            target_date = datetime.date.fromisoformat(date_str)
        except ValueError:
            pass

    # Find the next waiting token (Arrived first, then Booked)
    next_booking = (
        Booking.query.join(Slot)
        .filter(
            Booking.centre_id == centre_id,
            Slot.slot_date == target_date,
            Booking.booking_status.in_(['Arrived', 'Booked'])
        )
        .order_by(
            # Prioritize Arrived status, then lowest token number
            db.case((Booking.booking_status == 'Arrived', 1), else_=2),
            Booking.token_number.asc()
        )
        .first()
    )

    if not next_booking:
        flash('No waiting farmers in queue for this centre today.', 'info')
        return redirect(url_for('operator.queue', centre_id=centre_id, date=target_date.isoformat()))

    # Complete current in-procurement if any, or move next directly
    res = booking_service.update_queue_status(
        booking_id=next_booking.id,
        new_status='In Procurement',
        user_id=current_user.id
    )

    if res['success']:
        flash(f"Token #{next_booking.token_number} called! (टोकन सं. {next_booking.token_number} को बुलाया गया)", 'success')
    else:
        flash(res['message'], 'danger')

    return redirect(url_for('operator.queue', centre_id=centre_id, date=target_date.isoformat()))

@operator_bp.route('/queue/update', methods=['POST'])
@operator_required
def update_queue():
    booking_id = request.form.get('booking_id', type=int)
    new_status = request.form.get('status')

    if not booking_id or not new_status:
        flash('Booking ID and status are required.', 'danger')
        return redirect(request.referrer or url_for('operator.queue'))

    res = booking_service.update_queue_status(
        booking_id=booking_id,
        new_status=new_status,
        user_id=current_user.id
    )

    if res['success']:
        flash(res['message'], 'success')
    else:
        flash(res['message'], 'danger')

    return redirect(request.referrer or url_for('operator.queue'))

@operator_bp.route('/sms-logs')
@operator_required
def sms_logs():
    page = request.args.get('page', 1, type=int)
    logs = SMSLog.query.order_by(SMSLog.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('operator/sms_logs.html', logs=logs)

@operator_bp.route('/sms/simulate-delivery/<int:sms_id>', methods=['POST'])
@operator_required
def simulate_sms_delivery(sms_id):
    res = mock_sms_service.simulate_delivery(sms_id, user_id=current_user.id)
    if res['success']:
        flash(res['message'], 'success')
    else:
        flash(res['message'], 'danger')
    return redirect(request.referrer or url_for('operator.sms_logs'))
