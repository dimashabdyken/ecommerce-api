from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sesstionmaker,
    AsyncSession,
)
from app.core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=True)

AsyncSessionLocal = async_sesstionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)
