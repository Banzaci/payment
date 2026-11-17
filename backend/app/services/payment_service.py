
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.libs.solana import generate_solana_reference
from app.libs.solana_pay import create_payment_url
from app.models.payment import Payment
from app.schemas.payment import PaymentCreate, PaymentResponse


async def create_payment(
    payload: PaymentCreate,
    db: AsyncSession,
    merchant_id: str,
) -> PaymentResponse:
    reference = generate_solana_reference()

    payment_url = create_payment_url(
        recipient=payload.recipient_address,
        amount=payload.amount,
        mint=get_settings().solana_usdc_mint,
        reference=reference,
    )

    payment = Payment(
        **payload.model_dump(),
        merchant_id=merchant_id,
        reference=reference,
        payment_url=payment_url,
    )

    db.add(payment)
    await db.commit()
    await db.refresh(payment)

    return PaymentResponse(
        id=payment.id,
        amount=payment.amount,
        currency=payload.currency,
        network=payload.network,
        recipient_address=payment.recipient_address,
        status="pending",
        reference=payment.reference,
        payment_url=payment.payment_url,
    )
