# Saves the day's paper trades, desk events and logs to GitHub. Run by the "FNO End of Day Sync" task on weekdays.
$ErrorActionPreference = "Stop"
$RepoDir = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $RepoDir

$branch = git branch --show-current
git pull --quiet --rebase origin $branch
git add journal/ reports/ conversations/ data/live/events/
git diff --cached --quiet
if ($LASTEXITCODE -ne 0) {
    git commit --quiet -m ("Live desk: end-of-day paper trades {0:yyyy-MM-dd}" -f (Get-Date))
    git push --quiet origin $branch
}
