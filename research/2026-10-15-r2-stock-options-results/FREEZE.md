# Freeze record: R2 stock options around results (feasibility)

Frozen at commit `93a19c318003994c6cedd070d038ee89d45dd74e` (15 Oct 2026 IST), before any data of this study was
read: no stock-option volume, open interest, lot value, strike step, price, spread or event move. Nothing ran before
it. Ledger trial 53 names this commit.

| File | SHA-256 |
|---|---|
| `PROTOCOL.md` | `89947b4cacbdf4ad87ee956dfb6dca6e5e2b4cc1241b6556a8e1515be6e40a6b` |

The analysis script's hash is added here in its own commit before the first full run (`PROTOCOL.md` section 11).
Merging this branch into `main` must keep the freeze commit in history (a merge, never a squash or rebase), or B4's
ledger guard refuses the trial.

Check before reading results: `sha256sum -c` on the files above at the run commit.

## Pre-run amendment 1 (15 Oct 2026)

`AMENDMENT_1.md` (judge 97's follow-ups 1-3 and 5, and data details the protocol leaves open) is committed before
`study.py` and before any data of this study is read. It changes no threshold and no rule chosen with an outcome in
view; `PROTOCOL.md` keeps its hash above and governs.

| File | SHA-256 |
|---|---|
| `AMENDMENT_1.md` (revision 1, judge 109; the first version was `8b36416b...1da47d`) | `3b84ecae577fd3d8ab2426d788646e19fcbb338e3d40551fe41cf27e6435d1e6` |
