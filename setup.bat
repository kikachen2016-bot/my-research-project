@echo off
chcp 65001 >nul
echo ========================================
echo   Interview System - Setup
echo ========================================
echo.

set VENV_DIR=C:\interview-venv

echo [1/4] Checking Python...
python --version
if errorlevel 1 (
    echo ERROR: Python not found.
    echo Install from: https://www.python.org/downloads/release/python-3128/
    pause
    exit /b 1
)
echo OK

echo.
echo [2/4] Backend setup...
if exist "%VENV_DIR%" rmdir /s /q "%VENV_DIR%"
echo   Creating virtual environment on C drive...
python -m venv "%VENV_DIR%"
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment.
    pause
    exit /b 1
)
echo   Installing Python packages...
"%VENV_DIR%\Scripts\pip.exe" install -r "%~dp0backend\requirements.txt"
if errorlevel 1 (
    echo ERROR: pip install failed.
    pause
    exit /b 1
)
echo OK: Backend ready

echo.
echo [3/4] Frontend - npm install...
cd /d "%~dp0frontend"
call npm install
if errorlevel 1 (
    echo ERROR: npm install failed.
    pause
    exit /b 1
)
echo OK

echo.
echo [4/4] Installing global tools (next@14 + typescript)...
call npm install -g next@14 typescript
if errorlevel 1 (
    echo ERROR: global install failed.
    pause
    exit /b 1
)
echo OK: Frontend ready

echo.
echo ========================================
echo   Setup complete! Now run start.bat
echo ========================================
echo.
pause
