# Started by the "FNO Live Desk" scheduled task. Runs the desk and writes a log file per day.
$RepoDir = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$Python = Join-Path $RepoDir ".venv\Scripts\python.exe"
$LogDir = Join-Path $RepoDir "logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$LogFile = Join-Path $LogDir ("live-desk-{0:yyyy-MM-dd}.log" -f (Get-Date))

Set-Location $RepoDir
$env:PYTHONUTF8 = "1"
& $Python -m fno live run *>> $LogFile
exit $LASTEXITCODE  # a non-zero exit lets the scheduled task restart the desk
