import pytest_asyncio
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.models.merchant import Merchant
from app.models.payment import Payment
from app.services import payment_verification_service as service


SIGNATURE = "verified-solana-signature"


@pytest_asyncio.fixture
async def payment_db():
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
            reference="payment-reference",
            payment_url="solana:test",
        )
        db.add(payment)
        await db.commit()

        yield db, merchant.id, payment.id

    await engine.dispose()


@pytest.mark.asyncio
async def test_confirm_payment(payment_db, monkeypatch):
    db, merchant_id, payment_id = payment_db

    verify = AsyncMock(return_value=SIGNATURE)
    monkeypatch.setattr(
        service,
        "verify_solana_payment",
        verify,
    )

    payment = await service.confirm_payment(
        payment_id,
        merchant_id,
        db,
    )

    assert payment.status == "paid"
    assert payment.transaction_signature == SIGNATURE

    await db.refresh(payment)
    assert payment.status == "paid"

    verify.assert_awaited_once()


@pytest.mark.asyncio
async def test_unconfirmed_payment(payment_db, monkeypatch):
    db, merchant_id, payment_id = payment_db

    monkeypatch.setattr(
        service,
        "verify_solana_payment",
        AsyncMock(return_value=None),
    )

    payment = await service.confirm_payment(
        payment_id,
        merchant_id,
        db,
    )

    assert payment.status == "pending"
    assert payment.transaction_signature is None


@pytest.mark.asyncio
async def test_wrong_merchant(payment_db, monkeypatch):
    db, _, payment_id = payment_db

    verify = AsyncMock(return_value=SIGNATURE)
    monkeypatch.setattr(
        service,
        "verify_solana_payment",
        verify,
    )

    payment = await service.confirm_payment(
        payment_id,
        "another-merchant",
        db,
    )

    assert payment is None
    verify.assert_not_awaited()


@pytest.mark.asyncio
async def test_already_paid(payment_db, monkeypatch):
    db, merchant_id, payment_id = payment_db

    payment = await db.get(Payment, payment_id)
    payment.status = "paid"
    payment.transaction_signature = SIGNATURE
    await db.commit()

    verify = AsyncMock(return_value=SIGNATURE)
    monkeypatch.setattr(
        service,
        "verify_solana_payment",
        verify,
    )

    result = await service.confirm_payment(
        payment_id,
        merchant_id,
        db,
    )

    assert result.status == "paid"
    verify.assert_not_awaited()


@pytest.mark.asyncio
async def test_duplicate_transaction(payment_db, monkeypatch):
    db, merchant_id, payment_id = payment_db

    first = await db.get(Payment, payment_id)
    first.status = "paid"
    first.transaction_signature = SIGNATURE
    await db.commit()
    
    second = Payment(
        merchant_id=merchant_id,
        amount=Decimal("10.50"),
        currency="USDC",
        network="solana-devnet",
        recipient_address="recipient-wallet",
        reference="another-reference",
        payment_url="solana:another",
    )
    db.add(second)
    await db.commit()
    second_id = second.id

    monkeypatch.setattr(
        service,
        "verify_solana_payment",
        AsyncMock(return_value=SIGNATURE),
    )

    with pytest.raises(IntegrityError):
        await service.confirm_payment(
            second_id,
            merchant_id,
            db,
        )

    result = await db.execute(
        select(Payment).where(Payment.id == second_id)
    )
    assert result.scalar_one().status == "pending"
