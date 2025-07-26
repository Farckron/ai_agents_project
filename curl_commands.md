# Curl команди для тестування системи

## 1. Перевірити статус системи:
```bash
curl http://localhost:5000/api/status
```

## 2. Проаналізувати репозиторій:
```bash
curl "http://localhost:5000/api/repository/analyze?repo_url=https://github.com/Farckron/SimpleCalc"
```

## 3. Створити простий PR:
```bash
curl -X POST http://localhost:5000/api/pr/create -H "Content-Type: application/json" -d "{\"user_request\": \"Add hello.py file with print('Hello World')\", \"repo_url\": \"https://github.com/Farckron/SimpleCalc.git\"}"
```

## 4. Обробити запит без створення PR:
```bash
curl -X POST http://localhost:5000/api/process_request -H "Content-Type: application/json" -d "{\"request\": \"Analyze this repository\", \"repo_url\": \"https://github.com/Farckron/SimpleCalc\", \"create_pr\": false}"
```

## Що очікувати:

### Команда 1 (статус):
- Повинна повернути JSON з інформацією про систему
- `"status": "online"` означає що система працює

### Команда 2 (аналіз):
- Повинна повернути аналіз репозиторію
- `"status": "success"` означає що репозиторій доступний

### Команда 3 (PR):
- Повинна створити Pull Request у вашому репозиторії
- Поверне `request_id` та статус операції

### Команда 4 (обробка):
- Проаналізує репозиторій без створення PR
- Поверне рекомендації та аналіз