import sqlite3

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.database.database import get_db
from main import app

# Setup a test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


# Dependency override
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(scope="module")
def test_offer_data():
    return {
        "user_id": 1,
        "item_description": {"name": "Iron Ingot", "quantity": 10},
        "currency": "gold",
        "price": 100.0,
    }


def test_create_offer(test_offer_data):
    response = client.post("/offers/", json=test_offer_data)
    assert response.status_code == 201
    data = response.json()
    assert (
        data["item_description"]["name"] == test_offer_data["item_description"]["name"]
    )
    assert data["currency"] == test_offer_data["currency"]


def test_list_offers():
    response = client.get("/offers/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_offer():
    response = client.get("/offers/1")
    assert response.status_code == 200
    assert response.json()["id"] == 1


def test_update_offer():
    update_data = {"price": 120.0, "currency": "silver"}
    response = client.put("/offers/1", json=update_data)
    assert response.status_code == 200
    assert response.json()["price"] == update_data["price"]


def test_update_offer_status():
    response = client.patch("/offers/1/status?status=closed")
    assert response.status_code == 200
    assert response.json()["status"] == "closed"


def test_delete_offer():
    response = client.delete("/offers/1")
    assert response.status_code == 204
    response = client.get("/offers/1")
    assert response.status_code == 404
