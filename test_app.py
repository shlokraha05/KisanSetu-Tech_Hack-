import pytest
import datetime
from decimal import Decimal
from app import create_app
from config import TestingConfig
from app.extensions import db
from app.models import (
    User, Farmer, ProcurementCentre, Slot, Booking,
    SMSLog, Payment, AuditLog, SystemSetting
)
from app.services.booking_service import booking_service
from app.services.aadhaar_service import mock_aadhaar_service
from app.services.sms_service import mock_sms_service
from app.services.token_service import token_service

@pytest.fixture
def app():
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
        # Ensure setting
        SystemSetting.set_value('require_demo_verification', 'true')
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def sample_data(app):
    """Seed minimal test objects."""
    # 1. Admin
    admin = User(name="Test Admin", mobile="9990000001", email="admin@test.com", role="admin")
    admin.set_password("Pass@123")
    db.session.add(admin)

    # 2. Operator
    operator = User(name="Test Operator", mobile="9990000002", email="operator@test.com", role="operator")
    operator.set_password("Pass@123")
    db.session.add(operator)

    # 3. Farmer User & Profile
    farmer_user = User(name="Test Farmer", mobile="9990000003", email="farmer@test.com", role="farmer")
    farmer_user.set_password("Pass@123")
    db.session.add(farmer_user)
    db.session.flush()

    farmer = Farmer(
        user_id=farmer_user.id,
        village="Test Village",
        district="Raipur",
        state="Chhattisgarh",
        crop_type="Paddy (Dhan)",
        land_area=Decimal('5.0'),
        identity_status="Verified (Demo)"
    )
    db.session.add(farmer)

    # 4. Procurement Centre
    centre = ProcurementCentre(
        name="Test Mandi",
        code="TEST-01",
        location="Test Road",
        district="Raipur",
        state="Chhattisgarh",
        daily_capacity=50,
        is_active=True
    )
    db.session.add(centre)
    db.session.flush()

    # 5. Slot
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    slot = Slot(
        centre_id=centre.id,
        slot_date=tomorrow,
        start_time=datetime.time(10, 0),
        end_time=datetime.time(12, 0),
        capacity=2,
        booked_count=0,
        status="Available"
    )
    db.session.add(slot)
    db.session.commit()

    return {
        'admin': admin,
        'operator': operator,
        'farmer_user': farmer_user,
        'farmer': farmer,
        'centre': centre,
        'slot': slot
    }

