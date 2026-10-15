# Judge 200: G10 part 2, live and close-proxy cohorts: `story/g10-cohorts` 0b47894f (lane 1, scoring output)

Judge B. A16/G8 builder. This is judge 189 item 3 (G10 criterion 3: "live and close-proxy cohorts reported apart").
The LR1 reader change is also reviewed by the LR1 builder (orchestrator's go (b)). One commit, from `main` ab1cc442.

## Checks
- **The code.** `question_report` now builds two `Cohort`s, `close_proxy` (rows with `live` False) and `live`. In
  each, the forecasters, the primary baseline and the base rate are filtered to that cohort (`_in_cohort`, by
  `v.live is live`), and a forecaster appears only if it has rows there. `member_comparisons` (the looks) is
  unchanged: after the freeze it already counts only live rows.
- **Text and JSON.** The text has one heading per cohort. The JSON has `cohorts.{close_proxy, live}.{scores,
  comparisons}`, and the pooled top level is gone.
- **Other consumers.** A grep finds no other reader of the v4 report's top-level `scores` or `comparisons`. LR1 is
  updated, and it reads pre-G10 reports as `close_proxy`.
- **Real data, reproduced myself.** I ran `forecast-v4-scores report --as-of 2026-10-15` on the merge base and on this
  branch. Every scored question's `close_proxy` scores and comparisons equal the old pooled block exactly, and the
  `live` cohort is empty: today no v4 row is live.
- **My plants.**
  - Pooling the primary baseline across cohorts fails 1 test.
  - Pooling only the base rate fails none. That has no real effect, though: live and back-fill rows never share a day
    (the back-fill stops before the first live record), so the paired days are identical. One-line note, not a
    finding.
  - The builder's plants (pooling `_in_cohort`, a legacy report read as live) are claimed caught.
- **Gates on 0b47894f.** `-n auto`: **6,522 passed, 0 failed**. Ruff is clean.

## Notes (not blocking)
1. The base-rate filter's correctness rests on "no day has both a live and a back-fill row". That holds by
   construction today. If a re-run back-fill ever covered live days, a test with an overlapping day would be needed.
2. This changes `fno/forecast_scoring/v4/`, so merge it **before** the v4 freeze commit, as the builder says.

**Verdict: PASS for 0b47894f.** The LR1 part is subject to the LR1 builder's review, as agreed.
