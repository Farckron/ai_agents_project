#!/usr/bin/env python3
"""
Простий тест системи - покроково показує що відбувається
"""

import requests
import json
import time

def test_step_by_step():
    """Покроковий тест з поясненнями"""
    
    print("🧪 ПОКРОКОВИЙ ТЕСТ СИСТЕМИ")
    print("=" * 50)
    
    base_url = "http://localhost:5000"
    
    # Крок 1: Перевіряємо чи сервер працює
    print("\n📡 КРОК 1: Перевіряємо сервер...")
    try:
        response = requests.get(f"{base_url}/api/status", timeout=5)
        if response.status_code == 200:
            print("✅ Сервер працює!")
            data = response.json()
            print(f"   GitHub налаштовано: {data.get('github', {}).get('token_configured', False)}")
            print(f"   OpenAI налаштовано: {data.get('openai', {}).get('api_key_configured', False)}")
        else:
            print(f"❌ Сервер відповів з помилкою: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Сервер недоступний: {e}")
        print("   Запустіть сервер: python main.py")
        return False
    
    # Крок 2: Тестуємо аналіз репозиторію
    print("\n🔍 КРОК 2: Аналізуємо репозиторій...")
    try:
        repo_url = "https://github.com/Farckron/SimpleCalc"
        response = requests.get(
            f"{base_url}/api/repository/analyze",
            params={"repo_url": repo_url},
            timeout=30
        )
        
        if response.status_code == 200:
            print("✅ Репозиторій проаналізовано!")
            data = response.json()
            print(f"   Статус: {data.get('status', 'unknown')}")
            if 'repository_info' in data:
                print(f"   Репозиторій доступний: Так")
        else:
            print(f"⚠️  Помилка аналізу: {response.status_code}")
            print(f"   Відповідь: {response.text[:200]}")
    except Exception as e:
        print(f"❌ Помилка аналізу: {e}")
    
    # Крок 3: Створюємо простий файл (без PR)
    print("\n📝 КРОК 3: Тестуємо обробку запиту...")
    try:
        request_data = {
            "request": "Проаналізуй цей репозиторій та дай короткі рекомендації",
            "repo_url": "https://github.com/Farckron/SimpleCalc",
            "create_pr": False  # Не створюємо PR, тільки аналізуємо
        }
        
        response = requests.post(
            f"{base_url}/api/process_request",
            headers={"Content-Type": "application/json"},
            json=request_data,
            timeout=60
        )
        
        if response.status_code == 200:
            print("✅ Запит оброблено!")
            data = response.json()
            print(f"   Статус: {data.get('status', 'unknown')}")
            print(f"   Тип обробки: {data.get('processing_type', 'unknown')}")
            
            if 'analysis' in data:
                analysis = data['analysis']
                print(f"   Аналіз виконано: {analysis.get('status', 'unknown')}")
                if 'recommendations' in analysis:
                    recs = analysis['recommendations']
                    print(f"   Рекомендацій: {len(recs) if isinstance(recs, list) else 'N/A'}")
        else:
            print(f"⚠️  Помилка обробки: {response.status_code}")
            print(f"   Відповідь: {response.text[:300]}")
    except Exception as e:
        print(f"❌ Помилка запиту: {e}")
    
    # Крок 4: Спробуємо створити простий PR
    print("\n🚀 КРОК 4: Створюємо простий PR...")
    try:
        pr_data = {
            "user_request": "Додай файл hello.py з простим print('Hello, World!')",
            "repo_url": "https://github.com/Farckron/SimpleCalc.git",
            "options": {
                "pr_title": "Add hello.py file",
                "pr_description": "Simple hello world file for testing",
                "branch_name": "feature/hello-world"
            }
        }
        
        print("   Відправляємо запит на створення PR...")
        response = requests.post(
            f"{base_url}/api/pr/create",
            headers={"Content-Type": "application/json"},
            json=pr_data,
            timeout=120
        )
        
        print(f"   Відповідь сервера: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ PR запит прийнято!")
            print(f"   Request ID: {data.get('request_id', 'N/A')}")
            print(f"   Статус: {data.get('status', 'unknown')}")
            print(f"   Повідомлення: {data.get('message', 'N/A')}")
            
            if 'workflow_id' in data:
                print(f"   Workflow ID: {data['workflow_id']}")
            
            if data.get('status') == 'success' and 'pr_url' in data:
                print(f"🎉 PR створено: {data['pr_url']}")
            elif data.get('status') == 'error':
                print(f"❌ Помилка створення PR: {data.get('message', 'Unknown error')}")
        else:
            print(f"❌ Помилка PR: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Деталі: {error_data}")
            except:
                print(f"   Raw error: {response.text[:300]}")
                
    except Exception as e:
        print(f"❌ Помилка створення PR: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 ТЕСТ ЗАВЕРШЕНО!")
    print("\nЩо означають результати:")
    print("✅ - Функція працює правильно")
    print("⚠️  - Функція працює з попередженнями") 
    print("❌ - Функція не працює")
    print("\nЯкщо PR створено, перевірте:")
    print("https://github.com/Farckron/SimpleCalc/pulls")
    
    return True

if __name__ == "__main__":
    test_step_by_step()