#!/usr/bin/env python3
"""
Фінальний тест створення калькулятора через API
"""

import requests
import json
import time
import os
from dotenv import load_dotenv

load_dotenv()

def create_calculator_pr():
    """Створити PR з калькулятором"""
    
    print("🧮 Створення PR з Python калькулятором")
    print("=" * 50)
    
    # Перевіряємо чи сервер працює
    try:
        status_response = requests.get("http://localhost:5000/api/status", timeout=5)
        if status_response.status_code != 200:
            print("❌ Сервер не відповідає")
            return
        print("✅ Сервер працює")
    except:
        print("❌ Сервер недоступний. Запустіть: python main.py")
        return
    
    # Створюємо запит на калькулятор
    calculator_request = {
        "user_request": """Створи файл calculator.py з простим Python калькулятором:

Функції:
- add(a, b) - додавання
- subtract(a, b) - віднімання  
- multiply(a, b) - множення
- divide(a, b) - ділення з перевіркою на нуль
- main() - головне меню з циклом

Калькулятор повинен:
1. Показувати меню операцій
2. Запитувати два числа
3. Виконувати обрану операцію
4. Показувати результат
5. Повторювати до виходу
6. Обробляти помилки вводу""",
        
        "repo_url": f"https://github.com/{os.getenv('GITHUB_OWNER')}/{os.getenv('GITHUB_REPO')}",
        "create_pr": True,
        "pr_options": {
            "branch_name": "feature/add-calculator",
            "pr_title": "Add Python Calculator",
            "pr_description": """# Python Calculator

Додано інтерактивний калькулятор з базовими арифметичними операціями.

## Функції:
- ✅ Додавання, віднімання, множення, ділення
- ✅ Інтерактивне меню
- ✅ Обробка помилок
- ✅ Перевірка ділення на нуль

## Використання:
```bash
python calculator.py
```

---
*Створено автоматично AI Agent System*""",
            "base_branch": "main"
        }
    }
    
    print(f"Репозиторій: {calculator_request['repo_url']}")
    print("Відправляємо запит...")
    
    try:
        response = requests.post(
            "http://localhost:5000/api/process_request",
            headers={"Content-Type": "application/json"},
            json=calculator_request,
            timeout=180  # 3 хвилини на генерацію коду
        )
        
        print(f"\nВідповідь сервера: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            print("✅ Запит оброблено!")
            print(f"Статус: {result.get('status', 'unknown')}")
            print(f"Тип обробки: {result.get('processing_type', 'unknown')}")
            print(f"Зміни внесено: {result.get('changes_made', False)}")
            
            # Інформація про PR
            if result.get('changes_made') and 'pr_result' in result:
                pr_info = result['pr_result']
                print(f"\n🎉 PR створено!")
                print(f"PR статус: {pr_info.get('status', 'unknown')}")
                
                if 'pr_url' in pr_info:
                    print(f"🔗 PR URL: {pr_info['pr_url']}")
                if 'workflow_id' in pr_info:
                    print(f"Workflow ID: {pr_info['workflow_id']}")
            
            # Деталі аналізу
            if 'analysis' in result:
                analysis = result['analysis']
                if analysis.get('changes_needed'):
                    print(f"\n📝 Аналіз: Потрібні зміни")
                    if 'recommendations' in analysis:
                        print(f"Рекомендації: {len(analysis['recommendations'])} пунктів")
            
            # Деталі коду
            if 'code_result' in result:
                code_result = result['code_result']
                print(f"\n💻 Генерація коду: {code_result.get('status', 'unknown')}")
                if 'files' in code_result:
                    files = code_result['files']
                    print(f"Файлів створено: {len(files)}")
                    for filename in files.keys():
                        print(f"  - {filename}")
            
        else:
            print("❌ Помилка обробки запиту:")
            try:
                error_data = response.json()
                print(json.dumps(error_data, indent=2))
            except:
                print(f"Raw error: {response.text[:500]}")
    
    except requests.exceptions.Timeout:
        print("⏰ Timeout - запит займає багато часу")
        print("Це нормально для генерації коду. Спробуйте пізніше.")
    except requests.exceptions.ConnectionError:
        print("❌ Помилка підключення до сервера")
    except Exception as e:
        print(f"❌ Неочікувана помилка: {e}")

def test_local_calculator():
    """Тестуємо локальний калькулятор"""
    
    print("\n🧪 Тестування локального калькулятора...")
    print("-" * 50)
    
    if os.path.exists("calculator_demo.py"):
        print("✅ Локальний калькулятор знайдено: calculator_demo.py")
        print("Для тестування запустіть: python calculator_demo.py")
        
        # Показуємо перші рядки коду
        with open("calculator_demo.py", "r", encoding="utf-8") as f:
            lines = f.readlines()[:15]
            print("\nПерші рядки коду:")
            for i, line in enumerate(lines, 1):
                print(f"{i:2}: {line.rstrip()}")
            print("...")
    else:
        print("❌ Локальний калькулятор не знайдено")

if __name__ == "__main__":
    print("🚀 Фінальний тест створення калькулятора")
    print("=" * 60)
    
    create_calculator_pr()
    test_local_calculator()
    
    print("\n" + "=" * 60)
    print("Тест завершено!")
    print("\nЯкщо PR створено успішно, перевірте:")
    print(f"https://github.com/{os.getenv('GITHUB_OWNER')}/{os.getenv('GITHUB_REPO')}/pulls")