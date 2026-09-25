# ==============================================================================
# Enermax CRM - Local Development Startup Script (PowerShell / Windows)
# ==============================================================================

Write-Host ">>> Starting Enermax CRM Local Development Services..." -ForegroundColor Cyan

# 1. Start Backend in a background process
Write-Host ">>> Launching Backend FastAPI server on http://localhost:8000 ..." -ForegroundColor Green
Start-Process -FilePath "backend\.venv\Scripts\python.exe" -ArgumentList "-m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000" -WorkingDirectory "$PSScriptRoot\..\backend"

# 2. Start Frontend in current console
Write-Host ">>> Launching Frontend Vite server on http://localhost:5173 ..." -ForegroundColor Green
Set-Location -Path "$PSScriptRoot\..\frontend"
npm.cmd run dev
