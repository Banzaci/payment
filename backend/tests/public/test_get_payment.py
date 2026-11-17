from decimal import Decimal

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.merchant import Merchant
from app.models.payment import Payment

@pytest_asyncio.fixture
async def public_payment():
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
        )
        db.add(merchant)
        await db.flush()

        payment = Payment(
            merchant_id=merchant.id,
            amount=Decimal("10.50"),
            currency="USDC",
            network="solana-devnet",
            recipient_address="recipient-wallet",
            reference="test-reference",
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

    app.dependency_overrides.pop(get_db, None)
    await engine.dispose()


@pytest.mark.asyncio
async def test_get_public_payment(public_payment):
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get(
            f"/api/public/v1/payments/{public_payment}"
        )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == public_payment
    assert Decimal(data["amount"]) == Decimal("10.50")
    assert data["currency"] == "USDC"
    assert data["network"] == "solana-devnet"
    assert data["status"] == "pending"
    assert data["payment_url"] == "solana:test"
    assert data["enabled_payment_methods"] == ["usdc"]
    assert "merchant_id" not in data
    assert "transaction_signature" not in data
    assert "reference" not in data


@pytest.mark.asyncio
async def test_get_unknown_payment(public_payment):
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get(
            "/api/public/v1/payments/unknown-id"
        )

    assert response.status_code == 404
