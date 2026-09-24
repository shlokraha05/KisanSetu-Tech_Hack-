import os
import sys

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from app import create_app
from app.extensions import db
from app.models import User
from seed import seed_database

app = create_app()

with app.app_context():
    # Ensure database schema is initialized
    db.create_all()
    # Check if database has been seeded; if empty, seed automatically
    if User.query.count() == 0:
        print("[*] First run detected: Seeding initial demo data automatically...")
        seed_database()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', '1') in ('1', 'True', 'true')
    print(f"\n[+] KisanSetu Server Starting on http://127.0.0.1:{port}")
    print("[+] Press CTRL+C to quit.\n")
    app.run(host='127.0.0.1', port=port, debug=debug)
