FROM python:3.11-slim

WORKDIR /app

# Install system dependencies and locales
RUN apt-get update && apt-get install -y \
    fonts-liberation \
    libfreetype6-dev \
    libjpeg-dev \
    zlib1g-dev \
    locales \
    && rm -rf /var/lib/apt/lists/*

# Generate and set up Russian locale
RUN sed -i '/ru_RU.UTF-8/s/^# //g' /etc/locale.gen && \
    locale-gen && \
    update-locale LANG=ru_RU.UTF-8

ENV LANG ru_RU.UTF-8
ENV LANGUAGE ru_RU:ru
ENV LC_ALL ru_RU.UTF-8

# Copy and install Python dependencies first
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories and set permissions
RUN mkdir -p /app/logs /app/assets/avatars /app/assets/badges /app/assets/fonts /app/assets/templates \
    && chmod -R 777 /app

# Copy the rest of the application
COPY . .

# Ensure database directory is writable
RUN touch database.db && chmod 666 database.db

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the bot
CMD ["python", "main.py"]
