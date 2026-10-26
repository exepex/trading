# Judge 690: STAB1 capture only, `story/stab1-capture-only` at 15c05b394, judge P

**PASS**, lane 1 (config switches, scheduled workflows, the daily run). 0 blocking, 0 should fix, 2 minor. Second
judge: Q.

## Criteria

| # | Criterion | Verdict | Evidence |
|---|---|---|---|
| 1 | Every forecasting step records `not_live` / "school off"; day ends `day done` | MET | `test_every_forecasting_step...` builds the real wiring for 26 Oct, 27 Oct and 2 Nov. `problem_steps` ignores `not_live` (test). Plants that switch weather, price_ranges, premium_range_scores or school back on are all caught |
| 2 | Captures keep their steps and parts | MET | Plants `v4_pack: null` and `close_recheck: null` are caught. The v4 part starts with nifty, nse and indices on all 3 sessions. `git diff` touches no capture code |
| 3 | v4 capture key apart from the release key | MET | `wiring.py:262` uses `live[V4_RELEASE_STEP]`, and `v4_part.py:35` keeps `V4_PACK_LIVE_KEY`. The `step_notes` plant is caught by `tests/rehearsal/test_v4_pack.py` |
| 4 | Four forecasting workflows lose `schedule`/`push`; others unchanged | MET | The diff touches only those 4 workflow files. Plants restoring the `forecast-scores` schedule and the `v4-fire` push are caught. Every other workflow still has its own trigger (yaml read) |
| 5 | Lab editions and `recommend check` build nothing when not live | MET | Plants on the eager `build_composer`, the eager `records` and the ungated `recommend check` are caught |
| 6 | Health expects no forecast record and keeps every capture | MET | `expectations.py:79-82` use `FORECASTS_FROM = None`; the capture rows are unchanged; the plant is caught |
| 7 | No false alert from a switched-off item | MET | `not_live` is not a problem step. capture-watch only fires on runs that happen, and these 4 workflows no longer run. O8 has no other forecast row: grep of `fno/health` for weather, ranges, recommend, lab and school finds none |

## Hunt (not claimed, checked)

- Hidden captures inside the switched-off steps: none. `weather capture` reads stored global cues (`fno/weather/wiring.py:18`, `CueReader`). `pricedist`, `pricerange` and `premrange` read the 3 pm snapshots. The v4 capture writes its own `.canonical` (`v4_part.py:33`); the release only reads it.
- The desk (E3, Book 1, E6) reads no weather, card, range, recommend or lab output: grep of `fno/desk`, `fno/books` and `fno/evaluation` finds none. This agrees with the owner's 25 Oct "Correction: Books 1, 2 and 3 stay" (DESK_DECISIONS row 355).
- The owner's scheduled tasks (read with list_triggers, read-only): the Book 2 and Book 3 forecast routines and the weekly post-mortem routine have no cron. They are fired only by the workflows STAB1 de-triggers. A16, pre-open, the morning and evening routines and the P0b probe are unchanged.
- Gates on 15c05b394: `pytest -n 3` 18077 passed, 1 skipped, 13 xfailed. ruff, ruff format, `check_imports` and `check_records` are clean. Main has moved since the base by lane-3/docs files only, with no code.

## Minor (fix with the next push; not blocking)

1. CLAUDE.md "Daily desk routine" step 2 still says the v4 release runs "from `daily.live_from.v4_pack`". That is now wrong: it is `v4_release`. A routine reads this text, and one functionality should have one correct description. Fix: say `v4_release`.
2. `test_exactly_these_workflows_are_manual_only` does not catch a capture workflow that loses one of several triggers. My plant renamed `index-closes`' `schedule` key and survived. Criterion 4 is met by the diff, but the guard is weak for the future. Fix: pin each workflow's trigger set.

## Plants

14 planted (config 5, wiring 1, lab 2, recommend 1, health 1, workflows 3, step notes 1). 12 caught on their own. The step-notes plant was caught only once `tests/rehearsal` was added. 1 survivor (minor 2).

## Notes for the orchestrator

- Your scheduled task "Check November refit ratios stored" (2 Nov) tells a session to run `forecast-v4 capture-pack` by hand. With forecasting off, that is a forecasting step run by hand: cancel it or reword it.
- The REC1 and school reminder tasks (26-27 Oct) will find no record. That is expected, not a failure.
- The owner's open questions in the story still need answers: the weekly data-health summary is now off, and v4's freeze record.
