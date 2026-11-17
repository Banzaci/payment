
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from app.core.api_key import verify_api_key
from app.core.config import get_settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.merchant import Merchant


@pytest.mark.asyncio
async def test_create_merchant(monkeypatch):
    monkeypatch.setenv("PAYMENT_ADMIN_KEY", "test-admin-key")
    get_settings.cache_clear()

    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        engine,
        expire_on_commit=False,
    )

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/api/private/v1/merchants",
                headers={"X-Admin-Key": "test-admin-key"},
                json={
                    "name": "Test Merchant",
                    "default_currency": "USD",
                    "enabled_payment_methods": ["usdc"],
                },
            )

        assert response.status_code == 201

        data = response.json()
        assert data["name"] == "Test Merchant"
        assert data["api_key"].startswith("pk_")

        async with session_factory() as session:
            result = await session.execute(
                select(Merchant).where(
                    Merchant.id == data["id"]
                )
            )
            merchant = result.scalar_one()

            assert verify_api_key(
                data["api_key"],
                merchant.api_key_hash,
            )

    finally:
        app.dependency_overrides.clear()
        get_settings.cache_clear()
        await engine.dispose()


@pytest.mark.asyncio
async def test_create_merchant_without_admin_key():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/private/v1/merchants",
            json={
                "name": "Unauthorized Merchant",
                "default_currency": "USD",
                "enabled_payment_methods": ["usdc"],
            },
        )

    assert response.status_code == 401
