# Judge 598: G7b completion code, steps 5, 6 and 7, `story/g7b-completion` at bc1260a36 (round 1 of 2, judge K)

**FAIL, lane 1.** 1 blocking, 1 should-fix, 2 minor. The rules as coded match the passed text (judges 578.1, 591.2).
The branch fails against current main.

## Gates (trial merge of bc1260a36 into origin/main cd9b555f3, Slack token set)

- **Conflicts:** `config.yaml` and `tests/daily/test_steps.py`. Main now has `daily.live_from.v4_pack: "2026-10-26"`;
  the branch still has null. I resolved this only in my local trial copy, keeping main's date and adding
  `forecasts_v4_pack: null` (never pushed).
- **pytest -n auto: 15,843 passed, 1 skipped, 15 xfailed, 4 errors, exit 1.** ruff check and format, `check_imports`
  (2,667 files), `check_records` and `check_numbers` are clean.
- **No test posted to Slack:** #fno-desk, #fno-forecast and #fno-intraday are empty for the run's window
  (15:35:41-15:47:18 24 Oct UTC).

## Criteria (this slice)

| Item | Verdict | Own evidence |
|---|---|---|
| Write-once live rows, terms and outcomes; deadline before every write; `system_late` writes nothing | MET | `pack_capture.py:166-192`; plants "system_late written", "deadline exclusive", "changed row allowed" caught |
| Pack binding: pack rows name the released SHA, base rates none | MET | `check_pack_binding` per row against the release record's SHA; plants "base rate names pack" and "release SHA taken from the bytes" caught |
| W8: the back-fill only where A16 has no live row (void included) | MET | `pack_wiring.intraday_rv`; plant "back-fill overrides live" caught |
| W8 review trigger, [0.95, 1.05] over 20 days, raised once | MET | plants "band exclusive" and "void live paired" caught |
| V4 and V5 outcomes from stored terms; void stays void | MET | plant "void V4 terms read as no" caught; V5 resolved before the base rate (`pack_wiring.py`), see m1 |
| Proxy drift pairs `d` with `d`'s EOD | MET | plant "drift waits for d+1" caught |
| The future's traded flag from volume > 0 | MET | plant "zero volume counts" caught |
| Stored monthly ratio, never late | MET as coded | plant "late ratio" caught; but see SF1 |
| Criterion 21: closure hash | MET (claims) | `PACK_METHOD_FILES` walks the import closure from `pack_wiring.py`; not re-planted by me |
| O1 step after `v4_release`, own receipts, `not_live` while null | MET | `constants_operations.py`, `daily/wiring.py` diff; `LIVE_STEPS` gains the key |

## Findings

1. **Blocking: red on main, 4 errors.**
   - The errors are in `tests/forecast_scoring_v4/test_v4_needs_no_implied_vol.py` (2) and `tests/forecast_v4/test_iv_never_used.py` (2).
   - Main's new fixture `tests/forecast_scoring_v4/conftest.py` patches `fno.forecast_scoring.v4.wiring._drive_records`. The branch renamed that seam to `build_drive_records`, and the fixture's own docstring says G7b updates it.
   - I tried the rename alone: 2 tests still fail, `'NoDriveRecords' object has no attribute 'paths'` (`wiring.py:123`).
   - **Fix:** merge main; resolve the two conflicts as above; point `SEAM` at `build_drive_records`; give `NoDriveRecords` a `paths()` returning `[]`; run the full gates on the merged tree.
   - The Claims' "15,735 passed" holds only for the branch alone.
