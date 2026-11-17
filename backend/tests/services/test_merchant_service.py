
import pytest

from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
)

from app.core.api_key import verify_api_key
from app.db.base import Base
from app.models.merchant import Merchant
from app.services.merchant_service import create_merchant


@pytest.mark.asyncio
async def test_create_merchant():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        engine,
        expire_on_commit=False,
    )

    try:
        async with session_factory() as session:
            merchant, api_key = await create_merchant(
                db=session,
                name="Laughing Goat Ghana",
                default_currency="GHS",
                enabled_payment_methods=["usdc"],
            )

            assert isinstance(merchant, Merchant)
            assert merchant.id is not None
            assert merchant.name == "Laughing Goat Ghana"
            assert merchant.default_currency == "GHS"
            assert merchant.enabled_payment_methods == ["usdc"]
            assert api_key.startswith("pk_")
            assert merchant.api_key_hash != api_key
            assert verify_api_key(api_key, merchant.api_key_hash)

    finally:
        await engine.dispose()
