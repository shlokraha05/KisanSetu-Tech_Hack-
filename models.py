from datetime import datetime, timezone, time, date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app.extensions import db, login_manager

def utc_now():
    return datetime.now(timezone.utc)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    mobile = db.Column(db.String(15), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='farmer', index=True) # farmer, operator, csc, admin
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=utc_now)

    # Relationships
    farmer_profile = db.relationship('Farmer', backref='user', uselist=False, cascade='all, delete-orphan')
    bookings_created = db.relationship('Booking', backref='creator', foreign_keys='Booking.booked_by_user_id', lazy='dynamic')
    verifications_performed = db.relationship('FarmerVerification', backref='verifier', foreign_keys='FarmerVerification.verified_by', lazy='dynamic')
    audit_logs = db.relationship('AuditLog', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_farmer(self):
        return self.role == 'farmer'

    def is_operator(self):
        return self.role == 'operator'

    def is_csc(self):
        return self.role == 'csc'

    def is_admin(self):
        return self.role == 'admin'

    def can_assist(self):
        return self.role in ('operator', 'csc', 'admin')

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"


class Farmer(db.Model):
    __tablename__ = 'farmers'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    village = db.Column(db.String(150), nullable=False)
    district = db.Column(db.String(100), nullable=False, index=True)
    state = db.Column(db.String(100), nullable=False)
    crop_type = db.Column(db.String(100), nullable=False)
    land_area = db.Column(db.Numeric(6, 2), default=0.0) # In acres
    identity_status = db.Column(db.String(30), nullable=False, default='Pending', index=True) # Pending, Verified (Demo), Failed (Demo)
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    bookings = db.relationship('Booking', backref='farmer', lazy='dynamic', cascade='all, delete-orphan')
    verifications = db.relationship('FarmerVerification', backref='farmer', lazy='dynamic', cascade='all, delete-orphan')
    sms_logs = db.relationship('SMSLog', backref='farmer', lazy='dynamic', cascade='all, delete-orphan')
    payments = db.relationship('Payment', backref='farmer', lazy='dynamic', cascade='all, delete-orphan')

    @property
    def is_verified(self):
        return self.identity_status == 'Verified (Demo)'

    @property
    def full_name(self):
        return self.user.name if self.user else "Unknown Farmer"

    @property
    def mobile(self):
        return self.user.mobile if self.user else ""

    def __repr__(self):
        return f"<Farmer ID:{self.id} UserID:{self.user_id} Status:{self.identity_status}>"


class ProcurementCentre(db.Model):
    __tablename__ = 'procurement_centres'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    location = db.Column(db.String(255), nullable=False)
    district = db.Column(db.String(100), nullable=False, index=True)
    state = db.Column(db.String(100), nullable=False)
    daily_capacity = db.Column(db.Integer, nullable=False, default=100)
    is_active = db.Column(db.Boolean, nullable=False, default=True, index=True)
    created_at = db.Column(db.DateTime, default=utc_now)

    # Relationships
    slots = db.relationship('Slot', backref='centre', lazy='dynamic', cascade='all, delete-orphan')
    bookings = db.relationship('Booking', backref='centre', lazy='dynamic')

    def __repr__(self):
        return f"<ProcurementCentre {self.name} ({self.code})>"


class Slot(db.Model):
    __tablename__ = 'slots'

    id = db.Column(db.Integer, primary_key=True)
    centre_id = db.Column(db.Integer, db.ForeignKey('procurement_centres.id', ondelete='CASCADE'), nullable=False)
    slot_date = db.Column(db.Date, nullable=False, index=True)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    capacity = db.Column(db.Integer, nullable=False, default=20)
    booked_count = db.Column(db.Integer, nullable=False, default=0)
    status = db.Column(db.String(20), nullable=False, default='Available', index=True) # Available, Full, Inactive
    created_at = db.Column(db.DateTime, default=utc_now)

    # Relationships
    bookings = db.relationship('Booking', backref='slot', lazy='dynamic')

    @property
    def remaining_capacity(self):
        return max(0, self.capacity - self.booked_count)

    @property
    def is_full(self):
        return self.booked_count >= self.capacity

    @property
    def time_range_formatted(self):
        try:
            return f"{self.start_time.strftime('%I:%M %p')} - {self.end_time.strftime('%I:%M %p')}"
        except Exception:
            return f"{self.start_time} - {self.end_time}"

    def __repr__(self):
        return f"<Slot {self.slot_date} {self.time_range_formatted} ({self.booked_count}/{self.capacity})>"


class Booking(db.Model):
    __tablename__ = 'bookings'

    id = db.Column(db.Integer, primary_key=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey('farmers.id', ondelete='CASCADE'), nullable=False, index=True)
    slot_id = db.Column(db.Integer, db.ForeignKey('slots.id'), nullable=False)
    centre_id = db.Column(db.Integer, db.ForeignKey('procurement_centres.id'), nullable=False)
    token_number = db.Column(db.Integer, nullable=False)
    crop_type = db.Column(db.String(100), nullable=False)
    estimated_quantity = db.Column(db.Numeric(8, 2), nullable=False) # In quintals
    booking_status = db.Column(db.String(30), nullable=False, default='Booked', index=True) # Booked, Arrived, In Procurement, Completed, Cancelled, No Show
    booked_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    payment = db.relationship('Payment', backref='booking', uselist=False, cascade='all, delete-orphan')
    sms_logs = db.relationship('SMSLog', backref='booking', lazy='dynamic')

    @property
    def can_be_cancelled(self):
        return self.booking_status == 'Booked'

    def __repr__(self):
        return f"<Booking ID:{self.id} Token:{self.token_number} Status:{self.booking_status}>"


class FarmerVerification(db.Model):
    __tablename__ = 'farmer_verifications'

    id = db.Column(db.Integer, primary_key=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey('farmers.id', ondelete='CASCADE'), nullable=False, index=True)
    verification_mode = db.Column(db.String(50), nullable=False, default='Mock') # Mock, Aadhaar OTP — future, Offline KYC — future
    verification_status = db.Column(db.String(30), nullable=False, default='Pending') # Pending, Verified (Demo), Failed (Demo)
    demo_reference = db.Column(db.String(100), nullable=False)
    verified_at = db.Column(db.DateTime, default=datetime.utcnow)
    verified_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now)

    def __repr__(self):
        return f"<FarmerVerification {self.demo_reference} Status:{self.verification_status}>"


