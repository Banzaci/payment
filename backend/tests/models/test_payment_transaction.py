
import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.models.merchant import Merchant
from app.models.payment import Payment


@pytest.mark.asyncio
async def test_transaction_signature_must_be_unique():
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        session_factory = async_sessionmaker(
            engine,
            expire_on_commit=False,
        )

        async with session_factory() as session:
            merchant = Merchant(
                name="Test Merchant",
                default_currency="USD",
                enabled_payment_methods=["usdc"],
            )
            session.add(merchant)
            await session.flush()

            for index in range(2):
                session.add(
                    Payment(
                        merchant_id=merchant.id,
                        amount="10.50",
                        currency="USDC",
                        network="solana-devnet",
                        recipient_address="test-recipient",
                        reference=f"reference-{index}",
                        payment_url=f"solana:test-{index}",
                        transaction_signature="same-signature",
                    )
                )

            with pytest.raises(IntegrityError):
                await session.commit()

    finally:
        await engine.dispose()
