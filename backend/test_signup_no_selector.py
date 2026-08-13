import asyncio
from app.core.database import async_session_factory, init_db
from app.services.auth_service import AuthService
from app.schemas.auth import SignupRequest

async def run():
    print("Starting DB test WITHOUT selector loop")
    await init_db()
    async with async_session_factory() as db:
        print("Created service")
        service = AuthService(db)
        req = SignupRequest(email='dbtest999@example.com', password='Password123!', full_name='Test')
        try:
            print("Calling signup")
            res = await service.signup(req)
            print("Signup returned", res)
            await db.commit()
            print('Success')
        except Exception as e:
            import traceback
            traceback.print_exc()

asyncio.run(run())
