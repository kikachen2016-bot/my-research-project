@echo off
chcp 65001 >nul
cd /d "%~dp0backend"

echo [1/2] Creating virtual environment...
if not exist ".venv" (
    python -m venv .venv
)

echo [2/2] Installing packages...
.venv\Scripts\pip.exe install -r requirements.txt

echo.
echo Done. Now run start.ps1 to launch the system.
pause
