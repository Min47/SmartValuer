# To run in this path:
# C:\YourUser\Documents\SmartValuer\ > .\AutoScript\details_buy_0_1_2.ps1

$pairs = @(
    @{ mode = "Buy"; unit = "0" },
    @{ mode = "Buy"; unit = "1" },
    @{ mode = "Buy"; unit = "2" }
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
        $logfile = Join-Path $logDir "scraper_$($pair.mode)_$($pair.unit)_${timestamp}.txt"

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