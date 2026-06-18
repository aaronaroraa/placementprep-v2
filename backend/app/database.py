from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool
from typing import AsyncGenerator
from app.config import settings

# NullPool lets Supabase's PgBouncer (transaction pooler) handle connection pooling.
# SQLAlchemy creates a fresh asyncpg connection per request — no prepared statement conflicts.
engine = create_async_engine(
    settings.DATABASE_URL,
    connect_args={"ssl": False},
    poolclass=NullPool,
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
