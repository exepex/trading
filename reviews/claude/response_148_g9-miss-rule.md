# Response 148: G9 claims, missed forecasts in protocol v4 (revision 9)

Builder: Claude, 15 Oct 2026 IST. Branch `story/g9-miss-rule`. Lane 1 (forecast scoring and the v4 protocol before its
freeze). Story text: `docs/stories/G-forecasts.md` G9. Owner decisions: the 15 Oct rows "Missed forecast days: verdicts
on observed days only, with a miss cap" and "Test A stays undecided ..." (responses 144-147, judge 138-139, ChatGPT 112).

## What changed
- `fno/forecast_v4/misses.py` (new, pure): `MissReport` and `miss_report(rows, big_day)`. Counts from the forecaster's
  first forecast: misses (baseline present, forecast absent), 2% days among baseline days and among misses, input
  failures (neither forecast). `operations_undecided`: missed > 10% of baseline days, or 2% days missed > 10% of
  baseline 2% days, or any such miss when there are fewer than 10.
- `fno/forecast_v4/terms.py`: `MISS_CAP`, `BIG_DAY_MISS_CAP`, `BIG_DAY_ZERO_MISS_BELOW` (0.10, 0.10, 10).
- G8: `Comparison.misses`; `look.member_result` returns "not judged" for an operations-undecided member (never asks
  for thresholds, never a claim, never futile, so Test A stays undecided); the miss line in the look, the report text
  and both JSON outputs. The 2% day uses the same input as the scored window's regime (`Outcome.log_return`).
- `research/forecasts/PROTOCOL_v4.md` sections 4, 5 and 6 state the rule; `test_protocol_text.py` ties the numbers.

## Criteria
1. Miss, input failure, not started, unresolved and void: `tests/forecast_v4/test_misses.py` (first three tests). MET.
2. Both caps at their boundaries (10 of 100 / 11 of 100; 9 2% days with 0 or 1 miss; 10 with 1 or 2; 25 with 2 or 3)
   and an operations-undecided member through a full look (no threshold call, not judged, not futile, Test A
   undecided, miss line printed): `test_misses.py`, `tests/forecast_scoring_v4/test_look.py`. MET.
3. Miss counts on every comparison and look; protocol text equals `terms.py`. MET.

## Checks
- `python -m pytest -q`: see the merge note below for the full run on the merged tree.
- `ruff check fno tests tools`: clean. `python tools/check_imports.py`: clean. `ruff format`: applied.
- First full run on this session's shallow clone failed 9 history-based freeze tests (the clone had no history) and
  one A16b test that main has since fixed (c7910516); after `git fetch --unshallow` and merging main, they pass.

## For the judge
- Owner row of 15 Oct "G6 protocol v4: V6 becomes descriptive" is not in the code yet (`DESCRIPTIVE_ONLY` holds V7
  only); it goes through G6's path. G9 does not depend on it: a descriptive member is "not judged" before the miss
  check, and its miss line is still printed. With V6 descriptive, the miss rule matters for V1 and V2.
- Known limit (reasoning only): the zero-miss rule below 10 2% days is strict; one outage on a 2% day makes that look
  "undecided, operations". This is the owner's choice (ChatGPT 112) and can never cause a false "no".
