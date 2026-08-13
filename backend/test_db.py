import asyncio
import asyncpg
import sys

async def main():
    try:
        print("Trying to connect...")
        conn = await asyncpg.connect("postgresql://govscheme:govscheme123@127.0.0.1:5432/govscheme")
        print("CONNECTED!")
        await conn.close()
    except Exception as e:
        print("ERROR:", repr(e))

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
asyncio.run(main())
