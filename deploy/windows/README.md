# Running the live desk on a Windows machine

A spare Windows 10/11 PC that stays on is enough for the paper-trading month. Everything here moves unchanged to a
Mumbai cloud VM later (`deploy/README.md`). The desk never places real orders.

## 1. Install once

1. **Python 3.12 or newer** from python.org. In the installer tick *Add python.exe to PATH* (the `py` launcher is
   installed by default).
2. **Git for Windows** from git-scm.com (defaults are fine). The first `git push` opens a browser window to sign in to
   GitHub; Windows then remembers it.
3. **Clone the repository** in PowerShell:
   ```powershell
   cd $HOME
   git clone https://github.com/exepex/trading.git
   cd trading
   git checkout claude/beautiful-pascal-566jb5   # until the pull request is merged into main
   ```

## 2. Set up the desk

```powershell
powershell -ExecutionPolicy Bypass -File deploy\windows\setup_windows.ps1
```

The first run creates `%USERPROFILE%\.trading.env`. Open it (`notepad $HOME\.trading.env`), paste your
`FNO_SLACK_BOT_TOKEN`, save, and run the script again. It then installs the packages, runs the tests, keeps the PC
from sleeping, and registers two scheduled tasks:

| Task | When | What |
|---|---|---|
| FNO Live Desk | at logon, restarted within a minute if it stops | scans during market hours, keeps paper trades, posts to #fno-desk |
| FNO End of Day Sync | weekdays 16:00 | saves the day's trades and results to GitHub |

## 3. Keep it running

- Stay logged in (locking the screen is fine). After a reboot, log in once and the desk starts by itself.
  Optional: enable automatic sign-in (`netplwiz`) so a power cut or update restart needs no action.
- In Windows Update, set *active hours* to 08:00-17:00 so updates never restart the PC during the session.
- Use a wired connection if you can.

## Everyday commands (PowerShell, in the trading folder)

| What | Command |
|---|---|
| Status: open trades, today's P&L | `.venv\Scripts\python -m fno live status` |
| One diagnostic scan now | `.venv\Scripts\python -m fno live scan-once` |
| Signal accuracy so far | `.venv\Scripts\python -m fno live signal-report` |
| **Kill switch** | `.venv\Scripts\python -m fno live kill "reason"` |
| Release the kill switch | `.venv\Scripts\python -m fno live resume` |
| Today's log | `Get-Content logs\live-desk-$(Get-Date -f yyyy-MM-dd).log -Wait` |
| Update the code | `git pull`, then `Stop-ScheduledTask "FNO Live Desk"; Start-ScheduledTask "FNO Live Desk"` |

## Claude Code on this machine

Install Claude Code for Windows (see https://code.claude.com/docs) and sign in with your Claude account. The AI desk
(docs/AI_DESK_PLAN.md) will run its analyst roles through it, and you can work with Claude on this machine directly.
