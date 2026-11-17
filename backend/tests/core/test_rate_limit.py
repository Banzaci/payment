import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_rate_limit_returns_429():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        for _ in range(10):
            response = await client.get("/api/public/v1/health")
            assert response.status_code == 200

        response = await client.get("/api/public/v1/health")
        assert response.status_code == 429