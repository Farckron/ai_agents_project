@echo off
echo ========================================
echo Запуск GitHub PR Automation Server
echo ========================================

cd /d "C:\s\KiroProjects\ai_agents_project"

echo Перевіряємо Python...
python --version
if errorlevel 1 (
    echo Python не знайдено! Встановіть Python.
    pause
    exit /b 1
)

echo.
echo Запускаємо сервер...
echo Сервер буде доступний на: http://localhost:5000
echo Для зупинки натисніть Ctrl+C
echo.

python main.py

pause