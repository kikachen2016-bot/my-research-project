# pyvenv.cfg から実際のvenvパスを読み取って起動する
$scriptDir = if ($PSScriptRoot -and $PSScriptRoot -ne "") { $PSScriptRoot } else { (Get-Location).Path }
$cfgPath = Join-Path $scriptDir ".venv\pyvenv.cfg"

if (-not (Test-Path $cfgPath)) {
    Write-Host "ERROR: .venv not found. Run install.bat first." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# pyvenv.cfg の command 行から venv の実パスを取得
# 例: command = C:\...\python.exe -m venv G:\...\backend\.venv
$cfg = Get-Content $cfgPath
$cmdLine = ($cfg | Where-Object { $_ -match "^command\s*=" }) -replace "^command\s*=\s*", ""
$venvPath = ($cmdLine.Trim() -split " -m venv ")[1].Trim()

$python = Join-Path $venvPath "Scripts\python.exe"

if (-not (Test-Path $python)) {
    Write-Host "ERROR: python.exe not found at:" -ForegroundColor Red
    Write-Host "  $python" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Starting backend at http://127.0.0.1:8000 ..." -ForegroundColor Cyan
Write-Host "Python: $python" -ForegroundColor Gray
Set-Location $scriptDir
& $python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
Read-Host "Press Enter to exit"
