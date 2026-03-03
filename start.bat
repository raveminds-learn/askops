@echo off
cd /d "%~dp0"

echo Starting AskOps...
docker compose up -d 2>nul
start "AskOps API" cmd /k "cd /d "%~dp0" && call venv\Scripts\activate.bat && python -m uvicorn api.main:app --host 0.0.0.0 --port 8001"
start "AskOps Bot" cmd /k "cd /d "%~dp0" && call venv\Scripts\activate.bat && python bot\slack_bot.py"

echo.
echo API and Bot started in separate windows.
echo Run stop.bat to stop both.
pause