# 1. Test App Starts
def test_app_starts(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b"KisanSetu" in response.data
    assert b"Digital Procurement" in response.data

# 2. Test Database Connection
def test_database_connection(app, sample_data):
    centre = ProcurementCentre.query.filter_by(code="TEST-01").first()
    assert centre is not None
    assert centre.name == "Test Mandi"

# 3. Test Farmer Registration
def test_farmer_registration(client):
    res = client.post('/farmer/register', data={
        'name': 'New Farmer',
        'mobile': '9871112233',
        'email': 'newfarmer@test.com',
        'password': 'Password@123',
        'village': 'Navapara',
        'district': 'Raipur',
        'state': 'Chhattisgarh',
        'crop_type': 'Wheat (Gehun)',
        'land_area': '4.0'
    }, follow_redirects=True)
    assert res.status_code == 200
    
    user = User.query.filter_by(mobile='9871112233').first()
    assert user is not None
    assert user.role == 'farmer'
    assert user.farmer_profile.identity_status == 'Pending'
    assert user.farmer_profile.village == 'Navapara'

# 4. Test Duplicate Mobile Rejection
def test_duplicate_mobile_rejection(client, sample_data):
    # Attempt to register with sample_data farmer mobile (9990000003)
    res = client.post('/farmer/register', data={
        'name': 'Duplicate User',
        'mobile': '9990000003',
        'email': 'dup@test.com',
        'password': 'Pass@123',
        'village': 'Village 2',
        'district': 'Raipur',
        'state': 'Chhattisgarh',
        'crop_type': 'Paddy (Dhan)',
        'land_area': '2.0'
    }, follow_redirects=True)
    assert b"already registered" in res.data

# 5. Test Mock Identity Verification
def test_mock_identity_verification(app, sample_data):
    # Create unverified farmer
    u = User(name="Unverified", mobile="9870001122", email="unv@test.com", role="farmer")
    u.set_password("Pass@123")
    db.session.add(u)
    db.session.flush()

    f = Farmer(user_id=u.id, village="V", district="D", state="S", crop_type="Paddy (Dhan)", identity_status="Pending")
    db.session.add(f)
    db.session.commit()

    assert f.identity_status == "Pending"

    # Trigger Mock Aadhaar Verification
    result = mock_aadhaar_service.verify_identity(f.id, verified_by=sample_data['operator'].id)
    assert result['success'] is True
    assert result['status'] == 'Verified (Demo)'
    assert f.identity_status == 'Verified (Demo)'
    assert "UIDAI" in result['disclaimer']

# 6. Test Slot Creation
def test_slot_creation(app, sample_data):
    c = sample_data['centre']
    slot_date = datetime.date.today() + datetime.timedelta(days=2)
    new_slot = Slot(
        centre_id=c.id,
        slot_date=slot_date,
        start_time=datetime.time(14, 0),
        end_time=datetime.time(16, 0),
        capacity=15,
        booked_count=0,
        status='Available'
    )
    db.session.add(new_slot)
    db.session.commit()

    loaded = Slot.query.get(new_slot.id)
    assert loaded is not None
    assert loaded.remaining_capacity == 15
    assert loaded.is_full is False

# 7. Test Booking Creation
def test_booking_creation(app, sample_data):
    farmer = sample_data['farmer']
    slot = sample_data['slot']
    
    result = booking_service.create_booking(
        farmer_id=farmer.id,
        slot_id=slot.id,
        crop_type="Paddy (Dhan)",
        estimated_quantity=30.0,
        booked_by_user_id=sample_data['operator'].id
    )

    assert result['success'] is True
    booking = result['booking']
    assert booking.token_number == 101
    assert booking.booking_status == 'Booked'
    assert slot.booked_count == 1
    assert booking.payment is not None
    assert booking.payment.amount > 0

# 8. Test Token Generation (Sequential uniqueness)
def test_token_generation(app, sample_data):
    centre_id = sample_data['centre'].id
    slot_date = sample_data['slot'].slot_date

    token1 = token_service.generate_token(centre_id, slot_date)
    assert token1 == 101

    # Book first slot
    booking_service.create_booking(
        farmer_id=sample_data['farmer'].id,
        slot_id=sample_data['slot'].id,
        crop_type="Paddy (Dhan)",
        estimated_quantity=20.0,
        booked_by_user_id=sample_data['operator'].id
    )

    # Next token for same centre and date should be 102
    token2 = token_service.generate_token(centre_id, slot_date)
    assert token2 == 102

# 9. Test Full Slot Rejection
def test_full_slot_rejection(app, sample_data):
    slot = sample_data['slot']
    # Capacity is 2
    # Register second verified farmer
    u2 = User(name="Farmer 2", mobile="9879998877", email="f2@test.com", role="farmer")
    u2.set_password("Pass@123")
    db.session.add(u2)
    db.session.flush()
    f2 = Farmer(user_id=u2.id, village="V2", district="Raipur", state="C.G.", crop_type="Paddy (Dhan)", identity_status="Verified (Demo)")
    db.session.add(f2)

    # Register third verified farmer
    u3 = User(name="Farmer 3", mobile="9879998878", email="f3@test.com", role="farmer")
    u3.set_password("Pass@123")
    db.session.add(u3)
    db.session.flush()
    f3 = Farmer(user_id=u3.id, village="V3", district="Raipur", state="C.G.", crop_type="Paddy (Dhan)", identity_status="Verified (Demo)")
    db.session.add(f3)
    db.session.commit()

    # Fill capacity (2 slots)
    res1 = booking_service.create_booking(sample_data['farmer'].id, slot.id, "Paddy (Dhan)", 20.0, sample_data['operator'].id)
    assert res1['success'] is True

    res2 = booking_service.create_booking(f2.id, slot.id, "Paddy (Dhan)", 25.0, sample_data['operator'].id)
    assert res2['success'] is True
    assert slot.status == 'Full'

    # Third booking should fail
    res3 = booking_service.create_booking(f3.id, slot.id, "Paddy (Dhan)", 30.0, sample_data['operator'].id)
    assert res3['success'] is False
    assert "fully booked" in res3['message'].lower()

# 10. Test Duplicate Booking Rejection
def test_duplicate_booking_rejection(app, sample_data):
    farmer = sample_data['farmer']
    slot = sample_data['slot']

    # First booking succeeds
    res1 = booking_service.create_booking(farmer.id, slot.id, "Paddy (Dhan)", 20.0, farmer.user_id)
    assert res1['success'] is True

    # Same farmer tries to book active booking on same date again
    res2 = booking_service.create_booking(farmer.id, slot.id, "Paddy (Dhan)", 25.0, farmer.user_id)
    assert res2['success'] is False
    assert "already has an active booking" in res2['message'].lower()

# 11. Test SMS Log Creation and Delivery Simulation
def test_sms_log_creation_and_delivery(app, sample_data):
    farmer = sample_data['farmer']
    slot = sample_data['slot']

    res = booking_service.create_booking(farmer.id, slot.id, "Paddy (Dhan)", 20.0, farmer.user_id)
    booking = res['booking']

    sms = SMSLog.query.filter_by(booking_id=booking.id).first()
    assert sms is not None
    assert sms.status == 'Sent'
    assert str(booking.token_number) in sms.message

    # Simulate delivery
    delivery_res = mock_sms_service.simulate_delivery(sms.id, user_id=sample_data['operator'].id)
    assert delivery_res['success'] is True
    assert sms.status == 'Delivered'

# 12. Test Queue Update Transitions
def test_queue_update(app, sample_data):
    farmer = sample_data['farmer']
    slot = sample_data['slot']

    res = booking_service.create_booking(farmer.id, slot.id, "Paddy (Dhan)", 20.0, sample_data['operator'].id)
    booking = res['booking']
    assert booking.booking_status == 'Booked'

    # 1. Mark Arrived
    u1 = booking_service.update_queue_status(booking.id, 'Arrived', user_id=sample_data['operator'].id)
    assert u1['success'] is True
    assert booking.booking_status == 'Arrived'

    # 2. Mark In Procurement
    u2 = booking_service.update_queue_status(booking.id, 'In Procurement', user_id=sample_data['operator'].id)
    assert u2['success'] is True
    assert booking.booking_status == 'In Procurement'

    # 3. Mark Completed
    u3 = booking_service.update_queue_status(booking.id, 'Completed', user_id=sample_data['operator'].id)
    assert u3['success'] is True
    assert booking.booking_status == 'Completed'

# 13. Test Payment Update on Procurement Completion
def test_payment_update(app, sample_data):
    farmer = sample_data['farmer']
    slot = sample_data['slot']

    res = booking_service.create_booking(farmer.id, slot.id, "Paddy (Dhan)", 20.0, sample_data['operator'].id)
    booking = res['booking']
    assert booking.payment.payment_status == 'Pending'

    # When marked Completed, payment status transitions
    booking_service.update_queue_status(booking.id, 'Completed', user_id=sample_data['operator'].id)
    assert booking.payment.payment_status == 'Transferred (Demo)'
    assert booking.payment.payment_date is not None

# 14. Test Role-Based Access Control
def test_role_based_access_control(client, sample_data):
    # Log in as farmer
    client.post('/login', data={'email': 'farmer@test.com', 'password': 'Pass@123'}, follow_redirects=True)
    
    # Farmer attempts to access operator dashboard
    res = client.get('/operator/dashboard', follow_redirects=True)
    assert b"restricted to Procurement Operators" in res.data or res.status_code == 302

# 15. Test Admin-Only Access
def test_admin_only_access(client, sample_data):
    # Log in as operator
    client.post('/login', data={'email': 'operator@test.com', 'password': 'Pass@123'}, follow_redirects=True)
    
    # Operator attempts to access admin dashboard
    res = client.get('/admin/dashboard', follow_redirects=True)
    assert b"restricted to System Administrators" in res.data or res.status_code == 302

    # Log in as admin
    client.get('/logout', follow_redirects=True)
    client.post('/login', data={'email': 'admin@test.com', 'password': 'Pass@123'}, follow_redirects=True)
    res_admin = client.get('/admin/dashboard')
    assert res_admin.status_code == 200
    assert b"Government Administration Suite" in res_admin.data
