
import hmac
from app.core.config import get_settings

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.merchant import MerchantCreate, MerchantResponse
from app.services.merchant_service import create_merchant

router = APIRouter(prefix="/merchants", tags=["Merchants"])


def require_admin_key(
    x_admin_key: str | None = Header(default=None),
):
    admin_key = get_settings().payment_admin_key

    if (
        not admin_key
        or not x_admin_key
        or not hmac.compare_digest(x_admin_key, admin_key)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin key",
        )


@router.post("", response_model=MerchantResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin_key)])
async def create_merchant_endpoint(
    payload: MerchantCreate,
    db: AsyncSession = Depends(get_db),
):
    merchant, api_key = await create_merchant(
        db=db,
        name=payload.name,
        default_currency=payload.default_currency,
        enabled_payment_methods=payload.enabled_payment_methods,
    )

    return MerchantResponse(
        id=merchant.id,
        name=merchant.name,
        default_currency=merchant.default_currency,
        enabled_payment_methods=merchant.enabled_payment_methods,
        api_key=api_key,
    )
