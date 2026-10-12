# Running the desk on any machine

One setup and one set of commands for Windows, Linux and macOS. Use the always-on Windows PC for the paper month
and a Mumbai cloud VM later: the steps are the same. The desk never places real orders.

## Install once

1. **Python 3.11 or newer** (python.org; on Windows tick *Add python.exe to PATH*) and **git**
   (Windows: Git for Windows). Set the machine's time zone to **India Standard Time**.
2. Get the code:
   ```
   git clone https://github.com/exepex/trading.git
   cd trading
   git checkout claude/beautiful-pascal-566jb5     # until the pull request is merged into main
   ```
3. Run the setup (Windows: `py deploy\setup.py`, Linux/macOS: `python3 deploy/setup.py`).
   The first run creates `~/.trading.env` (`%USERPROFILE%\.trading.env` on Windows). Put your
   `FNO_SLACK_BOT_TOKEN` in it and run the setup again. It then installs everything into `.venv`, runs the tests,
   registers two jobs with the machine's own scheduler (Task Scheduler on Windows, cron elsewhere) and starts the
   desk.

| Job | When | What |
|---|---|---|
| FNO Desk Watchdog | every 5 minutes | starts the desk if it is not running (after a reboot, crash or update) |
| FNO End of Day Sync | weekdays 16:00 | saves the day's paper trades and results to GitHub |

On Windows the jobs run while you are logged on (a locked screen is fine). Optional: automatic sign-in
(`netplwiz`) so a restart needs no action. Set Windows Update *active hours* to 08:00-17:00.

## Everyday commands

Same on every machine. `PY` means `.venv\Scripts\python` on Windows and `.venv/bin/python` elsewhere.

| What | Command |
|---|---|
| Is the desk running? | `PY deploy/desk.py deploy status` |
| Open trades and today's P&L | `PY deploy/desk.py live status` |
| One diagnostic scan now | `PY deploy/desk.py live scan-once` |
| Signal accuracy so far | `PY deploy/desk.py live signal-report` |
| **Kill switch** (close all paper trades, no new ones) | `PY deploy/desk.py live kill "reason"` |
| Release the kill switch | `PY deploy/desk.py live resume` |
| Restart after `git pull` | `PY deploy/desk.py deploy stop` (the watchdog starts it again within 5 minutes) |
| Remove everything from the scheduler | `PY deploy/desk.py deploy uninstall` |

Logs: `logs/live-desk-<date>.log`.

## Claude Code on the machine

Install Claude Code (https://code.claude.com/docs) and sign in with your Claude account. The AI desk
(docs/AI_DESK_PLAN.md) will run its analyst roles through it, and you can work with Claude there directly.
