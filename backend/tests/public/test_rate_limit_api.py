
import pytest
from fakeredis.aioredis import FakeRedis
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.core.redis import get_redis


@pytest.mark.asyncio
async def test_rate_limit_returns_429():
    fake_redis = FakeRedis(decode_responses=True)

    app.dependency_overrides[get_redis] = lambda: fake_redis

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            for _ in range(10):
                response = await client.get("/api/public/v1/health")
                assert response.status_code == 200

            response = await client.get("/api/public/v1/health")
            assert response.status_code == 429
    finally:
        app.dependency_overrides.clear()
        await fake_redis.aclose()
