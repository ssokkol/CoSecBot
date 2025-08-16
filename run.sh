#!/bin/bash

echo "Запуск Discord бота..."
echo

# Проверяем наличие Python
if ! command -v python3 &> /dev/null; then
    echo "Ошибка: Python 3 не найден!"
    echo "Установите Python 3.8+ и попробуйте снова."
    exit 1
fi

# Проверяем наличие виртуального окружения
if [ ! -d "venv" ]; then
    echo "Создание виртуального окружения..."
    python3 -m venv venv
fi

# Активируем виртуальное окружение
echo "Активация виртуального окружения..."
source venv/bin/activate

# Устанавливаем зависимости
echo "Установка зависимостей..."
pip install -r requirements_refactored.txt

# Проверяем наличие .env файла
if [ ! -f ".env" ]; then
    echo "Создание .env файла..."
    cp env.example .env
    echo
    echo "ВНИМАНИЕ: Создан файл .env на основе env.example"
    echo "Отредактируйте .env файл, добавив ваш Discord токен!"
    echo
    read -p "Нажмите Enter для продолжения..."
fi

# Запускаем бота
echo "Запуск бота..."
python main_refactored.py
