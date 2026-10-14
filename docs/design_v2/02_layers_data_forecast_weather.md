# 2. Layers 1-3: data, forecasts, market weather

Each layer: purpose, inputs, outputs, interfaces (CLAUDE.md "design for change": every source, store and rule behind
an interface, concrete classes wired only in a composition root), evaluation metric, failure modes.

## 2.1 Layer 1: data

**Purpose.** Point-in-time facts that every later layer can trust: what was known, from which source, at what time.

**Already built (keep):** NSE raw archive and both F&O formats (A1, A2); NIFTY option panel, extended daily (A3, A13);
3 pm Groww quotes of NIFTY monthly options with bid/ask (A4, from 13 Oct 2026); session calendar (A7); events calendar
(A6); participant open interest (A8, measuring release times); FII/DII flows (P8); company filings for the Nifty 500
(A12); NSE margins (A14); India VIX daily closes from 2017 (A3, A10 warm-up).

**New in v2 (stories in `REPLAN_new_stories.md`):**

| Data | Source (read-only) | Frequency | Story | Why |
|---|---|---|---|---|
| 15-minute quotes: NIFTY spot, near future, option chain (weekly and monthly expiries, strikes within about 6% of spot) with bid/ask | Groww read-only API | 26 snapshots a session, 09:15-15:30 IST | A16 | Intraday realised volatility (a far less noisy target than daily closes), real exit prices for the monitor, the weekly chain at real quotes |
| Groww historical candles, if offered for indices and options | Groww API | one-time back-fill | A16 step 0 | If 15-minute index history exists, intraday realised volatility can be back-filled; if not, it is collected forward only |
| India VIX daily open, high, low, close back to its start | NSE historical files | daily | A15 | Weather calibration and crash replay need more than one crash (2008, 2011, 2013, 2016, 2020, 2024) |
| Global cues: previous US close (S&P 500, Nasdaq 100), Brent, USD/INR, US 10-year yield | Official or primary free sources first: NSE currency and MCX files for USD/INR and crude futures; FRED for US closes | daily, known before 09:15 IST | A17 | Overnight gap risk and the weather; the US close of day d-1 is known at 15:00 IST on d (US markets close about 01:30-02:30 IST) |
| Stock option chains around results | Already in the NSE archive (A1 reads every F&O instrument); results dates from A12 board-meeting filings | daily | R2 (study), A18 if it passes | The one source of many independent events (section 1.3) |

**Hosting rule (finding, not a decision).** GitHub Actions schedules ran 4.5-5.5 hours late here (response 91, strong
evidence for this repository), so they cannot run a 15-minute recorder. And a broker key never goes into GitHub
(owner decision of 13 Oct 2026, "the 3 pm quote recorder moves to GitHub Actions on NSE's public data, never a broker key in GitHub"). The 15-minute recorder and the live monitor (layer 7) therefore need a host chosen by the
owner; the options and their risks are in `06_risk_and_alerts.md` section 6.6.

**Outputs.** Raw files in Drive (owner principle of 13 Oct 2026, "all scheduled data fetching runs as GitHub Actions and stores published data in Google Drive"); small derived daily tables in the
repository (realised volatility per day from 15-minute returns, the 15:00 chain summary, global cues as of 15:00).
Every row carries `source`, `as_of`, `first_seen_at` and the raw file's SHA-256.

**Interfaces.** Existing: `Provider` (Groww, NSE), `RawFileStore`, `RawFileSource`, `DailyClosesSource`, `DataCheck`
(C3). New: `IntradayQuoteSource` (one adapter per source: Groww today), `GlobalCueSource` (one adapter per series),
`IntradayRealisedVol` (computes a day's realised variance from stored snapshots; a strategy, so the sampling rule can
change by version). Wiring: `fno/storage/wiring.py` for stores, `fno/pipeline/wiring.py` for jobs.

**Evaluation metric.** Completeness (snapshots recorded / snapshots due, per session), lateness (`first_seen_at` minus
due time), agreement (Groww 15:30 snapshot vs NSE close, per instrument), revisions (A11). Published weekly in the
post-mortem (layer 8).

**Failure modes.** Host down (snapshots missing: recorded as gaps, never filled by interpolation); Groww token or API
change (alert, fail closed); a stale quote repeated (C3's staleness check); a source rewriting history (A11 keeps both
versions); look-ahead (a value used before its `first_seen_at`: the forecast and decision inputs are built only from
rows whose `first_seen_at` is before the cutoff).

## 2.2 Layer 2: daily probabilistic forecasts

**Purpose.** Every trading day, every forecaster states probabilities (and, for volatility, a number with its own
uncertainty) for fixed questions, before the 15:00 cutoff; the outcome scores them later. This is the tool's main
evidence engine (section 1.3, consequence 1).

