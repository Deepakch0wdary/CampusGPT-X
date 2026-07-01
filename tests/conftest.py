import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Insert backend path for module resolution
backend_root = Path(__file__).resolve().parent.parent / "apps" / "backend"
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from app.main import app
from app.core.dependencies import get_db
from app.models.models import Base, Role, Permission

# Initialize SQLite in-memory DB for unit/integration testing
engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Initializes in-memory SQLite schema tables for the test session."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """Yields a transactional database session rolled back after every single test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    # Seed required roles
    for name in ["MASTER_ADMIN", "TEACHER", "STUDENT"]:
        role = Role(name=name, description=f"{name} test role")
        session.add(role)

    # Seed required permissions
    for name in ["users:create", "users:read", "audits:read", "roles:manage"]:
        perm = Permission(name=name, description=f"Test permission to {name}")
        session.add(perm)

    session.commit()
    yield session

    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function", autouse=True)
def override_database_dependency(db_session):
    """Binds the active test session to get_db context injections."""
    app.dependency_overrides[get_db] = lambda: db_session
    yield
    app.dependency_overrides.clear()

@pytest.fixture(scope="session")
def client() -> TestClient:
    """Session test HTTP client."""
    return TestClient(app)
