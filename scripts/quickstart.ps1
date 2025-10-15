# Quick Start Script for Windows PowerShell

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Visual Product Matcher - Quick Start" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check Python version
Write-Host "Checking Python version..." -ForegroundColor Yellow
$pythonVersion = python --version
Write-Host "Python version: $pythonVersion" -ForegroundColor Green

# Create virtual environment if it doesn't exist
if (-not (Test-Path "venv")) {
    Write-Host ""
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate virtual environment
Write-Host ""
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"

# Install dependencies
Write-Host ""
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install --upgrade pip
pip install -r requirements.txt

# Check if data is initialized
if (-not (Test-Path "data\products.db")) {
    Write-Host ""
    Write-Host "==========================================" -ForegroundColor Red
    Write-Host "Data Not Initialized" -ForegroundColor Red
    Write-Host "==========================================" -ForegroundColor Red
    Write-Host "You need to run the data initialization script:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  python init_data.py" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "This will scan fashion-images\ and build the search index." -ForegroundColor Yellow
    Write-Host "Estimated time: 30-60 minutes for 42K images" -ForegroundColor Yellow
    Write-Host ""
    
    $response = Read-Host "Run initialization now? (y/n)"
    if ($response -eq "y" -or $response -eq "Y") {
        python init_data.py
    } else {
        Write-Host "Skipping initialization. Run 'python init_data.py' before starting the app." -ForegroundColor Yellow
        exit 0
    }
}

# Start the application
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Starting Visual Product Matcher" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "The application will be available at:" -ForegroundColor Green
Write-Host "  http://localhost:5000" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

python app.py
