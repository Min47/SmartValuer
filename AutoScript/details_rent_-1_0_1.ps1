# To run in this path:
# C:\YourUser\Documents\SmartValuer\ > .\AutoScript\details_rent_-1_0_1.ps1

$pairs = @(
    @{ mode = "Rent"; unit = "-1" },
    @{ mode = "Rent"; unit = "0" },
    @{ mode = "Rent"; unit = "1" }
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

    Start-Job -ScriptBlock {
        param($pair, $logDir, $envFile, $mountDir)

        $timestamp = Get-Date -Format "yyyyMMdd_HHmmssfff"
        $logfile = Join-Path $dateDir "${timestamp}_details_$($pair.mode)_$($pair.unit)_.txt"

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