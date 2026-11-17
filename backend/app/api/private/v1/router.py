from fastapi import APIRouter
from app.api.private.v1 import health, payments, merchants

router = APIRouter(prefix="/api/private/v1")

router.include_router(health.router)
router.include_router(payments.router)
router.include_router(merchants.router)
