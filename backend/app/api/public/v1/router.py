from fastapi import APIRouter
from app.api.public.v1 import health, payments

router = APIRouter(prefix="/api/public/v1")

router.include_router(health.router)
router.include_router(payments.router)