$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path ".venv")) {
    Write-Host "Virtual environment not found. Running setup first..."
    .\setup.ps1
}

Write-Host "Starting ETL QA Accelerator web UI..."
.\.venv\Scripts\python.exe -m streamlit run app\streamlit_app.py
