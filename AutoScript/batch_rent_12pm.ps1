$pairs = @(
    @{ mode = "Buy"; unit = "0" },
    @{ mode = "Buy"; unit = "1" },
    @{ mode = "Buy"; unit = "2" }
)

foreach ($pair in $pairs) {
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmssfff"
    $logfile = "C:/Users/KarMing/Documents/SmartValuer/logs/scraper_${($pair.mode).ToLower()}_${($pair.unit)}_${timestamp}.txt"

    Write-Host "Preparing to run docker for Mode=$($pair.mode), Unit=$($pair.unit)"
    Write-Host "Log file will be: $logfile"

    # Docker command
    $dockerCmd = @(
        "run", "--env-file", "C:/Users/KarMing/Documents/SmartValuer/src/.env",
        "--rm",
        "-e", "MODES=$($pair.mode)",
        "-e", "UNIT_TYPES=$($pair.unit)",
        "-v", "C:/Users/KarMing/Documents/SmartValuer:/app",
        "smartvaluer-scraper"
    )

    Write-Host "Running docker: docker $($dockerCmd -join ' ')"
    & docker @dockerCmd *> $logfile

    # After running docker
    Write-Host "Finished docker for Mode=$($pair.mode), Unit=$($pair.unit)"
}