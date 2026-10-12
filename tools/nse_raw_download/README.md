# NSE raw download (run on your own computer)

Downloads NSE's daily F&O files from 2 Jan 2024 to today into your `fno-research` project folder. If that folder is
synced by Google Drive for desktop, Drive uploads everything by itself.

## Run

1. Install Python 3.9 or newer (python.org). No other packages are needed.
2. Unzip this folder anywhere, open a terminal in it and run (use your own Drive path):
   - Windows: `python nse_raw_download.py --dest "G:\My Drive\fno-research"`
   - Mac: `python3 nse_raw_download.py --dest "$HOME/Library/CloudStorage/GoogleDrive-<you>/My Drive/fno-research"`
3. It takes about 25-40 minutes for 2024-2026 (one request per second, about 1 GB). You can stop it (Ctrl+C) and run
   it again at any time: files already there are checked and skipped.

Options: `--start 2025-01-01` and `--end 2025-12-31` limit the dates.

## What it does

- Saves to `fno-research/raw/nse/derivatives/fo-bhavcopy/<YYYY>/<MM>/<NSE file name>`, the layout the research tool
  reads (see `fno/storage/README.md` in the repository).
- Checks every file against `manifest.csv` (the SHA-256 fingerprints recorded when the research data was built,
  2024-01-01 to 2026-10-09). A file that differs is reported as MISMATCH and never saved or overwritten.
- Skips weekends and the holidays listed in the manifest; for later dates it asks NSE and reports "no file" on a
  holiday.
- Stops at once if NSE refuses requests (HTTP 403/429), so your IP address is not blocked; run it again later.
- Ends with a summary: saved, already there, no file, mismatch. Exit code 1 if anything mismatched.
