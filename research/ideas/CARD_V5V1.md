# Idea card: CARD_V5V1 v5 side by side, V1's forecasters on the candle RV history (measurement: never promoted)

Template: `research/ideas/TEMPLATE.md`. Story G14 (`docs/stories/G14-v5-v1-candle.md`, text PASS: judge 497.1 and
judge 596 addendum 1). The owner's decision: DESK_DECISIONS 23 Oct 2026, "v5 trial: V1 next-session forecasts from
stored candle history" (owner: "Yes, start it"); switched on with the v4 sign-off (DESK_DECISIONS 24 Oct, "The owner
signs off protocol v4"). This is a **measurement**: it records and scores, it claims nothing, it is never screened,
never promoted and never a v4 member. Labels: **strong evidence**, **some evidence**, **reasoning only**.

## G0: the idea

| Field | Value |
|---|---|
| Id and version | CARD_V5V1 v1 (a changed forecaster, input rule, target or loss is a new card version, never an edit) |
| Ledger trial | 100 (`research/ledger.csv`, written by `python -m fno factory register CARD_V5V1` in the same commit as this card) |
| Registered research question | How do v4's five V1 next-session RV forecasters score (v4's QLIKE, against A16's live intraday RV) when their intraday input is the spliced candle-first history (A16b 2020-2026 plus A16's live rows), started now instead of after 20 live sessions? |
| Proposed by (role or AI) and date | quantitative modeller (Claude, G14 builder), 23 Oct 2026; taken over 24 Oct 2026 |
| Who pays and why | none: a forecast measurement, no trade |
| Forecast it rests on | v4's V1 forecasters (`fno/forecast_v4_rules/`, G7), imported unchanged |
| Instrument and structure | none (NIFTY's next-session realised variance) |
| Entry rule | none: one forecast row per forecaster per NSE session, made before 14:30 IST |
| Exit rule | none |
| Size | none |
| Worst loss in Rs | Rs 0 (no trade) |
| Expected gross per trade, with source | none stated: a measurement has no expected edge |
| Needs a reaction faster than 60 minutes? | No |
| Frequency | one row per forecaster per session, from the step's `daily.live_from` date |

## What it measures, said plainly

- Only `v5c_har_intraday` reads the candle history; `v5c_trailing` reads `d-1`'s live row (a candle row for `d-1` is
  never seen before `d`'s cutoff) and the other three read closes only. Four of the five are controls (reasoning only).
- The input mixes two measures: "candle RV (15m bars) vs live quote RV". On the 3 sessions with both, candle / live =
  0.962, 0.997, 1.009 (some evidence, n = 3). Every row and report carries that label.
- Decision 56 (response 113) forbids back-filled rows as live forecast inputs; the owner's 23 Oct row makes this one
  measurement an exception. Safeguards: point in time by `first_seen_at`, live outcomes only, labelled rows.
- It adds one trial (100) to the count the Innovation Lab's luck correction must pay for.
- It gives an earlier, honest, scored record; it does not give proof (judge 128's measured noise).

## Machine block (story R1)

Read by `python -m fno factory` (G0 fields only: a measurement is never screened).

```factory
id: CARD_V5V1
version: 1
trial: 100
experiment: v5-v1-candle-side-by-side-2026-10-24
description: "v5 side by side (G14): v4's five V1 next-session RV forecasters on the spliced A16b candle plus A16 live RV history, scored live against A16's live RV with v4's QLIKE; measurement, never promoted, never a v4 member"
question: v1-next-session-rv
hypothesis: no
measurement: yes
```

## G1-G6

| Field | Value |
|---|---|
| Feasibility screen | Not applied: a measurement is never screened |
| Data spend | The candle history is already `exposed` (`research/DATA_SPEND.md`, row "NIFTY intraday realised variance (A16b candles)"); fitting on it spends no fresh data. Every score is a live session after the first live day |
| Sample plan | none fixed: a descriptive record growing one row a session; read beside v4's own V1 once it starts (after 20 usable live A16 sessions) |
| Pass mark | none |
| Result and verdict | none (a measurement has no verdict) |
