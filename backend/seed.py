import asyncio
from app.core.database import async_session
from app.models.user import User

async def seed():
    async with async_session() as session:
        user = User(name='Ivan Dev', api_key='test')
        session.add(user)
        await session.commit()
        print('--- User created successfully! ---')

if __name__ == '__main__':
    asyncio.run(seed())
