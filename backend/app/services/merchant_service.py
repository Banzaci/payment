
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_key import generate_api_key, hash_api_key
from app.models.merchant import Merchant


async def create_merchant(
    db: AsyncSession,
    name: str,
    default_currency: str,
    enabled_payment_methods: list[str],
) -> tuple[Merchant, str]:
    api_key = generate_api_key()

    merchant = Merchant(
        name=name,
        default_currency=default_currency,
        enabled_payment_methods=enabled_payment_methods,
        api_key_hash=hash_api_key(api_key),
    )

    db.add(merchant)
    await db.commit()
    await db.refresh(merchant)

    return merchant, api_key
