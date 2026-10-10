import asyncio
import os
import sys

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.core.config import get_settings

settings = get_settings()
engine = create_async_engine(settings.DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def reduce_schemes():
    async with AsyncSessionLocal() as session:
        # Get 300 schemes to keep (mix of central and state)
        result = await session.execute(text("SELECT id FROM schemes LIMIT 300"))
        keep_ids = [row[0] for row in result.fetchall()]
        
        if len(keep_ids) == 0:
            print("No schemes found!")
            return
            
        print(f"Keeping {len(keep_ids)} schemes...")
        
        # Delete all other schemes
        keep_ids_str = ",".join(map(str, keep_ids))
        await session.execute(text(f"DELETE FROM schemes WHERE id NOT IN ({keep_ids_str})"))
        
        await session.commit()
        
        # Verify counts
        result = await session.execute(text("SELECT COUNT(*) FROM schemes"))
        total = result.scalar()
        
        result = await session.execute(text("SELECT COUNT(*) FROM schemes WHERE level = 'Central'"))
        central = result.scalar()
        
        result = await session.execute(text("SELECT COUNT(*) FROM schemes WHERE level = 'State'"))
        state = result.scalar()
        
        print(f"Total schemes remaining: {total}")
        print(f"Central schemes: {central}")
        print(f"State schemes: {state}")

if __name__ == "__main__":
    asyncio.run(reduce_schemes())
