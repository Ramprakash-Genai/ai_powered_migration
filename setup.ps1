# =========================
# Migration Platform Setup Script (Windows)
# Backend: Python + FastAPI + Agents
# Frontend: React
#
# Run from repo root:
#   .\setup.ps1
# =========================

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host " Migration Platform - Full Setup" -ForegroundColor Cyan
Write-Host " Backend (Python) + Frontend (React)" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# -------------------------------------------------
# Prerequisite Check
# -------------------------------------------------
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Python is not installed or not in PATH." -ForegroundColor Red
    exit 1
}

if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    Write-Host "WARNING: Node/npm not found. Frontend setup may be skipped." -ForegroundColor DarkYellow
}

# -------------------------------------------------
# [1/2] Backend Setup
# -------------------------------------------------
Write-Host "`n[1/2] Setting up Backend (Python)..." -ForegroundColor Yellow

if (-not (Test-Path "backend")) {
    Write-Host "ERROR: backend folder not found." -ForegroundColor Red
    exit 1
}

Push-Location "backend"

if (!(Test-Path ".venv")) {
    Write-Host "Creating virtual environment (.venv)..." -ForegroundColor Green
    python -m venv .venv
}

Write-Host "Activating virtual environment..." -ForegroundColor Green
. .\.venv\Scripts\Activate

Write-Host "Upgrading pip..." -ForegroundColor Green
python -m pip install --upgrade pip

if (Test-Path "requirements.txt") {
    Write-Host "Installing backend dependencies..." -ForegroundColor Green
    pip install -r requirements.txt
} else {
    Write-Host "ERROR: backend/requirements.txt not found." -ForegroundColor Red
    Pop-Location
    exit 1
}

# Install Playwright browsers (one-time, safe if repeated)
Write-Host "Installing Playwright browsers..." -ForegroundColor Green
playwright install

Pop-Location

# -------------------------------------------------
# [2/2] Frontend Setup
# -------------------------------------------------
Write-Host "`n[2/2] Setting up Frontend (React)..." -ForegroundColor Yellow

if (Test-Path "ui\ui-app\package.json") {
    Push-Location "ui\ui-app"
    Write-Host "Installing frontend dependencies (npm install)..." -ForegroundColor Green
    npm install
    Pop-Location
} else {
    Write-Host "WARNING: ui\ui-app\package.json not found. Skipping frontend setup." -ForegroundColor DarkYellow
}

# -------------------------------------------------
# Done
# -------------------------------------------------
Write-Host "`n=========================================" -ForegroundColor Cyan
Write-Host " Setup Completed Successfully ✅" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

Write-Host "`nNext Commands:" -ForegroundColor White
Write-Host "Backend :" -ForegroundColor Gray
Write-Host "  cd backend" -ForegroundColor Gray
Write-Host "  python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 5000" -ForegroundColor Gray
Write-Host "Frontend:" -ForegroundColor Gray
Write-Host "  cd ui\ui-app" -ForegroundColor Gray
Write-Host "  npm run dev" -ForegroundColor Gray
