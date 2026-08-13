import asyncio, httpx
async def run():
    async with httpx.AsyncClient(base_url='http://127.0.0.1:8000') as client:
        res = await client.post('/api/v1/auth/signup', json={'email': 'testuser9@example.com', 'password': 'Password123!', 'full_name': 'Test User', 'state': 'Maharashtra'})
        print(res.status_code, res.text)
asyncio.run(run())
