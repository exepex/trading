# Response 127: G7 phase 1, v4 baselines and rule forecasters for V6 and V1 (branch `story/g7-baselines`, lane 1)

Builder's claims for judge D. Story text: `docs/stories/G-forecasts.md` section G7 (judge 127 PASS on 992440f, one
minor). Protocol v4 merged at 597487f, **not frozen**: everything here is exploratory until v4's freeze. Labels:
**strong evidence**, **some evidence**, **reasoning only**.

## What was built

| File | What |
|---|---|
| `fno/forecast_v4_rules/series.py` | Regular-session closes and `vix_closes()` from `warmup_closes.csv`, close-proxy `RV_s`, V6a/V6b outcomes with their resolution session, A16's live `rv/` rows. The one place for these rules; G8 imports it |
| `baselines.py` | `BaseRate`, `Ewma`, `Har` (daily and intraday), `trailing_previous_session`; a value or a status (`missing`, `not_eligible`, `not_started`), never a filled value |
| `rules.py` | `v6_ewma_t4` (reported only, decision 70) and `v1_close_blend` (V1's `rules` slot); zero fitted parameters |
| `records.py` | G8's layout `research/forecasts/v4/<forecaster>/<question>.csv`: `day,value,status,label` then audit columns; validated; write-once |
| `capture.py` | `DayForecasts` (every forecaster for one day, point in time) and `capture_day` (today only, before 15:00 IST) |
| `backfill.py` | The exploratory back-fill, ending before the first live day; V1 rows not written before A16 has 20 live sessions |
| `wiring.py`, `cli.py` | Composition root; `python -m fno forecast-v4 capture` and `python -m fno forecast-v4 backfill` |
| `fno/constants.py` | Two ids: `v6_ewma_t4`, `v1_close_blend` |
| `fno/cli.py`, `CLAUDE.md` | The command registered; the new composition root listed |

**Changed from the story text while building (for judge D), said plainly:** the text named
`fno/forecast/baseline_wiring.py` (REPLAN's wording) and `fno/forecast v4-capture [--day D]`. The v2 freeze pins
every file of `fno/forecast/` (`research/forecasts/FREEZE_v2.md`); my first commit edited two of them and
`tests/forecast/test_freeze_v2.py` failed (found by the G8 builder on its merged branch; my own full run showed the
same 2 failures). Those two files are now byte-identical to main; the wiring and CLI live in the G7 package, as G4's
do in `fno/forecast_scoring/`. `--day` was dropped (self-review finding 1, below). The story text records this.

## Judge 127's minor and hand values (strong evidence: command output on the committed closes)

- Minor: V1 trailing is `d-1`'s intraday `RV_s`, **missing when `d-1` is void** (never an older session):
  `trailing_previous_session`, tested.
- Judge 127's hand values, reproduced by the code: EWMA `s2` through 14 Oct 2026 **7.72236e-05** (judge 7.7224e-05);
  `v6_ewma_t4` for 15 Oct **V6a 0.03232, V6b 0.15150** (judge 0.0323, 0.1515); V6a base rate **20 / 750 = 0.02667**.
  Also the protocol's disclosed counts: 100 of 2,409 and 331 of 2,405. All in
  `tests/forecast_v4_rules/test_v4rules_series_and_rules.py`.
- Independent recheck by my review agent (closed-form t(4) CDF, not the repository's `t_cdf`): the same values, plus
  V6b base rate 0.104 and HAR daily for 15 Oct (refit 1 Oct) 7.8241e-05.

## Criteria and their tests (`tests/forecast_v4_rules/`, 24 tests)

| Criterion | Code | Tests (positive, negative, boundary, empty) |
|---|---|---|
| 1 V6 outcomes | `series.big_move_outcomes` | disclosed counts; just over / just under 2%; V6b window and empty window; special and muhurat inside the next return; zero return kept |
| 2 Resolution timing | `Outcome.resolved_on`, `BaseRate` | resolved on the forecast day is not known; V6a at t+1, V6b at t+5 |
| 3 Base rate | `BaseRate` | 499 not eligible / 500 present; latest 750; empty |
| 4 Close-proxy RV, EWMA | `close_proxy_rv`, `Ewma` | seed = mean of 250; 249 sessions not eligible; hand-computed update |
| 5 HAR daily | `Har` | rebuilt by hand with numpy; one row short / exact minimum; nothing from `d` on changes the forecast; non-positive is missing |
| 6 V1 start, switch, decision 56 | `DayForecasts._v1` | 19 / 20 live sessions; a void session never counts; a row first seen after the cutoff does not count; HAR intraday 249 / 250; only `rv/` read (A16b's `rv-candle/` is another folder) |
| 7 Trailing | `trailing_previous_session` | `d-1` value; `d-1` void: missing; no row: missing |
| 8 Rule forecasters | `rules.py` | judge values; t(4) table point (2.776 gives 5%); missing inputs pass through; blend |
| 9 Records | `records.py` | invalid probability and variance refused; changed row refused; same row again a no-op; header |
| 10 Back-fill | `backfill.py` | ends before the first live day; skips unstarted V1; re-run byte-identical |
| 11 Live capture | `capture_day`, `cli.py` | before 15:00 writes 9 rows; at 15:00 refused; a Saturday refused; another day refused |

**Broken-code proof (quality rule 4):** 25 planted bugs, one per criterion's code line (scratch script, run without
bytecode, only pytest exit 1 counted): **25 of 25 caught** (strong evidence: command output).

## Self-review (quality rule 3): one independent review agent, and what I did

| Finding | Severity | Done |
|---|---|---|
| `--day` with a later session wrote a two-step-ahead row as `live` and then blocked the real row | should-fix | `--day` dropped; `capture_day` refuses any day but today; tested |
| A closed day or a late run exited 1 (G3 exits 0): every holiday would fail the job once it joins the routine | note | exits 0, as G3 |
| No freeze gate: `live` rows can exist before v4's freeze | note | not changed: protocol 8 says only post-freeze forecasts count; told the G8 builder to count live rows from the freeze date |
| Any edit to the method files makes a back-fill re-run conflict (method hash in every row) | note | the back-fill output is committed only from the judged code (not in this commit) |
| Method hash leaves out `student_t.py`, `terms.py`, `records.py`; inputs hash leaves out the calendar | note | written down; changes no value (owner's working rule) |
| `V4_LATER_DAYS` dead | note | removed |

## Real output (made by the committed code)

- `python -m fno forecast-v4 capture` at 15:21 IST on 15 Oct 2026: `v4 forecasts 2026-10-15: nothing written:
  2026-10-15 15:21 IST is at or after 2026-10-15's 15:00 cutoff` (exit 0).
- Back-fill run to a scratch folder (not the repository): 2,409 days (3 Jan 2017 - 14 Oct 2026), 9,636 rows, 0.4 s;
  4 files of about 480 KB (V6 base rate and `v6_ewma_t4`, V6a and V6b); first `ok`: `v6_ewma_t4` 5 Jan 2018 (251st
  session), base rate V6a 14 Jan 2019. The output is committed only after the judge's PASS (method hash).

## Gates

On a clean worktree at the code commit: full suite, `ruff check fno tests tools`, `ruff format --check`,
`tools/check_imports.py`: results in the message to the orchestrator. Every file under 350 lines.

## Known limits (one line each)

- `v6_ewma_t4`'s V6b assumes independent sessions (volatility clusters).
- V1 has no live data until A16 runs; its rows read `not_started`.
- The back-fill uses spent 2017-26 data: exploratory only (protocol 8).
- If `d-1`'s close is still missing at 15:00, EWMA and HAR use `d-2` (point in time; the row's inputs hash shows it).
