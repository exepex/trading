# Response 148: G9 claims, missed forecasts in protocol v4 (revision 9)

Builder: Claude, 15 Oct 2026 IST. Branch `story/g9-miss-rule`. Lane 1 (forecast scoring and the v4 protocol before its
freeze). Story text: `docs/stories/G-forecasts.md` G9. Owner decisions: the 15 Oct rows "Missed forecast days: verdicts
on observed days only, with a miss cap" and "Test A stays undecided ..." (responses 144-147, judge 138-139, ChatGPT 112).

## What changed
- `fno/forecast_v4/misses.py` (new, pure): `MissReport` and `miss_report(rows, big_day)`. Counts from the forecaster's
  first forecast: misses (baseline present, forecast absent), 2% days among baseline days and among misses, input
  failures (neither forecast). `operations_undecided`: missed > 10% of baseline days, or 2% days missed > 10% of
  baseline 2% days, or any such miss when there are fewer than 10.
- `fno/forecast_v4/terms.py`: `MISS_CAP`, `BIG_DAY_MISS_CAP` (0.10, 0.10). (Revision 2: the third constant,
  `BIG_DAY_ZERO_MISS_BELOW`, is gone; see below.)
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
- `python -m pytest -q` on the tree merged with main (FNO_SLACK_BOT_TOKEN unset): 5,553 passed.
- `ruff check fno tests tools`: clean. `python tools/check_imports.py`: clean. `ruff format`: applied.
- First full run on this session's shallow clone failed 9 history-based freeze tests (the clone had no history) and
  one A16b test that main has since fixed (c7910516); after `git fetch --unshallow` and merging main, they pass.

## For the judge
- Owner row of 15 Oct "G6 protocol v4: V6 becomes descriptive" is not in the code yet (`DESCRIPTIVE_ONLY` holds V7
  only); it goes through G6's path. G9 does not depend on it: a descriptive member is "not judged" before the miss
  check, and its miss line is still printed. With V6 descriptive, the miss rule matters for V1 and V2.
- Known limit (reasoning only): below 10 2% days, one outage on a 2% day makes that look "undecided, operations".
  This is not an extra rule: it is what "more than 10%" means for fewer than 10 days (judge 149 M1). It can never
  cause a false "no".

## Revision 2 (answer to judge 149, FAIL 0/3/4; commits `bd1c54d3`, merge of main `d5802345`, and the freeze-start fix)

Each finding checked before acting; all seven accepted, one more found by an independent review.

| Finding | Check | Decision and change |
|---|---|---|
| S1 input failures miss days neither file holds | Reproduced: `paired_rows` makes rows only for days a file holds, so a day the 3 pm capture never ran printed `input failures: 0` | Accept. `comparison._with_empty_days` adds an empty row per outcome day no file holds, for the miss count only (pairing unchanged). Test: `test_miss_outputs.py::test_a_day_neither_file_holds_is_an_input_failure...` |
| S2 report text, report JSON, recorded look untested | Planted each removal: suite stayed green before, as the judge said | Accept. `test_the_report_text_and_json_carry_the_miss_counts`, `test_the_recorded_look_carries_each_members_miss_line` |
| S3 claims lack quality rules 3, 4, 6 | True | Accept. Sections below |
| M1 zero-miss branch implied by 10% | 1 > 0.1 n for every n < 10, so the branch changes no result | Accept. Branch and `BIG_DAY_ZERO_MISS_BELOW` dropped; protocol says the zero rule follows from 10% |
| M2 2% day defined twice, `>=` untested | True (`regime.py` and `comparison.py`) | Accept. One `regime.is_big_move`, used by both; tests at exactly +-0.02 and 0.0199 |
| M3 Test A "yes" reading | Code checks "yes" first (`stop_rule.py`) | Accept the judge's reading: an operations-undecided member blocks a false "no" only; another member's real claim still gives Test A "yes". The owner should know this |
| M4 Out list, freeze numbers | BG1 owns stopping a failing book | Accept. Out line added. For the v4 freeze record: the owner row says "proposed 10%"; the 2% sub-cap came from response 147 item 2, shown in the final review, not asked alone. The freeze record must quote the owner confirming both 10% numbers |

**Found by the independent review (Important, accepted):** after the freeze, `_counted` drops earlier rows, so the miss
count started at the first live forecast after the freeze. A member broken for its first 30 days after the freeze,
then running 100, showed 0 of 100 missed and would be judged: exactly the "gain by skipping hard days" the rule
forbids. Fix: `scoring._miss_start` counts from the day after the freeze for a forecaster that had already started
(any row, back-fill included), else from its first forecast; `miss_report(rows, big_day, start)`. Protocol section 4
says so. Test: `test_after_the_freeze_misses_count_from_the_day_after_it_and_earlier_days_never_count` (8 days
observable, 3 missed, undecided; days before the freeze count as nothing).

### Independent review run (quality rule 3)
One `pr-review-toolkit:code-reviewer` agent on the whole G9 diff: 2 Important findings (the freeze start above, and
no test through `member_comparisons(counted_after)`); both fixed. It confirmed the caps at every multiple of 10 up to
5,000, unresolved and void handling, judged/not-judged order, empty rows after the freeze, the shared 2% predicate and
the size rules.

### Each criterion with proof its test fails when the code breaks (quality rule 4)
Planted on a scratch copy, `tests/forecast_v4` + `tests/forecast_scoring_v4`:

| Planted break | Caught by |
|---|---|
| `_with_empty_days` removed (`comparison.py`) | 3 tests in `test_miss_outputs.py` |
| `is_big_move` `>=` to `>` (`regime.py`) | `test_regime.py` and 4 in `test_miss_outputs.py` |
| miss line removed from report text (`render.py`) | `test_the_report_text_and_json_carry_the_miss_counts` |
| `misses` removed from report JSON (`render.py`) | same |
| `misses` removed from recorded look (`cli.py`) | `test_the_recorded_look_carries_each_members_miss_line` |
| 2% sub-cap removed (`misses.py`) | 3 `BIG_DAY_CASES` and `test_look.py` operations-undecided test |
| freeze start removed (`scoring.py`) | `test_after_the_freeze_misses_count...` |

The judge's earlier 16 caught mutations (criterion 1 and 2 boundaries, look check, start filter, void, unresolved,
constants vs protocol) still apply.

### Real output sample (quality rule 6)
`python -m fno forecast-v4-scores report --as-of 2026-10-15` on a scratch copy, V6b:

```
  v6_ewma_t4 vs base_rate: scored 1908, gate 1908, unresolved 1, void 0, forecaster missing 250, baseline missing 250, zero RV out of the gate 0
    scored window regime: mean India VIX 17.1, 94 2% days, band 13+
    misses: 0 of 1908 baseline days (0.0%), 0 of 94 2% days; input failures: 0
```

The 250 and 500 "forecaster missing" rows are all before each forecaster's first forecast (checked: 0 null rows after
it for `v6_ewma_t4` and `weather_checklist_v0`), so 0 misses is right: back-fill warm-up is "not started".
