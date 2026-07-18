@echo off
cd /d "%~dp0"
set PYTHON=C:\Users\Andri Januardi\AppData\Local\Programs\Python\Python312\python.exe

echo ========================================
echo         AndFlix - Starting...
echo ========================================
echo.

echo [1/2] Checking API Server...
taskkill /f /fi "WINDOWTITLE eq AndFlix-API" >nul 2>&1
if %errorlevel% equ 0 (
    echo   Restarting API Server...
    timeout /t 1 /nobreak >nul
) else (
    echo   Starting API Server...
)
start "AndFlix-API" "%PYTHON%" -m uvicorn api.server:app --reload --port 8000

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
