import os

# Check USE_SQLITE before load_dotenv so we can force SQLite for local dev
USE_SQLITE = os.getenv("USE_SQLITE", "").lower() in ("1", "true", "yes")

from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Get URL from environment variables; fallback to SQLite for local dev
DATABASE_URL = os.getenv("DATABASE_URL") if not USE_SQLITE else None

if USE_SQLITE or not DATABASE_URL:
    # Vercel serverless: filesystem is read-only except /tmp
    if os.getenv("VERCEL"):
        db_path = "/tmp/hrms_lite.db"
    else:
        db_path = os.path.join(os.path.dirname(__file__), "..", "hrms_lite.db")
    DATABASE_URL = f"sqlite:///{db_path}"

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    # Try MySQL; fall back to SQLite if unreachable (e.g. network/DNS/firewall)
    try:
        if "ssl_mode=" in DATABASE_URL:
            from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
            parsed = urlparse(DATABASE_URL)
            params = [(k, v) for k, v in parse_qsl(parsed.query) if k.lower() != "ssl_mode"]
            new_query = urlencode(params)
            clean_url = urlunparse(parsed._replace(query=new_query))
        else:
            clean_url = DATABASE_URL
        import ssl
        ssl_ctx = ssl.create_default_context()
        _engine = create_engine(
            clean_url,
            connect_args={"ssl": ssl_ctx},
            pool_pre_ping=True,
            pool_recycle=300
        )
        # Test connection
        with _engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        engine = _engine
    except Exception as e:
        import warnings
        warnings.warn(f"MySQL unreachable ({e}). Using SQLite for local development.")
        db_path = "/tmp/hrms_lite.db" if os.getenv("VERCEL") else os.path.join(os.path.dirname(__file__), "..", "hrms_lite.db")
        DATABASE_URL = f"sqlite:///{db_path}"
        engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()