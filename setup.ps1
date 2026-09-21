$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "Setting up AI-Powered ETL QA Accelerator..." -ForegroundColor Cyan

if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..."
    python -m venv .venv
}

Write-Host "Installing dependencies..."
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\pip.exe install -r requirements.txt

Write-Host "Creating sample files and folders..."
.\.venv\Scripts\python.exe scripts\create_samples.py
New-Item -ItemType Directory -Force -Path output, uploads, review, runs, metadata | Out-Null

if (-not (Test-Path ".env")) {
    Write-Host "WARNING: .env file not found. Copy .env.example values into .env before running validation." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Setup complete." -ForegroundColor Green
Write-Host "Next steps:"
Write-Host "  1. Ensure .env contains your Azure OpenAI and Databricks credentials"
Write-Host "  2. Double-click run_ui.ps1 or run: .\run_ui.ps1"
Write-Host "  3. Or use CLI: .\.venv\Scripts\python.exe main.py build --use-samples"
