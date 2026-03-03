@echo off
setlocal EnableDelayedExpansion

REM ============================================================
REM  AskOps by RaveMinds — One-Click Setup (Windows)
REM  Automatically starts Docker Desktop + Ollama
REM  Run once: setup.bat
REM ============================================================

echo.
echo AskOps setup
echo.

REM ── Use Python 3.11 (py -3.11) ─────────────────────────────────
set "PYEXE=py -3.11"
py -3.11 -c "exit(0)" 2>nul
if errorlevel 1 (
    echo   ERROR: Python 3.11 required. Install from https://python.org
    if exist venv echo   Remove venv and re-run:  rmdir /s /q venv
    pause
    exit /b 1
)
if exist venv\Scripts\python.exe (
    venv\Scripts\python.exe -c "import sys; v=sys.version_info; sys.exit(0 if v.major==3 and v.minor==11 else 1)" 2>nul
    if errorlevel 1 (
        echo   ERROR: venv has wrong Python. Remove and re-run:  rmdir /s /q venv
        pause
        exit /b 1
    )
)

REM ── Step 1: Docker Desktop ───────────────────────────────────
echo [1/8] Docker...
docker info >nul 2>&1
if errorlevel 1 (
    set "DOCKER_PATH="
    if exist "C:\Program Files\Docker\Docker\Docker Desktop.exe" set "DOCKER_PATH=C:\Program Files\Docker\Docker\Docker Desktop.exe"
    if exist "%LOCALAPPDATA%\Programs\Docker\Docker\Docker Desktop.exe" set "DOCKER_PATH=%LOCALAPPDATA%\Programs\Docker\Docker\Docker Desktop.exe"
    if "!DOCKER_PATH!"=="" (
        echo   ERROR: Docker not found. Install from https://docker.com
        pause & exit /b 1
    )
    start "" "!DOCKER_PATH!"
    set /a attempts=0
    :wait_docker
    timeout /t 5 /nobreak >nul
    set /a attempts+=1
    docker info >nul 2>&1
    if errorlevel 1 (
        if !attempts! LSS 18 goto wait_docker
        echo   ERROR: Docker did not start in time.
        pause & exit /b 1
    )
)
echo   ok

REM ── Step 2: Ollama ────────────────────────────────────────────
echo [2/8] Ollama...
where ollama >nul 2>&1
if errorlevel 1 (
    echo   ERROR: Ollama not installed. Install from https://ollama.ai
    pause & exit /b 1
)
curl -s http://localhost:11434 >nul 2>&1
if errorlevel 1 (
    start /min "" ollama serve
    timeout /t 5 /nobreak >nul
    curl -s http://localhost:11434 >nul 2>&1
    if errorlevel 1 (
        echo   ERROR: Ollama failed to start.
        pause & exit /b 1
    )
)
echo   ok

REM ── Step 3: Ollama models (Mistral + nomic-embed-text) ─────────
echo [3/8] Ollama models...
ollama list | findstr "mistral" >nul 2>&1
if errorlevel 1 (
    ollama pull mistral
    if errorlevel 1 ( echo   ERROR: Mistral pull failed. & pause & exit /b 1 )
)
ollama list | findstr "nomic-embed-text" >nul 2>&1
if errorlevel 1 (
    ollama pull nomic-embed-text
    if errorlevel 1 ( echo   ERROR: nomic-embed-text pull failed. & pause & exit /b 1 )
)
echo   ok

REM ── Step 4: Python venv ───────────────────────────────────────
echo [4/8] venv...
if not exist venv (
    !PYEXE! -m venv venv
    if errorlevel 1 (
        echo   ERROR: Python 3.11–3.13 not found. Install from https://python.org
        pause & exit /b 1
    )
)
echo   ok

REM ── Step 5: Dependencies ───────────────────────────────────────
echo [5/8] pip...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip setuptools wheel --quiet --disable-pip-version-check
pip install -r requirements.txt --quiet --disable-pip-version-check
if errorlevel 1 ( echo   ERROR: pip install failed. & pause & exit /b 1 )
echo   ok

REM ── Step 6: .env ───────────────────────────────────────────────
echo [6/8] .env...
if not exist .env copy .env.template .env >nul
echo   ok

REM ── Step 7: Docker services ───────────────────────────────────
echo [7/8] Docker services...
docker compose up -d
if errorlevel 1 ( echo   ERROR: docker compose failed. & pause & exit /b 1 )
timeout /t 12 /nobreak >nul
echo   ok

REM ── Step 8: Ingest mock data ───────────────────────────────────
echo [8/8] Ingest...
if exist lancedb rmdir /s /q lancedb
python ingestion\ingest.py
if errorlevel 1 ( echo   ERROR: Ingestion failed. & pause & exit /b 1 )
echo   ok

echo.
echo Done. Add Slack tokens to .env, run start_api.bat and start_bot.bat.
pause
