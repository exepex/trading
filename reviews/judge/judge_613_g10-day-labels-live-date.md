# Judge 613: G10 day labels from the pack's live date, `story/g10-day-labels-live-date` at b6d307787 (round 1 of 2, judge K)

**PASS, lane 1** (forecast records, protocol text). 1 minor.

**Gates.** A trial merge of b6d3077872a33ad180bce33da3656d2e32b2f6db into origin/main 9bf78ce83 is clean (9 files). On it,
with the Slack token set:
- `pytest -n auto`: 16,287 passed, 1 skipped, 14 xfailed, exit 0.
- ruff check and format clean; `check_imports` (2,722 files), `check_records` and `check_numbers` clean.
- **No test posted to Slack** (17:38:45-17:49:16 UTC): #fno-forecast and #fno-intraday are empty, and #fno-desk holds
  only the orchestrator's labelled "DRY RUN, 2026-10-23 replay" lines.

## Checks

| Asked | Verdict | Own evidence |
|---|---|---|
| No path still writes or reads labels from `forecasts_v4` | MET | `grep -rn '"forecasts_v4"\|labels_from'` in `fno/`: the only uses left are the O1 step itself (`daily/wiring.py:146-147`, `constants_operations.py:61`) and the deadline run (`v4_pack/wiring.py:88`). The reader `build_day_labels` goes through `label_start(cfg)` = `live_dates(cfg)["v4_pack"]`; `ReleaseRun` lost `labels_from` and catches up from its own `live_from`. Plant "label_start back on forecasts_v4": caught |
| The deadline's start | MET (by reading; see m1) | `DeadlineRun(..., live[V4_PACK_LIVE_KEY], ..., live["forecasts_v4"])`: the 15:10 catch-up still checks the real commitments from 22 Oct. Report: "deadline not checked 2", i.e. 22 and 23 Oct. `require_checked(unchecked, counted_after, look_day)` (`forecast_scoring/v4/cli.py:86`) bites only for days after the freeze, so 22 and 23 Oct can never block a look |
| Boundary day, 26 Oct | MET | `missing_label` gives none before `live_from` and pending on today. Tests: on 26 Oct, no label and pending 1; on 27 Oct, 26 Oct `system_late` and 22-23 Oct unlabelled. Plant "day == live_from unlabelled": caught |
| Rehearsal path (RL3) | MET | `run_live_dates` makes the pack live on the replayed day. RL3 now writes only that day (`{data/<release_path(DAY)>}`). Main holds no `receipts/data/v4/days` file (`git ls-tree`: 0 under `receipts/data/v4/`), so no rehearsal record has reached the real labels |
| PROTOCOL_v4's hash moves nothing recorded | MET | no `research/forecasts/FREEZE_v4.md` on main; `PROTOCOL_v4.md` appears only in `freeze_check.py`'s list for the future freeze; no record's method hash covers it. `test_protocol_text.py` pins the new 1.6 wording |
| Real sample | MET | `python -m fno forecast-v4-scores report --as-of 2026-10-23` on the merged tree: "days (live pack): A 0, system_late 0 ..., deadline not checked 2"; "live forecasts: 8" for V2, V3, V6a, V6b and the V2 series (V1 0, not started; V7 4). The report files were removed afterwards |

## Plants (mine, 6)

- **Caught (3):** labels back on `forecasts_v4`; the catch-up never writing `system_late`; the boundary day unlabelled.
- **Equivalent (2):** the catch-up's loop starting a week early (`missing_label` still gives none before `live_from`,
  so nothing is written); the reader's `today <= live_from` loosened to `<` (the session range is empty on that day).
- **Survivor (1), m1:** the deadline run's catch-up start moved from `forecasts_v4` to `v4_pack` in the wiring
  (`v4_pack/wiring.py:88`). No test pins it: the tests build `DeadlineRun` directly.

## Minor

- **m1:** the composition-root line passing `live["forecasts_v4"]` to `DeadlineRun` predates this branch and is correct.
  But the rule this change depends on ("the 15:10 deadline's catch-up stays at forecasts_v4", D2 revised) has no test.
  **Fix:** one wiring test, `build_deadline_run(cfg)` with `forecasts_v4` 22 Oct and `v4_pack` 26 Oct, catches up
  from 22 Oct. It can ride the next G10 change; it does not block Monday.

## Notes

- `LiveDayLabels.labels()` still returns every stored record, including one dated before `live_from`. None can exist
  now: the catch-up no longer writes them, and no receipt is on main. If a rehearsal ever pushed such a record with a
  receipt, the real report would drop that day. Today this is safe, by data only.