2. **Should fix: the monthly ratio needs no pack, but it is stored only when a pack was released.**
   - The ratio is written only inside `capture_pack`, through `PackForecasts.values`. `capture_pack` stops at `system_late` before reaching it. A missing release record raises `NotReleased` in `build_pack_capture`.
   - So a refit day (the first session of a month; the next is 2 Nov) that is `system_late`, or has no release, leaves the whole month with no ratio. Every V1, V2 and V3 premium-adjusted row is then `not_eligible`, and that includes **V2's primary, a family member's**: a month of its pairs is gone because of one pack failure.
   - The ratio reads only the EOD proxy, the closes and A16 or A16b rows, all from before the refit day.
   - **Fix:** on the refit day, store both measures' ratios whatever the release label, and before the release check. Test: a `system_late` refit day stores the ratios; the next day reads them; a non-refit day writes none.

## Rulings asked for

- **Item (3), the late-ratio text:** take the stricter rule. Change the text to "a refit day with no capture run leaves the month not eligible, counted; never a late ratio". State its cost in one line: a missed run on the refit day loses the month's premium-adjusted rows, V2's primary included. With SF1 fixed, that is only a day the routine does not run at all. The orchestrator's view is accepted: KISS, point-in-time safe, and the receipt-time filter would need each input's commit time.
- **Item (6), rejection accepted:** the ratio reads no pack and no clock, and every window point resolves before the refit day. A write after 15:10 gives the same bytes as one at 14:45. Only forecast rows need the deadline.

## Minor

- **m1:** the plant "V5 outcomes settled this run not added" (removing `history.with_v5_outcomes(written)` in `build_pack_capture`) survives. The test checks the helper alone, not the composition root. The effect is conservative (one run's lag).
- **m2:** `level_line` drops pairs whose close proxy is exactly 0 (`b > 0`). A ratio of sums should keep them (they add 0 to the denominator). This is rare.

## Plants

- **Mine: 14.** 12 caught. Survivors: m1, and "capture filter removed", which is equivalent as the builder says (`BaseRate.forecast` filters `resolved_on < d` itself).

## Addendum 1: the newer head `story/g7b-completion` at bcbf70e9e (still round 1, at the orchestrator's request; judge K)

**FAIL, lane 1.** 0 blocking, 1 should-fix (SF1 unchanged), 2 minor. This judges the whole steps 5-7 slice at
bcbf70e9e, which replaces bc1260a36. The head was built before my verdict above reached the builder, so this is still
round 1.

**Gates on a trial merge of bcbf70e9e into origin/main 6b09c4548** (no conflicts; Slack token set): `pytest -n auto`
15,935 passed, 1 skipped, 15 xfailed, exit 0; ruff check and format clean; `check_imports` (2,679 files),
`check_records` and `check_numbers` clean. **No test posted to Slack** (15:50:44-16:00:22 UTC): #fno-forecast and
#fno-intraday are empty; #fno-desk holds only the orchestrator's labelled "DRY RUN, 2026-10-23 replay" lines and the
scheduled 16:00 health check.

| Item | Verdict | Evidence |
|---|---|---|
| Blocking 1 (red on main) | fixed | the fixture now patches `build_drive_records` and `NoDriveRecords.paths()` returns `[]`; the 4 errored tests pass in the full run above |
| New `candle_history.candle_sessions` (W8's one reader) | MET | reads only `rv-candle-15m-v1` with `backfilled` provenance; void decided by status; it is in `PACK_METHOD_FILES`. My 3 plants are all caught: provenance not filtered, method not filtered, void decided by value |
| Item (3) text | MET | the stricter rule is stated, with its cost ("about 21 sessions") |
| SF1 (ratio stored only on a released day) | **still open** | `ratio_store.py` and `pack_capture.py` are unchanged; the text now also writes the cost into the rule ("or the day was `system_late`") |

**SF1 stands, with my reason against the new text.** Writing the cost down does not make it necessary. The ratio
reads no pack, so a pack failure on a month's first session need not cost V2's primary (a family member's) about 21
sessions of pairs. The fix is small: store both measures' ratios on the refit day before the release check. The text
then reads "a refit day with no capture run at all", and the "or the day was `system_late`" clause goes. The test is
as in SF1 above.

Minor m1 and m2 above are unchanged.
