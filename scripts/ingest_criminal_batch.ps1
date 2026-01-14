# PowerShell script to ingest criminal cases in batches
$env:DB_PASSWORD = "postgres"

Write-Host "Starting criminal cases ingestion..." -ForegroundColor Green
Write-Host ""

$years = @(2024, 2023, 2022, 2021, 2020, 2019, 2025)
$batchSize = 20

foreach ($year in $years) {
    Write-Host "Processing criminal_$year (batch of $batchSize)..." -ForegroundColor Yellow
    python scripts/ingest_judgments.py --folder "criminal_$year" --limit $batchSize
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] criminal_$year processed" -ForegroundColor Green
    } else {
        Write-Host "[ERROR] Failed processing criminal_$year" -ForegroundColor Red
    }
    Write-Host ""
}

Write-Host "Batch ingestion complete!" -ForegroundColor Green
Write-Host "Check status with: python scripts/check_status.py" -ForegroundColor Cyan
