import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from pathlib import Path

# Database URL pointing to local SQLite file
DEFAULT_DB_FILE = Path(__file__).resolve().parent / "edupulse.db"
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL or DATABASE_URL in ("sqlite:///./eduplus_v2.db", "sqlite:///./edupulse.db"):
    DATABASE_URL = f"sqlite:///{DEFAULT_DB_FILE.as_posix()}"

# connect_args={"check_same_thread": False} is required only for SQLite
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# SessionLocal is the factory for new database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for SQLAlchemy ORM models
Base = declarative_base()

def get_db():
    """
    FastAPI dependency that provides a database session to endpoints
    and automatically closes it after the request completes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
