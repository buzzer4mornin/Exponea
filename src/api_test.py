from httpx import AsyncClient
import pytest
from api import app


@pytest.mark.anyio
async def test_1():
    async with AsyncClient(app=app, base_url="http://127.0.0.1:8000") as ac:
        response = await ac.get(f"/api/smart/1000")
        assert response.status_code == 200
        assert response.headers.get('Content-Type') == 'application/json'
        assert len(response.json()) > 0


@pytest.mark.anyio
async def test_2():
    async with AsyncClient(app=app, base_url="http://127.0.0.1:8000") as ac:
        response = await ac.get("/api/smart/1000")
        assert response.status_code == 200
        assert response.headers.get('Content-Type') == 'application/json'
        if response.json()["message"] == "SUCCESS":
            assert len(response.json()) == 2
            assert "time" in response.json()
        elif response.json()["message"] == "ERROR":
            assert len(response.json()) == 1
            assert "time" not in response.json()


@pytest.mark.anyio
async def test_3():
    async with AsyncClient(app=app, base_url="http://127.0.0.1:8000") as ac:
        response = await ac.get("/api/smart/some_string")
        assert response.status_code == 200
        assert response.headers.get('Content-Type') == 'application/json'
        assert len(response.json()) == 1
        assert "Endpoint timeout parameter should be INTEGER" in response.json()["message"]


@pytest.mark.anyio
async def test_4():
    async with AsyncClient(app=app, base_url="http://127.0.0.1:8000") as ac:
        response = await ac.get("/api/smart/50")
        assert response.status_code == 200
        assert response.headers.get('Content-Type') == 'application/json'
        assert len(response.json()) == 1
        assert "Endpoint timeout parameter should be above 300" in response.json()["message"]