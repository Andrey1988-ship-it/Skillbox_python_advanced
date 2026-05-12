FROM python:3.10-slim

WORKDIR /app

# Установка зависимостей для Postgres
RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

# Копируем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем ВЕСЬ проект (включая папку dist и папку app)
COPY . .

# Создаем папку для загрузки медиа
RUN mkdir -p static/uploads

# Запуск сервера
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
