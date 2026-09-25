import asyncio
from app.db.session import engine
from app.db.base import Base
import app.models

async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("All Phase 3 tables created successfully!")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
