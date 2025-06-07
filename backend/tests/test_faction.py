import pytest
from fastapi import status

from app.schemas import FactionCreate


def test_create_faction_validation(client):
    # Test empty name
    response = client.post("/factions", json={"name": ""})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Test too long name
    response = client.post("/factions", json={"name": "a" * 101})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_concurrent_faction_creation(client):
    import asyncio
    from concurrent.futures import ThreadPoolExecutor

    async def create_faction(name: str):
        return client.post("/factions", json={"name": name})

    async def test_concurrent():
        tasks = []
        for i in range(5):
            tasks.append(create_faction(f"Faction{i}"))
        responses = await asyncio.gather(*tasks)

        # Check that only one creation succeeded
        success_count = sum(1 for r in responses if r.status_code == 201)
        assert success_count == 5

    asyncio.run(test_concurrent())
