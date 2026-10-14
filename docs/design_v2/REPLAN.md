# REPLAN: every planned story under design v2

Owner, 14 Oct 2026: "I want to include further development as per new design"; no old-plan story starts until
design v2 passes the judge and ChatGPT. **Built work stays.** Statuses are read from `docs/stories/*` on 15 Oct 2026.
New story texts (one paragraph each, full story text written when the slice starts) are in `REPLAN_new_stories.md`.

## 1. Built or in flight: keep, finish the judge round, no new scope now

These are built (or partly built) and stay. Each finishes its current judge round as it stands; design v2 changes to
them come later as separate stories, never by reopening a passed criterion.

| Story | Status today | Decision | Reason and any later change |
|---|---|---|---|
| A8 Participant OI | partly built, measuring release days | keep | Positioning data is new information (section 1.3); idea O1 waits for its 20 days |
| A12 Filings archive | built, awaiting judge | keep | Results dates and numbers for R2 (stock options around results) |
| A14 NSE margins | in progress | keep | Funds and margins for every card; later rows for one- and two-leg shapes (STR1) |
| C3 Data checks | built, judge pending | keep | Every decision; the monitor adds its own staleness check (LM1) |
| C4 Hard validity | re-judge pending | keep | The last gate; later STR1 shapes and C5 bucket caps |
| D3 Decision record | built, awaiting judge | keep | Every card is built from it |
| D6 Version registry | built, awaiting judge | keep | "Fixes become new versions" (layer 8) rests on it |
| E2 Market packs | built, awaiting judge | keep | Later a new pack version with v4 inputs (intraday RV, global cues) |
| E3 Timetable | built, not live | keep | Later: owner-timing fills (E8), many strategies a day, the card hook (T1) |
| E5 Book 1 | built, judge pending | keep | Rules book unchanged |
| E6 Scorecard and pauses | built, awaiting judge | keep | Later: drift CUSUM (LR3) |
| F1 AI sessions | forecast part built | keep | Trading part deferred to slice E |
| G1 Forecast protocol | v1-v3 frozen | keep | The plan's "later" line is stale; v3 keeps running; v4 is new (G6) |
| G5 AI books' capture | built, live from 14 Oct | keep | Later a v4 prompt version (G10) |
| S1 Evaluation protocol | draft built, judge pending | keep, change items | Section 4 lists the items design v2 changes |
| O6 Fetch and trigger | awaiting judge | keep | The pattern every new data job follows |
| P8, P10 | built; read-back items pending | keep | India market blocks |

## 2. Planned, not built: keep, change or drop

