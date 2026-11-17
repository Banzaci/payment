from fastapi import APIRouter
from app.api.public.v1 import health

router = APIRouter(prefix="/api/public/v1")

router.include_router(health.router)