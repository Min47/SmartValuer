# To run in this path:
# C:\YourUser\Documents\SmartValuer\ > .\AutoScript\batch_rent_12am.ps1

$pairs = @(
    @{ mode = "Buy"; unit = "0" },
    @{ mode = "Buy"; unit = "1" },
    @{ mode = "Buy"; unit = "2" }
)

$logDir = Join-Path (Get-Location) "logs"
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir | Out-Null
}

foreach ($pair in $pairs) {
    # Empty line for better readability
    Write-Host ""

    # Create a timestamped log file for each pair
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmssfff"

    # Ensure the log file name is unique
    $logfile = Join-Path $logDir "scraper_$($pair.mode)_$($pair.unit)_${timestamp}.txt"

    # Write the header to the log file
    Write-Host "Preparing to run docker for Mode=$($pair.mode), Unit=$($pair.unit)"
    Write-Host "Log file will be: $logfile"
    
    # Docker command
    $envFile = Join-Path (Get-Location) "src\.env"
    $mountDir = (Get-Location).Path

    $dockerCmd = @(
        "run", "--env-file", $envFile,
        "--rm",
        "-e", "MODES=$($pair.mode)",
        "-e", "UNIT_TYPES=$($pair.unit)",
        "-v", "${mountDir}:/app",
        "smartvaluer-scraper"
    )

    Write-Host "Running docker: docker $($dockerCmd -join ' ')"
    & docker @dockerCmd *> $logfile

    # After running docker
    Write-Host "Finished docker for Mode=$($pair.mode), Unit=$($pair.unit)"

    # Empty line for better readability
    Write-Host ""
}