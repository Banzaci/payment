
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_key import hash_api_key
from app.db.session import get_db
from app.models.merchant import Merchant


async def get_current_merchant(
    x_api_key: Annotated[str | None, Header()] = None,
    db: AsyncSession = Depends(get_db),
) -> Merchant:
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
        )

    result = await db.execute(
        select(Merchant).where(
            Merchant.api_key_hash == hash_api_key(x_api_key)
        )
    )

    merchant = result.scalar_one_or_none()

    if merchant is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    return merchant
