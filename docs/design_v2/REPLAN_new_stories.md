# New stories added by design v2

One paragraph each: what, why, depends, size (S under a day, M 1-3 days, L more), slice. Every new story is lane 1
(`docs/JUDGE.md`: new stories). The full story text (description, context, scope, design, acceptance criteria, test
plan, judge verifies) is written into `docs/stories/` when its slice starts, never earlier, so it reflects the code of
the day. Layer and section references are to the design v2 files.

## Data (layer 1)

- **A15 India VIX full history.** NSE's historical VIX daily open, high, low, close from its start, into Drive and a
  derived table, with A11's revision rule. Why: the weather and crash replays need more than one crash (2.1). Depends:
  A9, A11. S. Slice A.
- **A16 15-minute quote recorder.** Step 0: a one-session feasibility check of Groww's historical candles and of a
  15-minute snapshot of NIFTY spot, near future and the weekly and monthly chains within about 6% of spot (counts and
  timings only). Then the recorder: 26 snapshots a session, raw files to Drive, derived per-session realised variance in
  the repository, gaps recorded never filled. Host chosen by the owner (6.6). No order code, read-only key use.
  Acceptance includes section 4.4's contracts: Groww's terms checked first (raw quotes in Drive only), the clock
  contract and skew check. Depends: A7, A9, the owner's host decision. M. Slice A.
- **A17 Global cues.** Previous US close (S&P 500, Nasdaq 100), Brent, USD/INR and the US 10-year yield, each behind
  `GlobalCueSource`, with `first_seen_at`; official or primary sources first (NSE currency and MCX files, FRED). Why:
  overnight gap risk and the weather's drivers. Depends: A9, O6. M. Slice A.
- **A18 Stock options around results.** Point-in-time panel of F&O stock option chains around each results date (A12),
  with the F&O stock list as of each date. Only if R2 says the idea fits the cap and the costs. Depends: R2, A1, A12. L.
  Slice C.

## Forecasts (layer 2)

- **G6 Forecast protocol v4.** The volatility question set V1-V7, baselines, scoring and the registered family of
  section 5; minimum effects; power-check rule. Acceptance includes: V5's outcome uses the correct expiry's final
  settlement or reference level, with its source and timestamp frozen, never a later daily close; the freeze record
  discloses the 2017-26 base rates measured before it, on regular sessions only (judge 96 addendum 2). Freeze after
  the judge and ChatGPT agree (orchestrator decision of 13
  Oct 2026: G-protocols freeze only after ChatGPT review). G1 v3 keeps running beside it. Depends: G1, G2, G4. M
  (document). Slice A.
