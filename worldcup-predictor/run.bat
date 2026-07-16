@echo off
chcp 65001 >nul
cd /d "%~dp0"

set VENV_PYTHON=venv\Scripts\python.exe
set VENV_PIP=venv\Scripts\pip.exe

if not exist "%VENV_PYTHON%" (
    echo [x] Virtual environment not found.
    echo     Run: python -m venv venv
    pause
    exit /b 1
)

echo.
echo Checking dependencies...
"%VENV_PYTHON%" -c "import questionary, rich, requests, bs4, matplotlib, jinja2, numpy" 2>nul
if %errorlevel% neq 0 (
    echo Installing missing dependencies...
    "%VENV_PIP%" install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [x] Failed to install dependencies. Try running:
        echo     "%VENV_PIP%" install -r requirements.txt
        pause
        exit /b 1
    )
    echo.
)

echo Starting World Cup 2026 Predictor...
echo.
"%VENV_PYTHON%" -X utf8 main.py --interactive

if %errorlevel% neq 0 (
    echo.
    echo [x] An error occurred. Press any key to exit.
    pause
)
