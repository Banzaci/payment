from app.db.base import Base
from app.db.session import engine
from app.models.merchant import Merchant
from app.models.payment import Payment

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)