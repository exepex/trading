# 4. Layers 6-8: trade card and alerts, live monitor, learning loop

## 4.1 Layer 6: the trade card and phone alerts

**Purpose.** One short, honest message a day that the owner can act on from a phone, plus urgent alerts. It is what
the broker's research should have been: what, how much can I lose, why, how sure, and what would prove it wrong.

**A card exists every trading day.** Its status is one of `TRADE`, `NO TRADE` or `WATCH` (a candidate's shadow decision,
shown for learning, never to be traded). "No trade" carries a reason code: no approved strategy, weather RED, data
check failed, risk bucket full, budget stop, cost wall, devil's advocate found a hard-rule breach.

**Fields of a `TRADE` card (all from the desk's own records; the card never computes its own numbers).** The example
column is illustrative only: no such strategy is approved, and "x" marks digits the desk would fill in.

| Field | Example of content |
|---|---|
| What | NIFTY 24 Nov 2026 put spread: buy 1 lot 22,600 PE, sell 1 lot 22,450 PE |
| Entry range | Net debit Rs 52-58 a unit; do not enter above Rs 58 (from 15:00 bid/ask; card valid until 15:25) |
| Size | 1 lot (65 units); funds at entry from C2 and A14 (the debit plus the short leg's exposure margin, which a hedge does not reduce: about Rs 29,500 on 14 Oct, response 92) |
| Maximum loss | Rs 3,9xx including charges: fixed at entry; no stop-loss order needed or relied on |
| Worst case shown | The same structure through the worst 5 sessions of Mar 2020 and the 4 Jun 2024 week: loss capped at Rs 3,9xx |
| Exit plan | Take profit at Rs 120 a unit; exit at 15:00 seven sessions before expiry; exit if NIFTY closes above 23,000 |
| Forecast | House forecast: P(NIFTY realised volatility next 5 days above today's implied) = 0.62; that forecaster's record: "said 0.6-0.7 on 140 days, happened on 64%" |
| Weather | AMBER: VIX up 14% in 5 sessions |
| Devil's advocate | Three strongest objections, and its verdict: "no hard-rule breach" |
| Costs and tax | Charges and pads Rs 2xx; net breakeven after costs Rs 6x; tax at 31.2% on the year's net profit |
| Evidence | Rung and label, e.g. "rung 3, paper; some evidence: lower bound -0.02 per rupee risked after 38 trades" |
| Proves it wrong | The strategy's registered pause and retire rules |

**Scoring the card.** A `TRADE` card is scored by its paper trade's net result and by the forecast it quoted; a
`NO TRADE` card by the shadow results of what was skipped (the price of staying out, section 2.3).

**Delivery.** Slack #fno-desk (`C0C89E8QCCD`) with `FNO_SLACK_BOT_TOKEN` only; the owner turns on Slack's phone push for
the channel. Plain text first; images optional. Target: card on the phone by 15:08 IST (decision cutoff 15:00, plus
devil's advocate). A failed post is retried and logged "alert NOT sent"; the next card says so.
**Storage (owner decision of 15 Oct 2026):** card records are kept in Google Drive only; the public repository holds
only their hashes and scores, never live strikes or entry ranges.

**Interfaces.** `TradeCard` (data), `CardBuilder` (from decision, risk, forecast, weather and advocate records),
`CardRenderer` (Slack today, dashboard later: one class each), existing `AlertSender`, new `DevilsAdvocate`
(`07_ai_team.md`). Wiring: a new `fno/cards/wiring.py`.

**Evaluation metric.** Delivery time (cutoff to Slack), calibration of every probability the cards stated, the card's
net result, share of `NO TRADE` days and their price of staying out.

**Failure modes.** Numbers on the card differ from the desk's records (the card is built only from committed records,
with their hashes in the card footer); a stale card acted on late (valid-until time on every card); Slack outage
(retry, log, and the next card states the miss); too many messages (one card a day; alerts are rate-limited, 6.5).

## 4.2 Layer 7: live monitor of open paper trades

**Purpose.** During market hours, watch every open paper position and the market every 15 minutes, apply the exit
plans exactly as registered, and alert the owner fast on danger. It never opens a trade (decisions stay once a day,
owner decision of 12 Oct 2026, "Decisions once a day, around 3:00 pm", option C).

**Two modes, declared per strategy version.**
- `alert_only` (default): the monitor alerts; exits still happen only at the daily decision time.
- `intraday_exits`: the registered exit rules are evaluated on each 15-minute snapshot and paper exits fill at the
  owner's action time (E8), assuming up to 1 hour of owner delay (the owner's maximum, owner decision of 15 Oct 2026;
  R = 60 as the primary fill is the orchestrator's proposal, reasoning only, owner to confirm); an
  exit rule that only helps with a faster reaction is flagged and judged at R = 60. Whether intraday exits help is
  itself a registered comparison (the same version is shadowed in the other mode); the 12 Oct decision ("all-day
  watching later only if data shows it helps") is met by that test, not assumed.

**Checks on each snapshot.** Loss used reaches 50% and 80% of the position's maximum loss; NIFTY within 0.5% of a short
strike; an exit rule hit; NIFTY moved at least 1.5% from the previous close; VIX up at least 10% in the session; the
weather upgraded to RED; quotes stale for 30 minutes; expiry or physical settlement near (stock options settle by
delivery: an in-the-money stock option held to expiry is refused by C4 unless the plan exits before). Thresholds are
proposals (reasoning only), versioned, owner decides.

**Outputs.** Alert records (time of the snapshot, time sent, condition, position), paper exits in `intraday_exits`
mode, a heartbeat every snapshot.

**Interfaces.** `PositionMonitor` (runs checks), `MonitorCheck` (one class per check; strategy), existing `ExitRule`,
`AlertSender`, `IntradayQuoteSource` (A16). Wiring: a new `fno/monitor/wiring.py`.

**Evaluation metric.** Latency (snapshot to phone), missed alerts (a weekly replay of the day's snapshots through the
same checks finds any condition that was true but not sent), false-alarm share, uptime (snapshots checked / due).

**Failure modes.** Host down (a heartbeat; a second, independent checker alerts "monitor silent" after 30 minutes; the
daily card reports the day's uptime); stale quotes treated as live (staleness check first); alert storms (one alert per
condition per position per hour); scope creep into intraday trading (the monitor cannot create an entry: no entry code
path is wired into it, which the judge can check).

## 4.3 Layer 8: learning loop

**Purpose.** Learn from every outcome without fooling ourselves: separate bad luck from bad models, turn real errors
into new versions, and never edit the past.

**Weekly post-mortem (every Saturday; owner may pick the day).** Numbers by code, text by an AI writer that may only
cite those numbers, checked by the devil's advocate. Contents: forecasts resolved this week and their scores against
baselines; weather record and its misses; every card and its outcome; open positions; every loss's review; data health
(layer 1 metrics); budget used; factory status (ideas, gates, trial count); drift alarms.

**Why-it-was-wrong review of every loss** (and of every confident forecast miss: stated probability at least 0.8 or at
most 0.2 and wrong; and every GREEN day followed by a 2% move). Each is classified, by computation first:
1. **Within its stated odds** (luck): the event had a stated probability that makes it unsurprising (for example, a 30%
   outcome happened). Recorded as luck; no fix. Over many cases this class is checked by calibration: if "luck" happens
   more often than the stated odds allow, it was not luck but miscalibration.
2. **Model error:** the forecast or rule was miscalibrated or missed a known driver.
3. **Data error:** an input was wrong, late or missing.
4. **Execution error:** fills, costs, margins or expiry handled wrongly.
5. **Rule break:** a decision outside the registered rules (should be impossible; C4 and the judge check).
6. **Unknown or regime change:** recorded as such; watched by drift detection.

This is how "no place for luck" is made true in the only honest way: luck cannot be removed, but it is **measured and
labelled**, and it never gets credit for a win either. A win inside its stated odds is counted the same way.

**Fixes become new versions, never silent edits.** A fix to a forecaster, weather model, strategy or rule is a new
version in D6's registry, registered in the ledger, tested forward from its registration. The old version's record is
kept and never recomputed (S1 `reporting_per_version`).

**Drift detection.** A pre-registered CUSUM on each strategy's per-trade net and each forecaster's loss difference
against its baseline (rule in `05_volatility_research.md` section 5.8). A strategy alarm pauses new entries until the
owner reviews; a forecaster alarm lowers its house-forecast weight at the next scheduled review.

**Monthly report and quarterly reviews.** Story S4, unchanged in purpose; the quarterly review is the only place where
statistics retire or promote anything (S1 `review_dates`).

**Interfaces.** `PostMortemBuilder`, `LossReview` (classifier; one class per class test), `DriftDetector` (strategy:
CUSUM now), existing version registry (D6). Wiring: a new `fno/learning/wiring.py`.

**Evaluation metric.** Share of losses reviewed within a week; share classified as luck vs error, compared with the
calibration test; repeat errors of the same class; time from error found to new version registered.

**Failure modes.** Storytelling after the fact (the classification is computed from stated probabilities first; an AI
narrative cannot change the class); fixing on noise (a fix is a new version tested forward, never applied to past
results); review fatigue (the post-mortem is one page; details link to records).

## 4.4 Contracts every layer keeps (ChatGPT review 95, "Missing"; acceptance criteria of A16, T1 and LM1)

- **Issuance time independent of git.** Committer time is never evidence. The daily card's Slack post carries, in its
  footer, the SHA-256 of every forecast, weather record and objection it shows; Slack's server timestamp of that post
  is their issuance time, and GitHub's server-side push receipt is a second witness. A record with neither before its
  deadline is unscored.
- **Data rights, retention and security.** Before A16 records anything, the owner checks Groww's API terms on storing
  and publishing quotes. Raw quotes stay in Drive (private); the public repository holds only derived figures
  (per-session realised variance, counts, gaps) unless the terms allow more. Raw files are kept under A11's revision
  rule unless the terms require deletion. Key handling follows section 6.6. Card records follow section 8.5.
- **Clock contract.** Every time is stored in UTC with its offset and shown in IST. Each row keeps the source's own
  time (Groww quote time, NSE file time, the US close's date) apart from `first_seen_at` (our host's clock). The host
  clock is checked against Slack's and GitHub's server times each run; a skew above 5 seconds is a WARNING. Which day
  is a session comes only from the NSE session calendar (A7); a US close belongs to the IST date on which it is known.
- **Owner unavailable.** The owner's availability calendar (E8) is part of the owner profile. DANGER alerts are still
  sent and logged while the owner is away; the paper record assumes action at the next available time (E8), and a
  summary is sent when the owner is back. Every card and alert says: "if you cannot act by HH:MM, the paper record
  assumes ...".
