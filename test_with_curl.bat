@echo off
echo ========================================
echo Тестування GitHub PR Automation System
echo ========================================

echo.
echo 1. Перевіряємо статус системи...
curl -s http://localhost:5000/api/status

echo.
echo.
echo 2. Аналізуємо репозиторій...
curl -s "http://localhost:5000/api/repository/analyze?repo_url=https://github.com/Farckron/SimpleCalc"

echo.
echo.
echo 3. Створюємо простий PR...
curl -X POST http://localhost:5000/api/pr/create ^
  -H "Content-Type: application/json" ^
  -d "{\"user_request\": \"Add hello.py file with print('Hello World')\", \"repo_url\": \"https://github.com/Farckron/SimpleCalc.git\"}"

echo.
echo.
echo ========================================
echo Тестування завершено!
echo ========================================
pause