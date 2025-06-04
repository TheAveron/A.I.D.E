import pytest


def test_create_faction(client):
    response = client.post("/factions", json={"name": "Test Faction"})
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Faction"
    assert "id" in data


def test_create_duplicate_faction(client):
    response = client.post("/factions", json={"name": "Test Faction"})
    assert response.status_code == 400
    assert response.json()["detail"] == "Faction already exists"


def test_list_factions(client):
    response = client.get("/factions")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(f["name"] == "Test Faction" for f in data)


def test_update_faction(client):
    # First, get the faction ID
    list_resp = client.get("/factions")
    faction_id = list_resp.json()[0]["id"]

    response = client.put(f"/factions/{faction_id}", json={"name": "Updated Faction"})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Faction"


def test_update_nonexistent_faction(client):
    response = client.put("/factions/999", json={"name": "Ghost Faction"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Faction not found"
