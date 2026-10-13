# Checks of the NIFTY option-chain panel (story A3), 13 Oct 2026

Data checks only: no strategy or trial result is read here, so nothing is registered in `research/LEDGER.md`.

| Script | What it checks | Result file | Result (build of 13 Oct 2026, 2019-01-01 to 2026-10-12) |
|---|---|---|---|
| `check_panel.py RAW_FOLDER` | For every session: both raw files' SHA-256 equal the manifest; NIFTY option rows counted in the raw F&O file with plain `csv` equal the manifest's and the panel's rows of that day; every row's `underlying`/`vix` equal that day's Nifty 50 / India VIX close; size per year | `counts.json` | 1,928 days checked, 0 problems |
| `compare_extract.py` | Criterion 10: every contract of the capacity screen's extract (`research/2026-10-12-capacity-screen/data/nifty_options.csv.gz`, UDiFF, 2024-01-01 to 2026-10-09) is in the panel with the same close, settlement, volume, open interest and underlying; same days | `compare_extract.json` | 249,958 of 249,958 contracts found, 0 value differences, 689 = 689 days |

`RAW_FOLDER` is a local copy of the Drive project folder (`raw/nse/...`), read-only copied from Drive for the build.
The underlying comparison also shows that UDiFF's `UndrlygPric` equals NSE's Nifty 50 index close on all 689 days
(for the contracts in the extract), the assumption the old-format reader rests on (story A2).
