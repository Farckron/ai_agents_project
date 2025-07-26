#!/usr/bin/env python3
"""
Простий тест створення PR через process_request endpoint
"""

import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

def create_simple_pr():
    """Створити простий PR через process_request"""
    
    # Запит на створення простого калькулятора
    request_data = {
        "request": """Створи простий Python калькулятор у файлі calculator.py з наступними функціями:

1. Функція add(a, b) для додавання
2. Функція subtract(a, b) для віднімання  
3. Функція multiply(a, b) для множення
4. Функція divide(a, b) для ділення (з перевіркою на нуль)
5. Головна функція main() з інтерактивним меню
6. Обробка помилок для некоректного вводу

Калькулятор повинен працювати в циклі до тих пір, поки користувач не вибере вихід.""",
        
        "repo_url": f"https://github.com/{os.getenv('GITHUB_OWNER')}/{os.getenv('GITHUB_REPO')}",
        "create_pr": True,
        "pr_options": {
            "branch_name": "feature/python-calculator",
            "pr_title": "Add Python Calculator",
            "pr_description": "Added simple interactive Python calculator with basic arithmetic operations",
            "base_branch": "main"
        }
    }
    
    print("🧮 Створення Python калькулятора через process_request...")
    print(f"Репозиторій: {request_data['repo_url']}")
    print("-" * 60)
    
    try:
        response = requests.post(
            "http://localhost:5000/api/process_request",
            headers={"Content-Type": "application/json"},
            json=request_data,
            timeout=120  # Збільшуємо timeout для генерації коду
        )
        
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Запит оброблено успішно!")
            
            print(f"Статус: {result.get('status', 'unknown')}")
            print(f"Тип обробки: {result.get('processing_type', 'unknown')}")
            print(f"Зміни внесено: {result.get('changes_made', False)}")
            
            # Деталі PR якщо створено
            if 'pr_result' in result:
                pr_info = result['pr_result']
                print(f"PR статус: {pr_info.get('status', 'unknown')}")
                if 'pr_url' in pr_info:
                    print(f"🔗 PR URL: {pr_info['pr_url']}")
            
            # Деталі аналізу
            if 'analysis' in result:
                analysis = result['analysis']
                print(f"Аналіз: {analysis.get('analysis', 'N/A')[:100]}...")
            
            # Деталі коду
            if 'code_result' in result:
                code_result = result['code_result']
                print(f"Код статус: {code_result.get('status', 'unknown')}")
                
        else:
            print("❌ Помилка обробки запиту:")
            try:
                error_data = response.json()
                print(json.dumps(error_data, indent=2))
            except:
                print(f"Raw error: {response.text}")
    
    except requests.exceptions.Timeout:
        print("❌ Timeout - запит зайняв занадто багато часу (>120 сек)")
        print("Це нормально для першого запиту з генерацією коду")
    except requests.exceptions.ConnectionError:
        print("❌ Не вдалося підключитися до сервера")
    except Exception as e:
        print(f"❌ Помилка: {e}")

if __name__ == "__main__":
    print("🚀 Тестування створення PR через process_request")
    print("=" * 60)
    
    create_simple_pr()
    
    print("\n" + "=" * 60)
    print("Тест завершено!")