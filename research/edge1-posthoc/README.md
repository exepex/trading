# EDGE1 post-hoc checks (outside the frozen study)

Run after the frozen runs, never decided on; kept here, outside `research/edge1/`, so the study's guard is unchanged.
Each reads the same inputs as the study (Drive through the verified cache, the row cache in `work/edge1/`).

| Script | When | What it prints |
|---|---|---|
| `passer.py <tree>` | after run 1's re-run, for the owner's side-by-side (run with `<tree>` = a checkout of 3152ed44, then of 81f02afe) | BANKNIFTY SF TP50's 16 Nov 2021 cycle and the decided mean with and without it |
| `today_lot.py` | after run 2 | the passer re-run at today's lot (30) in run 1 and run 2 |
| `tp_check.py` | after run 2 | per run-2 trade of the passer: days, fully traded and valid days, the lowest mark / credit |