- **G7 v4 baselines and rule forecasters.** Trailing, EWMA, HAR (daily, later intraday), implied and implied-ratio
  baselines; back-fill on close proxies, labelled; live capture beside G3. Wiring in `fno/forecast/baseline_wiring.py`
  (G1's freeze pins `wiring.py`). Depends: G6. M. Phase 1 (V6, V1) slice A; phase 2 (V2-V5, V7) slice B.
- **G8 v4 scoring.** QLIKE, squared error on variance, Mincer-Zarnowitz, calibration slope and intercept, Brier skill
  score; the block-bootstrap comparisons and Holm of section 5.5; the 60-outcome power report. In
  `fno/forecast_scoring/`. Depends: G6, G4. M. Slice A.
- **G9 House forecast.** The combination rule of 7.4 as a versioned strategy, its calibration lines for the card, and
  its change only at quarterly reviews. Depends: G8, a first review. S. Slice C.
- **G10 AI books on the v4 questions.** A new prompt version for books 2 and 3 under the sealed-same-day rule and its
  audit. Depends: G6, G5. S. Slice C.

## Weather (layer 3)

- **M1 Weather as a scored forecaster.** `WeatherModel` with the v0 checklist (response 94's frozen rule) as baseline
  and a first model for `p_big_1d` and `p_big_5d`; colours from registered thresholds; drivers listed; scored under v4
  (V6). Depends: G6, A15 (helpful, not required). M. Slice A.
- **M2 Weather alerts and the price of calm.** RED upgrades as DANGER alerts; the monthly shadow result of trades RED
  blocked, beside the losses avoided. Depends: M1, T1, R1 shadows. S. Slice B.

## Factory (layer 4) and structures

- **R1 Strategy factory.** Idea cards with a ledger row at G0, `CostWall` (feasibility screen: expected net after costs
  and tail losses on a conservative bound; 2x shown only as a warning), `screened_out` ideas kept in the trial count,
  `DataSpendRegister` (`research/DATA_SPEND.md`), `SamplePlan`, the trial count and expected false passes on every
  report, and the path from idea to forward shadow through B4 and D1's research status. Documents in slice A, code in
  slice B. Depends: B4, C1, D1, A4. M.
- **R2 Stock options around results: feasibility study.** A registered study (ledger rows first): for F&O stocks with
  results in 2019-26, volume and open interest of near strikes, lot values, the cheapest defined-risk structures that
  fit Rs 10,000, and one live Groww snapshot of their bid/ask. It also reports the point-in-time F&O eligibility of
  each stock, physical-settlement obligations, bid/ask depth, and the **effective number of independent clusters**
  (events grouped by sector and results week, with the within-week correlation of event moves), not only raw events.
  Output: fits or does not fit, with numbers; it fails early if the Rs 10,000 cap makes most structures uneconomic. No
  P&L on outcomes in this study (it only decides whether a P&L study is worth registering). Depends: A1, A12. M.
  Slice A.
- **R3 First forward shadows.** The first ideas that pass the cost wall, registered as research candidates and recorded
  daily as shadows (experiment 2 model). V-ideas only after their forecast passes rung 1. Depends: R1, STR1. M. Slice B.
- **STR1 One- and two-leg structures.** B2's `Structure` builds any number of legs; C4's shape and independent max-loss
  checks, D1's codes, D2's candidates and A14's margin rows accept bought options and vertical spreads. Never a naked
  short leg. Response 92 sized it at about 8-10 files. Depends: B2, C4, D1, D2, A14. M. Slice B.

## Desk and risk (layer 5)

- **C5 Risk buckets and the Rs 20 lakh account.** Bucket, account and new-risk-per-day caps, the account drawdown brake
  and the daily stress line of section 6.2, in C2 with config through `fno/config.py`. Depends: C2, the owner's numbers.
  M. Slice B.
- **E8 Owner-timing fills.** `OwnerTiming`: fill at the first snapshot at or after card time plus the owner's reaction
  time, inside the card's entry range or recorded as missed; the next session when away or after 15:25. Primary
  R = 60 minutes, with R = 30 and R = 5 as sensitivities (owner decision of 15 Oct 2026); E4's fills reported too, so
  the cost of human delay is visible. Its code joins S1's `frozen_files` (owner decision of 15 Oct 2026).
  Depends: E4, A16 (falls back to A4 snapshots until A16 runs). M. Slice B.

## Cards and alerts (layer 6)

- **T1 Daily trade card.** One card every session (`TRADE`, `NO TRADE`, `WATCH`) built only from committed records,
  with record hashes in the footer; Slack #fno-desk; alert classes and limits of 6.5. Replaces P4. Acceptance includes
  section 4.4: the footer's issuance hashes, the clock contract and the owner-unavailable line. Depends: D3, E2, G3,
  M1. M. Slice A (v1: `NO TRADE` and forecasts), slice B (trade fields).
- **T2 Devil's advocate rule checks.** The code checks of 7.3, able to turn a card into `NO TRADE` with the reason.
  Depends: T1, C4, R1. S. Slice B.
- **T3 Devil's advocate objections.** A sealed AI session per card returning three scored objections; never a veto.
  Depends: T1, F1's session pattern, F8. M. Slice B.

## Live monitor (layer 7)

- **LM1 Position monitor, alert only.** `PositionMonitor` and one `MonitorCheck` class per check of 4.2, heartbeat and
  "monitor silent" checker, weekly replay for missed alerts. No entry code path. Acceptance includes section 4.4's
  clock contract and owner-unavailable fallback, and alerts written for up to 1 hour of owner delay (6.5). Starts only
  when the first paper or shadow position is open.
  Depends: A16, E1, T1, host. M. Slice B.
- **LM2 Intraday exits mode.** `intraday_exits` per strategy version, with the same version shadowed in the other mode
  as a registered comparison. Depends: LM1, E8. M. Slice C.

## Learning loop (layer 8)

- **LR1 Weekly post-mortem.** Code builds the numbers; an AI writer may cite only them; the devil's advocate reviews.
  Depends: G4, T1. S. Slice A.
- **LR2 Why-it-was-wrong reviews.** The six classes of 4.3, the computed "within its stated odds" test first, and the
  calibration check of the luck class. Depends: LR1, D3, E4. M. Slice B.
- **LR3 Drift detection.** The CUSUM rules of 5.8 for forecasters and strategies; strategy alarms pause new entries.
  Depends: G8, E6. S. Slice B.

## Budget, stop rules and real money

- **BG1 Budget meter and stop-rule tracker.** Monthly costs by item (8.1), caps and alerts, the stop-rule review date
  and its two tests computed ahead of time. Depends: F8. S. Slice A.
- **RM1 Real-money gate.** `research/evaluation/REAL_MONEY_GATE.md` with the conditions of 8.3, frozen and hashed
  before the first counted paper decision. Document plus a freeze record. Depends: S1. S. Slice B.
- **RM2 Real-money test record.** Records the owner's real fills against the card, the discipline record, and the pass
  and stop rules of 8.4. Never places an order. Depends: RM1, an approved strategy. M. When a strategy passes.
