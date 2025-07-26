#!/usr/bin/env python3
"""
Скрипт для створення PR з міні Python калькулятором
"""

import requests
import json
import time
import os
from dotenv import load_dotenv

load_dotenv()

def wait_for_server(url="http://localhost:5000", max_attempts=30):
    """Чекаємо поки сервер запуститься"""
    print("Чекаємо запуску Flask сервера...")
    
    for attempt in range(max_attempts):
        try:
            response = requests.get(f"{url}/api/status", timeout=2)
            if response.status_code == 200:
                print("✅ Сервер запущений!")
                return True
        except requests.exceptions.RequestException:
            pass
        
        print(f"Спроба {attempt + 1}/{max_attempts}...")
        time.sleep(2)
    
    print("❌ Сервер не запустився за відведений час")
    return False

def create_calculator_pr():
    """Створити PR з Python калькулятором"""
    
    # Перевіряємо чи сервер запущений
    if not wait_for_server():
        print("Запустіть сервер командою: python run.py")
        return
    
    # Дані для створення PR
    pr_request = {
        "user_request": "Створити міні Python калькулятор в одному файлі з базовими операціями (+, -, *, /) та інтерактивним меню",
        "repo_url": f"https://github.com/{os.getenv('GITHUB_OWNER')}/{os.getenv('GITHUB_REPO')}.git",
        "options": {
            "pr_title": "Add Python Mini Calculator",
            "pr_description": """# Python Mini Calculator

Додано простий інтерактивний калькулятор з наступними можливостями:

## Функції:
- ✅ Базові арифметичні операції (+, -, *, /)
- ✅ Інтерактивне меню
- ✅ Обробка помилок (ділення на нуль, некоректний ввід)
- ✅ Можливість виходу з програми
- ✅ Зручний користувацький інтерфейс

## Використання:
```bash
python calculator.py
```

Калькулятор запитає два числа та операцію, виконає обчислення та покаже результат.

---
*Створено автоматично AI Agent System*""",
            "base_branch": "main"
        }
    }
    
    print("🚀 Створюємо PR з Python калькулятором...")
    print(f"Репозиторій: {pr_request['repo_url']}")
    print("-" * 50)
    
    try:
        # Відправляємо запит на створення PR
        response = requests.post(
            "http://localhost:5000/api/pr/create",
            headers={"Content-Type": "application/json"},
            json=pr_request,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ PR створено успішно!")
            print(f"Request ID: {result.get('request_id', 'N/A')}")
            
            if 'workflow_id' in result:
                print(f"Workflow ID: {result['workflow_id']}")
            
            if 'pr_url' in result:
                print(f"🔗 PR URL: {result['pr_url']}")
            
            print(f"Статус: {result.get('status', 'unknown')}")
            print(f"Повідомлення: {result.get('message', 'N/A')}")
            
            # Якщо є деталі workflow
            if 'workflow_details' in result:
                details = result['workflow_details']
                print(f"Назва гілки: {details.get('branch_name', 'N/A')}")
                print(f"Заголовок PR: {details.get('pr_title', 'N/A')}")
            
        else:
            print(f"❌ Помилка створення PR: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Деталі помилки: {error_data}")
            except:
                print(f"Текст помилки: {response.text}")
    
    except requests.exceptions.Timeout:
        print("❌ Timeout - запит зайняв занадто багато часу")
    except requests.exceptions.ConnectionError:
        print("❌ Не вдалося підключитися до сервера")
        print("Переконайтеся що Flask сервер запущений: python run.py")
    except Exception as e:
        print(f"❌ Неочікувана помилка: {e}")

def check_pr_status(request_id):
    """Перевірити статус PR"""
    try:
        response = requests.get(f"http://localhost:5000/api/pr/status/{request_id}")
        if response.status_code == 200:
            result = response.json()
            print(f"Статус PR: {result}")
        else:
            print(f"Помилка отримання статусу: {response.status_code}")
    except Exception as e:
        print(f"Помилка перевірки статусу: {e}")

if __name__ == "__main__":
    print("🧮 Створення PR з Python калькулятором")
    print("=" * 50)
    
    create_calculator_pr()
    
    print("\n" + "=" * 50)
    print("Готово! Перевірте ваш GitHub репозиторій на наявність нового PR.")