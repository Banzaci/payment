
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.payment_verification_service import confirm_payment
from app.core.merchant_auth import get_current_merchant
from app.db.session import get_db
from app.models.merchant import Merchant
from app.schemas.payment import PaymentCreate, PaymentResponse
from app.services.payment_service import create_payment

router = APIRouter(prefix="/payments", tags=["Payments"])

@router.post(
    "",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_payment_endpoint(
    payload: PaymentCreate,
    merchant: Merchant = Depends(get_current_merchant),
    db: AsyncSession = Depends(get_db),
):
    return await create_payment(payload, db, merchant.id)



@router.post("/{payment_id}/verify")
async def verify_payment_endpoint(
    payment_id: str,
    merchant: Merchant = Depends(get_current_merchant),
    db: AsyncSession = Depends(get_db),
):
    payment = await confirm_payment(
        payment_id=payment_id,
        merchant_id=merchant.id,
        db=db,
    )

    if payment is None:
        raise HTTPException(
            status_code=404,
            detail="Payment not found",
        )

    return {
        "id": payment.id,
        "status": payment.status,
        "transaction_signature": payment.transaction_signature,
    }
