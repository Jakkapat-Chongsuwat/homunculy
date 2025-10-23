# Liquibase migration status check script for Windows PowerShell

Write-Host "Checking Liquibase migration status..." -ForegroundColor Green

# Check if liquibase.properties exists
if (!(Test-Path "liquibase.properties")) {
    Write-Host "Error: liquibase.properties not found!" -ForegroundColor Red
    exit 1
}

# Run liquibase status
try {
    & liquibase --defaultsFile=liquibase.properties status
    Write-Host "Migration status check completed." -ForegroundColor Green
} catch {
    Write-Host "Status check failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}