**Forecasters.**
- **Baselines (frozen, G2):** (a) risk-neutral from option prices, (b) base rate over 750 days, (c) simple statistical
  models (HAR-type for volatility, VIX mean reversion).
- **Rules (Book 1):** the mean of the baselines today (G1 section 5); v2 adds rule forecasters for the new volatility
  questions (G7: HAR on intraday realised variance, GARCH-type, implied volatility minus a fixed premium).
- **Hybrid (Book 2) and AI team (Book 3):** sealed same-day AI sessions (F1, G5; owner's 14 Oct conditions apply).
- **The weather (layer 3)** is itself a forecaster of large moves.
- **The house forecast:** the one the trade card shows; how it is chosen is in `07_ai_team.md` section 7.4.

**Questions.** G1's five questions stay frozen (v3). Design v2 adds a volatility question set as a **new protocol
version (v4)**, never an edit of v3: `05_volatility_research.md` section 5.2.

**Outputs.** Forecast records (`fno/forecast/schema.py`: book, date, cutoff, question, probability, method, pack hash),
plus for v4 point forecasts of variance. Scores (G4): Brier, log score, calibration tables; for v4 also QLIKE.

**Interfaces.** Existing: `Forecaster`, `OutcomeResolver`, `CaptureSource`, `LiveReports`. New: `PointForecaster`
(variance forecasts), `ForecastScore` (one class per scoring rule: Brier, log, QLIKE), `HouseForecast` (the
combination rule; a strategy, versioned). Wiring: `fno/forecast/baseline_wiring.py` for new rule forecasters (the G1
freeze pins `fno/forecast/wiring.py`), `fno/forecast_scoring/wiring.py` for scores.

**Evaluation metric.** Paired loss difference against the question's baseline, block bootstrap, Holm across the
registered family (section 5.5). Calibration: reliability table and the calibration slope.

**Failure modes.** Leakage (an input after the cutoff: the pack hash and `first_seen_at` rule prevent it); an AI session
breaking its seal (the 14 Oct audit rule makes that day unscored); overlapping targets counted as independent (block
bootstrap); many questions tested, one "wins" by chance (Holm, registered family); a forecaster quietly changed (method
hash in every record; a change is a new version).

## 2.3 Layer 3: market weather (green, amber, red)

**Purpose.** A calm, fast answer to "is today dangerous?": a survival signal, not a profit signal. Response 94 showed
the v0 rule did **not** add money for any weekly structure and gave up premium on two (strong evidence). The owner
kept "red means no new trade" as a survival rule (owner decision of 14 Oct 2026, "Trading principles for the research tool"). Design v2 keeps it and makes its price visible.

**Design change: the weather becomes a scored forecast.** Instead of a fixed checklist only, the weather publishes:
- `p_big_1d`: the probability that NIFTY's next-session absolute move is at least 2%;
- `p_big_5d`: the probability that the largest absolute close-to-close move over the next 5 sessions is at least 2%;
- a colour from fixed thresholds on those probabilities, registered before use (proposal: RED when either probability
  is at least 2.5 times its 750-day base rate, AMBER at 1.5 times; reasoning only, owner decides);
- the drivers that moved it (VIX level and change, recent large moves, realised volatility, overnight US move,
  scheduled events), so the card can say why.

The v0 checklist (response 94's frozen rule) becomes **weather baseline v0**, scored on the same questions, so any
new weather model must beat it and the base rate to replace it.

**Outputs.** One weather record a session at 15:00 (and intraday upgrades from the live monitor, layer 7: amber to red
only, never red to green inside a session); a Slack alert on any upgrade to RED.

**Interfaces.** `WeatherModel` (strategy; v0 checklist and later models as classes), reusing `Forecaster` for scoring
and `AlertSender` for Slack. Wiring: a new `fno/weather/wiring.py` composition root.

**Evaluation metric.**
- Forecast skill: Brier and log score of `p_big_1d` and `p_big_5d` against the base rate (strong expectation of some
  skill: volatility clustering is well documented; reasoning only for our thresholds).
- **Price of calm:** each month, the shadow net result of the trades the RED rule blocked (from the factory's shadow
  decisions), shown beside the losses it avoided. The owner sees exactly what the survival rule costs.
- Red frequency: share of sessions RED. Above about 25% the rule keeps the owner out too often (v0 was 26% of weeks).

**Failure modes.** False calm before an overnight shock (a gap after a GREEN day: inevitable sometimes; every gap day
with GREEN gets a why-it-was-wrong review); crying wolf (too many REDs: the owner stops reading it); thresholds tuned
after the fact (forbidden: a new threshold is a new version with its own record).
