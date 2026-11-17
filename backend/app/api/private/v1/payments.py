
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

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
