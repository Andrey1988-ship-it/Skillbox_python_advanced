import os

class Settings:
    PROJECT_NAME: str = "Microblog API"
    # По умолчанию для локального запуска, переопределится в Docker
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:password@localhost:5432/microblog"
    )

settings = Settings()
