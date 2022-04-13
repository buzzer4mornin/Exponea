import pytest
from httpx import AsyncClient
from aiohttp import ClientSession

from api_train import app


@pytest.mark.anyio
async def test_root():
    async with AsyncClient(app=app, base_url="http://127.0.0.1") as ac:
        response = await ac.get("/api/smart/800")
    assert response.status_code == 200
