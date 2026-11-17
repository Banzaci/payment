
import pytest
from decimal import Decimal
from urllib.parse import urlparse, parse_qs

from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
)

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.models.merchant import Merchant
from app.models.payment import Payment
from app.core.api_key import generate_api_key, hash_api_key
from app.core.config import get_settings
from app.libs.solana import is_valid_solana_address


@pytest.mark.asyncio
async def test_create_payment():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        engine,
        expire_on_commit=False,
    )

    async def override_get_db():
        async with session_factory() as session:
            yield session

    previous_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = override_get_db

    try:
        api_key = generate_api_key()

        async with session_factory() as session:
            merchant = Merchant(
                name="Test Hotel",
                default_currency="USDC",
                enabled_payment_methods=["usdc"],
                api_key_hash=hash_api_key(api_key),
            )

            session.add(merchant)
            await session.commit()
            await session.refresh(merchant)

            merchant_id = merchant.id

        payload = {
            "amount": "10.50",
            "currency": "USDC",
            "network": "solana-devnet",
            "recipient_address": "11111111111111111111111111111111",
        }

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/api/private/v1/payments",
                json=payload,
                headers={"X-API-Key": api_key},
            )

        assert response.status_code == 201

        data = response.json()

        assert is_valid_solana_address(data["reference"])

        parsed = urlparse(data["payment_url"])
        params = parse_qs(parsed.query)

        assert parsed.scheme == "solana"
        assert parsed.path == payload["recipient_address"]
        assert params["amount"] == ["10.50"]
        assert params["reference"] == [data["reference"]]
        assert params["spl-token"] == [get_settings().solana_usdc_mint]

        assert Decimal(data["amount"]) == Decimal("10.50")
        assert data["currency"] == "USDC"
        assert data["status"] == "pending"
        assert "id" in data

        async with session_factory() as session:
            result = await session.execute(
                select(Payment).where(Payment.id == data["id"])
            )
            saved = result.scalar_one()

            assert saved.merchant_id == merchant_id
            assert saved.amount == Decimal("10.50")
            assert saved.recipient_address == payload["recipient_address"]

    finally:
        app.dependency_overrides = previous_overrides
        await engine.dispose()


@pytest.mark.asyncio
async def test_create_payment_invalid_solana_address():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        engine,
        expire_on_commit=False,
    )

    async def override_get_db():
        async with session_factory() as session:
            yield session

    previous_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = override_get_db

    try:
        api_key = generate_api_key()

        async with session_factory() as session:
            merchant = Merchant(
                name="Test Hotel",
                default_currency="USDC",
                enabled_payment_methods=["usdc"],
                api_key_hash=hash_api_key(api_key),
            )

            session.add(merchant)
            await session.commit()

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/api/private/v1/payments",
                headers={"X-API-Key": api_key},
                json={
                    "amount": "10.50",
                    "currency": "USDC",
                    "network": "solana-devnet",
                    "recipient_address": "invalid-address",
                },
            )

        assert response.status_code == 422

    finally:
        app.dependency_overrides = previous_overrides
        await engine.dispose()
