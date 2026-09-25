import asyncio
import os
from typing import AsyncGenerator
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Set testing environment variables before importing app
os.environ["APP_ENV"] = "testing"
os.environ["DEBUG"] = "true"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only-at-least-32-chars-long"
os.environ["RATE_LIMIT_API_PER_MINUTE"] = "10000"


from app.core.config import settings
settings.RATE_LIMIT_API_PER_MINUTE = 10000
from app.db.base import Base

from app.db.session import get_db
import app.models  # Ensures all Phase 1, 2, and 3 tables are in Base.metadata
from app.main import app

from sqlalchemy.pool import StaticPool

# Create in-memory SQLite async engine for tests
test_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop per test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
async def prepare_database():
    """Create all tables before each test and drop them after, resetting rate limits."""
    from app.core.redis import redis_manager
    redis_manager._fallback_store.clear()
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    redis_manager._fallback_store.clear()



async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Override dependency in FastAPI app
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield a database session bound to the active test database."""
    async with TestSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()



@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Provide an async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


@pytest.fixture
async def async_client(client: AsyncClient) -> AsyncClient:
    return client


@pytest.fixture
async def auth_headers(client: AsyncClient) -> dict:
    import time
    unique_suffix = int(time.time() * 1000)
    reg_res = await client.post(
        "/api/v1/auth/register",
        json={
            "organization_name": f"Enermax Org A {unique_suffix}",
            "full_name": "Operator Alpha",
            "email": f"operator-a-{unique_suffix}@enermaxsolar.com",
            "password": "Password123!",
        },
    )
    assert reg_res.status_code == 200, f"Registration failed: {reg_res.text}"
    token = reg_res.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def other_tenant_auth_headers(client: AsyncClient) -> dict:
    import time
    unique_suffix = int(time.time() * 1000) + 1
    reg_res = await client.post(
        "/api/v1/auth/register",
        json={
            "organization_name": f"Enermax Org B {unique_suffix}",
            "full_name": "Operator Beta",
            "email": f"operator-b-{unique_suffix}@enermaxsolar.com",
            "password": "Password123!",
        },
    )
    assert reg_res.status_code == 200, f"Registration failed: {reg_res.text}"
    token = reg_res.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}

