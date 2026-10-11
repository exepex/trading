#!/usr/bin/env bash
# Saves the day's paper trades and logs to GitHub. Run by cron at 16:00 IST on weekdays.
set -euo pipefail
cd "$(dirname "$0")/.."
git pull --quiet --rebase origin "$(git branch --show-current)"
git add journal/ reports/ conversations/ data/live/events/ 2>/dev/null || true
if ! git diff --cached --quiet; then
  git commit --quiet -m "Live desk: end-of-day paper trades $(TZ=Asia/Kolkata date +%F)"
  git push --quiet origin "$(git branch --show-current)"
fi
