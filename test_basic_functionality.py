#!/usr/bin/env python3
"""
Базове тестування функціональності без створення PR
"""

import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

def test_repository_analysis():
    """Тестуємо аналіз репозиторію"""
    
    repo_url = f"https://github.com/{os.getenv('GITHUB_OWNER')}/{os.getenv('GITHUB_REPO')}"
    
    print("🔍 Тестування аналізу репозиторію...")
    print(f"Репозиторій: {repo_url}")
    print("-" * 50)
    
    try:
        response = requests.get(
            "http://localhost:5000/api/repository/analyze",
            params={"repo_url": repo_url},
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Аналіз репозиторію успішний!")
            print(f"Статус: {result.get('status', 'unknown')}")
            
            if 'analysis' in result:
                analysis = result['analysis']
                print(f"Аналіз статус: {analysis.get('status', 'unknown')}")
                if 'summary' in analysis:
                    print(f"Опис: {analysis['summary'][:200]}...")
            
            if 'repository_info' in result:
                repo_info = result['repository_info']
                print(f"Репозиторій інфо: {repo_info}")
                
        else:
            print("❌ Помилка аналізу:")
            try:
                error_data = response.json()
                print(json.dumps(error_data, indent=2))
            except:
                print(f"Raw error: {response.text}")
                
    except Exception as e:
        print(f"❌ Помилка: {e}")

def test_simple_request():
    """Тестуємо простий запит без створення PR"""
    
    print("\n📝 Тестування простого запиту...")
    print("-" * 50)
    
    simple_request = {
        "request": "Проаналізуй структуру цього репозиторію та дай рекомендації",
        "repo_url": f"https://github.com/{os.getenv('GITHUB_OWNER')}/{os.getenv('GITHUB_REPO')}",
        "create_pr": False
    }
    
    try:
        response = requests.post(
            "http://localhost:5000/api/process_request",
            headers={"Content-Type": "application/json"},
            json=simple_request,
            timeout=60
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Запит оброблено успішно!")
            print(f"Статус: {result.get('status', 'unknown')}")
            print(f"Тип обробки: {result.get('processing_type', 'unknown')}")
            print(f"Зміни внесено: {result.get('changes_made', False)}")
            
            if 'analysis' in result:
                analysis = result['analysis']
                print(f"Аналіз статус: {analysis.get('status', 'unknown')}")
                if 'analysis' in analysis:
                    print(f"Результат аналізу: {analysis['analysis'][:300]}...")
                    
        else:
            print("❌ Помилка запиту:")
            try:
                error_data = response.json()
                print(json.dumps(error_data, indent=2))
            except:
                print(f"Raw error: {response.text}")
                
    except Exception as e:
        print(f"❌ Помилка: {e}")

def create_local_calculator():
    """Створюємо калькулятор локально для демонстрації"""
    
    print("\n🧮 Створення локального калькулятора...")
    print("-" * 50)
    
    calculator_code = '''#!/usr/bin/env python3
"""
Simple Python Calculator
Created by AI Agent System
"""

def add(a, b):
    """Addition operation"""
    return a + b

def subtract(a, b):
    """Subtraction operation"""
    return a - b

def multiply(a, b):
    """Multiplication operation"""
    return a * b

def divide(a, b):
    """Division operation with zero check"""
    if b == 0:
        raise ValueError("Cannot divide by zero!")
    return a / b

def get_number(prompt):
    """Get a valid number from user input"""
    while True:
        try:
            return float(input(prompt))
        except ValueError:
            print("Please enter a valid number!")

def main():
    """Main calculator function"""
    print("🧮 Python Calculator")
    print("=" * 30)
    
    while True:
        print("\\nOperations:")
        print("1. Addition (+)")
        print("2. Subtraction (-)")
        print("3. Multiplication (*)")
        print("4. Division (/)")
        print("5. Exit")
        
        choice = input("\\nSelect operation (1-5): ").strip()
        
        if choice == '5':
            print("Thank you for using the calculator!")
            break
        
        if choice not in ['1', '2', '3', '4']:
            print("Invalid choice! Please select 1-5.")
            continue
        
        try:
            num1 = get_number("Enter first number: ")
            num2 = get_number("Enter second number: ")
            
            if choice == '1':
                result = add(num1, num2)
                operation = "+"
            elif choice == '2':
                result = subtract(num1, num2)
                operation = "-"
            elif choice == '3':
                result = multiply(num1, num2)
                operation = "*"
            elif choice == '4':
                result = divide(num1, num2)
                operation = "/"
            
            print(f"\\n{num1} {operation} {num2} = {result}")
            
        except ValueError as e:
            print(f"Error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()
'''
    
    # Зберігаємо калькулятор локально
    with open("calculator_demo.py", "w", encoding="utf-8") as f:
        f.write(calculator_code)
    
    print("✅ Калькулятор створено локально: calculator_demo.py")
    print("Для тестування запустіть: python calculator_demo.py")
    
    return calculator_code

if __name__ == "__main__":
    print("🧪 Базове тестування функціональності")
    print("=" * 60)
    
    test_repository_analysis()
    test_simple_request()
    calculator_code = create_local_calculator()
    
    print("\n" + "=" * 60)
    print("✅ Базове тестування завершено!")
    print("\nСтворений калькулятор можна протестувати локально.")
    print("Для створення PR потрібно налагодити GitHub Manager.")