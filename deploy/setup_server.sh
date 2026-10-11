#!/usr/bin/env bash
# One-time setup on a fresh Ubuntu 24.04 server (AWS Lightsail Mumbai). Run as the login user, not root:
#   bash deploy/setup_server.sh
set -euo pipefail
REPO_DIR="$HOME/trading"
ENV_FILE="$HOME/.trading.env"

sudo timedatectl set-timezone Asia/Kolkata
sudo apt-get update -qq
sudo apt-get install -y -qq python3-venv python3-pip git chromium-browser

cd "$REPO_DIR"
python3 -m venv .venv
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q -r requirements.txt
.venv/bin/python -m pytest -q

if [ ! -f "$ENV_FILE" ]; then
  cat > "$ENV_FILE" <<'VARS'
# Secrets for the F&O desk. Readable only by you (chmod 600). Never commit this file.
FNO_SLACK_BOT_TOKEN=
# Optional, only for the MotherDuck options in config.yaml (shared with the market-brief tool):
MOTHERDUCK_TOKEN=
# Groww Trade API, once subscribed:
GROWW_API_KEY=
GROWW_API_SECRET=
VARS
  chmod 600 "$ENV_FILE"
  echo "Created $ENV_FILE: fill in the values, then re-run this script."
  exit 0
fi

sudo cp deploy/fno-live.service "/etc/systemd/system/fno-live@.service"
sudo systemctl daemon-reload
sudo systemctl enable --now "fno-live@$USER"
( crontab -l 2>/dev/null | grep -v end_of_day_sync; echo "0 16 * * 1-5 $REPO_DIR/deploy/end_of_day_sync.sh >> $HOME/eod_sync.log 2>&1" ) | crontab -
echo "Live desk running. Logs: journalctl -u fno-live@$USER -f"
