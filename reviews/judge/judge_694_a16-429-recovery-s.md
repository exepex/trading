# Judge 694: A16 429 recovery, judge S (2 of 2)

Branch `story/a16-429-recovery` at `52ad50d47`. **FAIL, lane 1** (2 should fix, 1 minor; the code is sound). Full
clone, gates run, no Groww command.

## Criteria

| # | Criterion | Verdict | Evidence |
|---|---|---|---|
| 1 | The problem is real (26-29 Oct) | MET | slot CSVs: 104 marks, 21 incomplete, 19 with `quotes_failed` 23-117 (29 Oct 10:15: 112 of 220), 2 `chain_empty` |
| 2 | (b) The retry waits out the pause, sends nothing inside it, skips when the pause outlasts the window | MET | `groww_source.py` `_wait_out_pause`, `_note_rate_limit`. `is_rate_limit` matches `code == "429"` only, so a refused `GrowwRateLimitPaused` never moves the pause end. The client is `RateGuardedGroww` (`providers/groww.py:142`). Plants 1-3 caught |
| 3 | (a) The notes keep the **first** 429 | PARTLY | code right (`if self._first_429 is None`); no test pins it (finding 1) |
| 4 | Pace stays at 4 a second; non-429 and no-429 marks unchanged | MET | `test_the_retry_never_goes_faster_than_4_a_second`; no sleeps in those tests |
| 5 | The stated limit of what it recovers | NOT MET | finding 2 |
| 6 | No new public data | MET | `notes` live in the Drive raw document (`document.py:114`), not in the slot CSV |
| 7 | Gates | MET | 18071 passed, 2 failed, 1 skipped, 13 xfailed. Both failures are in `tests/forecast_v5_v1/test_v5v1_report.py` and fail on `origin/main` `24b2f70ae` too. Ruff, format and `check_imports` clean |

## Findings

1. **Should fix: nothing tests that the notes keep the first 429 (claim (a)).**
   - The plant `if True:` in place of `if self._first_429 is None:` (the latest 429 overwrites the note) passes all of
     `tests/intraday`.
   - Why: `test_the_first_429_stays_in_the_notes...` gets its second 429 in the retry pass, and it checks only that the
     note starts with "quote NIFTY26".
   - Fix expected: assert the note's call name and answer time equal the first 429's, with a second 429 in the retry.
2. **Should fix: the "What it can and cannot recover" figures are wrong.**
   - On a 429 mark, the retry ends at about the first pass's end + 60.5 s, wherever the 429 falls. So quotes lost =
     (first-pass end − 59.5 s) × 4. With 228 quotes, the first pass ends at chain time + 57.25 s.
   - The builder's own harness gives:

     | Chain calls | 429 at quote 92 or 130 |
     |---|---|
     | 0 s or 2 s | 0 lost |
     | 4 s | 8 lost |
     | 5 s | 12 lost |

   - So "5 s of chain calls ... the last 0-4 quotes" is wrong. Only the observed first-pass ends (58-60.6 s) give 0-4.
   - Claim 1's "now 0 are lost" is shown with 0 s of chain calls (`mark_with(range(92, 93))`), the best case.
   - Fix expected: state the formula and the real chain times, and add a test at a realistic chain time that asserts the
     computed loss.
3. **Minor: one plant survived.**
   - Plant: `self._pause_ends or pause_ends` in place of `max(...)`, so the earliest 429's pause end is used instead of
     the latest.
   - It matters only for two 429s at almost the same moment from overlapping workers. A test or a note is enough.

## Plants

6 planted, 4 caught: no wait, margin −2 s, no skip, no first-429 note. 2 survived: findings 1 and 3.

## Notes

- Why A16 gets 429s at all is not addressed: alone it asks 240 a minute, under 300. That was out of scope by the
  orchestrator's go. It is worth GW1's look (another taker on the account?).
- A 429 on the index, future or chain calls still loses the mark: the chains are not retried. This is old behaviour,
  unchanged here.
- `forecast_v5_v1` is red on `main` (2 tests). The orchestrator should route it.

## Correction and tip check (round 1; not a new round)

- **Criterion 6 was wrong.** `doc.notes` do reach the repository: `status.py:76` copies them into the slot row's
  `failures` field (that is how `quotes_retried:N` already travels). The new `first_429` note adds one contract symbol
  (a public instrument name), two times and `GrowwRateLimited:429`, once per mark. I staged such a row in a real slot
  CSV and `tools/check_records.py --staged` printed "clean". So claim 7 (`be3057122`) is right: MET.
- **Tip `be3057122`:** tests and the story only; `fno/` is unchanged since `52ad50d47`.
  - Findings 1 and 3 are fixed: the in-flight multi-429 test catches both plants that survived before
    (overwriting `_first_429`, keeping the earliest pause end). 13 passed; the new test passed 3 runs in a row.
  - The test syncs real threads with a barrier, `sleep(0.15 × order)` and 5 s timeouts. A note on flake risk, not a
    finding.
- **Finding 2 is still open:** story lines 24-25 and 36 still say "5 s of chain calls ... the last 0-4 quotes".
