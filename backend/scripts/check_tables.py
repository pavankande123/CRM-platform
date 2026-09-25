import asyncio
import app.models
from tests.conftest import test_engine, TestSessionLocal, Base
from sqlalchemy import text

async def f():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with TestSessionLocal() as db:
        r = await db.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        print('FOUND TABLES IN test_engine:', [x[0] for x in r.fetchall()])

if __name__ == "__main__":
    asyncio.run(f())
