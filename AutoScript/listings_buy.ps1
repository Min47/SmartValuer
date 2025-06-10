# To run in this path:
# C:\YourUser\Documents\SmartValuer\ > .\AutoScript\listings_buy.ps1

$OutputEncoding = [System.Text.Encoding]::UTF8

$pairs = @(
    @{ mode = "Buy"; unit = "0" },
    @{ mode = "Buy"; unit = "1" },
    @{ mode = "Buy"; unit = "2" },
    @{ mode = "Buy"; unit = "3" },
    @{ mode = "Buy"; unit = "4" },
    @{ mode = "Buy"; unit = "5" }
)

$baseDir = Get-Location
$logDir = Join-Path $baseDir "logs"
$envFile = Join-Path $baseDir "src\.env"
$mountDir = $baseDir.Path

if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir | Out-Null
}

foreach ($pair in $pairs) {
    Write-Host ""

    $timestamp = Get-Date -Format "yyyyMMdd_HHmmssfff"
    $logfile = Join-Path $logDir "listings_$($pair.mode)_$($pair.unit)_${timestamp}.txt"

    $dockerCmd = @(
        "run", "--env-file", $envFile,
        "--rm",
        "-e", "RUN_LISTINGS=true",
        "-e", "RUN_DETAILS=false",
        "-e", "LISTINGS_MODES=$($pair.mode)",
        "-e", "LISTINGS_UNIT_TYPES=$($pair.unit)",
        "-v", "${mountDir}:/app",
        "smartvaluer-scraper"
    )
    
    Write-Host "Running Docker | docker $($dockerCmd -join ' ')"
    & docker @dockerCmd | Out-File -FilePath $logfile -Encoding utf8
}

Write-Host ""