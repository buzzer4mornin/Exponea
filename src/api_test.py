from httpx import AsyncClient
from fastapi.testclient import TestClient
import pytest

from api_train import app

client = TestClient(app)


@pytest.mark.anyio
async def test1():
    """
    Given enough timeout to process requests, API must return successfull response
    """
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/smart/1000")
    assert response.status_code == 200
    assert response.json()['time'] is not None
    assert response.json()['is_successfull'] is True
    assert response.headers.get('Content-Type') == 'application/json'


@pytest.mark.anyio
async def test2():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/smart/100")
    assert response.status_code == 200
    assert response.json()['time'] is None
    assert response.json()['is_successfull'] is False
