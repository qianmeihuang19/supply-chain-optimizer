"""Database initialization — create SQLite and all 20 tables."""
from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .models import Base

DB_DIR = Path(__file__).resolve().parent.parent.parent / "data"
DB_PATH = DB_DIR / "supply_chain.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)


def get_session():
    """Return a new DB session (caller must close)."""
    return SessionLocal()


def init_db() -> str:
    """Create all tables. Returns the DB file path."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    return str(DB_PATH)


if __name__ == "__main__":
    path = init_db()
    print(f"Database initialized at {path}")
    print("Tables created:")
    for table_name in Base.metadata.tables:
        print(f"  - {table_name}")
