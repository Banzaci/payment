
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import get_settings
from app.models.payment import Payment
from app.services.solana_verification_service import (
    verify_solana_payment,
)

async def confirm_payment(
    payment_id: str,
    merchant_id: str,
    db: AsyncSession,
) -> Payment | None:
    result = await db.execute(
        select(Payment)
        .where(
            Payment.id == payment_id,
            Payment.merchant_id == merchant_id,
        )
        .with_for_update()
    )

    payment = result.scalar_one_or_none()

    if payment is None:
        return None

    if payment.status != "pending":
        return payment

    if (
        payment.currency != "USDC"
        or payment.network != "solana-devnet"
    ):
        return payment

    signature = await verify_solana_payment(
        reference=payment.reference,
        recipient=payment.recipient_address,
        mint=get_settings().solana_usdc_mint,
        amount=payment.amount,
    )

    if signature is None:
        return payment

    payment.status = "paid"
    payment.transaction_signature = signature

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise

    await db.refresh(payment)

    return payment
