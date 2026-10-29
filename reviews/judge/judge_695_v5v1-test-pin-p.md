# Judge 695: T-v5v1-test-pin, `story/v5v1-test-pin` at 1ea429bfc, judge P

**PASS**, lane 1 (tests of forecast records, by the orchestrator's order). 0 findings.

## Criteria

| # | Criterion | Verdict | Evidence |
|---|---|---|---|
| 1 | Root cause is growing data, not code | MET | On `origin/main` (adf6ebf54; no `fno/`, `tests/` or config change since base 24b2f70) both tests fail: 2 failed, 6 passed. The pairing (`candle_history.py:58-64`) and `score` (`report.py:40-56`) are correct on the new rows: 26 Oct is now present, so 23 Oct is scored, not pending |
| 2 | Assertions not weakened | MET | The diff changes only the inputs' day range (`d <= LAST_PINNED_DAY`) and adds one precondition (`live[16 Oct]` and `live[23 Oct]` void, 26 Oct absent). Every expected value is unchanged |
| 3 | Tests still test real code on real data | MET | Plants: pending as scored, void as scored, a zero live value paired, and removing the pin. All 4 caught |
| 4 | Production code, data, records untouched | MET | `git diff --stat`: the test file, the story, one register row |
| 5 | No other test drifts the same way | MET (spot-checked) | The remaining `live_rv()` callers in the file score only days ≤ 22 Oct (targets ≤ 23 Oct) or compare against v4's own outcomes read from the same rows. `test_v5v1_history.py` and `test_v5v1_capture.py` cut at a fixed day |

## Plants

4 planted, 4 caught.

## Notes

- Gates I ran on the branch: `tests/forecast_v5_v1` 74 passed; ruff, format and `check_imports` clean. I did not
  re-run the full suite: the change is one test file, whose folder I ran. The builder reports the full suite on the tip:
  18060 passed, 1 skipped, 13 xfailed.
- Write-once A16 rows mean the pinned slice cannot change. A later hand-edit of a 16-23 Oct row would break these tests,
  which is the intended guard.
