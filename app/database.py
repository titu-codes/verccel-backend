import os
import sys

# Check USE_SQLITE before load_dotenv so we can force SQLite for local dev
USE_SQLITE = os.getenv("USE_SQLITE", "").lower() in ("1", "true", "yes")

from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Railway/Vercel: ephemeral storage - SQLite data is LOST on restart. Must use PostgreSQL.
ON_RAILWAY = bool(
    os.getenv("RAILWAY_SERVICE_NAME")
    or os.getenv("RAILWAY_ENVIRONMENT_NAME")
    or os.getenv("RAILWAY_PROJECT_ID")
    or os.getenv("RAILWAY_PUBLIC_DOMAIN")
)
ON_VERCEL = bool(os.getenv("VERCEL"))

# Get URL: DATABASE_URL (Railway auto-sets this), or POSTGRES_URL (Neon), or SQLite for local only
# When DATABASE_URL is set (e.g. Railway PostgreSQL), always use it - ignore USE_SQLITE
DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")
if DATABASE_URL:
    USE_SQLITE = False  # Prefer persistent DB when available
    # Railway uses postgres:// - SQLAlchemy needs postgresql://
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = "postgresql" + DATABASE_URL[8:]  # postgres:// -> postgresql://

if ON_RAILWAY and not DATABASE_URL:
    print(
        "\n" + "!" * 60 + "\n"
        "WARNING: No DATABASE_URL set on Railway. Using SQLite (data lost on restart).\n"
        "For persistent data: Add PostgreSQL -> Variables -> DATABASE_URL\n"
        "See RAILWAY_SETUP.md\n"
        + "!" * 60 + "\n",
        file=sys.stderr,
        flush=True,
    )

if USE_SQLITE or not DATABASE_URL:
    # Local dev only - SQLite persists in project folder
    if ON_VERCEL:
        db_path = "/tmp/hrms_lite.db"  # Ephemeral - use only for testing
    else:
        db_path = os.path.join(os.path.dirname(__file__), "..", "hrms_lite.db")
    DATABASE_URL = f"sqlite:///{db_path}"

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
elif DATABASE_URL.startswith("postgresql"):
    # PostgreSQL (Railway, Neon, Supabase) - persistent
    try:
        # Ensure psycopg2 driver for postgresql:// URLs
        if DATABASE_URL.startswith("postgresql://") and "+" not in DATABASE_URL.split("://")[0]:
            DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)
        engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            pool_recycle=300,
            connect_args={"connect_timeout": 10},
        )
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        print(f"PostgreSQL connection failed: {e}", file=sys.stderr, flush=True)
        import warnings
        warnings.warn(f"PostgreSQL unreachable ({e}). Using SQLite fallback.")
        db_path = "/tmp/hrms_lite.db" if os.getenv("VERCEL") else os.path.join(os.path.dirname(__file__), "..", "hrms_lite.db")
        DATABASE_URL = f"sqlite:///{db_path}"
        engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    # MySQL (Aiven, Railway, PlanetScale)
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
        engine = create_engine(
            clean_url,
            connect_args={"ssl": ssl_ctx},
            pool_pre_ping=True,
            pool_recycle=300,
        )
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        import warnings
        warnings.warn(f"MySQL unreachable ({e}). Using SQLite fallback.")
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