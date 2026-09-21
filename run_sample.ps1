$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path ".venv")) {
    .\setup.ps1
}

Write-Host "Building sample draft ETL spec..."
$buildOutput = .\.venv\Scripts\python.exe main.py build --use-samples
Write-Host $buildOutput

$draftId = ($buildOutput | Select-String -Pattern "Draft ID: ([a-f0-9-]+)" | ForEach-Object { $_.Matches[0].Groups[1].Value })
if (-not $draftId) {
    throw "Could not detect draft ID from build output."
}

Write-Host "Approving draft and generating QA pack (no Databricks execution)..."
.\.venv\Scripts\python.exe main.py approve --draft-id $draftId --no-execute

Write-Host "Sample run complete. Check the output folder." -ForegroundColor Green
