from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings
import logging

logger = logging.getLogger("campusgpt.database")

# Initialize SQLAlchemy DB Engine
# pool_pre_ping checks connection health before issuing queries
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    """Dependency injection yield-pattern for retrieving a thread-local DB session."""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session exception: {e}")
        raise
    finally:
        db.close()
