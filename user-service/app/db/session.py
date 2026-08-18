from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.core.config import get_settings

settings = get_settings()
# SecretStr -> plain string for sqlalchemy
_db_url = settings.DB_URL.get_secret_value() if hasattr(settings.DB_URL, "get_secret_value") else str(settings.DB_URL)

engine = create_async_engine(
    _db_url,
    echo=False,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
