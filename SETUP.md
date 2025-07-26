# 🚀 Налаштування GitHub PR Automation System

## Швидкий старт

### 1. Очистити кеш та підготувати систему
```bash
python cleanup.py
```

### 2. Налаштувати .env файл
```bash
# Скопіювати приклад
cp .env.example .env

# Відредагувати .env файл
# Додати ваш GitHub token та інші налаштування
```

### 3. Запустити систему
```bash
python start.py
```

## Детальне налаштування

### GitHub Token
1. Перейдіть на [GitHub Settings](https://github.com/settings/tokens)
2. Створіть новий Personal Access Token (classic)
3. Виберіть scopes:
   - ✅ `repo` - повний доступ до репозиторіїв
   - ✅ `user:email` - доступ до email
   - ✅ `read:user` - читання профілю
   - ✅ `workflow` - робота з GitHub Actions (опціонально)

### OpenAI API Key (опціонально)
1. Перейдіть на [OpenAI Platform](https://platform.openai.com/api-keys)
2. Створіть новий API key
3. Додайте його в .env файл

### Налаштування .env файлу
```env
# Обов'язкові налаштування
GITHUB_TOKEN=ghp_your_token_here
GITHUB_REPO_URL=https://github.com/your-username/your-repo

# Опціональні налаштування
OPENAI_API_KEY=sk-your_key_here
SECRET_KEY=your-secret-key-for-sessions
FLASK_ENV=development
LOG_LEVEL=INFO
```

## Команди для роботи

### Очистити кеш
```bash
python cleanup.py
```

### Запустити систему
```bash
python start.py
```

### Запустити тільки Flask сервер
```bash
python main.py
```

### Запустити тести
```bash
# Всі тести
python -m pytest tests/ -v

# Тільки unit тести
python -m pytest tests/unit/ -v

# Тільки integration тести
python -m pytest tests/integration/ -v

# Швидкий тест інтеграції
python test_integration.py
```

### Тестування API
```bash
# Запустити сервер в одному терміналі
python main.py

# В іншому терміналі тестувати API
python test_api_endpoints.py
```

## Структура проекту

```
ai_agents_project/
├── .env                    # Конфігурація (створити самостійно)
├── .env.example           # Приклад конфігурації
├── cleanup.py             # Скрипт очищення
├── start.py               # Скрипт запуску
├── main.py                # Flask додаток
├── agents/                # AI агенти
│   ├── pr_manager.py      # Менеджер PR
│   ├── github_manager.py  # Менеджер GitHub
│   └── project_manager.py # Головний менеджер
├── utils/                 # Утиліти
│   ├── git_operations.py  # Git операції
│   ├── error_handler.py   # Обробка помилок
│   └── structured_logger.py # Логування
├── models/                # Моделі даних
├── config/                # Конфігурація
├── tests/                 # Тести
└── docs/                  # Документація
```

## API Endpoints

### Створення PR
```bash
POST /api/pr/create
{
  "user_request": "Add hello world function",
  "repo_url": "https://github.com/user/repo",
  "options": {
    "branch_name": "feature/hello-world",
    "pr_title": "Add hello world function",
    "base_branch": "main"
  }
}
```

### Аналіз репозиторію
```bash
GET /api/repository/analyze?repo_url=https://github.com/user/repo
```

### Статус системи
```bash
GET /api/status
```

## Troubleshooting

### Помилка імпорту модулів
```bash
# Встановити залежності
pip install -r requirements.txt

# Або використати start.py який встановить автоматично
python start.py
```

### Помилка GitHub API
- Перевірте GitHub token в .env
- Переконайтеся що token має правильні scopes
- Перевірте чи не закінчився термін дії token

### Помилка Flask
- Перевірте чи порт 5000 не зайнятий
- Встановіть FLASK_ENV=development в .env
- Перевірте логи в logs/app.log

### Помилки тестів
```bash
# Очистити кеш та перезапустити
python cleanup.py
python start.py
```

## Логи та моніторинг

Логи зберігаються в:
- `logs/app.log` - основні логи додатку
- Консоль - логи під час розробки

Для аналізу логів:
```bash
python utils/log_analyzer.py
```