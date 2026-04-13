@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Stopping any existing Next.js processes on port 3000...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":3000"') do taskkill /PID %%a /F 2>nul
timeout /t 1 >nul
echo Starting Next.js frontend on http://localhost:3000
echo.
npm run dev
pause
