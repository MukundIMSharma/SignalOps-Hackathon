import os
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = os.getenv("INVENTORY_DATABASE_URL", "sqlite:///./inventory.db")
# Fixed demo clock so results never drift between rehearsals.
AS_OF = datetime.fromisoformat(os.getenv("DEMO_AS_OF", "2026-11-24T12:00:00"))

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
