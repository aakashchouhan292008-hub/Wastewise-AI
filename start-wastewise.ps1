<#
.SYNOPSIS
    Starts the WasteWise AI FastAPI backend (port 8000) and React Vite frontend (port 5173)
    in separate PowerShell windows on Windows 11 without launching duplicate processes.
#>

$ErrorActionPreference = "Stop"
$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Join-Path $RootDir "backend"
$FrontendDir = Join-Path $RootDir "frontend"

function Test-PortListening {
    param([int]$Port)
    $match = netstat -ano | Select-String "127\.0\.0\.1:$Port\s+.*LISTENING"
    return [bool]$match
}

Write-Host "=== WasteWise AI Startup ===" -ForegroundColor Green

# 1. Start FastAPI Backend (port 8000)
if (Test-PortListening -Port 8000) {
    Write-Host "[Backend] Already running on http://127.0.0.1:8000 (skipping duplicate start)." -ForegroundColor Yellow
} else {
    Write-Host "[Backend] Starting FastAPI server on http://127.0.0.1:8000 ..." -ForegroundColor Cyan
    $backendCmd = "cd `"$BackendDir`"; .\.venv\Scripts\Activate.ps1; python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd
}

# 2. Start React Vite Frontend (port 5173)
if (Test-PortListening -Port 5173) {
    Write-Host "[Frontend] Already running on http://127.0.0.1:5173 (skipping duplicate start)." -ForegroundColor Yellow
} else {
    Write-Host "[Frontend] Starting React Vite dev server on http://127.0.0.1:5173 ..." -ForegroundColor Cyan
    $frontendCmd = "cd `"$FrontendDir`"; npm.cmd run dev"
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCmd
}

Write-Host ""
Write-Host "WasteWise AI URLs:" -ForegroundColor Green
Write-Host "  Frontend App : http://127.0.0.1:5173/"
Write-Host "  Backend Docs : http://127.0.0.1:8000/docs"
