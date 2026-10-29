# T-v5v1-test-pin. Two G14 report tests read rows that grow every session

**Repository:** trading. **Owner:** this builder session (orchestrator session_01Mt6dcBU5kp2htdPN2KmiZH). **Lane 1**
by the orchestrator's order (tests of forecast records; Judge P). **Status:** built on `story/v5v1-test-pin`, waiting
for Judge P.

**Description:** As the maintainer, I want `tests/forecast_v5_v1/test_v5v1_report.py` to give the same answer on every
day, so that `main` stays green as A16 and A16b add rows each session.

**Root cause (proved):** both tests read the committed realised-variance rows (`live_rv()`, `candle_rows()`). A16 has
rows for 26-29 Oct since the tests were written on 23 Oct. Reproduced on clean `origin/main`:
- `test_the_gap_table_prints_19_21_and_22_oct`: the table has 6 rows (`0.962 ... 1.008 1.036`), not 3, because 26-29 Oct
  now have an ok live row and an ok candle row.
- `test_a_void_or_unrecorded_live_target_is_never_resolved_by_a_candle_row`: its own comment says "26 Oct has no live
  row yet"; 26 Oct has one now (1.065e-4), so 23 Oct's forecast is scored (1, 0), not pending (0, 1).
The production code is correct and unchanged: the pairing and scoring behave as designed on the new rows.

## Fix

The two tests read the rows only as of 23 Oct (`LAST_PINNED_DAY`, two small helpers in the test file). Every assertion
is unchanged, and the pinned slice is the real committed rows, so the tests still read real data: 16 Oct void, 23 Oct
void, 26 Oct absent. No data, record or production file changes.

## Other tests that read growing live data (audit)

Searched every test using `live_rv`, `candle_rows`, `live_rows`, `candle_history`, `intraday_rv`, `candle_rv`,
`INTRADAY_FOLDER`. Passing now and kept: `test_v5v1_history.py` and `test_v5v1_capture.py` (take a fixed day `d` or
`oct(26)` and cut the history at it), `test_v5v1_report.py`'s other tests (explicit `SESSIONS`, expected values for
fixed days), `test_v4rules_candle_history.py` (compares the reader to itself). Unaffected: `test_g7_series.py`
(fake series), `test_v4rules_w8.py` line 44 (checked: asserts structure, passes). Left unchanged: none fail.

## Claims

| Claim | Evidence |
|---|---|
| Root cause is growing data, not code | Both failures reproduced on clean `origin/main`; values above come from the failing output and `live_rv()` |
| Assertions not weakened | `git diff` changes only the inputs' day range and one added precondition check |
| Production code and data untouched | diff touches only the test file, this story and the register |

**Gates (29 Oct 2026):** ruff check, ruff format --check, `tools/check_imports.py` clean; `python -m pytest -q -n auto`
(FNO_SLACK_BOT_TOKEN set): 18060 passed, 1 skipped, 13 xfailed. A first run in a shallow clone showed 22 failures and 9
errors in freeze and git-history tests; they pass after `git fetch --unshallow` (a clone limit, not this change).
