# Liquibase migration runner script for Windows PowerShell

Write-Host "Running Liquibase migrations..." -ForegroundColor Green

# Check if liquibase.properties exists
if (!(Test-Path "liquibase.properties")) {
    Write-Host "Error: liquibase.properties not found!" -ForegroundColor Red
    exit 1
}

# Run liquibase update
try {
    & liquibase --defaultsFile=liquibase.properties update
    Write-Host "Migrations completed successfully." -ForegroundColor Green
} catch {
    Write-Host "Migration failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}