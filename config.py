import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env if present
basedir = Path(__file__).resolve().parent
load_dotenv(basedir / '.env')

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'kisansetu-dev-secret-key-sih-2026')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Primary MySQL connection string
    # e.g., mysql+pymysql://root:@localhost:3306/kisansetu_db
    DB_URL = os.environ.get('DATABASE_URL')
    if not DB_URL:
        user = os.environ.get('MYSQL_USER', 'root')
        password = os.environ.get('MYSQL_PASSWORD', '')
        host = os.environ.get('MYSQL_HOST', 'localhost')
        port = os.environ.get('MYSQL_PORT', '3306')
        dbname = os.environ.get('MYSQL_DATABASE', 'kisansetu_db')
        DB_URL = f"mysql+pymysql://{user}:{password}@{host}:{port}/{dbname}"

    # Database resolution with resilient SQLite fallback if MySQL is offline
    ENABLE_FALLBACK = os.environ.get('ENABLE_SQLITE_FALLBACK', 'True').lower() in ('true', '1', 'yes')
    sqlite_db_path = basedir / 'kisansetu.db'
    
    # Check if MySQL is actually reachable when starting
    if DB_URL.startswith('mysql'):
        is_reachable = False
        try:
            import pymysql
            from urllib.parse import urlparse
            parsed = urlparse(DB_URL)
            host = parsed.hostname or 'localhost'
            port = parsed.port or 3306
            user = parsed.username or 'root'
            password = parsed.password or ''
            
            # Quick timeout check
            conn = pymysql.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                connect_timeout=1
            )
            conn.close()
            is_reachable = True
        except Exception:
            is_reachable = False
        
        if is_reachable:
            SQLALCHEMY_DATABASE_URI = DB_URL
            DATABASE_ENGINE = 'MySQL 8+'
        elif ENABLE_FALLBACK:
            SQLALCHEMY_DATABASE_URI = f"sqlite:///{sqlite_db_path}"
            DATABASE_ENGINE = 'SQLite (Local Fallback)'
        else:
            SQLALCHEMY_DATABASE_URI = DB_URL
            DATABASE_ENGINE = 'MySQL 8+ (Configured)'
    else:
        SQLALCHEMY_DATABASE_URI = DB_URL or f"sqlite:///{sqlite_db_path}"
        DATABASE_ENGINE = 'Configured DB'

    DEMO_MODE = os.environ.get('DEMO_MODE', 'True').lower() in ('true', '1', 'yes')
    REQUIRE_DEMO_AADHAAR = os.environ.get('REQUIRE_DEMO_AADHAAR', 'True').lower() in ('true', '1', 'yes')


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SERVER_NAME = 'localhost.localdomain'
    DATABASE_ENGINE = 'SQLite (In-Memory Testing)'
