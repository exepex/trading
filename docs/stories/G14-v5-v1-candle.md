# G14. v5 side by side: V1's forecasters started now on the stored candle RV history

**Repository:** trading. **Owner:** R2/G7 builder (session 0185gR5DmoDh2zBAvgRU4CEB). **Lane 1** (forecast records),
one judge (judge B). **Status:** text, for the judge.

**Description:** As the quantitative modeller, I want v4's five V1 forecasters (trailing, EWMA, HAR daily, HAR
intraday and the close blend) run every session from now on, on the candle-based intraday RV history A16b already
stored (2020-2026), so that V1 gets a live, scored record about four weeks before v4's own V1 can start.

**Context and why:**
- The owner's decision (orchestrator, 23 Oct 2026). v4's V1 starts only after 20 usable live A16 sessions (protocol
  v4 line 57; `fno/forecast_v4_rules/capture.py`, `V1_START_SESSIONS = 20`).
- On 22 Oct A16 had 3 live sessions, one of them void (16 Oct), so 2 were usable. That is about 18 more sessions:
  v4's V1 starts around 18 November.
- The candle history is `exposed` in `research/DATA_SPEND.md` (row "NIFTY intraday realised variance (A16b
  candles)"). Fitting on it spends no fresh data. Every score here comes from live sessions after the start date.

**Said plainly:**
- V1 is not provable in useful time under v4's rules: judge 128's measured noise makes it effectively unreachable.
  This candidate gives an earlier, honest, scored track record. It does not give proof.
- It adds one candidate to the trial count that the Innovation Lab's luck correction must pay for.

## Scope

- **In:**
  - The five V1 forecasters on a spliced intraday RV history (below).
  - Their daily live records in their own folder, with every record labelled with its input measure.
  - A measure-gap table: candle against live RV on every session that has both.
  - A scoring report against the same live A16 target as v4's V1, with v4's QLIKE.
  - One O1 daily step, `forecasts_v5_v1`, live from its own `daily.live_from` date.
  - An R1 measurement card and its ledger trial.
- **Out:**
  - Any change to a v4 file or a v4 output. G7's pure baselines are imported, never edited or copied.
  - Membership of v4's family. This candidate is never a v4 member and never enters a v4 look.
  - Any claim. It is a measurement: never screened, never promoted (R1 `measurement: yes`).
  - A back-fill of forecasts. History is used only as model input; the first scored forecast is the first live day.

## Design

### The input history

The question is what the forecast for day `d` may read, point in time, at `d`'s 14:30 cutoff.

