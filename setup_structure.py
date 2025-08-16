#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для настройки новой структуры папок
Автоматически перемещает файлы в соответствующие папки assets/
"""

import os
import shutil
import sys

def create_directory_structure():
    """Создает новую структуру папок"""
    directories = [
        'assets',
        'assets/templates',
        'assets/fonts', 
        'assets/badges',
        'assets/avatars',
        'data',
        'logs'
    ]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"✓ Создана папка: {directory}")
        else:
            print(f"✓ Папка уже существует: {directory}")

def move_files():
    """Перемещает файлы в соответствующие папки"""
    
    # Перемещение шаблонов (PNG файлы)
    png_files = [f for f in os.listdir('.') if f.endswith('.png') and 'template' in f.lower()]
    for file in png_files:
        if os.path.exists(file):
            dest = os.path.join('assets', 'templates', file)
            shutil.move(file, dest)
            print(f"✓ Перемещен шаблон: {file} → {dest}")
    
    # Перемещение шрифтов (OTF файлы)
    otf_files = [f for f in os.listdir('.') if f.endswith('.otf')]
    for file in otf_files:
        if os.path.exists(file):
            dest = os.path.join('assets', 'fonts', file)
            shutil.move(file, dest)
            print(f"✓ Перемещен шрифт: {file} → {dest}")
    
    # Перемещение аватаров (JPG файлы)
    jpg_files = [f for f in os.listdir('.') if f.endswith('.jpg') and 'avatar' in f.lower()]
    for file in jpg_files:
        if os.path.exists(file):
            dest = os.path.join('assets', 'avatars', file)
            shutil.move(file, dest)
            print(f"✓ Перемещен аватар: {file} → {dest}")
    
    # Перемещение значков из папки badges
    if os.path.exists('badges'):
        badge_files = [f for f in os.listdir('badges') if f.endswith('.png')]
        for file in badge_files:
            src = os.path.join('badges', file)
            dest = os.path.join('assets', 'badges', file)
            shutil.move(src, dest)
            print(f"✓ Перемещен значок: {file} → {dest}")
        
        # Удаляем пустую папку badges
        try:
            os.rmdir('badges')
            print("✓ Удалена пустая папка badges")
        except:
            print("⚠ Папка badges не пуста, оставлена")

def cleanup_old_files():
    """Удаляет старые файлы, которые больше не нужны"""
    old_files = [
        'main.py', 'main2.py', 'db.py', 'config.py', 'config2.py',
        'requirements.txt', 'witch.db', 'hui.json', 'README_REFACTORED.md',
        'run.bat', 'run.sh', '.dockerignore'
    ]
    
    for file in old_files:
        if os.path.exists(file):
            try:
                os.remove(file)
                print(f"✓ Удален старый файл: {file}")
            except Exception as e:
                print(f"⚠ Не удалось удалить {file}: {e}")

def create_env_file():
    """Создает .env файл если его нет"""
    if not os.path.exists('.env'):
        if os.path.exists('env.example'):
            shutil.copy('env.example', '.env')
            print("✓ Создан файл .env на основе env.example")
            print("⚠ ВАЖНО: Отредактируйте .env файл, добавив ваш Discord токен!")
        else:
            print("⚠ Файл env.example не найден!")

def main():
    """Главная функция"""
    print("🚀 Настройка новой структуры проекта...")
    print("=" * 50)
    
    try:
        # Создаем структуру папок
        create_directory_structure()
        print()
        
        # Перемещаем файлы
        move_files()
        print()
        
        # Удаляем старые файлы
        cleanup_old_files()
        print()
        
        # Создаем .env файл
        create_env_file()
        print()
        
        print("✅ Настройка завершена успешно!")
        print()
        print("📋 Следующие шаги:")
        print("1. Отредактируйте файл .env, добавив ваш Discord токен")
        print("2. Убедитесь, что все ресурсы перемещены в папку assets/")
        print("3. Запустите бота: python main.py")
        print()
        print("🐳 Для Docker запуска:")
        print("docker-compose up --build")
        
    except Exception as e:
        print(f"❌ Ошибка при настройке: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
