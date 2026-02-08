"""Test fixtures for API integration tests.

Provides a FastAPI `TestClient` backed by an in-memory SQLite database
and initializes default data required by tests.
"""

from typing import Generator
import warnings
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.core.deps import get_db
from app.db.init_db import ensure_admin
from app.main import app


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    # Reduce noisy third-party deprecation warnings during tests
    warnings.filterwarnings(
        "ignore",
        message="Please use `import python_multipart` instead.",
        category=PendingDeprecationWarning,
    )
    warnings.filterwarnings(
        "ignore",
        message="datetime.datetime.utcnow() is deprecated",
        category=DeprecationWarning,
    )
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    Base.metadata.create_all(bind=engine)
    
    # Initialize admin user
    db = TestingSessionLocal()
    ensure_admin(db)
    db.close()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()