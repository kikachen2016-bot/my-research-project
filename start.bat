@echo off
chcp 65001 >nul
echo ========================================
echo   Interview System - Starting
echo ========================================
echo.

if not exist "C:\interview-venv\Scripts\python.exe" (
    echo ERROR: Setup not complete. Please run setup.bat first.
    pause
    exit /b 1
)

if not exist "%~dp0frontend\node_modules" (
    echo ERROR: Frontend not set up. Please run setup.bat first.
    pause
    exit /b 1
)

echo Starting Backend (FastAPI)...
start "Backend - FastAPI" cmd /k "%~dp0backend\run.bat"

timeout /t 2 >nul

echo Starting Frontend (Next.js)...
start "Frontend - Next.js" cmd /k "%~dp0frontend\run.bat"

echo.
echo ========================================
echo   Both servers started!
echo ========================================
echo.
echo Open: http://localhost:3000
echo.
pause
