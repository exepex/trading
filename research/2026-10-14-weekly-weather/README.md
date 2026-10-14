# Weekly NIFTY options and a market-weather signal (14 Oct 2026)

The owner asked for a combined study. Verdict and roles' readings: `reviews/claude/response_93_weekly-and-weather.md`.

- `PROTOCOL.md`: every rule and threshold, frozen at `650dd8f` before any P&L or signal outcome; hashes in `FREEZE.md`.
- `study.py` builds the trades and the GREEN/AMBER/RED colour; `report.py` computes the tests. Run
  `python research/2026-10-14-weekly-weather/study.py`. `--check` prints data and fill counts only.
- `results.md`, `results.json`: the one run (byte-identical on a second run). `trades.json`: every opportunity, each
  structure's trade and the colour.
- Ledger trials 43-52 (`research/ledger.csv`), registered at `ea52245` before the run.
