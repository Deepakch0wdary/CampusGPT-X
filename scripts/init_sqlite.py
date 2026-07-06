# scripts/init_sqlite.py
import sys
from pathlib import Path

backend_root = Path(__file__).resolve().parent.parent / "apps" / "backend"
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from sqlalchemy import create_engine
from app.core.config import settings
from app.models.models import Base

def init_db():
    print("Database URL configured:", settings.DATABASE_URL)
    if not settings.DATABASE_URL.startswith("sqlite"):
        print("Not using SQLite database. Skipping auto table creation.")
        return

    print("Initializing SQLite tables in local DB file...")
    engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    print("All SQLAlchemy tables created successfully in SQLite!")

if __name__ == "__main__":
    init_db()
