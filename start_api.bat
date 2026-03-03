@echo off
echo Starting AskOps by RaveMinds API on http://localhost:8001 ...
call venv\Scripts\activate.bat
python -m uvicorn api.main:app --host 0.0.0.0 --port 8001 --reload
