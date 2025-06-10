# To run in this path:
# C:\YourUser\Documents\SmartValuer\ > .\AutoScript\details_rent_2_3_4_5.ps1

$pairs = @(
    @{ mode = "Rent"; unit = "2" },
    @{ mode = "Rent"; unit = "3" },
    @{ mode = "Rent"; unit = "4" },
    @{ mode = "Rent"; unit = "5" }
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

    Start-Job -ScriptBlock {
        param($pair, $logDir, $envFile, $mountDir)

        $timestamp = Get-Date -Format "yyyyMMdd_HHmmssfff"
        $logfile = Join-Path $logDir "${timestamp}_details_$($pair.mode)_$($pair.unit)_.txt"

        $dockerCmd = @(
            "run", "--env-file", $envFile,
            "--rm",
            "-e", "RUN_LISTINGS=false",
            "-e", "RUN_DETAILS=true",
            "-e", "DETAILS_MODES=$($pair.mode)",
            "-e", "DETAILS_UNIT_TYPES=$($pair.unit)",
            "-v", "${mountDir}:/app",
            "smartvaluer-scraper"
        )

        & docker @dockerCmd *> $logfile
    } -ArgumentList $pair, $logDir, $envFile, $mountDir
}

Write-Host ""
Get-Job | Wait-Job