import os
import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool
from app.main import app
from app.core.database import get_db, Base
from app.models.base import User

# Проверяем переменную окружения, если её нет — берем локальный адрес по умолчанию
TEST_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:password@db:5432/microblog"
)

# NullPool отключает кэширование соединений, что лечит InternalClientError
engine_test = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
async_session_test = async_sessionmaker(engine_test, expire_on_commit=False, class_=AsyncSession)

@pytest.fixture(scope="session")
def event_loop():
    """Создаем единый цикл событий на всю сессию тестов."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(autouse=True)
async def prepare_database():
    """Чистим базу перед каждым тестом."""
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine_test.dispose()

async def override_get_db():
    async with async_session_test() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest.fixture
async def test_user():
    async with async_session_test() as session:
        user = User(name="Test User", api_key="test_key")
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user
