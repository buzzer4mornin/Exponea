from httpx import AsyncClient
import pytest
from api import app


@pytest.mark.anyio
async def test_1():
    # This is general test.
    # Once the request sent to our server, we should receive status code 200 along with json which has a valid payload
    async with AsyncClient(app=app, base_url="http://127.0.0.1:8000") as ac:
        response = await ac.get(f"/api/smart/1000")
        assert response.status_code == 200
        assert response.headers.get('Content-Type') == 'application/json'
        assert len(response.json()) > 0


@pytest.mark.anyio
async def test_2():
    # This is the test when endpoint receives integer above 300.
    # In this case, we can only have SUCCESS or ERROR on message. And their payload should be checked accordingly.
    async with AsyncClient(app=app, base_url="http://127.0.0.1:8000") as ac:
        response = await ac.get("/api/smart/1000")
        assert response.status_code == 200
        assert response.headers.get('Content-Type') == 'application/json'
        assert response.json()["message"] == "SUCCESS" or response.json()["message"] == "ERROR"
        if response.json()["message"] == "SUCCESS":
            assert len(response.json()) == 2
            assert "time" in response.json()
        elif response.json()["message"] == "ERROR":
            assert len(response.json()) == 1
            assert "time" not in response.json()


@pytest.mark.anyio
async def test_3():
    # This is when endpoint receives string.
    # In this case, message should be checked accordingly.
    async with AsyncClient(app=app, base_url="http://127.0.0.1:8000") as ac:
        response = await ac.get("/api/smart/some_string")
        assert response.status_code == 200
        assert response.headers.get('Content-Type') == 'application/json'
        assert len(response.json()) == 1
        assert response.json()["message"] == "Endpoint timeout parameter should be INTEGER"


@pytest.mark.anyio
async def test_4():
    # This is when the endpoint receives integer lower than 300.
    # In this case, message should be checked accordingly.
    async with AsyncClient(app=app, base_url="http://127.0.0.1:8000") as ac:
        response = await ac.get("/api/smart/50")
        assert response.status_code == 200
        assert response.headers.get('Content-Type') == 'application/json'
        assert len(response.json()) == 1
        assert response.json()["message"] == "Endpoint timeout parameter should be above 300"
