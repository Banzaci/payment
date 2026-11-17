
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from app.core.api_key import hash_api_key
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.merchant import Merchant
from app.models.payment import Payment
from app.services import payment_verification_service as service


API_KEY = "test-merchant-api-key"
SIGNATURE = "verified-solana-signature"


@pytest_asyncio.fixture
async def payment_setup():
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

    async with session_factory() as db:
        merchant = Merchant(
            name="Test Merchant",
            default_currency="USD",
            enabled_payment_methods=["usdc"],
            api_key_hash=hash_api_key(API_KEY),
        )
        db.add(merchant)
        await db.flush()

        payment = Payment(
            merchant_id=merchant.id,
            amount=Decimal("10.50"),
            currency="USDC",
            network="solana-devnet",
            recipient_address="recipient-wallet",
            reference="payment-reference",
            payment_url="solana:test",
        )
        db.add(payment)
        await db.commit()

        payment_id = payment.id

    async def override_get_db():
        async with session_factory() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db

    yield payment_id

    app.dependency_overrides.clear()
    await engine.dispose()


@pytest.mark.asyncio
async def test_verify_pending_payment(payment_setup, monkeypatch):
    monkeypatch.setattr(
        service,
        "verify_solana_payment",
        AsyncMock(return_value=None),
    )

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            f"/api/private/v1/payments/{payment_setup}/verify",
            headers={"X-API-Key": API_KEY},
        )

    assert response.status_code == 200
    assert response.json()["status"] == "pending"
    assert response.json()["transaction_signature"] is None


@pytest.mark.asyncio
async def test_verify_successful_payment(payment_setup, monkeypatch):
    monkeypatch.setattr(
        service,
        "verify_solana_payment",
        AsyncMock(return_value=SIGNATURE),
    )

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            f"/api/private/v1/payments/{payment_setup}/verify",
            headers={"X-API-Key": API_KEY},
        )

    assert response.status_code == 200
    assert response.json()["status"] == "paid"
    assert response.json()["transaction_signature"] == SIGNATURE


@pytest.mark.asyncio
async def test_verify_without_api_key(payment_setup):
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            f"/api/private/v1/payments/{payment_setup}/verify"
        )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_verify_wrong_merchant(payment_setup):
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            f"/api/private/v1/payments/{payment_setup}/verify",
            headers={"X-API-Key": "wrong-api-key"},
        )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_verify_unknown_payment(payment_setup):
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/private/v1/payments/unknown-id/verify",
            headers={"X-API-Key": API_KEY},
        )

    assert response.status_code == 404
