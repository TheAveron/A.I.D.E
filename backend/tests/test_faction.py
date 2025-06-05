import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_create_faction(client):
    response = client.post("/factions", json={"name": "Test Faction"})
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Faction"
    assert "id" in data


def test_create_duplicate_faction(client):
    client.post("/factions", json={"name": "Test Faction"})
    response = client.post("/factions", json={"name": "Test Faction"})
    assert response.status_code == 400
    assert response.json()["detail"] == "Faction already exists"


def test_list_factions(client):
    client.post("/factions", json={"name": "Test Faction"})
    response = client.get("/factions")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(f["name"] == "Test Faction" for f in data)


def test_update_faction(client):
    # First, create a faction and get its ID
    create_resp = client.post("/factions", json={"name": "To Update"})
    faction_id = create_resp.json()["id"]

    response = client.put(f"/factions/{faction_id}", json={"name": "Updated Faction"})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Faction"


def test_update_nonexistent_faction(client):
    response = client.put("/factions/99999", json={"name": "Ghost Faction"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Faction not found"
