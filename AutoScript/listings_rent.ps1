# To run in this path:
# C:\YourUser\Documents\SmartValuer\ > .\AutoScript\listings_rent.ps1

$pairs = @(
    @{ mode = "Rent"; unit = "-1" },
    @{ mode = "Rent"; unit = "0" },
    @{ mode = "Rent"; unit = "1" },
    @{ mode = "Rent"; unit = "2" },
    @{ mode = "Rent"; unit = "3" },
    @{ mode = "Rent"; unit = "4" },
    @{ mode = "Rent"; unit = "5" }
)

$baseDir = Get-Location
$logDir = Join-Path $baseDir "logs"
$dateDir = Join-Path $logDir (Get-Date -Format "yyyy-MM-dd")
$envFile = Join-Path $baseDir "src\.env"
$mountDir = $baseDir.Path

if (-not (Test-Path $dateDir)) {
    New-Item -ItemType Directory -Path $dateDir | Out-Null
}

foreach ($pair in $pairs) {
    Write-Host ""

    $timestamp = Get-Date -Format "yyyyMMdd_HHmmssfff"
    $logfile = Join-Path $dateDir "${timestamp}_listings_$($pair.mode)_$($pair.unit)_.txt"

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