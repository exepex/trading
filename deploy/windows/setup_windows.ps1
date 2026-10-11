# One-time setup of the F&O live desk on a Windows 10/11 machine that stays on.
# Run in PowerShell from the repository folder:   powershell -ExecutionPolicy Bypass -File deploy\windows\setup_windows.ps1
# Safe to run again: it updates packages, re-runs the tests and re-registers the scheduled tasks.
$ErrorActionPreference = "Stop"

$RepoDir = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$Python = Join-Path $RepoDir ".venv\Scripts\python.exe"
$EnvFile = Join-Path $HOME ".trading.env"
$DeskTask = "FNO Live Desk"
$SyncTask = "FNO End of Day Sync"

foreach ($tool in @("git", "py")) {
    if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) {
        throw "'$tool' was not found. Install Python 3.12+ (python.org) and Git for Windows first; see deploy\windows\README.md."
    }
}

Set-Location $RepoDir
Write-Host "1/5 Python environment"
if (-not (Test-Path $Python)) { py -3 -m venv .venv }
& $Python -m pip install --quiet --upgrade pip
& $Python -m pip install --quiet -r requirements.txt

Write-Host "2/5 Tests"
& $Python -m pytest -q
if ($LASTEXITCODE -ne 0) { throw "Tests failed: fix them before starting the desk." }

Write-Host "3/5 Secrets file"
if (-not (Test-Path $EnvFile)) {
    @(
        "# Secrets for the F&O desk. Only your Windows account can read this file. Never commit it.",
        "FNO_SLACK_BOT_TOKEN=",
        "# Optional, only for the MotherDuck options in config.yaml (shared with the market-brief tool):",
        "MOTHERDUCK_TOKEN=",
        "# Groww Trade API, once subscribed:",
        "GROWW_API_KEY=",
        "GROWW_API_SECRET="
    ) | Set-Content -Path $EnvFile -Encoding UTF8
    icacls $EnvFile /inheritance:r /grant:r "$($env:USERNAME):(R,W)" | Out-Null
    Write-Host "Created $EnvFile. Fill in the values (notepad $EnvFile), then run this script again."
    exit 0
}

Write-Host "4/5 Keep the machine awake on mains power"
powercfg /change standby-timeout-ac 0
powercfg /change hibernate-timeout-ac 0
if ((Get-TimeZone).Id -ne "India Standard Time") {
    Write-Warning "This machine is not on India Standard Time. The desk uses IST internally, but the 16:00 sync task uses local time."
}

Write-Host "5/5 Scheduled tasks"
$runner = "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File"
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable `
    -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew

$deskAction = New-ScheduledTaskAction -Execute "powershell.exe" -WorkingDirectory $RepoDir `
    -Argument "$runner `"$RepoDir\deploy\windows\start_live_desk.ps1`""
Register-ScheduledTask -TaskName $DeskTask -Action $deskAction -Settings $settings -Force `
    -Trigger (New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME) | Out-Null

$syncAction = New-ScheduledTaskAction -Execute "powershell.exe" -WorkingDirectory $RepoDir `
    -Argument "$runner `"$RepoDir\deploy\windows\end_of_day_sync.ps1`""
$weekdays = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday, Tuesday, Wednesday, Thursday, Friday -At "16:00"
Register-ScheduledTask -TaskName $SyncTask -Action $syncAction -Trigger $weekdays -Settings $settings -Force | Out-Null

Start-ScheduledTask -TaskName $DeskTask
Write-Host "Done. The desk is running and starts again whenever you log on."
Write-Host "Check it:  .venv\Scripts\python -m fno live status      Logs:  $RepoDir\logs\"
