
import pytest

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
)

from app.db.base import Base
from app.models.merchant import Merchant
from app.models.payment import Payment


@pytest.mark.asyncio
async def test_create_payment_in_database():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        engine,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        merchant = Merchant(
            name="Test Hotel",
            default_currency="USDC",
        )

        session.add(merchant)
        await session.flush()

        payment = Payment(
            merchant_id=merchant.id,
            amount=Decimal("10.50"),
            currency="USDC",
            network="solana-devnet",
            recipient_address="11111111111111111111111111111111",
            reference="test-reference",
            payment_url="solana:test-payment",
        )

        session.add(payment)
        await session.commit()

        result = await session.execute(
            select(Payment).where(Payment.id == payment.id)
        )

        saved_payment = result.scalar_one()

        assert saved_payment.merchant_id == merchant.id
        assert saved_payment.amount == Decimal("10.50")
        assert saved_payment.currency == "USDC"
        assert saved_payment.status == "pending"

    await engine.dispose()
