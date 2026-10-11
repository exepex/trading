# Running the live desk on a server

The live desk is a long-running process that scans all NSE F&O underlyings during market hours and keeps paper
trades. It never places real orders.

## One-time setup (AWS Lightsail, Mumbai)

1. Create an instance: Ubuntu 24.04, 2 GB RAM, region Mumbai (ap-south-1). Attach a **static IP** (Groww only
   accepts API orders from a whitelisted static IP; we register it now so going live later is one step).
2. SSH in, then clone the repo and give the server push access (a deploy key with write access on GitHub):
   `git clone git@github.com:exepex/trading.git ~/trading`
3. Run `bash ~/trading/deploy/setup_server.sh`. The first run creates `~/.trading.env`; fill in the values
   (`nano ~/.trading.env`) and run the script again. It installs everything, runs the tests, starts the
   service and schedules the 16:00 end-of-day save to GitHub.
4. Optional: install Claude Code on the server and enable Remote Control to work with Claude there directly.

## Everyday commands (on the server, inside ~/trading)

| What | Command |
|---|---|
| Live log | `journalctl -u fno-live@$USER -f` |
| Status: open trades, today's P&L | `.venv/bin/python -m fno live status` |
| One diagnostic scan now | `.venv/bin/python -m fno live scan-once` |
| **Kill switch**: close everything, stop new trades | `.venv/bin/python -m fno live kill "reason"` |
| Release the kill switch | `.venv/bin/python -m fno live resume` |
| Restart after a code update | `git pull && sudo systemctl restart fno-live@$USER` |
