from typing import AsyncGenerator
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from app.core.config import settings
from app.core.logging import logger

db_url = settings.get_database_url()

# Configure engine options based on dialect
engine_kwargs = {
    "echo": False,
    "future": True,
}

if "sqlite" in db_url:
    # SQLite does not support PostgreSQL connection pooling parameters
    engine_kwargs["connect_args"] = {"check_same_thread": False, "timeout": 30}
else:
    # Production PostgreSQL connection pooling parameters
    engine_kwargs.update({
        "pool_pre_ping": True,
        "pool_size": settings.DB_POOL_SIZE,
        "max_overflow": settings.DB_MAX_OVERFLOW,
        "pool_recycle": settings.DB_POOL_RECYCLE,
        "pool_timeout": settings.DB_POOL_TIMEOUT,
        "connect_args": {
            "server_settings": {
                "statement_timeout": str(settings.DB_STATEMENT_TIMEOUT),
                "idle_in_transaction_session_timeout": str(settings.DB_IDLE_TIMEOUT),
            }
        },
    })

engine: AsyncEngine = create_async_engine(db_url, **engine_kwargs)


def get_db_pool_status() -> dict:
    """Returns runtime connection pool utilization metrics for observability."""
    try:
        pool = engine.sync_engine.pool
        return {
            "size": pool.size() if hasattr(pool, "size") else 0,
            "checked_in": pool.checkedin() if hasattr(pool, "checkedin") else 0,
            "checked_out": pool.checkedout() if hasattr(pool, "checkedout") else 0,
            "overflow": pool.overflow() if hasattr(pool, "overflow") else 0,
        }
    except Exception:
        return {"size": 0, "checked_in": 0, "checked_out": 0, "overflow": 0}


if "sqlite" in db_url:
    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency yielding an async database session with automatic transaction management.
    Rolls back automatically upon uncaught exceptions.
    """
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_database_health() -> bool:
    """
    Check if the database connection is alive and healthy.
    Used by /ready endpoint.
    """
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            return result.scalar() == 1
    except Exception as exc:
        logger.error(f"Database health check failed: {exc}", exc_info=False)
        return False
