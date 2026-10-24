# Judge 606: v4 freeze code (story/v4-freeze @ 10dc1c1c3), judge B, round 1 of 2

**FAIL (1 blocking; 1 note). Lane 1** (frozen files, forecast and score records). Criteria 1-4, 9, 11 and 12 of
`docs/stories/G6-v4-freeze.md` (text passed as 597.2), judged against main with G11 merged, as the orchestrator asked.

## Criteria

| # | Criterion | Result | My evidence |
|---|---|---|---|
| 1 | the three classes | PARTLY | `freeze_classes.py`: on the merged tree, 139 byte-checked, 60 recorded, 44 not deciding (the claim says 45). Every "named in FREEZE.md/_v2/_v3" lock is true: my scan of the three records finds every such path. A4's lock file `tests/quotes/test_recorder_baseline.py` exists. `recorder.py` and its capture modules are recorded (597.2 m3). Incomplete against G11: B1 |
| 2 | protocol commit | MET | `protocol_problems`: exactly one line, the commit exists and is an ancestor, and it is the last commit touching the protocol (`Git.commits_touching` is oldest-first, `ledger.py:104-106`, so `[-1]` is right), with the text hash checked. Plants "protocol check dropped" and "not-last accepted" caught |
| 3 | the rate | MET | `fno/forecast_v4/pricing.py` is byte-identical to G7b's (same SHA-256 on `story/g7b-completion`). The pack's rule is `build_iv30_rule` at the constant, and `pricing.py` is in `IV30_METHOD_FILES`. The tool refuses today on purpose: on my merged tree it prints exactly the two G7b readers (`forecast_v4_rules/wiring.py`, `forecast/wiring.py`), exit 1. Plants: pack rate 0.07, pricing dropped from the method, scan blind to `cfg[...]`: all caught |
| 4 | look refuses a broken freeze | MET | `cli._look` refuses unless `holds()`; the report's first lines are the check's. `freeze` is a keyword-only argument with no default. A shallow clone gives "NOT CHECKED". Plants "look ignores", "shallow read as checked" caught |
| 9 | disclosure | MET (read) | `freeze_disclosure.py` with its tests passes on both trees; the tool refuses a dirty tree (`refusals`) |
| 11 | the import walk | NOT MET on the merge | passes on the branch head (4 passed); fails on the trial merge: B1 |
| 12 | recorded drift printed | MET | `drift` from the recorded rows only (a 3-column pattern, apart from the byte-checked 2-column rows); plants "drift not printed", "drift ignores changes" caught |
| Gates | trial merge into origin/main 9d14a9332 (clean, 532b46ac9) | NOT MET | ruff, format (2,572), imports (2,701), record scan (9,176), check_numbers clean; **3 failed**, 16,145 passed, 1 skipped, 14 xfailed (token kept): the three walk tests |

## Findings

1. **Blocking B1: the classes miss G11 as merged on main.** On the trial merge `test_freeze_walk.py` fails 3 tests. My
   run of its `walk` lists 7 unclassed modules, each with its importer: `fno/ai/run_terms.py` (13 importers, among them
   `versions.py`, `outcome.py`, `scoring_gate.py`, `stop_rule.py`, `v4_fire.py`; the passed text classes it as recorded),
   `fno/ai/budget_stop.py` (from `v4_fire.py`), `fno/ai/record_writer.py` (`v4_collect.py`),
   `fno/budget/usage_ledger.py` and `fno/research_engine/statistics.py` (`v4_cost.py`), and `fno/alerts/sender.py` and
   `fno/pipeline/trigger.py` (`v4_fire.py`). It also finds one stale entry, `fno/ai/timing.py`, which is recorded but
   reached by nothing. The table was built before G11 merged. Fix: merge main, class each of the 7 with its reason
   (`run_terms.py`, `budget_stop.py`, `record_writer.py` decide AI rows, stops or misses, so recorded in the AI
   registration table; `usage_ledger.py`, `statistics.py`, `sender.py` and `trigger.py` each on its own reading), drop
   or justify `timing.py`, and rerun the full gates on the merged tree.

## Plants

12 planted on the branch head, 12 caught: drop the `fno/v4_pack` glob; drop `recorder.py` from recorded; shallow read
as checked; protocol check dropped; a not-last protocol commit accepted; drift not printed; drift ignoring changes; a
file added after the freeze ignored; the look ignoring a broken freeze; the pack's rate not the constant; `pricing.py`
out of `iv30_method`; the rate scan blind to `cfg["risk_free_rate"]`. The walk itself is shown working: it is what
fails on the merge.

## Notes

1. `fno/forecast/wiring.py` (v1, frozen) reads the configured rate and can never change. The tool stops naming it only
   once G7b's `forecast_v4_rules/wiring.py` no longer imports it (its only v4 importer: `forecast_scoring/wiring.py`
   is v3's). Then the walk flags it as stale and it leaves `RECORDED`. That is the intended path (blocker 3); say it
   in the reason string.
