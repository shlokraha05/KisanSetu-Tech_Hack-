"""
KisanSetu Database Seeder
Seeds fictional demo data for Smart India Hackathon (SIH) prototype demonstration.
No real Aadhaar or biometric data is stored. All mobile numbers and references are fictional.
"""

import sys
import datetime
from decimal import Decimal

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from app import create_app
from app.extensions import db
from app.models import (
    User, Farmer, ProcurementCentre, Slot, Booking,
    FarmerVerification, SMSLog, Payment, AuditLog, SystemSetting
)
from app.services.sms_service import mock_sms_service

app = create_app()

def seed_database():
    with app.app_context():
        print("[*] Initializing database schema...")
        db.create_all()

        print("[*] Cleaning existing demo records...")
        # Clear tables in reverse dependency order
        Payment.query.delete()
        SMSLog.query.delete()
        Booking.query.delete()
        FarmerVerification.query.delete()
        Slot.query.delete()
        ProcurementCentre.query.delete()
        Farmer.query.delete()
        AuditLog.query.delete()
        SystemSetting.query.delete()
        User.query.delete()
        db.session.commit()

        print("[*] Seeding System Settings...")
        SystemSetting.set_value('require_demo_verification', 'true', 'Require mock Aadhaar verification prior to booking')
        SystemSetting.set_value('demo_mode_active', 'true', 'Enable simulation banner and mock gateways')

        print("[*] Seeding Core Demo User Accounts...")
        # 1. Admin
        admin_user = User(
            name="Admin Officer (Govt. of C.G.)",
            mobile="9876500001",
            email="admin@kisansetu.demo",
            role="admin",
            is_active=True
        )
        admin_user.set_password("Admin@123")
        db.session.add(admin_user)

        # 2. Procurement Operator
        operator_user = User(
            name="Vikram Singh (Raipur Mandi Desk)",
            mobile="9876500002",
            email="operator@kisansetu.demo",
            role="operator",
            is_active=True
        )
        operator_user.set_password("Operator@123")
        db.session.add(operator_user)

        # 3. CSC / Village Assistant Operator
        csc_user = User(
            name="Pooja Sharma (Abhanpur CSC Kendra)",
            mobile="9876500003",
            email="csc@kisansetu.demo",
            role="csc",
            is_active=True
        )
        csc_user.set_password("Csc@123")
        db.session.add(csc_user)

        # 4. Primary Demo Farmer
        primary_farmer_user = User(
            name="Ramesh Kumar",
            mobile="9876543210",
            email="farmer@kisansetu.demo",
            role="farmer",
            is_active=True
        )
        primary_farmer_user.set_password("Farmer@123")
        db.session.add(primary_farmer_user)

        db.session.commit()

        print("[*] Seeding Procurement Centres...")
        centres_data = [
            {
                'name': 'Raipur Procurement Centre',
                'code': 'RAIPUR-01',
                'location': 'Near APMC Main Gate, Dharsiwa Road',
                'district': 'Raipur',
                'state': 'Chhattisgarh',
                'daily_capacity': 120
            },
            {
                'name': 'Abhanpur Procurement Centre',
                'code': 'ABHANPUR-01',
                'location': 'Sub-Mandi Yard, Abhanpur Chowk',
                'district': 'Raipur',
                'state': 'Chhattisgarh',
                'daily_capacity': 80
            },
            {
                'name': 'Durg Procurement Centre',
                'code': 'DURG-01',
                'location': 'Ganj Mandi Yard, Station Road',
                'district': 'Durg',
                'state': 'Chhattisgarh',
                'daily_capacity': 100
            }
        ]

        created_centres = []
        for c in centres_data:
            pc = ProcurementCentre(
                name=c['name'],
                code=c['code'],
                location=c['location'],
                district=c['district'],
                state=c['state'],
                daily_capacity=c['daily_capacity'],
                is_active=True
            )
            db.session.add(pc)
            created_centres.append(pc)
        db.session.commit()

        raipur_centre, abhanpur_centre, durg_centre = created_centres

        print("[*] Seeding 5 Fictional Farmers...")
        farmers_info = [
            {
                'user': primary_farmer_user,
                'village': 'Dharsiwa',
                'district': 'Raipur',
                'state': 'Chhattisgarh',
                'crop_type': 'Paddy (Dhan)',
                'land_area': Decimal('6.5'),
                'identity_status': 'Verified (Demo)',
                'demo_ref': 'DEMO-FARMER-0001'
            },
            {
                'name': 'Suresh Verma',
                'mobile': '9876543211',
                'email': 'suresh.verma@kisansetu.demo',
                'village': 'Tilda',
                'district': 'Raipur',
                'state': 'Chhattisgarh',
                'crop_type': 'Wheat (Gehun)',
                'land_area': Decimal('4.0'),
                'identity_status': 'Verified (Demo)',
                'demo_ref': 'DEMO-FARMER-0002'
            },
            {
                'name': 'Anita Devi',
                'mobile': '9876543212',
                'email': 'anita.devi@kisansetu.demo',
                'village': 'Bhilai Village',
                'district': 'Durg',
                'state': 'Chhattisgarh',
                'crop_type': 'Soybean',
                'land_area': Decimal('3.5'),
                'identity_status': 'Verified (Demo)',
                'demo_ref': 'DEMO-FARMER-0003'
            },
            {
                'name': 'Mahesh Patel',
                'mobile': '9876543213',
                'email': 'mahesh.patel@kisansetu.demo',
                'village': 'Abhanpur Rural',
                'district': 'Raipur',
                'state': 'Chhattisgarh',
                'crop_type': 'Maize (Makka)',
                'land_area': Decimal('5.0'),
                'identity_status': 'Verified (Demo)',
                'demo_ref': 'DEMO-FARMER-0004'
            },
            {
                'name': 'Sunita Sahu',
                'mobile': '9876543214',
                'email': 'sunita.sahu@kisansetu.demo',
                'village': 'Patan',
                'district': 'Durg',
                'state': 'Chhattisgarh',
                'crop_type': 'Gram (Chana)',
                'land_area': Decimal('4.2'),
                'identity_status': 'Pending',
                'demo_ref': 'DEMO-FARMER-0005'
            }
        ]

        created_farmers = []
        for fi in farmers_info:
            if 'user' in fi:
                u = fi['user']
            else:
                u = User(
                    name=fi['name'],
                    mobile=fi['mobile'],
                    email=fi['email'],
                    role='farmer',
                    is_active=True
                )
                u.set_password("Farmer@123")
                db.session.add(u)
                db.session.flush()

            farmer = Farmer(
                user_id=u.id,
                village=fi['village'],
                district=fi['district'],
                state=fi['state'],
                crop_type=fi['crop_type'],
                land_area=fi['land_area'],
                identity_status=fi['identity_status']
            )
            db.session.add(farmer)
            db.session.flush()
            created_farmers.append(farmer)

            # Verification record
            verif = FarmerVerification(
                farmer_id=farmer.id,
                verification_mode='Mock',
                verification_status=fi['identity_status'],
                demo_reference=fi['demo_ref'],
                verified_by=operator_user.id if fi['identity_status'] == 'Verified (Demo)' else None
            )
            db.session.add(verif)

        db.session.commit()
        ramesh, suresh, anita, mahesh, sunita = created_farmers

        print("[*] Seeding Slots across today and future dates...")
        today = datetime.date.today()
        dates_to_seed = [
            today - datetime.timedelta(days=2),
            today - datetime.timedelta(days=1),
            today,
            today + datetime.timedelta(days=1),
            today + datetime.timedelta(days=2),
            today + datetime.timedelta(days=3),
        ]

        time_windows = [
            (datetime.time(9, 0), datetime.time(11, 0)),
            (datetime.time(11, 30), datetime.time(13, 30)),
            (datetime.time(14, 30), datetime.time(16, 30))
        ]

        all_slots = {}
        for centre in created_centres:
            for s_date in dates_to_seed:
                for start_t, end_t in time_windows:
                    slot = Slot(
                        centre_id=centre.id,
                        slot_date=s_date,
                        start_time=start_t,
                        end_time=end_t,
                        capacity=20,
                        booked_count=0,
                        status='Available'
                    )
                    db.session.add(slot)
                    all_slots[(centre.id, s_date, start_t)] = slot

        db.session.commit()

        print("[*] Seeding Sample Bookings, Queue Items, and Payments...")
        # Today Raipur Slots
        raipur_slot_today_morning = all_slots[(raipur_centre.id, today, datetime.time(9, 0))]
        raipur_slot_today_afternoon = all_slots[(raipur_centre.id, today, datetime.time(14, 30))]

        # Past days slots for charts
        yesterday = today - datetime.timedelta(days=1)
        two_days_ago = today - datetime.timedelta(days=2)

        durg_slot_yesterday = all_slots[(durg_centre.id, yesterday, datetime.time(9, 0))]
        abhanpur_slot_2days_ago = all_slots[(abhanpur_centre.id, two_days_ago, datetime.time(11, 30))]

        # Booking 1: Ramesh Kumar (Primary farmer) — In Procurement right now at Raipur!
        b1 = Booking(
            farmer_id=ramesh.id,
            slot_id=raipur_slot_today_morning.id,
            centre_id=raipur_centre.id,
            token_number=101,
            crop_type='Paddy (Dhan)',
            estimated_quantity=Decimal('45.0'),
            booking_status='In Procurement',
            booked_by_user_id=ramesh.user_id,
            created_at=datetime.datetime.utcnow() - datetime.timedelta(hours=3)
        )
        raipur_slot_today_morning.booked_count += 1
        db.session.add(b1)
        db.session.flush()

        p1 = Payment(
            booking_id=b1.id,
            farmer_id=ramesh.id,
            amount=Decimal('45.0') * Decimal('2300.00'),
            payment_status='Processing',
            payment_reference='PAY-KS-2026-00101',
            created_at=datetime.datetime.utcnow()
        )
        db.session.add(p1)

        # Booking 2: Suresh Verma — Arrived (Waiting in queue) at Raipur today
        b2 = Booking(
            farmer_id=suresh.id,
            slot_id=raipur_slot_today_morning.id,
            centre_id=raipur_centre.id,
            token_number=102,
            crop_type='Wheat (Gehun)',
            estimated_quantity=Decimal('35.0'),
            booking_status='Arrived',
            booked_by_user_id=operator_user.id, # Assisted booking!
            created_at=datetime.datetime.utcnow() - datetime.timedelta(hours=2)
        )
        raipur_slot_today_morning.booked_count += 1
        db.session.add(b2)
        db.session.flush()

        p2 = Payment(
            booking_id=b2.id,
            farmer_id=suresh.id,
            amount=Decimal('35.0') * Decimal('2275.00'),
            payment_status='Pending',
            payment_reference='PAY-KS-2026-00102',
            created_at=datetime.datetime.utcnow()
        )
        db.session.add(p2)

        # Booking 3: Anita Devi — Booked (Upcoming for today afternoon)
        b3 = Booking(
            farmer_id=anita.id,
            slot_id=raipur_slot_today_afternoon.id,
            centre_id=raipur_centre.id,
            token_number=103,
            crop_type='Soybean',
            estimated_quantity=Decimal('28.0'),
            booking_status='Booked',
            booked_by_user_id=csc_user.id, # Assisted booking via CSC!
            created_at=datetime.datetime.utcnow() - datetime.timedelta(hours=1)
        )
        raipur_slot_today_afternoon.booked_count += 1
        db.session.add(b3)
        db.session.flush()

        p3 = Payment(
            booking_id=b3.id,
            farmer_id=anita.id,
            amount=Decimal('28.0') * Decimal('4892.00'),
            payment_status='Pending',
            payment_reference='PAY-KS-2026-00103',
            created_at=datetime.datetime.utcnow()
        )
        db.session.add(p3)

        # Booking 4: Mahesh Patel — Completed yesterday at Durg with payment transferred
        b4 = Booking(
            farmer_id=mahesh.id,
            slot_id=durg_slot_yesterday.id,
            centre_id=durg_centre.id,
            token_number=101,
            crop_type='Maize (Makka)',
            estimated_quantity=Decimal('50.0'),
            booking_status='Completed',
            booked_by_user_id=operator_user.id,
            created_at=datetime.datetime.utcnow() - datetime.timedelta(days=1, hours=4)
        )
        durg_slot_yesterday.booked_count += 1
        db.session.add(b4)
        db.session.flush()

        p4 = Payment(
            booking_id=b4.id,
            farmer_id=mahesh.id,
            amount=Decimal('50.0') * Decimal('2090.00'),
            payment_status='Transferred (Demo)',
            payment_reference='PAY-KS-2026-00098',
            payment_date=datetime.datetime.utcnow() - datetime.timedelta(days=1),
            created_at=datetime.datetime.utcnow() - datetime.timedelta(days=1, hours=4)
        )
        db.session.add(p4)

        # Booking 5: Completed past booking at Abhanpur
        b5 = Booking(
            farmer_id=suresh.id,
            slot_id=abhanpur_slot_2days_ago.id,
            centre_id=abhanpur_centre.id,
            token_number=101,
            crop_type='Paddy (Dhan)',
            estimated_quantity=Decimal('40.0'),
            booking_status='Completed',
            booked_by_user_id=csc_user.id,
            created_at=datetime.datetime.utcnow() - datetime.timedelta(days=2, hours=5)
        )
        abhanpur_slot_2days_ago.booked_count += 1
        db.session.add(b5)
        db.session.flush()

        p5 = Payment(
            booking_id=b5.id,
            farmer_id=suresh.id,
            amount=Decimal('40.0') * Decimal('2300.00'),
            payment_status='Transferred (Demo)',
            payment_reference='PAY-KS-2026-00085',
            payment_date=datetime.datetime.utcnow() - datetime.timedelta(days=2),
            created_at=datetime.datetime.utcnow() - datetime.timedelta(days=2, hours=5)
        )
        db.session.add(p5)

        db.session.commit()

        print("[*] Seeding Dynamic Mock SMS Logs...")
        sample_bookings = [b1, b2, b3, b4, b5]
        for b in sample_bookings:
            msg = mock_sms_service.generate_booking_message(
                token_number=b.token_number,
                centre_name=b.centre.name,
                slot_date=b.slot.slot_date,
                time_range=b.slot.time_range_formatted,
                crop_type=b.crop_type
            )
            sms = SMSLog(
                booking_id=b.id,
                farmer_id=b.farmer_id,
                mobile=b.farmer.mobile,
                message=msg,
                message_type='Booking Confirmation',
                provider='MockSMS-Gateway-GovSim',
                status='Delivered' if b.booking_status == 'Completed' else 'Sent',
                created_at=b.created_at
            )
            db.session.add(sms)

        print("[*] Seeding System Audit Trail...")
        audit_records = [
            (admin_user.id, 'SYSTEM_INIT', 'System', None, 'KisanSetu procurement database initialized in Demo Mode.'),
            (operator_user.id, 'USER_LOGIN', 'User', operator_user.id, 'Procurement centre operator logged in.'),
            (operator_user.id, 'ASSISTED_FARMER_REGISTRATION', 'Farmer', ramesh.id, 'Assisted registration for Ramesh Kumar (9876543210).'),
            (operator_user.id, 'IDENTITY_VERIFY_SIMULATION', 'Farmer', ramesh.id, 'Simulated KYC verification approved (DEMO-FARMER-0001).'),
            (ramesh.user_id, 'SLOT_BOOKED', 'Booking', b1.id, 'Token #101 issued at Raipur Procurement Centre for Paddy.'),
            (operator_user.id, 'QUEUE_STATUS_UPDATE', 'Booking', b1.id, 'Token #101 marked as In Procurement for weighing.'),
            (csc_user.id, 'SLOT_BOOKED', 'Booking', b3.id, 'CSC operator assisted booking for Anita Devi (Token #103).')
        ]
        for uid, action, etype, eid, desc in audit_records:
            audit = AuditLog(
                user_id=uid,
                action=action,
                entity_type=etype,
                entity_id=eid,
                description=desc,
                created_at=datetime.datetime.utcnow() - datetime.timedelta(minutes=15)
            )
            db.session.add(audit)

        db.session.commit()

        print("\n" + "="*60)
        print("[SUCCESS] KISANSETU DEMO DATABASE SEEDED SUCCESSFULLY!")
        print("="*60)
        print("Demo Personas & Credentials:")
        print("  1. Admin:    admin@kisansetu.demo    / Admin@123")
        print("  2. Operator: operator@kisansetu.demo / Operator@123")
        print("  3. CSC Desk: csc@kisansetu.demo      / Csc@123")
        print("  4. Farmer:   farmer@kisansetu.demo   / Farmer@123 (Ramesh Kumar)")
        print("\nFictional Farmers Seeded:")
        print("  - Ramesh Kumar (9876543210) - Raipur (Paddy)")
        print("  - Suresh Verma (9876543211) - Raipur (Wheat)")
        print("  - Anita Devi   (9876543212) - Durg (Soybean)")
        print("  - Mahesh Patel (9876543213) - Raipur (Maize)")
        print("  - Sunita Sahu  (9876543214) - Durg (Gram - Pending KYC)")
        print("\nProcurement Centres Seeded:")
        print("  - Raipur Procurement Centre (RAIPUR-01)")
        print("  - Abhanpur Procurement Centre (ABHANPUR-01)")
        print("  - Durg Procurement Centre (DURG-01)")
        print("="*60 + "\n")

if __name__ == '__main__':
    seed_database()
