from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.public.v1.router import router as public_v1_router
from app.api.private.v1.router import router as private_v1_router
from app.db.init_db import init_db
from app.db.session import engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await engine.dispose()


app = FastAPI(
    title="Payment Platform API",
    lifespan=lifespan,
)

app.include_router(public_v1_router)
app.include_router(private_v1_router)
