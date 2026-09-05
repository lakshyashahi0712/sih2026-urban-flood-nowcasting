"""Database configuration and session management for the water monitoring system."""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# SQLite database file lives alongside the backend
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "water_monitor.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # required for SQLite with FastAPI
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables. Run once at startup."""
    try:
        from backend import models  # noqa: F401
    except ImportError:
        import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
