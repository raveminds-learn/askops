@echo off
cd /d "%~dp0"

echo Stopping AskOps...

REM Kill API (process using port 8001)
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":8001" ^| findstr "LISTENING"') do (
    taskkill /PID %%a /F >nul 2>&1
    echo Stopped API (PID %%a)
)

REM Kill Bot (python running slack_bot)
for /f "skip=1 tokens=1" %%a in ('wmic process where "commandline like '%%slack_bot%%'" get processid 2^>nul') do (
    if not "%%a"=="" (
        taskkill /PID %%a /F >nul 2>&1
        echo Stopped Bot (PID %%a)
    )
)

echo.
echo AskOps stopped.
pause
