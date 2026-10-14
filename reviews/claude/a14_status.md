# A14 status (builder session 01FVYzWZtDAZrZLDZ6DtmSYL)

Updated: 14 Oct 2026, about 08:58 IST. Branch `story/A14-nse-margins`, draft PR #90, issue #89.

**Ready for judge** at code tip `9f8b815` (main merged at a52c82e; this status file is the only later
commit). Full suite 2,357 passed on the merged tree; ruff, ruff format --check and `tools/check_imports.py` clean.

Judge 77 must-fixes (claims response 77, section "Judge 77 must-fixes"):
1. Mirror never-looser test: open debit BF then new credit SF (and all 4 orders, 14 books), C2 equal to the broker to
   the paisa. The judge's plant (dropping the proposal's own liability) now fails 3 tests.
2. Exposure gap, option (a): the job writes no row until `config.yaml` `risk.margins.nse_span_check` records a passed
   broker check (source and passed_on; both null now). Until then it prints rows, writes none, refused by name.
   Plant (switch off) fails 4 tests. Criterion 1 stays NOT MET until the owner's Groww check.

Not merged into main.
