
import pytest
from fastapi import HTTPException
from unittest.mock import AsyncMock, MagicMock

from app.core.api_key import generate_api_key, hash_api_key
from app.core.merchant_auth import get_current_merchant
from app.models.merchant import Merchant


@pytest.mark.asyncio
async def test_valid_api_key_returns_merchant():
    api_key = generate_api_key()

    merchant = Merchant(
        name="Test Hotel",
        default_currency="GHS",
        api_key_hash=hash_api_key(api_key),
    )

    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = merchant
    db.execute.return_value = result

    authenticated = await get_current_merchant(
        x_api_key=api_key,
        db=db,
    )

    assert authenticated is merchant


@pytest.mark.asyncio
async def test_invalid_api_key_returns_401():
    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    db.execute.return_value = result

    with pytest.raises(HTTPException) as exc:
        await get_current_merchant(
            x_api_key="invalid_key",
            db=db,
        )

    assert exc.value.status_code == 401
