# Response 302: A4f code, NIFTY weekly expiries and open interest in the 3 pm capture (builder's claims, for Judge F)

Builder session 01MKtUHByHsR9cNwaP5KhFYH. Branch `story/a4f-nifty-weekly-oi`, three commits after the story text merge
(dec56398): 075c1bd8 (step 1, the split), c4b9a6c3 (step 2, OI), fe89e640 (step 3, the weeklies). Story text: judge 433
PASS. Lane 1 (it touches the 3 pm quote record and Groww calls): not merged; I merge only after your PASS.

## What changed

1. **Split first (step 1).** `recorder.py` was at the size limit. The row builder and the CSV writer moved unchanged to
   `fno/quotes/snapshot_rows.py`. `recorder.py` re-exports `COLUMNS`, because the byte-frozen
   `tools/forecast_live_golden.py` imports it from there, and `quote_validity`, because E8's `desk/owner_timing`
   imports it from there. Both re-exports carry a noqa note saying why. The baseline fixtures were untouched in step 1.
2. **`open_interest` (step 2).** This is the last column. It holds the chain leg's OI as a whole number (`str(round())`,
   not `:g`, because `:g` keeps 6 significant digits and 12,345,675 would become `1.23457e+07`).
3. **Weeklies (step 3).**
   - `fno/quotes/weekly.py`: `nearest_weeklies` returns the two nearest listed expiries after today that are not
     monthlies.
   - `Slot` gains `weeklies` and `stem_suffix`.
   - `weekly_slot()` is A4c's index slot for NIFTY with `weeklies=2` and stem `niftyweekly`: the same 15:01-15:13 window,
     3 workers and 2.5 requests a second, recorded after BANKNIFTY, FINNIFTY and MIDCPNIFTY in `record-indices`.
   - Each run has its own dataset, `groww/derivatives/quote-snapshots-weekly`, and its own Drive-only store. No reader
     of `nifty_*.canonical` in A4's dataset can see it.
   - The index recorders moved to the new composition root `fno/quotes/index_wiring.py`; `composition.py` is now at 328
     lines. It is listed in CLAUDE.md.
   - O1's indices part adds the `niftyweekly_*` pathspec and the weekly canonical marker, which O1/O2 agreed to. A rerun
     restarts the part when only the weekly marker is missing (`tests/daily/test_part_resume.py`).
   - CLAUDE.md step 3b's `git add` line gains the `niftyweekly_*` glob.

## Judge 433's three minors

1. **Today's expiring weekly is not recorded.** At about 15:05 it has minutes left, and piece 2's next-session range
   cannot score it. The rule is `e > day`. Test: `test_today_s_own_weekly_is_not_taken_on_its_expiry_day` (13 Oct, a
   Tuesday expiry). If no weekly is listed after today, there is one attempt with no chain call, and the day ends `none`
   at once with reason `no NIFTY weekly expiry listed after today`; the reason counts as final, so it is not retried.
2. **Edges.**
   - The 5% band at spot 20000 keeps 19000.0, 19000.01, 20999.99 and 21000.0, and drops 18999.99 and 21000.01.
   - The stop: a request at 15:12:59 starts, one at 15:13:00 starts (the stop is inclusive, A4c's existing `sent >
     stop_at`), and one at 15:13:01 does not.
   - The judge's "15:12:59 versus 15:13:00" reads as if 15:13:00 should be refused. A4c's existing rule lets it start,
     and I kept that rule rather than changing A4c's behaviour inside A4f. Say so if you want 15:13:00 refused; that
     would be an A4c change.
3. **OI 0 versus missing.** A leg the chain lacks gives an empty cell. A leg the chain has with OI 0 gives `0`.
   - Groww's parser turns a missing field into 0 (`fno/providers/groww.py`, `or 0`), so the two cannot be told apart.
   - The rule is stated in `snapshot_rows.py`'s module docstring: readers treat 0 as unknown, never as "no open
     interest".
   - I did not change Groww's parser: that is A4's provider, shared by every reader.

## Planted-bug proofs (each made, its test run, then reverted)

| Planted bug | Result |
|---|---|
| `e >= day` (today's weekly taken) | 4 tests fail |
| stop exclusive (`sent >= stop_at`) | 1 test fails |
| band strict (`<` for `<=`) | 1 test fails |
| OI 0 written as an empty cell | 1 test fails (`test_open_interest.py`) |

## Claims you asked for

- **A4 baseline diff is only the new column.** A script compared every changed fixture under
  `tests/fixtures/quote_recorder_golden/` between dec56398 and fe89e640:
  - 5 CSVs, 52 lines: each new line is the old line plus exactly one last field;
  - 5 sidecars: equal once `csv_sha256` is removed.
- **Golden check:** `python tools/forecast_live_golden.py` prints "live golden cases unchanged: case_a, case_b".
- **Gates on fe89e640:**
  - `pytest -n auto`: 8963 passed, 17 xfailed;
  - `ruff check` and `ruff format --check`: clean;
  - `check_imports`: clean (1753 files);
  - record scan: clean.
  - `check_numbers` will run on `main` at merge.
- **First live day's weekly line and timing:** not yet observed; it is still owed. I report it after the first trading
  day once merged: the `NIFTY weekly` result line, its expiries, row count, request times and the end time against
  15:13. Expected cost: about 2 x 2 x 25-45 strikes, that is 100-180 extra book requests at 2.5 a second, about 40-75
  seconds after the other three indices. **This is reasoning only:** if the three indices already run close to 15:13, the
  weekly may be cut short (then it is incomplete and retried until 15:13, then `none`). The first live day will show it.

## Deviation and findings

- **Deviation:** the OI caveat is in the code docstring, not in the sidecar note, so the baseline diff stays the column
  only (plus `csv_sha256`).
- **Pre-existing, out of scope:** A4's `_num` writes `bid_qty` and `ask_qty` with `:g` too, so a quantity over 999,999
  loses precision. NIFTY's top-of-book quantities rarely get there; this needs its own fix (an A4 baseline change).
