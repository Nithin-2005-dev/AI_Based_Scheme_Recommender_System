"""Database inspection script."""
import asyncio
import aiosqlite

async def check():
    async with aiosqlite.connect("govscheme.db") as db:
        cursor = await db.execute("SELECT COUNT(*) FROM schemes WHERE is_active=1")
        count = (await cursor.fetchone())[0]
        print(f"Total active schemes: {count}")

        cursor = await db.execute("SELECT level, COUNT(*) FROM schemes WHERE is_active=1 GROUP BY level")
        levels = await cursor.fetchall()
        for l in levels:
            print(f"  {l[0]}: {l[1]}")

        cursor = await db.execute("SELECT DISTINCT scheme_category FROM schemes LIMIT 10")
        cats = await cursor.fetchall()
        print("Sample scheme_categories:", [c[0] for c in cats])

        cursor = await db.execute("SELECT DISTINCT target_category FROM schemes WHERE target_category IS NOT NULL LIMIT 20")
        target_cats = await cursor.fetchall()
        print("Sample target_categories:", [c[0] for c in target_cats])

        cursor = await db.execute("SELECT DISTINCT target_state FROM schemes WHERE target_state IS NOT NULL LIMIT 20")
        target_states = await cursor.fetchall()
        print("Sample target_states:", [c[0] for c in target_states])

asyncio.run(check())
