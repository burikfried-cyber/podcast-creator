# Integration Testing Quick Start Script
# Run this script to start both backend and frontend servers

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Integration Testing Quick Start" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Check if Node.js is installed
Write-Host "[1/6] Checking Node.js..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version
    Write-Host "  ✓ Node.js found: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Node.js not found! Please install Node.js 18.x or 20.x" -ForegroundColor Red
    Write-Host "  Download: https://nodejs.org/" -ForegroundColor Yellow
    exit 1
}

# Check if Python is installed
Write-Host "[2/6] Checking Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version
    Write-Host "  ✓ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Python not found! Please install Python 3.11+" -ForegroundColor Red
    Write-Host "  Download: https://www.python.org/" -ForegroundColor Yellow
    exit 1
}

# Check backend dependencies
Write-Host "[3/6] Checking backend dependencies..." -ForegroundColor Yellow
$backendDir = Join-Path $scriptDir "backend"
$venvPath = Join-Path $backendDir "venv"

if (Test-Path $venvPath) {
    Write-Host "  ✓ Virtual environment found" -ForegroundColor Green
} else {
    Write-Host "  ⚠ Virtual environment not found. Creating..." -ForegroundColor Yellow
    Set-Location $backendDir
    python -m venv venv
    Write-Host "  ✓ Virtual environment created" -ForegroundColor Green
}

# Check frontend dependencies
Write-Host "[4/6] Checking frontend dependencies..." -ForegroundColor Yellow
$frontendDir = Join-Path $scriptDir "frontend"
$nodeModulesPath = Join-Path $frontendDir "node_modules"

if (Test-Path $nodeModulesPath) {
    Write-Host "  ✓ Node modules found" -ForegroundColor Green
} else {
    Write-Host "  ⚠ Node modules not found. Installing..." -ForegroundColor Yellow
    Set-Location $frontendDir
    npm install
    Write-Host "  ✓ Node modules installed" -ForegroundColor Green
}

# Run verification script
Write-Host "[5/6] Running verification script..." -ForegroundColor Yellow
Set-Location $frontendDir
try {
    $verifyResult = node verify_implementation.js
    Write-Host "  ✓ Verification complete" -ForegroundColor Green
} catch {
    Write-Host "  ⚠ Verification script failed, but continuing..." -ForegroundColor Yellow
}

# Instructions for starting servers
Write-Host "[6/6] Ready to start servers!" -ForegroundColor Yellow
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Open TWO separate PowerShell terminals:" -ForegroundColor White
Write-Host ""
Write-Host "Terminal 1 - Backend Server:" -ForegroundColor Yellow
Write-Host "  cd $backendDir" -ForegroundColor White
Write-Host "  .\venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000" -ForegroundColor White
Write-Host ""
Write-Host "Terminal 2 - Frontend Server:" -ForegroundColor Yellow
Write-Host "  cd $frontendDir" -ForegroundColor White
Write-Host "  npm run dev" -ForegroundColor White
Write-Host ""
Write-Host "Then open your browser to:" -ForegroundColor Yellow
Write-Host "  Frontend: http://localhost:5173" -ForegroundColor Cyan
Write-Host "  Backend API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Happy Testing! 🚀" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Ask if user wants to open terminals automatically
$response = Read-Host "Would you like to open both terminals automatically? (y/n)"
if ($response -eq 'y' -or $response -eq 'Y') {
    Write-Host ""
    Write-Host "Opening terminals..." -ForegroundColor Yellow
    
    # Start backend terminal
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$backendDir'; Write-Host 'Backend Server Terminal' -ForegroundColor Cyan; Write-Host 'Run: .\venv\Scripts\Activate.ps1' -ForegroundColor Yellow; Write-Host 'Then: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000' -ForegroundColor Yellow"
    
    # Start frontend terminal
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$frontendDir'; Write-Host 'Frontend Server Terminal' -ForegroundColor Cyan; Write-Host 'Run: npm run dev' -ForegroundColor Yellow"
    
    Write-Host "✓ Terminals opened!" -ForegroundColor Green
    Write-Host "  Follow the instructions in each terminal to start the servers." -ForegroundColor White
}

Write-Host ""
Write-Host "For detailed testing instructions, see:" -ForegroundColor White
Write-Host "  INTEGRATION_TESTING_GUIDE.md" -ForegroundColor Cyan
Write-Host ""
