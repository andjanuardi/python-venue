@echo off
cd /d "%~dp0"
set PYTHON=C:\Users\Andri Januardi\AppData\Local\Programs\Python\Python312\python.exe

echo ========================================
echo      AndFlix - Installing Dependencies
echo ========================================
echo.

echo [1/2] Installing Python dependencies...
"%PYTHON%" -m pip install -r api/requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Python install failed
    pause
    exit /b 1
)
echo.

echo [2/2] Installing Frontend dependencies...
npm install
if %errorlevel% neq 0 (
    echo ERROR: Frontend install failed
    pause
    exit /b 1
)

echo.
echo ========================================
echo  All dependencies installed!
echo  Run run.bat to start AndFlix
echo ========================================
echo.
pause
