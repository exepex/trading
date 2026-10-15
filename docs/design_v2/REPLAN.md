# REPLAN: every planned story under design v2

Owner, 14 Oct 2026: "I want to include further development as per new design"; no old-plan story starts until
design v2 passes the judge and ChatGPT. **Built work stays.** Statuses are read from `docs/stories/*` on 15 Oct 2026.
New story texts (one paragraph each, full story text written when the slice starts) are in `REPLAN_new_stories.md`.

## 1. Built or in flight: keep, no new scope now

These are built (or partly built) and stay. Statuses are from `reviews/judge/README.md` on `main` (15 Oct 2026). Design
v2 changes to them come later as separate stories, never by reopening a passed criterion.

| Story | Status today | Decision | Reason and any later change |
|---|---|---|---|
| A8 Participant OI | merged (judge 89 and 95 addenda); measuring 20 release days | keep | Positioning data is new information (section 1.3); idea O1 waits for its 20 days |
| A12 Filings archive | merged in parts (judge 51 addenda 4-7); backfill running | keep | Results dates and numbers for R2 (stock options around results) |
| A14 NSE margins | PASS, merged (judge 77 addenda 4-5) | keep | Funds and margins for every card; later rows for one- and two-leg shapes (STR1) |
| C3 Data checks | PASS, merged as e3506ec (judge 81) | keep | Every decision; the monitor adds its own staleness check (LM1) |
| C4 Hard validity | PASS, merged (judge 83 addenda 3-5) | keep | The last gate; later STR1 shapes and C5 bucket caps |
| D3 Decision record | PASS, merged as f314254 (judge 80) | keep | Every card is built from it |
| D6 Version registry | PASS, merged as c12137e (judge 78) | keep | "Fixes become new versions" (layer 8) rests on it |
| E2 Market packs | PASS, merged as b4f1e1b (judge 72) | keep | Later a new pack version with v4 inputs (intraday RV, global cues) |
| E3 Timetable | PASS, merged (judge 82 addenda); not live (no routine yet) | keep | Later: owner-timing fills (E8), many strategies a day, the card hook (T1) |
| E5 Book 1 | PASS, merged as 58f5781 (judge 84) | keep | Rules book unchanged |
| E6 Scorecard and pauses | PASS, merged as 374ad67 (judge 73) | keep | Later: drift CUSUM (LR3) |
| F1 AI sessions | forecast part PASS (judges 62, 88, 90) | keep | Trading part deferred to slice E |
| G1 Forecast protocol | v1-v3 frozen (v3 confirmed, judge 64) | keep | The plan's "later" line is stale; v3 keeps running; v4 is new (G6) |
| G5 AI books' capture | PASS (judge 62), live from 14 Oct | keep | Later a v4 prompt version (G10) |
| S1 Evaluation protocol | tooling and draft merged (judges 85, 94); protocol still a draft, not frozen | keep, change items | Section 4 lists the items design v2 changes |
| O6 Fetch and trigger | judge 52: "FAIL for now, no defect" (side-by-side sessions and the owner's steps pending) | keep | The pattern every new data job follows |
| P8, P10 | PASS (judges 66, 79); read-back items pending | keep | India market blocks |

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
| F8 AI usage and cost | keep, **move earlier** (slice A) | The budget cap (BG1) needs it, and S1's freeze needs its code |
| F9 Role-value evaluation | keep; **code earlier** (slice B), use in slice E | S1 v1 cannot freeze until F9's code exists (owner's option A); building it early unblocks counting |
| S2 Scoreboard B | keep, **change** (slice B) | Adds the do-nothing index fund and cash benchmarks, after-tax results, net per rupee of capital tied (one definition frozen before use: return per rupee-day of funds at entry, the index over the same rupee-days), and the count of independent bucket-weeks |
| S3 Scoreboard A | keep; **code earlier** (slice B) | Same reason as F9: S1 v1's freeze needs its code; it reports only once books 2-3 trade |
| S4 Monthly report and reviews | **change** | Split: weekly post-mortem (LR1, slice A) and monthly report plus quarterly reviews (S4, slice C) |
| S5 Research feedback loop | **change: becomes LR2 and LR3** | Why-it-was-wrong reviews and drift detection, feeding new versions |
| P1 Read-model contract | keep, change, **slice A** (owner, 15 Oct 2026: "2 Yes", "1 Yes", "2 B") | Becomes the F&O data catalog: schemas, Mock examples (positive, negative, empty) and field tables of the card, weather, Forecast lab, Strategy lab and paper trades in the dashboard's contract, the single master contract (owner, 15 Oct 2026: "contract A"; this repository keeps the pinned copy and drift check); Slack still comes first (T1) |
| P2 Read-model builder | keep, change, slice C | Same |
| P3 Atomic publisher to Azure | **change** | No new publisher: reuse P6/P7's `ReadModelPublisher` and run status; P3's remaining scope is the book and card pages |
| P4 Slack daily message and alerts | **change: becomes T1 plus the alert classes** | The card is the owner's main surface (layer 6), so it moves to slice A |
| P5 Frame read models | keep, defer to slice C | The order window serves the Manual account |
| MA1 Manual paper account | keep, defer to slice C | Now also the only place for the owner's own ideas (no overrides on the books) |
| W1 Shared dashboard repository | keep | Done in practice (W8's note); its status line should be corrected by the orchestrator |
| W3 F&O screens | keep, change, slice C | Screens for the card, forecast lab (37), strategy lab (38) and weather |
| W4 Access and freshness tests | keep, slice C | With W3 |
| W5, W6, W7, K1, K2, K3, K4 | keep, unchanged | Stock side and cutover: paused with stock work (owner decision of 13 Oct 2026, "Priority: build Omenix F&O end to end first"); design v2 does not touch them |
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

### Slice A (planning range: about 3-6 weeks from 15 Oct 2026): the first release

**Scope, revised after ChatGPT review 95 (section 11, accepted in part):** trustworthy inputs, frozen and scored V6 and
V1 forecasts, the daily `NO TRADE` card and a measured budget. Everything that only matters once paper trades exist
(risk buckets, owner-timing fills, the advocate's rule checks, the monitor) moves to slice B. Two cheap items stay
here although ChatGPT's minimal list omits them: the R2 feasibility study (a few days of research, no build, and it
decides whether a whole branch of the plan exists) and the weekly post-mortem (the only place the owner sees the
scores weekly).

The order below is a sequence, not a calendar. It depends on ChatGPT's review of G6 (v4 cannot freeze before it), the
owner's host decision for A16 and Groww's terms (section 4.4 of the design).

1. Judge rounds of anything still open in section 1. No new scope on them.
2. **G6** forecast protocol v4 written (section 5 of the design): judge, then ChatGPT; **frozen before any counted v4
   forecast**. G7 and G8 may be built and back-filled before the freeze (labelled exploratory); only forecasts after
   the freeze count. G1 v3 keeps running unchanged.
3. **A16 step 0:** Groww's terms on storing and publishing quotes (owner), then a one-session feasibility check of
   historical candles and live 15-minute snapshots (read-only; counts, no outcomes); the owner decides the host (6.6).
4. **R1 documents:** `research/DATA_SPEND.md`, the idea-card template, the feasibility-screen rule text.
5. **R2 feasibility study**, registered before running: stock options around results, from the NSE archive (volume,
   open interest, lot values against the Rs 10,000 cap) and one Groww snapshot of their bid/ask. Answer: can any
   defined-risk stock-option structure fit the cap with a positive expected net on a conservative bound, and how many
   effective independent clusters (sector and results week) are there a year? Yes or no, with numbers.
6. **A15** VIX full history; **A17** global cues (daily).
7. **G7 phase 1:** baselines and rule forecasters for V6 (now, daily closes) and V1 (once A16 has 20 sessions).
8. **M1** weather as a scored forecaster (V6; the v0 checklist as its baseline).
9. **G8** v4 scoring (the QLIKE ranking loss `ln f + RV / f`, no floor; Brier, calibration, the null-centred bootstrap
   and the HAC sensitivity).
10. **T1** daily card v1 to Slack: `NO TRADE` with reason, weather, house forecasts (baselines until something passes)
    with their records, and the issuance hashes. **First real thing on the owner's phone.**
11. **A16** recorder live, once the host and terms allow.
12. **F8** (minimal) and **BG1** budget meter with the stop-rule dates.
13. **LR1** weekly post-mortem: forecasts, weather, data health only.
14. **P1** F&O data catalog (owner, 15 Oct 2026; a third builder, one-time exception to the pace): the card, weather,
    Forecast lab, Strategy lab and paper-trades contracts with Mock examples, so T1, M1, G8 and W3 build against one
    contract. P2-P5 and the screens stay in slice C.

**Fallback (ChatGPT review 96):** if A16's host or Groww's terms are delayed, slice A ships without A16: V6, the
`NO TRADE` card and the budget go live, and V1 stays pending. Anything that needs A16 shows "not enough data yet" in
the card and LR1, never a failure.

### Slice B (after slice A): the factory runs forward, the record becomes countable

G7 phase 2 (V2-V5, V7), STR1 (one- and two-leg structures), R1 code, first forward shadow ideas registered (screened
ideas kept in the trial count; V-ideas may run as `exploratory_shadow` from the start, with promotion waiting for rung
1), C5 risk buckets and the Rs 20 lakh settings (owner's numbers), E8 owner-timing fills, T2 advocate rule checks, RM1
(real-money gate frozen before any counted paper decision), S2 change, S3 and F9 scoring code (so S1 v1 can freeze under
the owner's option A; this code must not produce a scored Book-3 trading comparison before the common start, which S1's
pilot rule already forbids), S1 freeze, LR2 loss reviews, LR3 drift, T3 advocate objections, O1 and O2 changes. **LM1**
monitor, `alert_only`, starts only when the first paper or shadow position is open: a monitor with nothing to watch adds
nothing.

### Slice C (December 2026 - January 2027): surfaces and depth

G9 house forecast (first quarterly review), LM2 `intraday_exits` mode with its registered comparison, A18 stock-option
data if R2 passed, P2, P3 (changed), P5, W3, W4, O3, O4, S4, MA1, G10 (AI books on v4 questions).

### Slice D (from about 31 May 2027): the stop-rule review

Section 8.2's review. Its outcome decides whether slice E starts, the budget halves, or the project stops or pivots.

### Slice E (when there is something to trade): the AI books trade

D4, D5, F1 trading part, F2, F4 (changed), F5, F6, F7, S3 reporting. **Decided (owner, 15 Oct 2026):** start
when at least one strategy is approved to paper or an idea reaches rung 2, because before that books 2-3 would record
"no trade" every day at AI cost and teach nothing about judgement.

## 4. S1 protocol items design v2 changes (13 open items plus the t-check; all accepted by the owner on 15 Oct 2026)

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
| t-based lower bound beside the bootstrap | **Added** (owner, 15 Oct 2026; design v2 relies on honest intervals; 6 blocks under-cover, some evidence) |

The five decided items (`uncertainty_criterion`, `catastrophic_loss_strategy`, `ai_cost_allocation`,
`reporting_per_version`, `frozen_files`) are not reopened. Design v2 adds nothing to `frozen_files` by itself. G8's
forecast scoring is frozen by protocol v4's own freeze (G6), not by S1. One addition is put to the owner as decision 12
(section 5).

## 5. Owner decisions this design needed (all 12 decided on 15 Oct 2026; still open: the availability calendar)

1. **Decided 15 Oct 2026: (a), a Claude routine** (6.6).
2. **Decided 15 Oct 2026: accepted as proposed** (bucket Rs 30,000; open maximum losses at most Rs 1.5 lakh; new risk
   Rs 50,000 a day; brake Rs 1.2 lakh) (6.2).
3. **Decided 15 Oct 2026: weather thresholds as proposed** (relative and absolute levels, maximum RED frequency 15%)
   (2.3).
4. **Decided 15 Oct 2026: minimum effects 3% QLIKE or Brier skill 0.02**, also the stop rule's futility margin; exact
   unit confirmed by the owner, 15 Oct 2026 (on RV > 0 paired dates, at least 3% of the baseline's mean textbook QLIKE;
   zero-RV dates counted separately) (5.5).
5. **Decided 15 Oct 2026: 5 minutes when available, 30 on average, at most 1 hour**; every E8 paper trade fills at 5, 30
   and 60 minutes, all reported, and the verdict uses 60 minutes (owner, 15 Oct 2026); the availability
   calendar is still to be given (3.2, 6.5).
6. **Decided 15 Oct 2026: AI share at most half of measured plan minutes; any new recurring cost needs a yes** (8.1).
7. **Decided 15 Oct 2026:** the stop-rule review as in 8.2; on "undecided", option 1 if the projected date is within
   2 years, otherwise option 2. **Amended 15 Oct 2026:** zero eligible or resolved shadows gives Test B "undecided /
   no_economic_test", never "no".
8. **Decided 15 Oct 2026: the real-money gate and test accepted**; the exact account size (about Rs 2 lakh) and
   per-trade cap (Rs 4,000-5,000) are confirmed before RM1 freezes (8.3, 8.4). **Amended 15 Oct 2026:**
   selection-adjusted evidence always (a second untouched forward period or Holm across the trial count), and the
   real-money pass is a paired real-vs-paper test with a prediction interval.
9. **Decided 15 Oct 2026: (b), card records in Google Drive only**; the public repositories hold no live strikes or
   entry ranges (8.5).
10. **Decided 15 Oct 2026:** books 2-3 start trading at the first approved strategy or rung-2 idea (slice E).
11. **Decided 15 Oct 2026:** all S1 changes of section 4 accepted, plus the t-based check.
12. **Decided 15 Oct 2026: (a), E8's code joins S1's `frozen_files`.** The question was: add E8's owner-timing fill code
   to S1's `frozen_files`? [(a) yes; ChatGPT review 95 also recommends it; or (b)
   S1 binds E8's exact version and hash in a separate freeze record] Reason: E8 decides the fill price of every counted
   paper trade; unhashed, the fill rule could be changed after results are seen and alter counted results. Cost of
   doing it: S1 v1 cannot freeze before E8 exists (planned for slice B, alongside S3 and F9, so little extra delay).
   Cost of not doing it: counted results rest on a fill rule that is not frozen with them. This would change the
   owner's decided `frozen_files` item, so it is the owner's call, not this design's.
