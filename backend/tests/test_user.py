import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.database import Base, get_db
from app.main import app
from app.database.models import user as user_models

# --- Setup test database (in-memory SQLite) ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override the dependency
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close() # type: ignore

app.dependency_overrides[get_db] = override_get_db

# Create test database
Base.metadata.create_all(bind=engine)

client = TestClient(app)

# --- Fixtures ---
@pytest.fixture
def test_user():
    return {"username": "testuser", "password": "testpass"}

# --- Tests ---
def test_register_user(test_user):
    response = client.post("/users/register", json=test_user)
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == test_user["username"]
    assert "id" in data
    assert "is_admin" in data

def test_duplicate_user_register(test_user):
    client.post("/users/register", json=test_user)  # First registration
    response = client.post("/users/register", json=test_user)  # Duplicate
    assert response.status_code == 400
    assert response.json()["detail"] == "Username already taken"

def test_login_user(test_user):
    client.post("/users/register", json=test_user)
    response = client.post("/users/login", json=test_user)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_invalid_password(test_user):
    client.post("/users/register", json=test_user)
    response = client.post("/users/login", json={"username": test_user["username"], "password": "wrongpass"})
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid credentials"
