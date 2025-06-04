import pytest
from sqlalchemy.orm import Session

from backend.app.database import User
from backend.app.api.auth import hash_password

def test_register_user(client):
    response = client.post("/register", json={
        "username": "testuser",
        "password": "testpass"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert "id" in data

def test_register_existing_user(client):
    response = client.post("/register", json={
        "username": "testuser",
        "password": "testpass"
    })
    assert response.status_code == 400
    assert response.json()["detail"] == "Username already taken"

def test_login_user(client):
    response = client.post("/login", json={
        "username": "testuser",
        "password": "testpass"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_wrong_password(client):
    response = client.post("/login", json={
        "username": "testuser",
        "password": "wrongpass"
    })
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"
