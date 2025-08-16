@echo off
echo Запуск Discord бота...
echo.

REM Проверяем наличие Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Ошибка: Python не найден!
    echo Установите Python 3.8+ и попробуйте снова.
    pause
    exit /b 1
)

REM Проверяем наличие виртуального окружения
if not exist "venv" (
    echo Создание виртуального окружения...
    python -m venv venv
)

REM Активируем виртуальное окружение
echo Активация виртуального окружения...
call venv\Scripts\activate.bat

REM Устанавливаем зависимости
echo Установка зависимостей...
pip install -r requirements_refactored.txt

REM Проверяем наличие .env файла
if not exist ".env" (
    echo Создание .env файла...
    copy env.example .env
    echo.
    echo ВНИМАНИЕ: Создан файл .env на основе env.example
    echo Отредактируйте .env файл, добавив ваш Discord токен!
    echo.
    pause
)

REM Запускаем бота
echo Запуск бота...
python main_refactored.py

pause
