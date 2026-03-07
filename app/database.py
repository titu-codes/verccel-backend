import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Get URL from environment variables
DATABASE_URL = os.getenv("DATABASE_URL")

# SSL is REQUIRED for Aiven MySQL
engine = create_engine(
    DATABASE_URL,
    connect_args={
        "ssl": {
            "ssl_mode": "REQUIRED"
        }
    },
    pool_pre_ping=True,  # Automatically reconnects if the connection drops
    pool_recycle=300     # Refreshes connections every 5 minutes
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()