# Используем официальный Python образ
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libjpeg-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libopenjp2-7-dev \
    libtiff5-dev \
    libwebp-dev \
    libharfbuzz-dev \
    libfribidi-dev \
    libxcb1-dev \
    && rm -rf /var/lib/apt/lists/*

# Копируем файлы зависимостей
COPY requirements_refactored.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements_refactored.txt

# Копируем исходный код
COPY src/ ./src/
COPY main_refactored.py .

# Копируем ресурсы в новую структуру
COPY assets/ ./assets/

# Создаем пользователя для безопасности
RUN useradd --create-home --shell /bin/bash bot
RUN chown -R bot:bot /app
USER bot

# Открываем порт (если понадобится для веб-интерфейса)
EXPOSE 8000

# Команда по умолчанию
CMD ["python", "main_refactored.py"]
