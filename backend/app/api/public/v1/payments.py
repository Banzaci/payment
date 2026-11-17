
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.payment import Payment

router = APIRouter(prefix="/payments", tags=["Public Payments"])

@router.get("/{payment_id}")
async def get_public_payment(
    payment_id: str,
    db: AsyncSession = Depends(get_db),
):
    payment = await db.get(Payment, payment_id)

    if payment is None:
        raise HTTPException(
            status_code=404,
            detail="Payment not found",
        )

    return {
        "id": payment.id,
        "amount": str(payment.amount),
        "currency": payment.currency,
        "network": payment.network,
        "status": payment.status,
        "payment_url": payment.payment_url,
    }
