@echo off
cd /d "%~dp0"
set PYTHON=C:\Users\Andri Januardi\AppData\Local\Programs\Python\Python312\python.exe

echo ========================================
echo         AndFlix - Starting...
echo ========================================
echo.

echo [1/2] Checking API Server...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000 " ^| findstr "LISTEN"') do set PID=%%a
if defined PID (
    echo   Restarting API Server (PID %PID%)...
    taskkill /f /pid %PID% >nul 2>&1
    timeout /t 1 /nobreak >nul
    set PID=
) else (
    echo   Starting API Server...
)
start "AndFlix-API" cmd /c ""%PYTHON%" -m uvicorn api.server:app --reload --port 8000"

timeout /t 3 /nobreak >nul

echo [2/2] Starting Frontend...
start "AndFlix-Web" cmd /c "npx vite --open"

echo.
echo ========================================
echo  AndFlix is running!
echo  API  : http://localhost:8000
echo  Web  : http://localhost:3000
echo  Close this window to stop.
echo ========================================
echo.
pause
