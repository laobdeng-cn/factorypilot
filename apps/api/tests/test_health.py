import pytest
from httpx import ASGITransport, AsyncClient, Response

from app.main import app


async def request(path: str) -> Response:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        return await client.get(path)


@pytest.mark.asyncio
async def test_service_info() -> None:
    response = await request("/")

    assert response.status_code == 200
    body = response.json()
    assert body["service"] == "FactoryPilot API"
    assert body["environment"] == "test"


@pytest.mark.asyncio
async def test_liveness() -> None:
    response = await request("/api/v1/health/live")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["checks"]["application"] == "ok"
    assert response.headers["X-Request-ID"]


@pytest.mark.asyncio
async def test_readiness_without_infrastructure_checks() -> None:
    response = await request("/api/v1/health/ready")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["checks"]["database"] == "not_checked"
    assert body["checks"]["redis"] == "not_checked"


@pytest.mark.asyncio
async def test_not_found_uses_standard_error_envelope() -> None:
    response = await request("/api/v1/does-not-exist")

    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "http_404"
    assert body["error"]["request_id"]
