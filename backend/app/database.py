from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from typing import AsyncGenerator
from app.config import settings

# statement_cache_size=0 is required when using Supabase's PgBouncer transaction
# pooler — prepared statements are not supported in transaction mode.
engine = create_async_engine(
    settings.DATABASE_URL,
    connect_args={"statement_cache_size": 0, "ssl": "require"},
    pool_size=5, max_overflow=5, pool_pre_ping=True,
    echo=settings.APP_ENV == "development",
)
AsyncSessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession,
    expire_on_commit=False, autoflush=False, autocommit=False,
)

class Base(DeclarativeBase):
    pass

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