- **Measured, 23 Oct:** a candle RV row for session `d-1` is first seen on `d` at about 15:33 IST (A16b's catch-up,
  for example 21 Oct's row was first seen at 2026-10-22T10:03:11Z). That is after `d`'s 14:30 cutoff.
- A live A16 row for `d-1` is first seen on `d-1` at about 15:31 IST.
- So a candle-only history always lacks the latest session, and V1's trailing forecaster ("the previous session's RV")
  would become "the RV of two sessions ago".
- **Proposed (reasoning only): one spliced series.** For each session before `d`:
  - the candle row when it was first seen before `d`'s cutoff;
  - otherwise the live A16 row when it was;
  - otherwise nothing (void and missing stay missing, never filled).
- Every value keeps its source (`candle` or `live`). The record states how many of the inputs each source gave, so a
  measure mix is never hidden.
- Rejected alternative: candle only, with a one-session lag. It is a different forecaster from v4's, and it is weaker
  for a next-session question. The judge may require it instead; the code keeps the source as one strategy.

### The measure gap (said in every record and report)

- **Label:** "candle RV (15m bars) vs live quote RV".
- The candle RV (`rv-candle-15m-v1`) uses 15-minute index candles: the first bar's open and 25 bar closes.
- The live A16 RV (`rv-quote-15m-v1`) uses quote snapshots at the 15-minute marks, filled from one-minute candle
  closes for 25 of its 26 slots (`basis_counts candle_1m_close:25;candle_1m_open:1` on 21 Oct).
- **Measured on the two sessions with both (some evidence, n = 2):**
  - 19 Oct: live 1.5336e-4 against candle 1.4760e-4, live 3.9% higher;
  - 21 Oct: live 1.1426e-4 against candle 1.1392e-4, live 0.3% higher.
- The report prints this table, growing by one row a day.

### The forecasters (imported from G7, unchanged)

| Forecaster | Formula (G7, `fno/forecast_v4_rules/`) | Input it uses here |
|---|---|---|
| `v5c_trailing` | previous scored session's RV | the spliced series |
| `v5c_ewma_094` | EWMA lambda 0.94 of close-proxy RV | closes, as v4 |
| `v5c_har_daily` | HAR on close-proxy RV, monthly refit | closes, as v4 |
| `v5c_har_intraday` | HAR on intraday RV, at least 250 sessions, up to 750 | the spliced series (eligible from day 1: 1,665 usable of 1,684 candle sessions, 2020-2026) |
| `v5c_close_blend` | mean of HAR daily and EWMA | closes, as v4 |

- Three of the five use closes only. They are v4's own formulas without v4's 20-session start gate, so their values
  will equal what v4's V1 rows will show once V1 starts.
- They are kept because the owner asked for the five, and they are the like-for-like baselines for the two that use
  intraday RV.

### Records, step, report

- `fno/forecast_v5_v1/` (new package, every file under 350 lines):
  - `history.py`: the splice;
  - `capture.py`: one day's five values;
  - `records.py`: G7's record format plus `input_measure` and `input_sources` columns;
  - `gap.py`: the measure-gap table;
  - `report.py`: QLIKE per forecaster against the live A16 target, the gap table and void counts;
  - `wiring.py` and `cli.py`: `python -m fno forecast-v5-v1 capture`, `report`.
- Records go to `research/forecasts/v5/v1_candle/<forecaster>/v1_rv_next_session.csv`, live rows only, write-once,
  each with the method hash of this package's files.
- O1 step `forecasts_v5_v1`: right after `forecasts_v4`, the same 14:30 cutoff. It is only a `LiveFrom` row in
  `fno/daily/wiring.py` and `DAILY_RUN_STEPS`, agreed with the O1 builder first.
- Its `daily.live_from` date is set only after the owner signs v4 (about Tue 27 Oct). Its code merges once judged.
- **Agreed with the O1 builder (session_014zYLf18PgCzR7YoHs1X5Dp, 23 Oct).** I add the step on this branch, in
  `fno/daily/wiring.py`, `fno/constants_operations.py`, `config.yaml` and `tests/daily/test_steps.py`. Terms:
  - Wiring: copy `forecasts_v4`'s pattern exactly, with the command and pathspecs as named constants beside
    `FORECASTS_V4`, and the name added to `LIVE_STEPS`. Any `receipts/` folder the capture writes goes in the
    pathspecs too.
  - The 14:30 refusal exits non-zero, so the run records it as refused and alerts.
  - These tests change with the step list: `tests/daily/test_day_run.py`, `tests/daily/test_steps.py`,
    `tests/health/test_desk_and_data_checks.py` and O11's `tests/e2e_acceptance/replay.py`. The whole e2e folder is
    run.
  - The committed run log holds status only (`command:ok`); values live in this story's own records.
  - Judge D judges the O1 parts. The branch is never merged between 14:00 and 16:15 IST.
  - Timing: v4 ran 14:11:25-14:11:27 on 22 Oct, so this step starts at about 14:12.
- Freeze: before its first live day, a short `FREEZE_v5_v1.md` hashes this package's files and the imported G7
  files, with a `Frozen on:` line, the same rule as v4.

### Registration (R1)

- A measurement card, `research/forecasts/v5/CARD_V5V1.md`, with a `factory` block (`measurement: yes`,
  `hypothesis: no`, question `v1-next-session-rv`).
- `python -m fno factory register` writes its ledger trial and gate-log row in the same commit as the card, before
  any code runs.

## Acceptance criteria and tests

1. The splice is point in time:
   - a candle row first seen after `d`'s cutoff is never read for `d`;
   - a void or missing session is missing;
   - `input_sources` counts match.
   Tests use the real 16-22 Oct rows.
2. No v4 file changes: `freeze_check.problems()` is unchanged, and no file under `fno/forecast_v4*/` or
   `research/forecasts/v4/` is in the diff.
3. Each forecaster equals G7's own function on the same input series (an equality test, no copy).
4. Every record row carries `input_measure` = "candle RV (15m bars) vs live quote RV" and its method hash.
5. The gap table matches the 19 and 21 Oct figures above.
6. The report scores only live forecasts against live A16 outcomes, never a candle outcome.
7. The O1 step is `not_live` before its date and refuses after 14:30, as v4's does.
8. Code size, ruff and the full suite pass.

## Claims

(Filled by the builder for the judge.)
