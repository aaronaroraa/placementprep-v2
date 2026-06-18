import uuid
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool
from typing import AsyncGenerator
from app.config import settings

# Supabase's transaction pooler (PgBouncer on :6543) multiplexes server connections,
# which breaks asyncpg prepared statements. We must:
#   - NullPool: let PgBouncer own pooling; a fresh connection per request
#   - statement_cache_size=0: disable asyncpg's own statement cache
#   - prepared_statement_cache_size=0: disable SQLAlchemy's dialect cache (source of
#     the "__asyncpg_stmt_N__ already exists" collisions)
#   - prepared_statement_name_func: unique names so multiplexed backends never collide
# The two prepared_statement_* args are SQLAlchemy asyncpg-dialect params and are
# consumed by the dialect before asyncpg.connect() is called.
engine = create_async_engine(
    settings.DATABASE_URL,
    connect_args={
        "ssl": False,
        "statement_cache_size": 0,
        "prepared_statement_cache_size": 0,
        "prepared_statement_name_func": lambda: f"__asyncpg_{uuid.uuid4()}__",
    },
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
