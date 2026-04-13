# ============================================================
# 初回セットアップスクリプト（1回だけ実行）
# ============================================================
# 実行方法：PowerShellで以下を入力
#   cd "このフォルダのパス"
#   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
#   .\setup.ps1
# ============================================================

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  面談評価システム - 初回セットアップ" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Pythonの確認
Write-Host "[1/3] Pythonの確認..." -ForegroundColor Yellow
try {
    $pyVersion = python --version 2>&1
    Write-Host "OK: $pyVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Pythonが見つかりません。" -ForegroundColor Red
    Write-Host "https://www.python.org/downloads/ からPython 3.12をインストールしてください。" -ForegroundColor Red
    Write-Host "インストール時に「Add Python to PATH」にチェックを入れてください。" -ForegroundColor Red
    Read-Host "Enterキーを押して終了"
    exit 1
}

# バックエンドのセットアップ
Write-Host ""
Write-Host "[2/3] バックエンドのセットアップ（Python仮想環境 + パッケージインストール）..." -ForegroundColor Yellow
Set-Location "$Root\backend"

if (-not (Test-Path ".venv")) {
    Write-Host "  仮想環境を作成中..." -ForegroundColor Gray
    python -m venv .venv
}

Write-Host "  パッケージをインストール中（少し時間がかかります）..." -ForegroundColor Gray
& ".\.venv\Scripts\pip.exe" install -r requirements.txt --quiet
Write-Host "OK: バックエンドのセットアップ完了" -ForegroundColor Green

# フロントエンドのセットアップ
Write-Host ""
Write-Host "[3/3] フロントエンドのセットアップ（npm install）..." -ForegroundColor Yellow
Set-Location "$Root\frontend"
npm install --silent
Write-Host "OK: フロントエンドのセットアップ完了" -ForegroundColor Green

Set-Location $Root

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  セットアップ完了！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "次のコマンドでシステムを起動してください：" -ForegroundColor Cyan
Write-Host "  .\start.ps1" -ForegroundColor White
Write-Host ""
Read-Host "Enterキーを押して終了"
