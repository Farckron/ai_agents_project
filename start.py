#!/usr/bin/env python3
"""
Скрипт для запуску GitHub PR Automation System
"""

import os
import sys
import subprocess
import time

def check_dependencies():
    """Перевірити залежності"""
    print("🔍 Перевірка залежностей...")
    
    required_packages = [
        'flask', 'requests', 'python-dotenv', 
        'PyGithub', 'openai', 'pytest'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Відсутні пакети: {', '.join(missing_packages)}")
        print("Встановлюю відсутні пакети...")
        
        for package in missing_packages:
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
                print(f"✅ Встановлено: {package}")
            except subprocess.CalledProcessError:
                print(f"❌ Не вдалося встановити: {package}")
                return False
    
    print("✅ Всі залежності встановлені")
    return True

def check_configuration():
    """Перевірити конфігурацію"""
    print("🔍 Перевірка конфігурації...")
    
    if not os.path.exists('.env'):
        print("❌ Файл .env не знайдено!")
        return False
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        github_token = os.getenv('GITHUB_TOKEN')
        openai_key = os.getenv('OPENAI_API_KEY')
        
        if not github_token:
            print("❌ GITHUB_TOKEN не налаштовано в .env")
            return False
            
        if not openai_key:
            print("⚠️  OPENAI_API_KEY не налаштовано (деякі функції можуть не працювати)")
        
        print("✅ Конфігурація в порядку")
        return True
        
    except Exception as e:
        print(f"❌ Помилка конфігурації: {e}")
        return False

def run_tests():
    """Запустити швидкі тести"""
    print("🧪 Запуск швидких тестів...")
    
    try:
        # Запустити базові тести
        result = subprocess.run([
            sys.executable, '-c', 
            """
from agents.pr_manager import PRManager
from agents.github_manager import GitHubManager
from utils.git_operations import GitOperations
print('[OK] All components import successfully')

pm = PRManager()
gm = GitHubManager()
go = GitOperations()
print('[OK] All components initialize successfully')

# Test basic functionality
branch_name = pm.generate_branch_name('test feature')
assert branch_name, 'Branch name should be generated'
print(f'[OK] Branch name generation works: {branch_name}')

is_valid, _ = go.validate_branch_name('valid-branch-name')
assert is_valid, 'Valid branch name should pass validation'
print('[OK] Branch name validation works')
            """
        ], capture_output=True, text=True, timeout=30, encoding='utf-8')
        
        if result.returncode == 0:
            print("✅ Базові тести пройшли успішно")
            return True
        else:
            print(f"❌ Тести не пройшли: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Тести зависли (timeout)")
        return False
    except Exception as e:
        print(f"❌ Помилка запуску тестів: {e}")
        return False

def start_server():
    """Запустити Flask сервер"""
    print("🚀 Запуск Flask сервера...")
    
    try:
        # Встановити змінні середовища
        os.environ['FLASK_APP'] = 'main.py'
        os.environ['FLASK_ENV'] = 'development'
        
        print("Сервер запускається на http://localhost:5000")
        print("Натисніть Ctrl+C для зупинки")
        print("-" * 50)
        
        # Запустити Flask
        subprocess.run([sys.executable, 'main.py'])
        
    except KeyboardInterrupt:
        print("\n🛑 Сервер зупинено користувачем")
    except Exception as e:
        print(f"❌ Помилка запуску сервера: {e}")

def main():
    print("🚀 GitHub PR Automation System - Запуск\n")
    
    # Перевірити залежності
    if not check_dependencies():
        print("❌ Не вдалося встановити залежності")
        return
    
    # Перевірити конфігурацію
    if not check_configuration():
        print("❌ Конфігурація не налаштована")
        print("\nІнструкції:")
        print("1. Створіть .env файл на основі .env.example")
        print("2. Додайте ваш GitHub token")
        print("3. Додайте ваш OpenAI API key (опціонально)")
        return
    
    # Запустити тести
    if not run_tests():
        print("❌ Базові тести не пройшли")
        response = input("Продовжити запуск? (y/N): ")
        if response.lower() != 'y':
            return
    
    print("\n" + "="*50)
    print("✅ Система готова до роботи!")
    print("="*50)
    
    # Запустити сервер
    start_server()

if __name__ == "__main__":
    main()