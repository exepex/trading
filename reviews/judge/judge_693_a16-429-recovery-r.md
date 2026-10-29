# Judge 693: A16 429 recovery, Judge R

Branch `story/a16-429-recovery`, SHA 52ad50d47b1a36300113b5298119166ef675741a. Judge R
(session_01KR5SiKNBq2bYMHtd8GbdN6), judge 1 of 2; Judge S's verdict not read. **FAIL** (1 should fix, 1 minor). Lane 1.

## Criteria

| # | Criterion | Result | Evidence |
|---|---|---|---|
| 1 | The problem as stated | MET | 26-29 Oct ledger on main: 104 marks, 21 incomplete, 19 with `quotes_failed` 23-117; 29 Oct 10:15 `quotes_failed:112;quotes_retried:129` |
| 2 | Retry waits out the pause, never calls inside it | MET | `_wait_out_pause`; the estimate is the source's answer time + 60.5 s, later than the guard's own `start()` (`groww_rate_guard.py:46`), so it is safe; `GrowwRateLimitPaused` has no code, so a refusal never extends it (`is_rate_limit`, line 32) |
| 3 | Nothing at or after the 120 s window; retry skipped with a note | MET | skip branch; plant P2 caught |
| 4 | Pace unchanged; non-429 failures unchanged | MET | same pool and pacer; no wait when `_pause_ends` is None |
| 5 | First 429 kept | PARTLY | written once, but no test has two 429s (plant P4 survives) |
| 6 | Several 429s: wait for the latest pause | PARTLY | `max(...)` is right, but untested (plant P6 survives) |
| 7 | Gates | MET | ruff check and format, `check_imports`, `check_records` clean; pytest 18,071 passed, 2 failed: both in `tests/forecast_v5_v1/test_v5v1_report.py`, which also fail on a clean origin/main (checked) |

## Findings

1. **Should fix: no test with more than one 429.** With 4 workers, the calls already in flight when the first 429
   lands are likely to get 429s too. Each one restarts the guard's pause (`RateGuardedGroww._guarded` calls
   `_pause.start()` on every 429). Two plants pass all 12 tests:
   - P4: overwrite `_first_429` on every 429, so the note keeps the last 429 instead of the first.
   - P6: keep only the first 429's pause end, so the retry starts inside the second pause and is refused again.
   This is the 29 Oct failure coming back. Fix: a test with two or more 429s a few hundred ms apart, under the real
   guard, asserting the note names the first, no call is sent before the last 429's pause ends, and the loss bound
   still holds.
2. **Minor: the new notes also go into the public ledger.** `doc.notes` feed `SlotVerdict.failures`
   (`status.py:76`), which `taken_row` writes to the committed slot CSV (`ledger.py:60`). So `first_429: quote <symbol>
   sent ... answered ...` and `quotes_retry_skipped: ...` land in `research/data/intraday/slots/`, not only in the
   Drive raw file. The record scan passes it (I checked a sample row: clean), and a contract symbol is a public
   instrument, not a strategy. But `status.py`'s rule is "failed contract quotes are counted, not listed one by one,
   so a ledger row and an alert stay readable". Say so in the story's Claims, or keep only the class and times in
   the ledger.

## Plants

6: P1 no wait (3 tests fail), P2 no skip (1 fails), P3 no 429 note (5 fail), P5 a pause 5 s short (4 fail): caught.
P4 last 429 instead of first, P6 first pause end only: survived (finding 1).

## Notes

- The 0-4 unasked quotes after an early 429 (5 s + 55 s + 60 s = 120 s) are an honest bound; widening the window or
  the pace is GW1's call, as the story says.
- The two `test_v5v1_report.py` failures are red on main itself; someone should own them (reported to the
  orchestrator).
- No Groww command was run. Merge only after both PASS and after 15:35 IST.
