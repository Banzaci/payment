from fastapi import APIRouter
from app.api.private.v1 import health, payments

router = APIRouter(prefix="/api/private/v1")

router.include_router(health.router)
router.include_router(payments.router)
