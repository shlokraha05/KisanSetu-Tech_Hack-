# 🌾 KisanSetu (किसान सेतु)

**Omni-Channel Agricultural Procurement & Slot Management System**

*"Technology should adapt to the farmer — the farmer should not have to adapt to technology."*

KisanSetu is a comprehensive government agricultural procurement platform designed specifically for rural farmers. It bridges the digital divide by offering a robust system that caters not just to tech-savvy users, but primarily to farmers who may not own smartphones or possess digital literacy. 

---

## 🎯 Vision & Purpose

During peak harvest seasons, government procurement mandis face severe overcrowding, long waiting times, and chaotic token distribution. Farmers often travel long distances only to be turned away due to daily capacity limits.

**KisanSetu solves this by:**
1. Eliminating long physical queues through transparent, capacity-based slot booking.
2. Ensuring zero digital friction for rural farmers via an "Assisted-First" model.
3. Keeping farmers informed via simple text messages (SMS) in regional languages.
4. Providing real-time dashboard analytics for government administrators to manage logistics.

## 🚀 Key Features

### 1. Omni-Channel Access
- **Self-Service Portal**: Tech-savvy farmers can log in, complete KYC, and book slots directly.
- **Assisted Helpdesks (CSC/Mandi)**: Operators can register walk-in farmers, verify their identity, and print physical token receipts on their behalf.

### 2. Smart Slot & Queue Management
- **Capacity Controls**: Each procurement centre has dynamic daily and hourly capacity limits to prevent overcrowding.
- **Live Queue Board**: Operators have a live dashboard to call tokens sequentially, automatically triggering SMS alerts to farmers to bring their carts to the weighbridge.

### 3. Integrated KYC & Communications (Demo Integrations)
- **Aadhaar/OTP Verification**: Implemented via Supabase Auth. Ensures only legitimate, verified farmers can book slots.
- **SMS Gateway**: Integrated with Twilio to send automated booking confirmations, queue alerts, and payment updates directly to the farmer's basic feature phone. (Includes a robust mock-SMS fallback for demo environments).

### 4. Admin & Analytics Dashboard
- Comprehensive real-time metrics showing total procurements, centre-wise load, crop-type distribution (MSP calculations), and queue analytics using Chart.js.

---

## 🛠️ Technology Stack

- **Backend Framework**: Python / Flask
- **Database**: MySQL 8.0 (Production) with resilient SQLite Fallback (Local Development)
- **ORM**: SQLAlchemy
- **Frontend**: HTML5, Tailwind CSS, Jinja2 Templating, Vanilla JavaScript
- **Integrations**: Supabase (Auth/OTP), Twilio (SMS Gateway)
- **Testing**: Pytest

---

## 💻 Running the Project Locally

### Prerequisites
- Python 3.8+
- (Optional) MySQL Server 

### 1. Installation
Clone the repository and install the dependencies:
```bash
python -m pip install -r requirements.txt
```

### 2. Environment Configuration
Create a `.env` file in the root directory (you can copy `.env.example`).
```env
# Database (Leave blank to use local SQLite fallback)
DATABASE_URL=

# Supabase Details (For Aadhaar/OTP Verification)
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key

# Twilio Details (For real SMS dispatches)
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_PHONE_NUMBER=your_twilio_phone
```

### 3. Seed the Database
To populate the database with procurement centres, demo farmers, and available time slots for the current week:
```bash
python seed.py
```
*Note: Run this script whenever you need fresh time slots for testing.*

### 4. Run the Server
```bash
python run.py
```
Access the application at: `http://127.0.0.1:5000`

---

## 👥 Demo User Personas

The `seed.py` script automatically provisions the following demo accounts:

| Role | Email | Password |
|------|-------|----------|
| **Admin** | admin@kisansetu.demo | Admin@123 |
| **Operator** | operator@kisansetu.demo | Operator@123 |
| **CSC Desk** | csc@kisansetu.demo | Csc@123 |
| **Farmer** | farmer@kisansetu.demo | Farmer@123 |

*(Farmer Ramesh Kumar is pre-seeded with mobile: `9876543210`)*

---

## 🛡️ Hackathon / SIH Note
This is a prototype developed for the Smart India Hackathon (SIH). It utilizes mock gateways for Aadhaar verification and SMS delivery by default to prevent third-party API costs during development, with production-ready SDKs (Supabase/Twilio) wired in and ready to be toggled via environment variables.