| Story | Decision | Reason |
|---|---|---|
| B6 Candidate scan | **change: replaced by R1** | A scan over 2019-26 NIFTY history is a new trial on spent data (response 92); the factory's gates (idea card, cost wall, data spend, sample plan) replace it |
| D4 Book 2's envelope | keep, defer to slice E | Needed only when the hybrid book trades |
| D5 Book 3's constitution | keep, defer to slice E | Same, for the AI team book |
| F2 Role agents and finding cards | **change** | Limited to the analyst roles of `07_ai_team.md`; built with slice E, since a finding card is scored only through a decision |
| F3 Red team | **change: becomes T2 and T3** | The owner's devil's advocate attacks every call, every day, from slice A; the rule part is code (T2), the objections AI (T3) |
| F4 AI judge parts 2-3, owner overrides, monthly audit | **change** | Owner overrides on paper are **dropped** (owner: never override on paper; only S1's safety stop remains); the AI judge parts stay for slice E; the monthly session audit already runs under the 14 Oct conditions |
| F5 Book 2 decisions | keep, defer to slice E | Three approaches stay (owner, 13 Oct) |
| F6 Book 3 and its pilot | keep, defer to slice E | Same |
| F7 Matched shadow decisions | keep, defer to slice E | Scoreboard A needs all three books |
| F8 AI usage and cost | keep, **move earlier** (slice A, week 3) | The budget cap (BG1) needs it, and S1's freeze needs its code |
| F9 Role-value evaluation | keep; **code earlier** (slice B), use in slice E | S1 v1 cannot freeze until F9's code exists (owner's option A); building it early unblocks counting |
| S2 Scoreboard B | keep, **change** (slice B) | Adds the do-nothing index fund and cash benchmarks, after-tax results, net per rupee of capital tied, and the count of independent bucket-weeks |
| S3 Scoreboard A | keep; **code earlier** (slice B) | Same reason as F9: S1 v1's freeze needs its code; it reports only once books 2-3 trade |
| S4 Monthly report and reviews | **change** | Split: weekly post-mortem (LR1, slice A) and monthly report plus quarterly reviews (S4, slice C) |
| S5 Research feedback loop | **change: becomes LR2 and LR3** | Why-it-was-wrong reviews and drift detection, feeding new versions |
| P1 Read-model contract | keep, change, slice C | Adds card, forecast and weather pages; Slack comes first (T1) |
| P2 Read-model builder | keep, change, slice C | Same |
| P3 Atomic publisher to Azure | **change** | No new publisher: reuse P6/P7's `ReadModelPublisher` and run status; P3's remaining scope is the book and card pages |
| P4 Slack daily message and alerts | **change: becomes T1 plus the alert classes** | The card is the owner's main surface (layer 6), so it moves to slice A |
| P5 Frame read models | keep, defer to slice C | The order window serves the Manual account |
| MA1 Manual paper account | keep, defer to slice C | Now also the only place for the owner's own ideas (no overrides on the books) |
| W1 Shared dashboard repository | keep | Done in practice (W8's note); its status line should be corrected by the orchestrator |
| W3 F&O screens | keep, change, slice C | Screens for the card, forecast lab (37), strategy lab (38) and weather |
| W4 Access and freshness tests | keep, slice C | With W3 |
| W5, W6, W7, K1, K2, K3, K4 | keep, unchanged | Stock side and cutover: paused with stock work (decision 52); design v2 does not touch them |
| O1 Daily desk routine | **change**, slice B | One daily run: data checks, forecasts, weather, desk, card; fired from Actions as O6 does |
| O2 Failure handling | keep, change, slice B | Adds the monitor heartbeat and "alert NOT sent" paths |
| O3 Cross-repository tests | keep, slice C | With P1-P3 and W3 |
| O4 Runbook | keep, slice C | Covers the new layers |

**Dropped outright:** B6's history scan (replaced by R1) and F4's owner-override part. Nothing else is dropped: the
three books, the dashboard and the stock-side stories stay, in a later order.

## 3. New slice order

The milestones M2-M7 of `docs/IMPLEMENTATION_PLAN.md` and slices 3-5 of `docs/BUILD_MAP.md` are replaced, for unbuilt
work, by the slices below. Each slice is done only when its real output reaches the owner (BUILD_MAP rule 3). At most
two builders plus the judge at a time (owner's pace).

### Slice A (15 Oct - 4 Nov 2026): volatility forecasts and an honest daily card

**Week 1 (15-21 Oct)**
1. Judge rounds of the built queue (section 1). No new scope on them.
2. **G6** forecast protocol v4 written (section 5 of the design): judge, then ChatGPT; freeze after agreement.
3. **R1 (documents only):** `research/DATA_SPEND.md` filled in, the idea-card template, the cost-wall rule text.
4. **A16 step 0:** one-session feasibility check of Groww's historical candles and live 15-minute snapshots (read-only;
   counts, no outcomes); the owner decides the host (section 6.6).
5. **R2 feasibility study**, registered before running: stock options around results, from the NSE archive (volume,
   open interest, lot values against the Rs 10,000 cap) and one Groww snapshot of their bid/ask. Answer: can any
   defined-risk stock-option structure fit the cap with costs below half its plausible gross? Yes or no, with numbers.

**Week 2 (22-28 Oct)**
6. **G7** v4 baselines and rule forecasters on close proxies (V2, V3, V5, V6, V7), back-filled and labelled.
7. **M1** weather as a scored forecaster (v0 checklist as its baseline).
8. **T1** daily card v1 to Slack: `NO TRADE` with reason, weather, house forecasts with their records. **First real
   thing on the owner's phone.**
9. **A15** VIX full history; **A17** global cues (daily).
10. **A16** recorder live, if the host is decided.

**Week 3 (29 Oct - 4 Nov)**
11. **G8** v4 scoring (QLIKE, calibration slope) in `fno/forecast_scoring/`.
12. **F8** (minimal) and **BG1** budget meter with the stop-rule dates.
13. **C5** risk buckets and the Rs 20 lakh account settings (owner's numbers).
14. **E8** owner-timing fills.
15. **T2** devil's advocate rule checks on the card.
16. **LR1** first weekly post-mortem (Saturday 31 Oct): forecasts, weather, data health only.

### Slice B (November 2026): the factory runs forward, the record becomes countable

STR1 (one- and two-leg structures), R1 code, first forward shadow ideas registered (only those passing the cost wall;
V-ideas wait for rung 1), RM1 (real-money gate frozen before any counted paper decision), S2 change, S3 and F9 scoring
code (so S1 v1 can freeze under the owner's option A), S1 freeze, LR2 loss reviews, LR3 drift, T3 advocate objections,
LM1 monitor in `alert_only` mode (needs A16 and its host), O1 and O2 changes.

### Slice C (December 2026 - January 2027): surfaces and depth

G9 house forecast (first quarterly review), LM2 `intraday_exits` mode with its registered comparison, A18 stock-option
data if R2 passed, P1, P2, P3 (changed), P5, W3, W4, O3, O4, S4, MA1, G10 (AI books on v4 questions).

### Slice D (from about 31 May 2027): the stop-rule review

Section 8.2's review. Its outcome decides whether slice E starts, the budget halves, or the project stops or pivots.

### Slice E (when there is something to trade): the AI books trade

D4, D5, F1 trading part, F2, F4 (changed), F5, F6, F7, S3 reporting. **Proposal (reasoning only; owner decides):** start
when at least one strategy is approved to paper or an idea reaches rung 2, because before that books 2-3 would record
"no trade" every day at AI cost and teach nothing about judgement.

## 4. S1 protocol items design v2 changes (13 open items plus the open t-check)

| Item | Effect of design v2 |
|---|---|
| `common_start` | Unchanged rule; note that with slice E late, the three-book common start may be a year away; per-strategy and per-forecaster evaluation become primary until then |
| `pilot_evidence` | Unchanged |
| `timetable` | **Changes:** E8's owner-timing fills, the card's 15:08 delivery and the monitor's 15-minute slots join the timetable |
| `segments` | Unchanged |
| `primary_metric` | **Changes:** adds after-tax net and the two benchmarks per rupee of capital tied, as reported figures (the verdict measure itself stays net per unit of risk) |
| `scoreboard_a_standardisation` | Unchanged; used from slice E |
| `paper_gate` | **Changes:** 20 positions and 3 months stay a floor; each strategy also registers its own required sample from its expected edge and SD (section 5.5), and the larger number applies |
| `strategy_review_rule` | **Changes:** adds the drift CUSUM as an input |
| `catastrophic_loss_book` | **Changes:** Rs 30,000 on Rs 5 lakh becomes the account brake and bucket caps on Rs 20 lakh (section 6.2; owner's numbers) |
| `immediate_pauses` | **Changes:** the drift pause is a named exception (owner accepted drift detection on 14 Oct) |
| `review_dates` | **Changes:** adds the weekly post-mortem (descriptive) and the project stop-rule review (section 8.2) |
| `role_value_schedule`, `role_value_minimum_sample` | Unchanged; deferred to slice E |
| Open: t-based lower bound beside the bootstrap | **Recommend adding it** (design v2 relies on honest intervals; 6 blocks under-cover, some evidence) |

The five decided items (`uncertainty_criterion`, `catastrophic_loss_strategy`, `ai_cost_allocation`,
`reporting_per_version`, `frozen_files`) are not reopened. Note on `frozen_files`: the new scoring code (S2's change,
G8, E8) joins the hashed list before the freeze.

## 5. Owner decisions this design needs (one line each; proposals in brackets)

1. Host for the 15-minute recorder and monitor [(b) Azure Functions, or (a) routines first] (6.6).
2. Risk buckets and caps [bucket Rs 30,000; account Rs 1.5 lakh; new risk Rs 50,000 a day; brake Rs 1.2 lakh] (6.2).
3. Weather thresholds [RED at 2.5x the base rate of a 2% move, AMBER 1.5x] (2.3).
4. Minimum effects for "beats baseline" [3% QLIKE, Brier skill 0.02] (5.5).
5. Owner reaction time and availability [15 minutes in market hours] (3.2).
6. Monthly AI share and cash cap [half of measured plan minutes; any new recurring cost needs a yes] (8.1).
7. The stop-rule review and its outcomes (8.2).
8. The real-money gate and test numbers (8.3, 8.4).
9. Trade cards in public repositories [make private, or keep cards in Drive] (8.5).
10. When books 2-3 start trading [at the first approved strategy or rung-2 idea] (slice E).
11. S1 item changes (section 4).
