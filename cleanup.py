#!/usr/bin/env python3
"""
Скрипт для очищення кешу та підготовки до перезапуску
"""

import os
import shutil
import glob

def cleanup_cache():
    """Очистити Python кеш файли"""
    print("🧹 Очищення Python кешу...")
    
    # Видалити __pycache__ директорії
    for root, dirs, files in os.walk('.'):
        for dir_name in dirs:
            if dir_name == '__pycache__':
                cache_path = os.path.join(root, dir_name)
                print(f"  Видаляю: {cache_path}")
                shutil.rmtree(cache_path, ignore_errors=True)
    
    # Видалити .pyc файли
    pyc_files = glob.glob('**/*.pyc', recursive=True)
    for pyc_file in pyc_files:
        print(f"  Видаляю: {pyc_file}")
        os.remove(pyc_file)
    
    print("✅ Python кеш очищено")

def cleanup_logs():
    """Очистити лог файли"""
    print("Cleaning logs...")
    
    log_patterns = ['logs/*.log', '*.log', 'logs/*.txt']
    for pattern in log_patterns:
        log_files = glob.glob(pattern)
        for log_file in log_files:
            try:
                print(f"  Removing: {log_file}")
                os.remove(log_file)
            except PermissionError:
                print(f"  Skipping (file in use): {log_file}")
            except Exception as e:
                print(f"  Error removing {log_file}: {e}")
    
    print("Logs cleanup completed")

def cleanup_temp_files():
    """Очистити тимчасові файли"""
    print("🧹 Очищення тимчасових файлів...")
    
    temp_patterns = [
        '*.tmp', '*.temp', '.DS_Store', 'Thumbs.db',
        'test_integration.py', 'test_comprehensive.py'
    ]
    
    for pattern in temp_patterns:
        temp_files = glob.glob(pattern)
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                print(f"  Видаляю: {temp_file}")
                os.remove(temp_file)
    
    print("✅ Тимчасові файли очищено")

def create_directories():
    """Створити необхідні директорії"""
    print("📁 Створення необхідних директорій...")
    
    directories = ['logs', 'temp', 'uploads']
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"  Створено: {directory}/")
    
    print("✅ Директорії створено")

def check_env_file():
    """Перевірити наявність .env файлу"""
    print("🔍 Перевірка конфігурації...")
    
    if not os.path.exists('.env'):
        print("❌ Файл .env не знайдено!")
        print("   Створіть .env файл на основі .env.example")
        return False
    
    # Перевірити основні змінні
    required_vars = ['GITHUB_TOKEN', 'OPENAI_API_KEY', 'SECRET_KEY']
    missing_vars = []
    
    try:
        with open('.env', 'r') as f:
            env_content = f.read()
            
        for var in required_vars:
            if f"{var}=" not in env_content or f"{var}=\n" in env_content or f"{var}=" == env_content.split(f"{var}=")[1].split('\n')[0]:
                missing_vars.append(var)
        
        if missing_vars:
            print(f"⚠️  Не заповнені змінні в .env: {', '.join(missing_vars)}")
            return False
        
        print("✅ Конфігурація .env в порядку")
        return True
        
    except Exception as e:
        print(f"❌ Помилка читання .env: {e}")
        return False

def main():
    print("🚀 Підготовка GitHub PR Automation System до запуску\n")
    
    cleanup_cache()
    cleanup_logs()
    cleanup_temp_files()
    create_directories()
    
    print("\n" + "="*50)
    env_ok = check_env_file()
    
    if env_ok:
        print("\n✅ Система готова до запуску!")
        print("\nДля запуску виконайте:")
        print("  python main.py")
        print("\nАбо для тестування:")
        print("  python -m pytest tests/ -v")
    else:
        print("\n❌ Потрібно налаштувати .env файл перед запуском")
        print("\nІнструкції:")
        print("1. Відредагуйте .env файл")
        print("2. Додайте ваш GitHub token")
        print("3. Додайте ваш OpenAI API key")
        print("4. Запустіть cleanup.py знову")

if __name__ == "__main__":
    main()