class SMSLog(db.Model):
    __tablename__ = 'sms_logs'

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id', ondelete='SET NULL'), nullable=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey('farmers.id', ondelete='CASCADE'), nullable=False, index=True)
    mobile = db.Column(db.String(15), nullable=False)
    message = db.Column(db.Text, nullable=False)
    message_type = db.Column(db.String(50), nullable=False, default='Booking Confirmation')
    provider = db.Column(db.String(50), nullable=False, default='MockSMS-Gateway')
    status = db.Column(db.String(20), nullable=False, default='Sent', index=True) # Sent, Delivered, Failed
    created_at = db.Column(db.DateTime, default=utc_now)

    def __repr__(self):
        return f"<SMSLog ID:{self.id} To:{self.mobile} Status:{self.status}>"


class Payment(db.Model):
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id', ondelete='CASCADE'), unique=True, nullable=False)
    farmer_id = db.Column(db.Integer, db.ForeignKey('farmers.id', ondelete='CASCADE'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False, default=0.0)
    payment_status = db.Column(db.String(30), nullable=False, default='Pending', index=True) # Pending, Processing, Transferred (Demo), Failed
    payment_reference = db.Column(db.String(100), unique=True, nullable=False)
    payment_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now)

    def __repr__(self):
        return f"<Payment Ref:{self.payment_reference} Amt:{self.amount} Status:{self.payment_status}>"


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    action = db.Column(db.String(100), nullable=False, index=True)
    entity_type = db.Column(db.String(50), nullable=False)
    entity_id = db.Column(db.Integer, nullable=True)
    description = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now)

    def __repr__(self):
        return f"<AuditLog Action:{self.action} Entity:{self.entity_type}#{self.entity_id}>"


class SystemSetting(db.Model):
    __tablename__ = 'system_settings'

    id = db.Column(db.Integer, primary_key=True)
    setting_key = db.Column(db.String(100), unique=True, nullable=False)
    setting_value = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @classmethod
    def get_value(cls, key, default='false'):
        setting = cls.query.filter_by(setting_key=key).first()
        return setting.setting_value if setting else default

    @classmethod
    def get_bool(cls, key, default=False):
        val = cls.get_value(key, str(default).lower())
        return val.lower() in ('true', '1', 'yes')

    @classmethod
    def set_value(cls, key, value, description=None):
        setting = cls.query.filter_by(setting_key=key).first()
        if not setting:
            setting = cls(setting_key=key, setting_value=str(value), description=description)
            db.session.add(setting)
        else:
            setting.setting_value = str(value)
            if description:
                setting.description = description
        db.session.commit()
        return setting

    def __repr__(self):
        return f"<SystemSetting {self.setting_key}={self.setting_value}>"
