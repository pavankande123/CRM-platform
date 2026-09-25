# ==============================================================================
# Enermax CRM - Comprehensive Test Runner (PowerShell)
# ==============================================================================

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Running Enermax CRM Phase 1 Verification Test Suite" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Run Backend Pytest Suite
Write-Host "`n>>> [1/2] Running Backend Pytest Suite..." -ForegroundColor Yellow
$backendExit = & "$PSScriptRoot\..\backend\.venv\Scripts\pytest.exe" "$PSScriptRoot\..\backend\tests" -v
if ($LASTEXITCODE -ne 0) {
    Write-Host "Backend tests FAILED!" -ForegroundColor Red
    exit 1
}
Write-Host "Backend tests PASSED!" -ForegroundColor Green

# 2. Run Frontend Typecheck and Build
Write-Host "`n>>> [2/2] Running Frontend Type Check and Production Build..." -ForegroundColor Yellow
Push-Location "$PSScriptRoot\..\frontend"
$frontendExit = & npm.cmd run build
Pop-Location
if ($LASTEXITCODE -ne 0) {
    Write-Host "Frontend build FAILED!" -ForegroundColor Red
    exit 1
}
Write-Host "Frontend build PASSED!" -ForegroundColor Green

Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host "ALL TESTS AND BUILDS PASSED SUCCESSFULLY!" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
