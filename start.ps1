# ============================================================
# 起動スクリプト（毎回使用）
# ============================================================
# 実行方法：PowerShellで以下を入力
#   cd "このフォルダのパス"
#   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
#   .\start.ps1
# ============================================================

$Root = $PSScriptRoot

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  面談評価システム - 起動中" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# バックエンドを別ウィンドウで起動
Write-Host "バックエンド（FastAPI）を起動中..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "
    Set-Location '$Root\backend';
    Write-Host 'バックエンド起動中 http://localhost:8000' -ForegroundColor Cyan;
    & '$Root\backend\.venv\Scripts\python.exe' -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
"

Start-Sleep -Seconds 2

# フロントエンドを別ウィンドウで起動
Write-Host "フロントエンド（Next.js）を起動中..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "
    Set-Location '$Root\frontend';
    Write-Host 'フロントエンド起動中 http://localhost:3000' -ForegroundColor Cyan;
    npm run dev
"

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  起動完了！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "ブラウザで以下を開いてください：" -ForegroundColor White
Write-Host "  http://localhost:3000" -ForegroundColor Cyan
Write-Host ""
Write-Host "停止するには：各ウィンドウで Ctrl+C を押してください" -ForegroundColor Gray
Write-Host ""
Read-Host "Enterキーを押してこのウィンドウを閉じる"
