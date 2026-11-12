"""Shared fixtures.

The models tests use an in-memory SQLite database; no PostgreSQL server is
needed to run the test suite.
"""

import pytest
from app.api.auth import login_limiter
from app.database import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture(autouse=True)
def _fresh_login_limiter():
    """Failed-login counters are process-wide: every test starts from zero."""
    login_limiter.clear()
    yield
    login_limiter.clear()


@pytest.fixture(scope="function")
def session():
    engine = create_engine("sqlite:///:memory:", echo=False)
    TestingSessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
