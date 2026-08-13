import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_create_user():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.post("/users", json={"email": "test@example.com"})
    assert r.status_code == 200
