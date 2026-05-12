import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from app.api import tweets, users
from app.core.database import engine, Base
from app.models.base import User, Tweet, Media


# 1. Новый способ управления жизненным циклом (Lifespan)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Код, который выполняется ПРИ СТАРТЕ
    async with engine.begin() as conn:
        # Создаем таблицы в БД
        await conn.run_sync(Base.metadata.create_all)

    # Создаем папку для загрузки медиа
    os.makedirs("static/uploads", exist_ok=True)

    yield  # Здесь приложение РАБОТАЕТ

    # Код, который выполняется ПРИ ВЫКЛЮЧЕНИИ
    await engine.dispose()


# Передаем lifespan в инициализацию FastAPI
app = FastAPI(title="Microblog API", lifespan=lifespan)


# 2. Глобальная обработка ошибок
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "result": False,
            "error_type": type(exc).__name__,
            "error_message": str(exc)
        }
    )


# 3. Роутеры
app.include_router(tweets.router, prefix="/api")
app.include_router(users.router, prefix="/api")

# 4. Настройка путей к фронтенду
# В Docker рабочая директория /app
DIST_DIR = "/app/dist"
if not os.path.exists(DIST_DIR):
    # Запасной вариант для локального запуска без Docker
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DIST_DIR = os.path.join(BASE_DIR, "dist")

# Монтируем статику бэкенда (аватарки, загрузки)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Монтируем CSS и JS из папки dist (если они существуют)
for folder in ["css", "js"]:
    path = os.path.join(DIST_DIR, folder)
    if os.path.exists(path):
        app.mount(f"/{folder}", StaticFiles(directory=path), name=folder)


# 5. Раздача фронтенда (SPA)
@app.get("/")
@app.get("/{path:path}")
async def serve_spa(path: str = None):
    index_path = os.path.join(DIST_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)

    return JSONResponse({
        "result": False,
        "error_message": f"Файлы фронтенда не найдены по пути: {index_path}"
    })
