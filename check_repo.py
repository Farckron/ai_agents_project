#!/usr/bin/env python3
"""
Перевірка доступу до GitHub репозиторію
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

def check_repository():
    """Перевірити доступ до репозиторію"""
    
    token = os.getenv('GITHUB_TOKEN')
    owner = os.getenv('GITHUB_OWNER')
    repo = os.getenv('GITHUB_REPO')
    
    print("🔍 Перевірка GitHub репозиторію...")
    print(f"Owner: {owner}")
    print(f"Repo: {repo}")
    print(f"Token: {token[:10]}..." if token else "Token: НЕ НАЛАШТОВАНО")
    print("-" * 50)
    
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    # Перевіряємо репозиторій
    try:
        url = f'https://api.github.com/repos/{owner}/{repo}'
        print(f"Перевіряємо URL: {url}")
        
        response = requests.get(url, headers=headers)
        print(f"Статус відповіді: {response.status_code}")
        
        if response.status_code == 200:
            repo_data = response.json()
            print("✅ Репозиторій знайдено!")
            print(f"   Назва: {repo_data['full_name']}")
            print(f"   Приватний: {repo_data['private']}")
            print(f"   Гілка за замовчуванням: {repo_data['default_branch']}")
            print(f"   URL: {repo_data['html_url']}")
            
            # Перевіряємо права доступу
            permissions = repo_data.get('permissions', {})
            print(f"   Права: push={permissions.get('push', False)}, pull={permissions.get('pull', False)}")
            
            return True
            
        elif response.status_code == 404:
            print("❌ Репозиторій не знайдено!")
            print("Можливі причини:")
            print("1. Репозиторій не існує")
            print("2. Неправильна назва репозиторію")
            print("3. Репозиторій приватний і токен не має доступу")
            
            # Показуємо доступні репозиторії
            print("\n🔍 Ваші доступні репозиторії:")
            user_repos_url = 'https://api.github.com/user/repos'
            repos_response = requests.get(user_repos_url, headers=headers)
            
            if repos_response.status_code == 200:
                repos = repos_response.json()
                for repo_info in repos[:10]:  # Показуємо перші 10
                    print(f"   - {repo_info['full_name']} ({'private' if repo_info['private'] else 'public'})")
            
            return False
            
        elif response.status_code == 401:
            print("❌ Помилка автентифікації!")
            print("GitHub токен недійсний або закінчився термін дії")
            return False
            
        elif response.status_code == 403:
            print("❌ Доступ заборонено!")
            print("Токен не має прав доступу до цього репозиторію")
            return False
            
        else:
            print(f"❌ Невідома помилка: {response.status_code}")
            print(f"Відповідь: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Помилка підключення: {e}")
        return False

def suggest_fix():
    """Запропонувати виправлення"""
    
    print("\n" + "=" * 50)
    print("🛠️  РЕКОМЕНДАЦІЇ ДЛЯ ВИПРАВЛЕННЯ:")
    print("=" * 50)
    
    print("\n1. ПЕРЕВІРТЕ НАЗВУ РЕПОЗИТОРІЮ:")
    print("   - Перейдіть на https://github.com/Farckron")
    print("   - Знайдіть правильну назву репозиторію")
    print("   - Оновіть GITHUB_REPO в .env файлі")
    
    print("\n2. СТВОРІТЬ НОВИЙ РЕПОЗИТОРІЙ:")
    print("   - Перейдіть на https://github.com/new")
    print("   - Створіть репозиторій з назвою 'SimpleCalc'")
    print("   - Зробіть його публічним")
    
    print("\n3. ПЕРЕВІРТЕ GITHUB TOKEN:")
    print("   - Перейдіть на https://github.com/settings/tokens")
    print("   - Перевірте що токен не закінчився")
    print("   - Переконайтеся що є права 'repo'")
    
    print("\n4. ОНОВІТЬ .env ФАЙЛ:")
    print("   GITHUB_OWNER=ваш_username")
    print("   GITHUB_REPO=назва_репозиторію")
    print("   GITHUB_REPO_URL=https://github.com/ваш_username/назва_репозиторію.git")

if __name__ == "__main__":
    print("🔧 Діагностика GitHub репозиторію")
    print("=" * 50)
    
    success = check_repository()
    
    if not success:
        suggest_fix()
    else:
        print("\n🎉 Репозиторій налаштовано правильно!")
        print("Тепер можна створювати PR.")
    
    print("\n" + "=" * 50)