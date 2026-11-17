import pytest_asyncio
from fakeredis.aioredis import FakeRedis

from app.main import app
from app.core.redis import get_redis


@pytest_asyncio.fixture(autouse=True)
async def mock_redis():
    redis = FakeRedis(decode_responses=True)
    previous_overrides = app.dependency_overrides.copy()

    app.dependency_overrides[get_redis] = lambda: redis

    yield redis

    app.dependency_overrides = previous_overrides
    await redis.aclose()