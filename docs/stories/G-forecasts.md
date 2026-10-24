# Epic G: daily forecasts (a secondary diagnostic)

Roles: statistician (owner), quantitative modeller, volatility trader, mathematician. Goal: every book answers five
frozen probability questions each session day, scored against frozen point-in-time baselines, as a diagnostic of
market reading that can never promote an unprofitable book (design 12.7, 12.8). Story template, definition of done
and the full story index: `docs/IMPLEMENTATION_PLAN.md`.

---

## G1. Forecast protocol and the 30-day ATM implied-volatility estimator

**Repository:** trading

**Description:** As the statistician, I want the five questions, their exact targets, the scoring rules and the
multiplicity adjustment frozen in a protocol before any forecast is scored, so that forecast results cannot be
reshaped after the fact.

**Context and why:** Design 12.7 questions: (1) P(NIFTY close in 20 trading days > today's close); (2)
P(|NIFTY return over the next 20 trading days| >= 3%); (3) P(next-20-day annualised realised volatility > trailing
20-day realised volatility today); (4) P(India VIX close in 10 trading days > today's close); (5) P(next-20-day
annualised realised volatility < today's 30-day at-the-money implied volatility). Scoring: Brier for all, log score
with probabilities clipped to [0.01, 0.99], calibration tables, pairwise differences by forecast date with a
moving-block bootstrap of block length 20 trading days, multiplicity fixed before scoring. Review 19 left the exact
30-day ATM IV estimator to story level. Forecasts start earlier than trading (12.11).

**Scope.** In: the protocol document, exact target definitions, the 30-day ATM IV estimator, the frozen multiplicity
method, the forecast record schema. Out: producing forecasts (G3), baselines (G2), scoring code (G4).

**Expected design:** `research/forecasts/PROTOCOL.md` frozen (FREEZE record with commit and hashes, like B5) and
registered in the ledger (B4). Targets use the session calendar (A1) for "trading days", NIFTY 50 and India VIX closes
(A3 index closes), realised volatility exactly as B1 (root mean square of daily log returns, not demeaned, times
sqrt(252)). **30-day ATM IV:** variance interpolation in time between the two monthly expiries bracketing 30 calendar
days, each expiry's ATM IV from the average of the call and put implied volatilities at the B1 ATM strike (B1 rules
for prices and solver failures); if 30 days is not bracketed, the nearest expiry with at least 7 days, flagged.
Inputs at the forecast cutoff come from the common market pack (E2) for live forecasts and from the panel for
history. Record schema `fno/forecast/schema.py`: `book, date, cutoff, question, probability, method_or_version,
pack_sha256`.

**Acceptance criteria:**
1. Each target is computed by a reference function that a test checks against hand-worked values on fixture data
   (all five questions, including a holiday inside the window).
2. The 30-day ATM IV estimator matches a hand computation on two fixture days (bracketed and not bracketed).
3. The protocol is frozen and its commit precedes the first scored forecast (checked by G4).
4. The multiplicity method (questions x book pairs) is named with its exact procedure before scoring.

**Test plan:** target and estimator unit tests; freeze-order test.

**Judge verifies:** recomputes one target and one IV value by hand; checks the freeze commit order.

**Depends:** A1, A3, B1, B4 · **Size:** M · **Status:** v1 frozen (judge 47 addendum 2 MET) (protocol v1 with review 28 changes; freeze record research/forecasts/FREEZE.md). v2 (`research/forecasts/PROTOCOL_v2.md`, review 29's eight changes): judge 47 addendum 3 PASS; frozen (protocol commit ab2e811, freeze record research/forecasts/FREEZE_v2.md, ledger trials 37-41). v3 (`PROTOCOL_v3.md`, the panel extends daily, A13; ChatGPT review 30, response 69): judge 64 addenda 1-2 PASS; freeze record `FREEZE_v3.md` (c1bf97f, two sections), confirmed frozen 14 Oct 2026 (protocol commit 904c036; amended before confirmation in f67065a; `docs/DESK_DECISIONS.md`)

---

## G2. Frozen baselines

**Repository:** trading

**Description:** As the quantitative modeller, I want three baselines computed point-in-time by frozen methods, so that
each book's forecasts are judged against what the market and simple statistics already said.

**Context and why:** Design 12.7: (a) the risk-neutral probabilities implied by NIFTY option prices, labelled
risk-neutral (option prices include risk premia, not real-world probabilities); (b) a historical base rate from a
frozen rolling window; (c) for questions 3-5, a frozen simple statistical model. Book 1's own forecasts come from a
frozen point-in-time method, never refitted after outcomes.

**Scope.** In: the three baselines, their exact methods, the history back-fill for evaluation. Out: AI forecasts.

**Expected design:** `fno/forecast/baselines.py`. (a) Risk-neutral: from the A4 snapshot (live) or panel closes
(history): questions 1 and 2 from the option-implied distribution of the expiry nearest 20 trading days (Breeden-
Litzenberger on call prices with a stated smoothing and interpolation, or the lognormal with the ATM IV as a fallback,
both frozen in G1's protocol); questions 3-5 marked "no risk-neutral equivalent" where none exists (VIX options are not
in the data). (b) Base rate: frequency of the event over the previous 750 trading days (frozen window). (c) Questions
3-5: a frozen simple model (e.g. a HAR-type realised-volatility regression fitted only on data before each forecast
date with a fixed refit schedule), its specification frozen in the protocol.

**Acceptance criteria:**
1. A look-ahead test (B1 harness) proves no baseline uses data after its cutoff.
2. Each baseline reproduces hand-computed values on fixture days.
3. The refit schedule of (c) is fixed and a test proves a refit uses only earlier data.
4. Every baseline value is labelled with its method name and version.

**Test plan:** fixture tests; look-ahead tests.

**Judge verifies:** recomputes one risk-neutral probability and one base rate by hand.

**Depends:** G1, A3, A4 · **Size:** M · **Status:** done (judge 54 PASS; claims: response 62 and its v2 addendum; live values under protocol v2, frozen at ab2e811)

---

## G3. Book 1 forecast capture

**Repository:** trading

**Description:** As the head of desk, I want Book 1's five probabilities committed each session day by its frozen
method, so that forecast scoring can start before any book trades and before the AI books exist.

**Context and why:** Design 12.7 (Book 1's forecasts come from a frozen point-in-time method, never refitted after
outcomes) and 12.11 (forecasts start earlier than trading). The AI books' forecasts come later with their sessions
(G5; ChatGPT review 26: M3 must not claim three-book forecasts before the AI books exist).

**Scope.** In: Book 1's method, capture, validation, commit. Out: AI books (G5), scoring (G4).

**Expected design:** `fno/forecast/book1_method.py` (frozen; by default the base-rate and statistical baselines
combined by a fixed rule written in the protocol); records validated by `fno/forecast/schema.py` and committed daily
(before the deadline once the desk runs; by the daily routine before then).

**Acceptance criteria:**
1. Book 1 has five probabilities in [0, 1] per session day, or a recorded "no forecast" (missing, never imputed).
2. Book 1's method is identical on every day of a version (hash of the method file in each record).
3. Forecasts committed after the deadline are ignored.

**Test plan:** validation tests; method-hash test.

**Judge verifies:** checks one week of Book-1 forecast files for completeness and commit order.

**Depends:** G1, G2 · **Size:** S · **Status:** done as built (judge 54 PASS; claims: response 62 and its v2 addendum; the job runs protocol v2's live capture from Wed 14 Oct 2026; first live runs 14 and 15 Oct, research/forecasts/live_v2/)

---

## G4. Forecast scoring and reports

**Repository:** trading

**Description:** As the statistician, I want each book's forecasts scored against outcomes and baselines with
overlap-aware uncertainty, so that we know who reads the market best, labelled as secondary to profit.

**Context and why:** Design 12.7 and 12.8: Brier, clipped log score, calibration tables, pairwise differences by date
with a 20-day moving-block bootstrap, multiplicity as frozen; forecasts cannot promote an unprofitable book.

**Scope.** In: outcome resolution, scores, calibration, pairwise comparisons, the report section for S4 and the
dashboard. Out: decisions about books (S4 review).

**Expected design:** `fno/forecast/scoring.py`; resolves each forecast when its target date passes (A1 calendar,
A3 closes); computes per book and baseline Brier, log score, calibration bins (fixed edges), and pairwise score
differences with the block bootstrap (seed fixed in the protocol) and the frozen multiplicity adjustment; output
`research/forecasts/scores/<date>.json` for P2.

**Acceptance criteria:**
1. Known-answer tests: Brier and log score on a fixture set match hand values; clipping is applied.
2. The block bootstrap with the fixed seed reproduces a committed interval exactly.
3. A forecast is never scored before its target date is resolvable.
4. Every report labels forecasts as secondary to net profit.

**Test plan:** known-answer tests; determinism tests.

**Judge verifies:** recomputes one book's Brier score for one month.

**Depends:** G1, G3 (G5 for books 2 and 3) · **Size:** M · **Status:** done (judge 58 PASS; claims `reviews/claude/response_66_g4.md`; code in `fno/forecast_scoring/`, outside the frozen `fno/forecast/`). AI books' scoring (judge 58's list) added after the pass: response 66 section "Addendum"

---

## G5. AI books' forecast capture

**Repository:** trading

**Description:** As the statistician, I want books 2 and 3 to answer the same five questions in their isolated
sessions every session day, so that all three books are compared on forecasts too.

**Context and why:** Design 12.7 (all books answer the five questions every trading day); F1 (isolated sessions,
receipt and promotion deadlines). Split from G3 after ChatGPT review 26.

**Scope.** In: the forecast part of the AI books' session output, validation, commit; G4 reports missing AI forecasts
before this story is done as "not yet running", never as zero skill. Out: scoring (G4).

**Expected design:** the AI book's session output (F1) includes `forecasts`; validated by `fno/forecast/schema.py` and
committed with the decision before the promotion deadline.

**Acceptance criteria:**
1. Each AI book has five probabilities per session day, or a recorded "no forecast".
2. Forecasts received after the receipt deadline are ignored.
3. G4's report shows each book's coverage (days with forecasts / session days).

**Test plan:** validation tests with fake session outputs.

**Judge verifies:** checks one week of AI-book forecast files.

**Depends:** G1, G3, F1 · **Size:** S · **Status:** built: criterion 3 (coverage in G4's report) MET (judge 62 addendum 1); G4's scoring gate PASS (judge 62 addendum 2); first live run 14 Oct 2026 ~15:10 IST

---

## G6. Forecast protocol v4 (movement size, questions V1-V7)

**Repository:** trading

**Description:** As the statistician, I want the volatility questions V1-V7, their baselines, scores, registered family,
minimum effects and power rule written and tested before any v4 score, so that no result can shape its own rules.

**Context and why:** Design v2 section 5 and the stop rule of 8.2 (owner decisions of 15 Oct 2026); judge 96 and its
addenda; ChatGPT reviews 95-98 (review 98's caveat: cumulative Holm with p = 1 for hypotheses not yet judged, and every
report stating family membership and the decision timestamp). G1 v3 stays frozen and keeps running.

**Scope.** In: `research/forecasts/PROTOCOL_v4.md`, its executable rules in `fno/forecast_v4/`, tests and fixtures.
Out: the freeze record (after the judge's PASS and ChatGPT's review), baselines' code (G7), scoring and reports (G8).

**Acceptance criteria** (REPLAN_new_stories.md, plus the orchestrator's list of 15 Oct 2026), each with a passing test:
1. The QLIKE ranking loss `ln f + RV / f` at zero, near-zero and missing RV, with no floor; its paired differences equal
   the textbook form's when RV > 0.
2. The frozen day sets: the primary test on every scored non-void date (zeros in); the 3% minimum-effect gate on the
   same paired dates with RV > 0; the excluded-zero count on every report.
3. The exact one-sided null-centred block bootstrap, p = (1 + #{D* - D <= D}) / (B + 1) (seed, blocks, missing pairs);
   HAC as a sensitivity only.
4. Holm across the registered family; p = 1 for members not judged; family membership and decision timestamp stated.
5. Baseline eligibility: premium-adjusted implied primary for V2 and V3; V5's Brier-scored option-implied probability.
6. V4's units with a dimensionally checked golden example (calendar IV against session RV).
7. V5's outcome from the expiry's final settlement, with its source and timestamp frozen, never a later daily close.
8. The session set: A7 regular sessions, muhurat excluded.
9. The stop rule's decision unit and A/B table with zero trials, missing and void outcomes; futility against the
   minimum effect.
10. The 60-outcome power report.
11. Disclosure of the 2017-26 base rates measured before the freeze, on regular sessions only.

**Test plan:** known-answer and hand-rebuild tests in `tests/forecast_v4/`; planted mutations.

**Judge verifies:** re-derives the V4 golden example and the disclosed base rates; rebuilds one bootstrap p-value.

**Depends:** G1, G2, G4 · **Size:** M · **Status:** built on `story/g6-protocol-v4`, awaiting the judge, then ChatGPT;
not frozen (claims `reviews/claude/response_99_g6-protocol-v4.md`)

---

## G7. v4 baselines and rule forecasters, phase 1 (V6 now, V1 when A16 has 20 sessions)

**Repository:** trading

**Description:** As the quantitative modeller, I want protocol v4's baselines and one simple rule forecaster per
question for V6a, V6b and V1, computed point in time from committed data, back-filled (labelled exploratory) and
captured live each session, so that G8 can score them and the daily card can show them before anything else passes.

**Context and why:** REPLAN slice A item 7; `REPLAN_new_stories.md` G7; protocol v4 (`research/forecasts/PROTOCOL_v4.md`,
merged at 597487f, **not frozen yet**) sections 1-3 and 5.6; design 5.7 rule 5 (a rule forecaster fits at most 5
parameters, on rolling past windows only); decision 56 (rows with provenance `backfilled`, A16b, never count as live
forecast inputs); the owner's 15 Oct rules (keep the design simple; test real cases only). G7's file hashes go into
v4's freeze record after G7 and G8 exist and the judge checks them, so G7's files are kept stable and named.

**Scope.**
- **In:** V6a and V6b: their outcomes from official closes, the base-rate baseline (primary) and one rule forecaster.
  V1: the session RV series (A16's live `rv/` rows; the close proxy for the daily models), the trailing, EWMA, HAR
  daily and HAR intraday baselines, the primary switch, and one rule forecaster. The v4 forecast record, its files and
  its validation; the exploratory back-fill (V6 from 2017; V1 from A16's live rows only); a live capture command;
  wiring in `fno/forecast_v4_rules/wiring.py`.
- **Out:** V2-V5 and V7 (phase 2), the raw and premium-adjusted implied baselines (phase 2: they are V2's and V3's
  primary and only "also reported" for V1), scoring, pairs and reports (G8), adding the capture to the daily routine
  (at v4's freeze, a schedule change), the freeze record (G6), M1's weather model.

**Expected design** (pure calculations apart from I/O; G6's `fno/forecast_v4/` is called, never re-implemented):
- `fno/forecast_v4_rules/` (new package; every file under 350 lines):
  - `series.py`: regular-session closes and `vix_closes()` (India VIX, for G8's V7) from `research/data/nifty-panel/warmup_closes.csv`
    (`session == regular`, `forecast_v4.sessions`), close-proxy `RV_s`, V6a and V6b outcomes with their resolution
    session, and A16's live intraday `RV_s` rows. **The one place for these rules:** G8 imports them to resolve
    outcomes; G7 writes no outcome files (agreed with G8, 15 Oct).
  - `baselines.py`: `Trailing`, `Ewma`, `HarDaily`, `HarIntraday`, `BaseRate` behind one interface (`PointBaseline`
    for variances, `ProbabilityBaseline` for probabilities), each returning a value or `None` (missing, never filled).
  - `rules.py`: the two rule forecasters below.
  - `records.py`: the v4 record and its CSV files; `capture.py`: one session's forecasts at the cutoff; `backfill.py`.
  - `wiring.py` (composition root) and `cli.py`: `python -m fno forecast-v4 capture` (today only) and `python -m fno
    forecast-v4 backfill`.
- **Changed while building (for judge D):** the text first named `fno/forecast/baseline_wiring.py` (REPLAN's wording)
  and `fno/forecast v4-capture [--day D]`. The v2 freeze pins every file of `fno/forecast/` (`FREEZE_v2.md`;
  `tests/forecast/test_freeze_v2.py` fails on any edit, found by the G8 builder), so the wiring and the CLI live in
  this package, as G4's do in `fno/forecast_scoring/`. `--day` is dropped: a live row is made on its own day only.
- **Point in time (protocol 3.1):** an input enters a forecast for `d` only if it was first seen before `d`'s 15:00 cutoff.
  `d`'s own close and `d`'s own `RV_s` are not known at 15:00, so the latest session RV a forecast for `d` reads is
  `d-1`'s, and protocol 3.1's "ending at `d`" is read as "ending at the last session first seen before the cutoff"
  (stated for the judge).

**The two rule forecasters (zero fitted parameters; design 5.7 rule 5):**
- **`v6_ewma_t4` (V6a, V6b):** `s` = the square root of the EWMA close-proxy session variance (lambda 0.94, the EWMA
  baseline's own series) at the last session before the cutoff; `p1 = P(|X| >= 0.02)` with `X = s x T / sqrt(2)`, `T`
  Student's t with 4 degrees of freedom (variance 2, so `X` has variance `s^2`), using `forecast_v4.student_t.t_cdf`;
  V6a = `p1`, V6b = `1 - (1 - p1)^5` (independent sessions: reasoning only). Fixed choices, said plainly: lambda 0.94
  (RiskMetrics) and 4 degrees of freedom (fat tails of daily index returns, reasoning only; not fitted, so nothing is
  tuned on the spent 2017-26 data).
- **`v1_close_blend` (V1):** the mean of the HAR daily and EWMA one-session variance forecasts on the close proxy;
  missing when either is missing. Reasoning only: an equal-weight blend of two simple models, as Book 1 v1-v3 blends its
  baselines.
- **Slots (protocol 5.6):** `v1_close_blend` is proposed for V1's `rules` slot. V6's `rules` slot is named for M1's
  weather model in protocol 5.6, so `v6_ewma_t4` is registered as **reported only** (orchestrator decision 70, 15 Oct:
  V6's `rules` slot is M1's; `v1_close_blend` takes V1's `rules` slot). Registration itself (the ledger rows) happens at v4's freeze.

**Acceptance criteria** (each with a test; real cases: positive, negative, boundary and empty):
1. **V6 outcomes** from regular-session closes: `abs(ln(c(t+1) / c(t))) >= 0.02` (at 0.02 exactly: yes; just under: no);
   V6b any of the next 5 returns; a special or muhurat session's move sits inside the next regular return. The
   committed closes reproduce the disclosed counts (protocol 8): 100 of 2,409 and 331 of 2,405.
2. **Resolution timing:** V6a for `t` resolves at `t+1`'s close, V6b at `t+5`'s; an outcome counts for a base rate on
   `d` only if resolved before `d`'s cutoff.
3. **Base rate:** the share of 1s among the most recent 750 resolved, non-void outcomes before the cutoff; at least
   500, else missing (499 missing, 500 present).
4. **Close-proxy RV and EWMA:** `RV_s = (ln c(t) / c(t-1))^2`, zero kept; EWMA `s2_t = 0.94 s2_(t-1) + 0.06 RV_t` seeded
   with the mean of the first 250 sessions, eligible from session 251 (hand-computed fixture).
5. **HAR daily:** OLS in levels of the mean next-`h` RV on an intercept and the mean RV of the last 1, 5 and 22
   sessions; the most recent 750 rows resolved before the refit (500 minimum: 499 none); refit on the first scored
   session of each month; a refit uses only rows resolved before it (look-ahead test); forecast `h x prediction`;
   a forecast that is not strictly positive is missing.
6. **V1 inputs and switch:** V1 starts after 20 non-void **live** A16 sessions (19: not started); `HarIntraday` is
   eligible from 250 live sessions (up to 750), and from its first eligible day it is V1's primary for good
   (`forecast_v4.eligibility.primary_baseline`); rows with provenance `backfilled` (A16b's `rv-candle/`) never count
   toward 20, 250 or any live input (decision 56); a void session is never a value.
7. **Trailing (V1):** the last live non-void intraday `RV_s` before the cutoff.
8. **Rule forecasters:** `v6_ewma_t4` and `v1_close_blend` reproduce hand-computed values; missing when an input is
   missing.
9. **Records (layout agreed with G8, 15 Oct):** `research/forecasts/v4/<forecaster>/<question>.csv`, one row per day,
   first columns `day,value,status,label`: value = a variance (finite, > 0) or a probability (in [0, 1]), empty unless
   `status` is `ok` (`missing`, `not_eligible`, `not_started`: never imputed); `label` = `live` or
   `backfill_exploratory`; then G7's audit columns: forecaster version, kind (`baseline` or `rule`), slot (`rules` or
   `reported`), the method file's SHA-256, the inputs' SHA-256, `made_at`. Folder names are the ids in
   `fno/constants.py` (`base_rate`, `trailing`, `ewma_094`, `har_daily`, `har_intraday`; new constants for
   `v6_ewma_t4` and `v1_close_blend`), so G8 looks forecasters up by those constants. Invalid values are refused,
   never written.
10. **Back-fill:** V6 baselines and rule from 2017 closes, V1 from A16's live rows (none yet), every row
    `backfill_exploratory`; the back-fill ends before the first live day (one row per day); re-running gives identical
    files.
11. **Live capture:** `v4-capture` for today writes before 15:00 IST only from inputs first seen before the cutoff;
    a run after the cutoff writes nothing and says so (as G3); V1 rows read "not enough data yet" until criterion 6.

**Test plan:** `tests/forecast_v4_rules/`: hand-computed fixtures (series, EWMA, HAR, base rate, both rules), the
committed-closes reproduction of criterion 1, look-ahead tests for every baseline and rule (a later input changed
must not change an earlier forecast), the boundaries named above, empty inputs. Real data only from committed files;
no imagined failure modes (owner, 15 Oct).

**Judge verifies:** recomputes one base rate, one EWMA value, one HAR forecast and one `v6_ewma_t4` probability by hand
from the committed closes; checks that no input after the cutoff reaches a forecast.

**Gap list** (`REPLAN_new_stories.md` G7 and protocol v4 sections 1-3 for V1, V6a, V6b):

| Requirement | Covered by |
|---|---|
| Trailing baseline | criterion 7 (V1) |
| EWMA baseline | criterion 4 |
| HAR daily, later intraday | criteria 5-6 |
| Implied and implied-ratio baselines | out: phase 2 (V2/V3's primary; for V1 only "also reported") |
| Base rate (V6 primary) | criteria 2-3 |
| V1's primary switch (HAR daily, then intraday, one way) | criterion 6 |
| Rule forecasters (design 2.2, 5.7 rule 5) | criterion 8 |
| Back-fill on close proxies, labelled | criterion 10 |
| Live capture beside G3 | criterion 11 (adding it to the routine: at v4's freeze) |
| Point in time (protocol 3.1) | Expected design; look-ahead tests |
| Decision 56 (backfilled rows never live inputs) | criterion 6 |
| Session set (regular only) | criterion 1 |
| Wiring (REPLAN named `baseline_wiring.py`, frozen by v2) | `fno/forecast_v4_rules/wiring.py`, Expected design |
| V2-V5, V7 | out: phase 2 |

**Known limits:** `v6_ewma_t4`'s independence for V6b is an approximation (volatility clusters); V1 has no live data
until A16 runs; the back-fill uses spent 2017-26 data and is exploratory only (protocol 8).

**Depends:** G6 (merged, not frozen), O6 (closes), A16 (V1) · **Size:** M · **Status:** story text, awaiting the
judge (rule 1)

---

## G7b. v4 baselines and rule forecasters, phase 2 (V2, V3 and V7 now; the implied baselines, V5 and V4 later)

**Repository:** trading · **Lane:** 1 (it decides forecast and evaluation records) · **Judge:** D (judged G7 phase 1)

**Description:** As the quantitative modeller, I want the remaining v4 questions (V2, V3, V4, V5, V7) to have their
protocol baselines and one simple rule forecaster each, computed point in time and recorded like phase 1, so that G8
can score them and the V2 idea ("buy protected movement when forecast movement is above implied") has the numbers it
needs.

**Context and why:** The owner's decision of 16 Oct 2026 (`docs/DESK_DECISIONS.md`, "Books 2 and 3: D4 and D5 code
starts now; ... G7 phase 2 start now"). The decision "v4 freezes with V6a/V6b (V1 when A16 is ready); V2-V5 later in G7
phase 2 under their own record". REPLAN slice B ("G7 phase 2 (V2-V5, V7)"). Protocol v4 sections 1.2-1.5, 3.1-3.2,
5.6 and section 3 of `PROTOCOL_v4_calibration.md` (V7 descriptive only). G7 phase 1 is on main
(`fno/forecast_v4_rules/`). G10 moved v4's clock to the pack observed 14:30-14:40; its protocol text is not yet
applied on main (`PROTOCOL_v4.md:38` still says 15:00).

**Does this change a trade or stop decision?** Not directly.
- V3, V4 and V5 are reported only (`terms.REPORTED_ONLY`). V7 is descriptive only (`terms.DESCRIPTIVE_ONLY`). V2 is a
  family member, but protocol 11 D says it will almost surely never be claimed (about 8-22 years of outcomes).
- Its use is the V2 idea's inputs (R3, `docs/stories/R-factory.md:54`) and the descriptive implied-against-realised
  comparisons. That comparison is the volatility risk premium every option-selling idea rests on, measured forward
  rather than on spent history.
- Said plainly: nothing here makes a trade profitable. It gives the numbers that can show whether one is.

### What exists and what is missing (checked on main a24cfa0d)

| Need | State | Evidence |
|---|---|---|
| Closes, VIX closes, close-proxy RV | on main | `series.py`; 2,411 regular rows 2 Jan 2017-15 Oct 2026, each with a VIX close |
| Trailing, EWMA, HAR, base rate | on main, horizon-generic | `baselines.py`: `Ewma.forecast(d, h)`, `Har(rv, h, ...)`, `BaseRate(outcomes)` |
| EOD IV30 proxy (premium ratio window) | on main | `fno/forecast/iv30.py` `PanelAtmIv30`. Measured today on the panel, 1 Jan 2024-15 Oct 2026: 686 regular sessions, **647 unflagged**, 39 flagged single-expiry (15/13/11 by year). Strong evidence that the 500 minimum holds, as protocol 3.1 assumed |
| v4 pack (14:30-14:40: spot, future, chains, IV30, `observed_at`, SHA-256) | **not built** | only the day-label reader (`fno/forecast_scoring/v4/days.py`); G10's next step, A16/G8 builder (`WORK_REGISTER.md` row "G10 v4 timeline") |
| A4 at 14:30 with two monthlies | A4 records the two nearest monthlies, but at 14:55-15:10 | `fno/quotes/recorder.py:36` |
| A16 weekly ATM bid/ask | recorded only inside the raw Groww payload; no parser | `fno/intraday/groww_source.py`, `document.py` |
| V4 and V5 outcomes | nobody resolves them | `fno/forecast_scoring/v4/scoring.py:26` prints "not started"; `units.v4_outcome` and `settlement.v5_outcome` are uncalled |
| V5 outcome `first_seen_at` | no ready source | the bhavcopy manifest has no time; A8's `release_times.first_seen_times` is the nearest source |

### Scope, in four parts (each judged on its own branch; part a first)

- **Part a (closes only; proposed before the v4 freeze, see question 1):**
  - V2 and V3: the trailing, EWMA and HAR daily baselines on the close proxy, plus a rule forecaster for each.
  - V7: the base rate (its primary baseline) and a rule forecaster.
  - Back-fill and live capture as phase 1.
  - Needs no pack and no new data.
- **Part b (needs G10's pack):** V2 and V3's raw implied and premium-adjusted implied baselines (V2/V3's primary).
  - The ratio window comes from the EOD proxy, back-filled from 2024 (exploratory).
  - The daily `(day, pack IV30, EOD IV30)` series that G8's `diagnostics.proxy_drift` needs.
- **Part c (needs the pack and V5's outcome source):** V5's option-implied probability (primary, Brier); V5's outcome
  resolution in G7's rule module (G8 imports it, as `series.py`); V5's base rate.
- **Part d (needs an A16 weekly quote parser):** V4's outcome resolution and base rate. **Recommended: defer** (question
  4).

**Out:** building the pack (G10's), scoring and reports (G8), the freeze records (G6, and V2-V5's own record), adding
captures to the routine (a schedule change at go-live), the AI books' V-answers (G11). Moving records to Drive is also
out: phase 2 writes in phase 1's layout, which G8 reads; story O9 moves data files step by step and is not this story.

### Part a, exact rules (zero fitted parameters, design 5.7 rule 5)

- **V2 and V3 baselines** (protocol 3.1, `h` = `terms.HORIZON_SESSIONS`: 5 and 20; the close proxy for the whole of v4,
  protocol 1.1):
  - **Trailing:** the sum of close-proxy `RV_s` over the last `h` sessions before `d`. Phase 1's point-in-time reading
    of "ending at `d`": `d`'s own close is not known at the cutoff.
  - **EWMA:** `h x s2` at the last session before `d`.
  - **HAR daily:** `Har(rv, h, sessions)`, horizon `h`.
  - Each is missing when not strictly positive.
- **Rule forecasters:**
  - `v2_close_blend` (V2, proposed for V2's `rules` slot) and `v3_close_blend` (V3, reported): the mean of HAR daily
    and EWMA at that horizon; missing when either input is missing. This is phase 1's `v1_close_blend` with the
    question's horizon (reasoning only, the same equal-weight argument).
  - `v7_vix_vs_mean20` (V7, reported; V7's slots stay at p = 1 in v4): the two-cell rival that
    `PROTOCOL_v4_calibration.md` section 3 measured (`tools/v4_vix_null.py:50-57`), with one change for the cutoff.
    - Among the most recent 750 V7 outcomes resolved before the cutoff (at least 500, as the base rate), take the share
      of 1s on the same side as `d`. "Below" means VIX strictly below its 20-session mean (that session and the 19
      before it).
    - With fewer than 100 outcomes on that side, use the window's plain share, as the tool does.
    - **The one change, said plainly:** the tool reads each day's own close. At 14:30 `d`'s VIX close is not known, so
      `d` takes the side at `d-1`, and each past day `t` is filed under its side at `t-1`. This lagged rule was not
      itself measured. The calibration's regime finding carries over by reasoning only.
- **V7 base rate:** phase 1's `BaseRate` on V7 outcomes `VIX(t+5) > VIX(t)` (strict). The outcome rule goes into
  `series.py` beside `vix_closes`, so G8's `SeriesOutcomes` and G7 share one rule. G8 forms V7 today in
  `fno/forecast_scoring/v4/outcomes.py`, so this is agreed with its owner first (question 3).
- **Records:**
  - Phase 1's layout and `records.write` are used unchanged.
  - `records.POINT_QUESTIONS` becomes `terms.POINT_QUESTIONS` (V1-V3), so a V2 or V3 variance is validated as a
    variance.
  - The new forecaster ids go in `fno/forecast_v4_rules/constants.py`: `fno/constants.py` has 349 of its 350 lines,
    and the weather ids already moved out the same way (E4c). Phase 1's ids stay where they are.
- **Re-running the back-fill (found while building):** every row carries `method_sha256`, the hash of G7's method
  files.
  - G10's edit to `capture.py` already changed that hash. Re-running phase 1's back-fill on main a24cfa0d is
    therefore refused as a conflict (`records.write`).
  - The values themselves reproduce: all 9,636 rows, 0 differences apart from the hash.
  - So the exploratory back-fill files are regenerated whenever the method files change before the freeze. They are
    reproducible and never counted. The freeze uses the last regeneration, made with the hashed code.

### Parts b-d, rules to settle in the protocol text before the v4 freeze (questions 1-2)

The v4 freeze hashes `PROTOCOL_v4.md`, so wording questions about V2-V5's methods must be settled before 22-23 Oct
even if their code comes later:
- **Flagged IV30 on a live day:** the ratio window already drops flagged days (protocol 3.1). Proposed: on a live day
  whose pack IV30 is flagged (single expiry), raw and premium-adjusted implied are **missing** (counted, never
  filled). One estimator then runs through the window and the forecast.
  - G10 noted that an `A2` day's IV30 is usually flagged; `A2` is dropped (16 Oct), so this no longer arises.
  - Reasoning only. The alternative is to keep flagged values with a label, which mixes two estimators in one scored
    series.
- **V5 and V4 base rates:** live outcomes only. V5 needs about 2 years of daily outcomes to reach 500; V4 needs about 2
  years of A16 days. Until then the base rate is `not_eligible` (V4's is already said, protocol 3.1).
  - Proposed for V5 too: no EOD history fills it. V5's back-fill from traded closes has no bid/ask, so the 5% spread
    rule of 1.5 cannot be applied.
- **V5's outcome `first_seen_at`:** protocol 1.5 already names "the archive time of A11's first version", but no
  stored field holds that time (the bhavcopy manifest has `date,url,status,sha256,size_bytes` only; A11's revisions
  cover later versions). Proposed: that time where one is recorded, otherwise the first sighting in A8's release-check
  log (`fno/research_data/release_times.first_seen_times`). A day with neither stays unresolved (never "now").
- **A fourth wording (judge 258's note):** trailing ("ending at `d`") and EWMA ("`h x s2_d`") are read as the last
  session before `d`, as phase 1's code does: `d`'s own close is not known at the cutoff.
- **Drafted on this branch** (`PROTOCOL_v4.md` sections 1.5 and 3.1, with a test that reads the wording), for judge
  D, who judged G6; the owner signs them with the freeze. The wordings add sentences only, so G10's planned
  "15:00 -> the pack's" edits apply on top without conflict.

### Acceptance criteria for part a (each with a test; real cases: positive, negative, boundary, empty)

1. **V2 and V3 inputs:**
   - Trailing, EWMA and HAR daily at `h` = 5 and 20 reproduce hand-computed values on a fixture.
   - A forecast for `d` never reads `d`'s close (a look-ahead test: changing `d`'s close changes no forecast for `d`).
   - Each is missing when not strictly positive.
2. **V2 and V3 rule forecasters:** `v2_close_blend` and `v3_close_blend` equal the mean of their two inputs; missing
   when either is missing.
3. **V7 outcome:**
   - `VIX(t+5) > VIX(t)`: a tie is "no", one tick up is "yes". It is resolved at `t+5`'s close over regular sessions only.
   - G8's existing V7 outcomes are reproduced exactly from the shared rule; G8's tests are left unedited.
4. **V7 base rate:** the most recent 750 resolved outcomes before the cutoff; 499 missing, 500 present.
5. **`v7_vix_vs_mean20` (judge 258: the measured rival, with one stated adaptation for the cutoff):**
   - **Side, as measured:** "below" means VIX strictly below its 20-session mean, that session and the 19 before it
     (`tools/v4_vix_null.py:50-51`). Equal counts as "not below". A session with fewer than 20 sessions to average has
     no side.
   - **Window, as measured:** the most recent 750 resolved outcomes. The tool computes its rival only where the base
     rate is valid, so the rule is not eligible below 500. A cell under 100 falls back to the window's plain share
     (`MIN_CELL`, tool lines 55-57).
   - **The one adaptation:** the tool's information set is the close of `t`. The 14:30 cutoff moves it back one
     session: `d` takes its side at `d-1`, each past day `t` is filed under its side at `t-1`, and the window holds the
     outcomes resolved before `d`. Nothing else changes. The lagged rule itself was not measured, so the calibration's
     regime finding applies by reasoning only.
   - **Tests** (`tests/forecast_v4_rules/test_v4rules_phase2.py`):
     - the hand-computed cell share;
     - the 20-session boundary;
     - a flat VIX (equal is "not below");
     - a spike that leaves a cell under 100 (the plain share);
     - fewer than 500 (not eligible);
     - a look-ahead test: `d`'s own VIX moved 30% down and up changes none of `d`'s values;
     - mutations: the day's own close, a non-strict side, and no cell minimum each fail.
6. **Records:** V2 and V3 values are validated as variances (finite and > 0; 0 or negative refused); V7 values as
   probabilities in [0, 1].
7. **Back-fill:** from 2017 closes, every row `backfill_exploratory`, ending before the first live day. A re-run writes
   identical files. **Phase 1's V6 rows keep every value, status and inputs hash**, and only `method_sha256` changes.
   The regenerated files replace the old ones in the same commit. **A test checks that every committed G7 row's
   `method_sha256` equals this tree's method-file hash** (`wiring.method_sha256`; judge 258 addendum 1, the freeze
   checklist item), so a method edit without a regenerated back-fill fails the gates.
8. **Live capture:** before the 14:30 cutoff only (phase 1's `capture_day`); after it, nothing is written and the
   command says so.
9. **Size and design:** every file stays under 350 lines. No `fno/forecast_v4/` rule is re-implemented. The method hash
   covers the new files.

Parts b-d get their own criteria in their own text once their blockers clear: the pack's format, agreed with its
builder, and question 4.

### Questions for the orchestrator and the owner (recommendation first, each marked)

1. **Does part a go inside the v4 freeze of 22-23 Oct?** Recommended: yes, if judge D can pass it before then.
   - Then V2's `rules` slot has a registered forecaster from the first counted day, and phase 1's files are hashed once,
     with V2/V3/V7 included.
   - Otherwise part a goes into V2-V5's own record later, and must not touch the frozen phase 1 files (a new package
     `fno/forecast_v4_phase2/`, phase 1's code imported unchanged).
   - Reasoning only.
2. **Do the three protocol wordings above go into `PROTOCOL_v4.md` before the freeze?** Recommended: yes.
   - Otherwise they become a new protocol version later.
   - The G6 text owner writes them, or I propose them to the G6 owner.
3. **V7 outcome rule's home:** move it into `series.py` (G8 imports it), as agreed for V6. The A16/G8 builder
   (01VK88LxJvV1Gi7Wbr3D4fzp) must agree first.
4. **V4 (part d): defer.**
   - Its only baseline needs about 2 years of A16 days, and it is a reported diagnostic.
   - Recommended: build it only when G11's AI books answer V4, so their V4 rows can be scored. Reasoning only.
5. **The pack (parts b-c):** I build nothing for it. I agree its fields with the A16/G8 builder: spot, the `e` future,
   chain mids with bid and ask, IV30 with its flag, and `observed_at`.

**Known limits:**
- V2 and V3 on the close proxy carry noise; QLIKE still ranks correctly (protocol 1.1, Patton 2011).
- The measured rival behind `v7_vix_vs_mean20` was regime-dependent (calibration section 3); its lagged form was not
  measured.
- All back-fill is spent data and exploratory (protocol 8).
- Parts b-c wait on the pack. Until then V2's primary is missing every day, so no V2 comparison exists (it is counted,
  never filled).

**Depends:** G7 phase 1 (merged), G6 (merged, not frozen), G8 (V7 outcomes), G10's pack (parts b-c), A16 (part d) ·
**Size:** part a S, parts b-c M, part d S · **Status:** story text for judge D

---

## G7b completion. v4's implied baselines, V4 and V5 in full (owner, 24 Oct 2026: "close v4 full first")

**Repository:** trading · **Lane:** 1 (forecast, baseline and outcome records) · **Builder:** session
`session_017GCFK7JLcsYeFKESyXtCyf` (orchestrator's assignment, 24 Oct; the earlier R2/G7 builder is out of reach) ·
**Judge:** K (judge 578, round 1 FAIL at 485cf6053; round 2 answers below) · **Branch:** `story/g7b-completion`

**Description:** As the quantitative modeller, I want every protocol v4 baseline and every V4 and V5 rule (terms,
outcome, base rate, rule forecaster) built, so that every question in `PROTOCOL_v4.md` can be scored and G8 stops
printing "not started" for V4 and V5.

**Why:** owner, 24 Oct 2026 (`docs/DESK_DECISIONS.md`, "Close v4 in full first"): "let's close v4 full first ... I
want full implementation". The 24 Oct audit listed V2's baselines as missing. G7b part a (V2, V3 and V7 from closes) is
merged (8367029a); parts b-d were planned in the G7b text above and in response 250 and never built.

**Does this change a trade or stop decision?** Not directly. V2 is a family member; V3, V4 and V5 are reported only
(`terms.REPORTED_ONLY`). Without V2's primary baseline every V2 pair is missing, so the stop rule's Test A can never
count V2 (protocol 3.2: missing, never filled). The implied-against-realised numbers are the forward measurement of the
volatility risk premium that every option-selling idea rests on. Said plainly: nothing here makes a trade profitable;
it gives the yardstick that can show whether one is.

### What exists and what is missing (verified on main d5ee18d0, 24 Oct 2026)

| Need | State | Evidence |
|---|---|---|
| Raw implied, premium-adjusted implied (V2, V3 primary; V1 "also reported") | **missing** | ids only (`fno/constants.py:203`); no writer: `grep raw_implied fno` finds only the constant and `terms.PRIMARY_BASELINE` |
| Premium ratio window rule, proxy-drift statistic | pure functions, uncalled | `forecast_v4/eligibility.py:37` `premium_ratio_window`; `forecast_v4/diagnostics.py:26` `proxy_drift`: no caller outside `fno/forecast_v4/` |
| EOD IV30 proxy (`iv30_eod_close_proxy`) | estimator on main | `fno/forecast/iv30.py:63` `PanelAtmIv30`; G7b measured 686 regular sessions 1 Jan 2024-15 Oct 2026, 647 unflagged |
| V5 option-implied probability (primary) | **missing** | id only (`constants.py:204`) |
| V5 terms (e, K, P), outcome, base rate | **missing** | `forecast_v4/settlement.py:26` `v5_outcome` uncalled; `NseFinalSettlement` exists (`fno/desk/settlement.py:53`) |
| V4 terms (expiry, ATM IV), outcome, base rate | **missing** | `forecast_v4/units.py:34` `v4_outcome` uncalled |
| V4 and V5 forecaster rows (any forecaster) | **none** | `research/forecasts/v4/` has no `v4_*` or `v5_*` file; G11's books answer only what the `rules` slot answers (G11 criterion 1) |
| G8 scoring of V4 and V5 | hard-coded "not started" | `fno/forecast_scoring/v4/scoring.py:26` `NOT_STARTED`; `outcomes.py` resolves V1-V3, V6, V7 only |
| The pack's data model, codec, release record, `ReleasedPacks`, binding guard, `CommitmentTimes` | on main | `fno/v4_pack/model.py`, `release.py:75`, `guard.py:22`, `commitment.py:20` |
| The pack builder and the 14:30 capture that writes packs | **not on main** | G10 completion, another builder, `story/g10-completion` (not pushed when this text was written) |
| v4 freeze | not frozen | no `research/forecasts/FREEZE_v4.md`, so G7's files may still change (the back-fill is regenerated, part a rule) |

### Scope

**In** (one branch, built in this order; each step committed with its tests):
1. **Part b1, now (EOD panel and closes, no pack):** the EOD IV30 proxy series; the premium ratio and its monthly
   refit; the exploratory back-fill of raw and premium-adjusted implied for V2 and V3.
2. **Part c and d logic, now (against G10's `Pack` model on main, with fixture packs):** V4 and V5 terms, V5's
   option-implied probability, V4's and V5's outcome resolution and base rates, the two rule forecasters.
3. **Part b2, c and d live (needs G10's released packs):** the post-release capture that writes the pack-derived rows
   for each live day, and the daily proxy-drift row.
4. **Part e, G8's side (assigned here by the orchestrator, 24 Oct: G8's earlier owner is out of reach):** V4 and V5
   leave `NOT_STARTED`; G8 reads the new outcomes and Drive records; the report prints the proxy drift. Rules below.
5. **Part f, V2 and V3's intraday versions (protocol 1.1; assigned here by the orchestrator, 24 Oct):** the separate,
   reported series, from A16's first full window. Rules below.
6. **The O1 step** `forecasts_v4_pack` (its place in `DAILY_RUN_STEPS` and its `daily.live_from` key, null until the
   owner's go), reviewed by O1's builder through the orchestrator.
7. **Protocol wordings** W1-W7 below, in `PROTOCOL_v4.md` (not frozen), with a test that reads them.

**Out, with reasons:**
- Building the pack, its 14:30 capture, its release and which expiries and strikes it holds: G10's (owner rule "one
  builder per function"). This story states what it reads (interface below) and builds no second pack.
- Scoring maths, pairs, the family, looks: G8 and the frozen-to-be `fno/forecast_v4/` functions, called, never
  re-implemented.
- AI books' V4 and V5 answers: G11 (they follow the `rules` slot automatically once these rows exist).
- Ledger registration and `FREEZE_v4.md` (G6 freeze); the routine's schedule and `daily.live_from` dates (owner and
  O1's builder).
- Moving phase 1's committed CSVs to Drive: story O9, not this one.
- Setting `daily.live_from.forecasts_v4_pack` to a date: the owner's go (it stays null in this story).
- G8's look reconciliation (register row "G8 look reconciliation"): its own story; nothing here changes it.

### The rules (exact; zero fitted parameters, design 5.7 rule 5; every cutoff is the pack's 14:40, protocol 1.6)

**Shared terms.**
- Scored sessions are A7 `regular` sessions (`forecast_v4.sessions`). `d+h` is the h-th scored session after `d`.
  Calendar days are counted from A7's committed calendar; a horizon past the calendar's end gives missing ("baseline
  missing: calendar", as G4).
- Black-76 IVs use B1's `fno/research_engine/implied_vol.py`, rate 6.5%, time `C_e / 365` (protocol 1.4). A leg whose IV
  does not solve is a void day, never a guessed IV.
- A **live two-sided quote** (1.4, 1.5; judge 578 SF2) is a pack quote with bid > 0 and ask >= bid, both present,
  **and a trade in the contract on `d`**, decided by A4's own rule `traded_today` (`fno/quotes/quote_validity.py:11-19`)
  on the pack's `last_trade_time` (protocol 1.6 keeps that field for exactly this check). One rule, one place: a small
  adapter hands the pack quote to `traded_today`; the rule is never copied. Its mid is `(bid + ask) / 2`; its spread
  rule is `(ask - bid) / mid <= 0.05` (5% exactly passes). A quote without a trade on `d` voids the day
  (`no_trade_today`). Said plainly: A4's `quote_validity` also asks for bid and ask sizes, which the pack does not
  carry (G10's `ChainQuote` has none) and protocol 1.4 does not ask for, so size is not checked (W5).
- **ATM / K:** among the strikes the pack holds for that expiry, the one nearest the pack's spot; a tie goes to the
  lower strike (as G1).

**Raw implied (V2, V3; protocol 3.1).** `IV30(d)^2 x (calendar days from d to d+h) / 365`, `h` = 5 or 20,
`IV30(d)` = the released pack's `iv30.value`. A flagged pack IV30 (`iv30.flagged`) gives no raw and no
premium-adjusted value that day (missing, counted). Must be strictly positive, else missing.

**Premium ratio and premium-adjusted implied (V1, V2, V3; protocol 3.1).**
- Window points `t`: regular sessions from 1 Jan 2024 with an unflagged EOD IV30 (`PanelAtmIv30` on the A3 panel's
  first-archived chains) and a resolved, non-void outcome of the question's own measure, `RV_h(t)`. The point's
  resolution day is `t+h`. The window at a refit is `eligibility.premium_ratio_window(points, refit_day)`: resolved
  before the refit day, the most recent 750, at least 500 (else not eligible).
- Ratio: the **median** of `RV_h(t) / raw_h(t)`, with `raw_h(t) = IV30_EOD(t)^2 x (calendar days t to t+h) / 365`.
- Refit on the first scored session of each month (as HAR); every day of that month uses that refit. **The ratio is
  computed once, on the refit day, from the inputs present then, and stored write-once** (`v4/ratios/<question>/<YYYY-MM>.json`:
  the ratio, the window's first and last day, its count, and the inputs' SHA-256); every later day of the month reads
  the stored ratio and never recomputes it with files archived after the refit day (judge 578 m3). A refit day with no
  stored ratio (the capture did not run) is computed at the next run only from inputs whose receipts GitHub received
  before that refit day; none: the month's premium-adjusted rows are missing, counted.
- Value for `d`: raw implied of `d` times the refit's ratio; missing when either is missing.
- **V2 and V3** use the close proxy (protocol 1.1). **V1 and part f's intraday series: the owner's choice (W3,
  judge 578 SF4), reasoning only for both options:**
  - **Option A, own measure:** the window uses the intraday A16 `RV_s` (live, non-void rows of `V1_INTRADAY_METHOD`;
    A16b's back-filled rows never count, decision 56). Same measure on both sides of the ratio. **Cost:** the window
    holds only live days from 16 Oct 2026, so V1's and part f's premium-adjusted baseline is missing (`not_eligible`)
    for about two years (longer for V3's 20-session series).
  - **Option B, the close-proxy ratio (available now):** the V2 / V3 window's ratio, at `h` = 1 for V1, multiplies the
    pack's raw implied. **Cost:** a measure mismatch: the ratio is fitted on close-to-close `RV_s` and applied to an
    intraday-with-overnight target. Both estimate the same daily variance, and the window already mixes measures (the
    EOD IV30 stands in for the 14:30 IV30, protocol 3.1), but the 26-snapshot quote RV can differ in level from the
    close proxy; that level gap moves the baseline and so every paired difference. Each report then prints the mean
    ratio of intraday to close-proxy `RV_s` over the live days, so the gap is seen, not assumed away.
  - **Recommendation (reasoning only): B.** Both uses are "also reported" (protocol 3.2; never a member's test), so a
    labelled mismatch now costs less than two years with no value. The build implements the option the owner signs;
    until then it builds B behind one switch in the wiring and labels the rows `premium_ratio_measure=close_proxy`.
  V1's raw implied (`h` = 1, its horizon) is computed only as this input: protocol 3.2 does not report raw implied for V1.

**V5 terms, frozen from the pack of `d` (protocol 1.5).** `e` = the nearest monthly expiry strictly after `d`, read
from the pack's future (`pack.future.expiry`; on an expiry day itself, the next month's). **The pack is not trusted for
this (judge 578 m5):** `e` must be after `d` and equal the first monthly after `d` in NSE's listed expiries known before
`d` (`ListedExpiries.listed(NIFTY, d)`, the previous session's NSE file, `fno/quotes/expiry_listing.py:26`, with
`fno/research_data/expiries.monthly_expiries`); otherwise void (`future_not_monthly`; no list: `expiry_list_unavailable`).
`K` = ATM of `e`; `P` = mid of the `e` K call + mid of the `e` K put, each a live two-sided quote under the 5% rule; `F`
= the future's mid under the same rule, including `traded_today` on what the pack's future carries: its
`last_trade_time`, else its day volume (A4's rule falls back the same way); a future with neither is void
(`no_trade_today`) (W2, W5); `S_e` = the scored sessions in `(d, e]` and
`C_e` = calendar days from `d` to `e` (judge 578 m2). Any failing part makes the day void, with its reason
(`no_quote`, `no_trade_today`, `spread`, `iv_unsolved`, `no_future_quote`), counted.

**V5 option-implied probability (primary, Brier; protocol 3.1).** `s` = the mean of the K call's and K put's Black-76
IVs on `F`; `tau = C_e / 365`; `z(x) = (ln(x / F) + s^2 tau / 2) / (s sqrt(tau))`; `p = N(z(K + P)) - N(z(K - P))`.
Labelled "risk-neutral, not a real-world probability" in its record's version string. A probability outside [0, 1]
cannot arise; one that is not finite is missing.

**V5 outcome (protocol 1.5, `settlement.v5_outcome`).** Resolved only from `NseFinalSettlement` on NSE's daily F&O file
of the expiry day (`NseDailyFoSource.path_for(e)`), every expiring NIFTY row agreeing; inside when `abs(level - K) < P`
(strict: equal is outside). `first_seen_at`, in this order (judge 578 SF3): **A11's first archived version time =
Drive's `createdTime` of the raw file at `NseDailyFoSource.path_for(e)`**, read through the existing `CreationTimes`
interface (`fno/storage/creation_times.py:14-28`, `GoogleDriveCreationTimes` on the raw area, as A17b uses it; raw
files are write-once, so the created time is the first version's); where it answers None, the first sighting in A8's
release-check log (`release_times.first_seen_times`); else unresolved, never "now". A
level first seen before 15:30 IST on `e` is refused (`v5_outcome` raises; the day stays unresolved and the refusal is
printed). The resolved outcome is written once with the source path, the file's SHA-256 and `first_seen_at` (frozen
with the outcome, 1.5). A missing file keeps it unresolved; never the index-close file. Later versions (A11's
`revisions.py`, `available_from` / `found_at`) are never the source: 1.5 names the first version. No wording is needed
(W4 dropped).

**V4's expiry rule, one pure function (G10's answer, 24 Oct: A4e's `v4` window imports it).**
`first_v4_expiry(day, listed_expiries, calendar) -> date | None` in `fno/forecast_v4_rules/v4_expiry.py`: the first
listed NIFTY expiry `e > day` with at least 5 A7 `regular` sessions in `(day, e]` (special and muhurat sessions not
counted); None when no listed expiry has 5. No I/O, no Groww, no clock. It is the **first commit of the build**, so it
can merge on its own ahead of the rest (lane 1, its own judge round) and G10's capture imports it from `main`; until
then G10 builds against the same signature. One rule, one place: G7b's terms and A4e's capture call the same function.

**V4 terms, frozen from the pack of `d` (protocol 1.4).** `e` = the pack's `v4_expiry` (the expiry the capture chose
with `first_v4_expiry`, interface item 3 below); `S_e` = its scored sessions in `(d, e]`; `C_e` = calendar days from `d` to `e`. ATM
call and put of `e`, each a live two-sided quote under the 5% rule; parity forward `F = K + e^(r C_e / 365) (C_mid -
P_mid)`; each leg's Black-76 IV on `F`; the ATM IV is their mean; `sigma_IV = units.implied_vol_session_clock(IV, C_e,
S_e)`. Void with its reason otherwise. **`e` comes only from `pack.v4_expiry`** (judge 578 SF1; G10 agreed at
d4e72f20d: copied from the capture's sidecar, never recomputed at release; `first_v4_expiry` chose it from the expiries
listed at the cutoff). If `v4_expiry` is None, or the pack lacks that expiry's ATM call or put, the day is void
(`no_v4_expiry`), counted, never another expiry: a day with the monthly present and the weekly's quotes missing is void,
never read as "V4's expiry is the monthly". One check that does not trust the pack: a `v4_expiry` with fewer than 5
scored sessions in `(d, e]` on A7's calendar is void (`v4_expiry_mismatch`).

**V4 outcome (protocol 1.4, `units.v4_outcome`).** `sigma_RV` from A16's live intraday `RV_s` of `d+1..d+5`
(`V1_INTRADAY_METHOD`, non-void, never A16b's back-fill); outcome `sigma_RV < sigma_IV`. Any void session voids the
day; a missing session leaves it unresolved. **Measure (W1):** intraday, as 1.4's "any void session voids the day" and
3.1's "V4's base rate needs 500 resolved A16 days" both imply; 1.1 does not name V4's measure, so W1 writes it down.

**Base rates for V4 and V5 (protocol 3.1).** Phase 1's `BaseRate` on live outcomes only, resolved before `d`'s cutoff,
non-void; the most recent 750, at least 500. No end-of-day history fills them, so both read `not_eligible` for about two
years after their start. No back-fill rows.

**Rule forecasters (reported only; V4 and V5 are never family members, protocol 5.6).** Both read the released pack, so
both name its SHA-256.
- **`v5_ewma_lognormal` (V5):** the baseline's formula with physical instead of implied variance: `v = S_e x s2`, `s2` =
  phase 1's EWMA close-proxy per-session variance at the last session before `d`;
  `z(x) = (ln(x / F) + v / 2) / sqrt(v)`, `p = N(z(K + P)) - N(z(K - P))`. Missing when the EWMA is not eligible or the
  V5 terms are void. Reasoning only: it asks "is the straddle priced above what recent realised movement implies?".
  Said plainly: it ignores the rest of `d`'s session after 14:40 (about 50 minutes of about 6 hours 15 minutes).
- **`v4_ewma_chi2` (V4):** under the rule's model each of the 5 `RV_s` is `s2 x Z^2`, `Z` standard normal, independent,
  so `sum / s2` is chi-square with 5 degrees of freedom. Threshold `T = sigma_IV^2 x 5 / 252` (the window's integrated
  implied variance); `p = F_chi2(5)(T / s2)`, closed form `erf(sqrt(x/2)) - sqrt(2x/pi) e^(-x/2) (1 + x/3)`. Said
  plainly (reasoning only): `s2` is a close-proxy variance while the outcome is intraday; chi-square with 5 degrees
  overstates the spread of a sum of 26-interval sessions, so `p` is pulled toward the middle. Not tuned, so nothing is
  fitted on spent data.

**Records and storage.**
- **Day label on every new row (protocol 1.6; judge 578 m4):** a `day_label` field, copied from today's release
  record (`ReleasedPacks.release(d).label`) by the post-release capture: always `A`, because that capture writes
  nothing on a `system_late` day; back-fill rows carry `backfill_exploratory` in `label` and an empty `day_label`
  (no pack existed).
- Every new row uses phase 1's record fields (`day,value,status,label`, version, kind, slot, method SHA-256, inputs
  SHA-256, `pack_sha256`, `made_at`; `records.validate` rules: a V1-V3 value is a variance > 0, a V4 or V5 value a
  probability in [0, 1]).
- **Storage follows CLAUDE.md and O9 (every data file write-once in Drive, GitHub keeps receipts; register row G7b:
  "values in Drive only"):** pack-derived values come from Groww quotes and never enter the repository. Live rows:
  `v4/records/live/<forecaster>/<question>/<YYYY>/<date>.json`; V4 and V5 terms: `v4/terms/<question>/<YYYY>/<date>.json`;
  resolved V5 outcomes: `v4/outcomes/v5/<YYYY>/<date>.json`; proxy drift: `v4/diagnostics/proxy_drift/<YYYY>/<date>.json`;
  all through O9's `DataStore.put`, read through `DriveCache` (verified SHA). Part b1's back-fill (NSE public data
  only) also goes to Drive, one file per method hash, `v4/records/backfill/<method12>/<forecaster>/<question>.csv`, so a
  regeneration after a method change is a new write-once file and the reader takes the file of this tree's hash.
- A live row is written once: a rerun with the same bytes is a no-op; different bytes are refused and printed.

**The post-release capture** (`python -m fno forecast-v4 capture-pack`, a new subcommand in G7's CLI):
- Reads today's release record through `ReleasedPacks`. `system_late` (or no record): writes nothing and says so (the
  day is excluded for everyone, protocol 4).
- Otherwise writes, for `d`: raw implied (V2, V3), premium-adjusted (V1, V2, V3), V5 terms and option-implied
  probability, V4 terms, both rule forecasters, V4's and V5's base rates; then resolves pending V5 outcomes and pending
  proxy-drift rows whose inputs now exist.
- Pack-reading rows carry the released `pack_sha256` and pass `v4_pack.guard.check_pack_binding`; base rates read no
  pack and carry it empty.
- Writes nothing from 15:10:00 IST (`terms.V4_DEADLINE`) on this host's clock and says so; whether a row counts is still
  decided by GitHub's receipt time of its receipt (`CommitmentTimes`, G10), not by this check.

### What depends on G10's pack, and what runs now

| Piece | Needs the pack? | Runs from |
|---|---|---|
| EOD IV30 proxy series, premium ratio and refits | no | A3 panel (Drive), closes |
| Back-fill raw and premium-adjusted for V2, V3 (exploratory, the close-proxy cohort) | no | EOD IV30 of `d` stands in for the pack, protocol 1.6 |
| V1's premium-adjusted ratio window | no pack for the window; live A16 rows | `not_eligible` until 500 live points |
| V4 and V5 rule maths, chi-square, lognormal, terms selection | logic no (fixture packs on G10's `Pack` model) | tests |
| V5 outcome resolver | no | historical expiry-day F&O files (Drive), real cases |
| V4 outcome resolver | V4 terms (pack) + A16 rows | A16 live rows exist from 16 Oct |
| Live raw and premium-adjusted, V5 option-implied, V4/V5 terms and rules, proxy drift | **yes** | released packs from G10's capture |

**The pack's interface, as G10 answered (story/g10-completion c876ede53, "The pack's interface for G7b and G11",
criterion 3a; relayed by the orchestrator, 24 Oct):**
1. **Expiries:** the two monthlies as today, plus the first listed expiry with at least 5 scored sessions when it is not
   a monthly (from `first_v4_expiry`, imported); nearer weeklies are skipped (V4 uses only that expiry). Accepted: it
   is all V4 reads, and it saves Groww load.
2. **Strikes:** A4's 5% band around spot (`fno/quotes/recorder.py` `SPOT_BAND`) for every recorded expiry. Accepted:
   it covers ATM and the strikes either side. G7b never chooses V4's expiry from what the pack holds (item 3).
   Each chain quote keeps `last_trade_time` for the traded-today rule (W5).
3. **`v4_expiry` (agreed, G10 d4e72f20d):** the pack names the expiry the capture chose with `first_v4_expiry` from
   the expiries listed at the cutoff (None when it returned None), copied from the capture's sidecar, never recomputed.
   G7b reads V4's `e` only from it.
4. **The future:** one Groww quote of `e`'s future with bid, ask and `observed_at` (G10's new `FutureQuotes`
   interface). A failed future quote leaves bid and ask empty and V5 voids itself (`no_future_quote`); the pack is not
   `system_late`. Accepted. For the traded-today rule (W5) the future also needs its `last_trade_time` or its day
   volume in the pack: G10's cherry-picked commit 7cab92b06 brings the future's traded volume; `FutureQuote` on
   G10's tip (d4e72f20d) does not show it yet, so this is confirmed with G10 through the orchestrator.
5. `iv30.flagged` as on main; `ReleasedPacks`, `ReleaseRecord.pack_sha256`, `Pack` and `check_pack_binding` keep their
   names (G10's answer to G11).
6. **Day labels:** the release record in Drive `v4/days/<YYYY>/<date>.json`, read only through
   `ReleasedPacks.release(day)`; `research/data/v4_days/` is retired by G10. The post-release capture and part e read
   labels only that way.

**The O1 step (reviewed by O1's builder, session_016CU8KFuEEtWAM7ZNnFcKxv, through the orchestrator):**
- `fno/constants_operations.py`: a new step `forecasts_v4_pack` in `DAILY_RUN_STEPS`, in the order G10's text fixes:
  `forecasts_v4`, `v4_release`, **`forecasts_v4_pack`**, `versions` (so before `card`, and the card can say whether it
  ran). G10 adds `v4_release`; G7b adds only its own step. Its value is the subcommand above, run as a child
  process like the other steps; it commits only its own receipt paths (`receipts/data/v4/records/`,
  `receipts/data/v4/terms/`, `receipts/data/v4/outcomes/`, `receipts/data/v4/diagnostics/`).
- `config.yaml`: `daily.live_from.forecasts_v4_pack: null` (`not_live` until the owner sets a date; `fno/config.py`'s
  allowed keys gain it).
- A `system_late` day: the step is `ok` with "no pack today, nothing written". A run that reaches it at or after
  15:10:00: `refused`, one alert, as the other v4 captures (O1's existing handling).
- Tests: the step's place in the order (after the release step, before `card`), `not_live` while the key is null, and
  the committed paths. Said plainly: this edits O1's files (lane 1, outside services' schedule), so O1's builder
  reviews that part before the judge.

### Part e: G8's side (rules)

- `fno/forecast_scoring/v4/scoring.py`: `NOT_STARTED` is removed. A question with no forecaster rows still prints "not
  enough data yet" (protocol 1.3), never a failure.
- `outcomes.py`: `OutcomeSeries` gains `v4_outcomes()` and `v5_outcomes()`, filled by G7b's resolvers (one rule, one
  place, as V6 and V7). A V4 or V5 day with void terms is `Outcome(void=True)`; an unresolved day has no entry. V5's
  outcome is read only from its written outcome record, never computed from a close. The regime inputs
  (`_first_session`) stay as they are.
- `inputs.py`: a second `V4ForecastSource`, `DriveForecastRecords`, reads the new live and back-fill records through
  `DriveCache`; a composite gives G8 one source. Two rows for one forecaster, question and day (CSV and Drive, or two
  Drive files) stop the report and name them; never a silent pick.
- The report (`render.py`) prints, after the question blocks, the proxy-drift line from `diagnostics.proxy_drift`: the
  paired pack / EOD IV30 ratio's median over all live days and the latest 20, and their drift, labelled "descriptive
  only; the EOD proxy is not claimed equal to the pack's IV30" (protocol 3.1). V4's block carries "probabilistic
  diagnostic, not a variance-risk-premium estimate" and V5's "terminal intrinsic-payoff proxy, not evidence of money"
  (protocol 1.4, 1.5). The report's JSON only gains keys, so LR1's reader (`forecast_section.py`) keeps working; a test
  reads one old report through it.
- Day labels (`A`, `system_late`) come only from G10's reader of the Drive release records (`ReleasedPacks.release`);
  part e never reads `research/data/v4_days/` (retired by G10).
- Wiring in `fno/forecast_scoring/v4/wiring.py` only.

### Part f: V2 and V3's intraday versions (protocol 1.1, reported only)

- **Outcome:** the sum of A16's live intraday `RV_s` (method `V1_INTRADAY_METHOD`, never A16b's back-fill) over
  `d+1..d+h`, h = 5 or 20. Any void session voids the day; a missing session leaves it unresolved. The rule sits in
  G7's `series.py` beside the close-proxy one.
- **First full window:** the series starts at the first forecast day `d` whose `d+1..d+h` are all live A16 sessions.
  16 Oct 2026 was A16's first live session, so by that rule the first `d` is **15 Oct 2026** (`d+1` = 16 Oct; judge 578
  m1). 16 Oct's A16 row is void (A16f fixed it after its first day), so every window holding it is void and counted.
- **Cohorts:** the live and the back-fill cohorts stay apart in part f too (G10); the back-fill rows end before the
  first live day, so part f in practice scores live rows, and any back-fill row it meets is reported apart, never
  pooled.
- **Forecasts scored:** the same V2 and V3 forecaster rows (no new forecaster, no new record); each is scored against
  this outcome as its own series, `v2_rv_next_5_sessions/intraday` and `v3_rv_next_20_sessions/intraday` in the
  report, never pooled with the close-proxy series and never in the family, Test A or a look.
- **Its primary baseline:** premium-adjusted implied, its ratio as the owner chooses in W3: under option B available
  now; under option A `not_eligible` until 500 window points (about two years for V2, longer for V3), the pair missing
  and counted, and the report printing each forecaster's QLIKE only.
- Reasoning only, said plainly: QLIKE ranks correctly under either proxy (protocol 1.1, Patton 2011); this series
  exists to show whether the close proxy's noise hides a difference, not to judge anyone.

### Protocol wordings to add before the freeze (W1-W7; the owner signs them with the freeze)

- **W1 (1.4):** V4's realised side is A16's intraday `RV_s` (method `V1_INTRADAY_METHOD`), live rows only.
- **W2 (1.5, 3.1):** V5's `F` is the pack's future at mid, a live two-sided quote under the 5% spread rule; else void.
  V5's leg IVs use Black-76 on that `F` at 6.5%.
- **W3 (3.1), a choice:** V1's and part f's premium ratio is either (A) fitted on their own intraday measure (no value
  for about two years) or (B) the close-proxy ratio (available now, with a measured measure gap printed). Recommended
  B, reasoning only. V2 and V3 use the close proxy either way.
- **W4: dropped** (judge 578 SF3). Protocol 1.5's "archive time of A11's first version" exists: Drive's `createdTime`
  through `CreationTimes`. No wording needed.
- **W5 (1.4, 1.5):** "a live two-sided quote" is bid > 0 and ask >= bid, both in the pack, and a trade in the contract
  that day by A4's `traded_today` rule on the pack's `last_trade_time`; sizes are not checked (the pack has none).
- **W6 (1.3, 3.1):** V4 starts when the pack holds an expiry with at least 5 scored sessions and A16 records `RV_s`
  (1.3 still says "when A16 records weekly ATM quotes", written before the pack); the V4 and V5 rule forecasters read
  the released pack and name its SHA-256.
- **W7 (1.1):** V2 and V3's intraday versions sum A16's live intraday `RV_s` over the horizon; any void session voids
  the day; they start at the first forecast day whose whole horizon is live A16 sessions; scored as separate reported
  series with their own premium-adjusted baseline (W3), never pooled, never family members.

**For the owner to sign, in plain words (one place):**

| # | What it says | Why it is needed |
|---|---|---|
| W1 | V4 measures realised movement from the 15-minute intraday quotes (A16), not from daily closes | the protocol implies it but never says it |
| W2 | V5 uses the future's mid price (halfway between bid and ask) as its forward, and drops the day if that quote's spread is over 5% | the protocol says "the future" without saying which price |
| W3 | **Your choice.** For V1 and the intraday V2/V3 series, the "premium-adjusted" yardstick (implied movement scaled by how much realised movement has run below it) is either (A) scaled on the same intraday measure: no value for about two years; or (B) scaled on daily closes: a value now, with a small known mismatch shown on every report. Recommended: B (reasoning only); both are side reports, never the main test | the protocol does not say which, and the two cost different things |
| W4 | Dropped: the "first seen" time of the expiry-day file is Drive's own creation time, which the protocol already means | nothing to sign |
| W5 | A "live" option quote needs a bid, an ask (ask not below bid) and a trade in that contract the same day, the rule the 3 pm quotes already use; order sizes are not checked because the pack does not hold them | the protocol does not define "live"; without the trade check a stale quote could pass |
| W6 | V4 starts when the pack holds a suitable expiry and A16 records movement (old text named A16's weekly quotes); V4's and V5's rule forecasts read the pack and name its fingerprint | the old start line predates the pack |
| W7 | V2's and V3's intraday versions: how they are summed, voided, started and reported | the protocol names the series but not its rules |

### Acceptance criteria (each with its test in `tests/forecast_v4_rules/`, good, bad, boundary and empty cases, and the planted break that must fail it)

| # | Criterion | Cases | Planted break |
|---|---|---|---|
| 1 | EOD IV30 proxy series: one value and flag per regular session from 1 Jan 2024; flagged days kept with their flag, dropped by every window | fixture panel; a single-expiry day; empty panel gives no points; on the real panel the 686/647 counts of G7b are reproduced (claims) | flagged days not dropped |
| 2 | Raw implied = `IV30^2 x calendar days / 365` over `d..d+h` | hand values at h 5 and 20 across a holiday; flagged gives missing; horizon past the calendar gives missing; 0 IV gives missing | sessions instead of calendar days; `d+h` one session off |
| 3 | Premium ratio: median over `premium_ratio_window`, computed once on the month's first scored session and stored write-once; later days read the stored ratio | 499 points not eligible, 500 present; a point resolving on the refit day excluded, the day before included; `t` on 31 Dec 2023 excluded; a file archived after the refit day changes no stored ratio | mean instead of median; `<=` refit day; recomputed each day |
| 4 | Premium-adjusted = raw x ratio; V1 and part f with the ratio W3 chooses (switch in the wiring, labelled on each row) | either input missing gives missing; option A: A16b back-filled rows never enter the window, 499 live points `not_eligible`; option B: the close-proxy ratio at `h` = 1, the row labelled `close_proxy`, the intraday / close-proxy level line printed | option A counting back-filled rows; option B rows without the label |
| 5 | Back-fill (b1) for V2, V3: every row `backfill_exploratory`, ends before the first live day, re-run byte-identical, stored per method hash, reader refuses a missing hash file | re-run; changed method file gives a new path, never an overwrite | writing over an existing back-fill file |
| 6 | V5 terms: `e` checked against NSE's listed monthlies known before `d`, K (tie lower), P, F, `S_e`, `C_e`; a live quote needs a trade on `d` (A4's `traded_today`, imported) | spread exactly 5% passes, 5.01% void; a one-sided leg void; a leg whose last trade is the day before: void `no_trade_today`; `d` an expiry day takes next month; a pack future on a weekly or on `d`: void `future_not_monthly`; no listed-expiry file: void `expiry_list_unavailable`; no future quote void | tie to the upper strike; `<` for the spread; `traded_today` copied or skipped; `e` trusted from the pack |
| 7 | V5 option-implied probability equals a hand-computed golden value (30-digit decimals, fixture JSON) | IV unsolved gives missing; deep wide P near 1; tiny P near 0 | drift term dropped; `tau` in sessions |
| 8 | V5 outcome from the expiry-day file only, strict inside, `first_seen_at` = `CreationTimes.created_at(NseDailyFoSource.path_for(e))`, else A8's log, refusals, written once with path, SHA and time | level equal to `K + P` outside; first seen 15:29:59 refused, 15:30:00 accepted; created time None and an A8 sighting: A8's time; neither: unresolved; a later revision's time never used; a later day's close never used; one real past expiry's file resolves (claims) | `<=` for inside; "now" as fallback time; another expiry's file |
| 9 | V4 terms: `e` only from `pack.v4_expiry`, parity forward, mean IV, session clock; `v4_golden.json` reproduced (13.656% vs 13.567%: no; 9 calendar days: yes) | `v4_expiry` None: void `no_v4_expiry`; **the monthly present and the weekly `v4_expiry` without ATM legs: void `no_v4_expiry`, never the monthly**; a `v4_expiry` with 4 scored sessions: void `v4_expiry_mismatch`; spread, no-trade-today and quote voids | the first expiry in the pack with 5 sessions used instead of `v4_expiry`; raw IV compared without the clock change |
| 10 | V4 outcome on live A16 `RV_s` of `d+1..d+5` | one void session voids; a missing fifth session unresolved; back-filled rows ignored | back-filled rows used; a void session skipped |
| 11 | V4 and V5 base rates on live outcomes only, resolved before the cutoff | 499 not eligible, 500 present; an outcome resolved after the cutoff excluded; no back-fill rows exist | an outcome resolved on `d` counted |
| 12 | `v5_ewma_lognormal` and `v4_ewma_chi2` equal hand values; chi-square(5) closed form equals known table values (e.g. `F(11.0705) = 0.95`) to 1e-6 | EWMA not eligible gives missing; void terms give missing | `v = s2` without `S_e`; chi-square with 4 degrees |
| 13 | Post-release capture: nothing on `system_late`; every pack-reading row names the released SHA (guard); base rates empty SHA; nothing from 15:10:00; write-once (same bytes no-op, other bytes refused); every row carries `day_label` `A` from the release record (back-fill rows empty) | 15:09:59 writes, 15:10:00 refuses; another pack's SHA refused; no release record writes nothing | a pack row with an empty SHA; overwrite allowed; `day_label` missing or not from the release record |
| 14 | Proxy drift: one `(day, pack IV30, EOD IV30)` row per live day once `d`'s EOD chain is archived; a flagged side is empty; G8's `proxy_drift` reads the rows | EOD not archived yet: pending, written on a later run; both flagged | EOD of `d+1` used for `d` |
| 15 | Part e: V4 and V5 leave `NOT_STARTED` (no rows: "not enough data yet"); G8's V4 and V5 outcomes come from these resolvers; G8 reads the Drive records beside the CSVs; the report prints the proxy drift and the V4 and V5 labels; LR1's reader reads the new report. **Sections 4 and 5 for V4, V5 and part f (judge 578 SF5):** Brier primary (unclipped); log score clipped to [0.01, 0.99], the 10-bin reliability table, calibration slope and intercept and the Brier skill score against the base rate, reported; block L 10 for V4, 20 for V5, 10 and 20 for part f's V2 and V3 series (`terms.BLOCK_LENGTH`); comparisons numbered after 15 (`seed_word`; part f's series key `<question>/intraday` gives a number apart from the close-proxy comparison's); never family members, never in Test A or a look; a `system_late` day out for every forecaster and counted; a live row whose receipt GitHub received after 15:10:00 is a miss (G10's deadline verdict, applied as for every other v4 row) | a V4 day with void terms is void, not missing; two rows for one day stop the report and name them; an old report still reads; V4 with a base rate present on 3 days: Brier skill on those 3 only; a V5 probability of 0.999: Brier unclipped, log score on 0.99; V4's comparison uses blocks of 10 (a fixture where 5 would give a different bootstrap); part f's and V2's close-proxy comparison carry different seed words; a V4 or V5 forecaster in the slot file is refused as a member; a `system_late` day counted apart; a row received at 15:10:00 counts, 15:10:01 is a miss; G8's other tests unedited. Said plainly: the test that expects "not started" for V4 and V5 changes, a lane-1 test edit, shown in the claims | V5 scored on the index close; a duplicate day silently picked; V4 on block 5; part f pooled with the close-proxy series; a late row scored |
| 16 | W1-W7 in `PROTOCOL_v4.md`, read by a text test | each wording present once | a wording removed |
| 17 | Part f: the intraday V2 and V3 outcome (sum of live A16 `RV_s`; void and unresolved rules; first full window), scored as separate series, never pooled, never in the family | one void session voids; the 4th of 5 sessions missing is unresolved; A16b's rows ignored; no live window yet prints "not enough data yet"; the close-proxy series' scores unchanged | pooling the two series; a void session skipped |
| 18 | The O1 step: `forecasts_v4_pack` directly after the release step and before `card`, `not_live` while its key is null, commits only its receipt paths, refused from 15:10:00 | key null: `not_live`; a date: runs; `system_late`: ok with nothing written | step placed before the release; another path committed |
| 19 | Design and size: no file or class over 350 lines; no `fno/forecast_v4/` rule re-implemented (imports checked); every outside source behind an interface (pack source, settlement prices, first-seen times, record store), wired in `fno/forecast_v4_rules/wiring.py`; the method hash covers the new files and the hash gate covers the back-fill's path | `tests/test_code_size.py`; the gate fails on a stale back-fill | a new method file left out of the hash |
| 20 | `first_v4_expiry`: the first listed expiry with at least 5 regular sessions in `(d, e]`; V4 terms use the pack's `v4_expiry` and refuse a mismatch | a Monday with Tuesday's weekly (1 session) takes the next weekly (6); exactly 5 taken, 4 not; a muhurat or special session not counted; no such expiry: None; pack without `v4_expiry` or without its rows: void `no_v4_expiry`; a pack naming a 4-session expiry: void `v4_expiry_mismatch` | `>= 5` to `> 5`; special sessions counted; first expiry in the pack used instead of `v4_expiry` |

**Real output sample (claims):** one back-filled V2 premium-adjusted row and one V5 outcome from a past expiry's public
file, made by the committed code; a live-shaped sample only from a fixture pack (no Groww value, no live strike, record
scan clean).

**Builder self-review:** independent code-review agents on the diff before the judge; the Claims section lists what
they found and what was fixed or why not.

### Gap list (protocol v4 sections 1.4, 1.5, 3.1 and 3.2; every requirement named)

| Requirement | Covered by |
|---|---|
| 3.1 Trailing, EWMA, HAR daily (V1-V3) | on main (G7, G7b part a) |
| 3.1 HAR intraday (V1) | on main (G7) |
| 3.1 Raw implied (V2, V3 also reported) | criterion 2, live capture 13 |
| 3.1 Flagged IV30 gives no implied value | criteria 1, 2 |
| 3.1 Premium-adjusted implied, ratio window, EOD proxy from 2024, monthly refit | criteria 1, 3, 4 |
| 3.1 Forward diagnostic (pack / EOD IV30 drift) | criterion 14 (series), 15 (report) |
| 3.1 Option-implied probability (V5), risk-neutral label | criteria 6, 7 |
| 3.1 Base rate, every probability question; V4 and V5 live only | criterion 11 (V4, V5); on main for V6, V7 |
| 3.1 Not strictly positive or not computable gives missing | criteria 2, 4, 7, 12 |
| 3.2 Primary per question: V2, V3 premium-adjusted; V4 base rate; V5 option-implied | criteria 4, 11, 7; G8's `primary_values` picks them by `terms.PRIMARY_BASELINE` (15) |
| 3.2 V1 also reported: premium-adjusted | criterion 4 (`not_eligible` about two years, W3) |
| 3.2 V2, V3 also reported: raw implied, HAR, trailing, EWMA | criterion 2; the rest on main |
| 3.2 V5 also reported: base rate | criterion 11 |
| 3.2 Primary not eligible gives a missing pair | G8 on main (`primary.py`), unchanged |
| 1.4 Expiry with at least 5 scored sessions, `S_e`, `C_e` | criteria 9, 20 (`first_v4_expiry`, shared with A4e's capture) |
| 1.4 ATM, tie lower, two-sided quotes, 5% spread, mid | criteria 6, 9 (W5) |
| 1.4 Black-76 IV at 6.5% on the parity forward, mean of legs | criterion 9 |
| 1.4 Units on one session clock, golden example | criterion 9 |
| 1.4 Outcome `sigma_RV < sigma_IV`, any void session voids | criterion 10 (W1) |
| 1.4 V4 diagnostic, not a VRP estimate | label in the record version; G8's report wording (15) |
| 1.5 `e`, K, P frozen from the pack, 5% rule | criterion 6 |
| 1.5 Strict inside on the expiry's final settlement, every row agreeing | criterion 8 |
| 1.5 Source path, SHA-256, `first_seen_at` order (Drive `createdTime`, then A8's log), before-15:30 refusal, missing file unresolved | criterion 8 |
| 1.5 `e` the nearest monthly strictly after `d` (not trusted from the pack) | criterion 6 |
| 1.6 Day label on every v4 record | `day_label` (Records and storage), criterion 13 |
| 1.6 `last_trade_time` only for the traded-today check | criteria 6, 9 (W5) |
| 4 Probability questions (V4, V5): Brier primary, log score, reliability, calibration, skill score vs base rate | criterion 15 |
| 4 Point series (part f): QLIKE primary, squared error, Mincer-Zarnowitz; scored set and gate set | criterion 15 (G8's existing point scoring, called) |
| 4 `system_late` out for every member; a commitment after 15:10:00 a miss | criteria 13, 15 (G10's deadline verdict) |
| 4 Misses for reported forecasters (V4, V5 rules) | criterion 15 (G9's counting, unchanged; not a member, so no "undecided, operations" verdict) |
| 5 Block L: V4 10, V5 20, part f 10 and 20 | criterion 15 (`terms.BLOCK_LENGTH`) |
| 5.2 Reported comparisons numbered after 15 | criterion 15 (`seed_word`, part f's own series key) |
| 5.6 V3, V4, V5 (and part f) never members | criterion 15 |
| 5.3-5.5 Claim, futility and minimum effect for V4, V5 and part f | not applied: reported only (5.6); G8 prints the same numbers, never a verdict |
| 1.5 V5 not evidence of money | G8's report wording (15) |
| 1.3 Starts (V4 from the pack and A16; V5 from the freeze) | W6; criterion 13 writes from `daily.live_from` |
| 1.1 V2, V3 intraday versions (separate reported series) | part f, criterion 17 (W7) |
| G8 scores V4 and V5; the report's diagnostics and labels | part e, criterion 15 |
| The capture runs daily after the release | the O1 step, criterion 18 |
| Rule forecasters for V4 and V5 (so G11's books answer them) | criterion 12 |
| Point in time and the pack binding | criteria 3, 11, 13, 14 |

### Decisions so far and what is still open

- **Decided by the orchestrator, 24 Oct:** part e and part f are in this story; the G10 interface asks went to the
  G10 completion builder (session_011hvvn9CahAD5dCPHS3kowN), its answer comes back through the orchestrator; the O1
  step is written here and O1's builder reviews it; W1-W7 go to the owner at the freeze.
- **Storage:** Drive for every new row (CLAUDE.md, O9, register row G7b). Phase 1's repo CSVs would put Groww-derived
  values in the repository: refused.
- **G10's answers received (c876ede53, d4e72f20d):** items 1-6 above agreed; the step order is G10's. G10 also
  re-points G8's day-label readers (`build_scoring`, `build_ai_slot_days`, `build_day_counts` in
  `fno/forecast_scoring/v4/wiring.py`) to the Drive release records; part e depends on that change and never
  re-implements it.
- **Open (asked of G10 through the orchestrator):** that its `v4_deadline` verdict also covers this story's receipt
  path `receipts/data/v4/records/live/` (section 4's 15:10 rule, part e below). **Merge order:** `first_v4_expiry` merges first (G10's capture imports it); the rest of this
  story after G10's pack and release are on `main`.

### Round 2: answers to judge 578, by number

| Finding | Accepted? | What changed (section) |
|---|---|---|
| SF1 V4's expiry could be a farther one | yes: my "among the expiries the pack holds" could take the monthly when the weekly failed | `e` only from `pack.v4_expiry` (G10 d4e72f20d); void `no_v4_expiry` when its ATM legs are missing; criterion 9 gains "monthly present, weekly missing: void"; interface items 2-3 fixed |
| SF2 W5 dropped the traded-today rule | yes: `quote_validity.py:11-38` checked; Groww gives no quote time, so the trade today is the only freshness evidence | live quote needs A4's `traded_today` on `last_trade_time` (imported, never copied); sizes not checked, said plainly (the pack has none); criteria 6 and 9; W5 and the owner row rewritten |
| SF3 A11's archive time exists | yes: `creation_times.py:14-28` read; raw files are write-once, so `createdTime` is the first version's | `CreationTimes` at `NseDailyFoSource.path_for(e)`, then A8's log; criterion 8 tests it; W4 dropped, owner row says so |
| SF4 W3 presented as forced | yes: 1.1 forbids pooling scored series, not mixing inputs; the window already mixes measures | W3 is a choice, A (own measure, about two years missing) or B (close-proxy ratio now, gap printed); recommended B, reasoning only; criterion 4 covers both |
| SF5 sections 4 and 5 missing | yes | gap list rows for sections 4 and 5; criterion 15 cases (Brier, log score, reliability, skill, blocks 10/20, numbering, never members, `system_late`, 15:10 miss) |
| m1 15 Oct, cohorts | yes | part f: first `d` is 15 Oct, windows holding void 16 Oct are void; cohorts apart |
| m2 `S_e` for V5 | yes | defined in V5 terms |
| m3 ratio computed once | yes | stored write-once on the refit day; criterion 3 |
| m4 day label | yes | `day_label` copied from the release record; criterion 13 |
| m5 future's expiry trusted | yes | checked against NSE's listed monthlies known before `d`; criterion 6 |

### Claims, build step 1: `first_v4_expiry` (criterion 20), to merge alone ahead of the rest

- **Code:** `fno/forecast_v4_rules/v4_expiry.py` (`first_v4_expiry(day, listed_expiries, calendar) -> date | None`, the
  signature G10's text d4e72f20d imports; `scored_sessions_until(day, expiry, calendar)` for `S_e`). The minimum 5 is
  `terms.HORIZON_SESSIONS[V4]`, not a new literal. Pure: no I/O, no clock. A day the calendar does not cover raises
  `CalendarError` (the day is looked up first, so it raises even with nothing listed after it).
- **Tests:** `tests/forecast_v4_rules/test_v4rules_v4_expiry.py`, 12 tests on the committed NSE calendar: good (Mon 26
  Oct 2026 skips Tue 27 Oct's 1-session weekly for 3 Nov's 6), boundary (5 sessions taken, 4 not), the 8 Nov 2026
  muhurat and the 20 Jan 2024 special Saturday never counted, the window `(day, expiry]` with a holiday expiry and a
  Sunday day, order and repeats, bad (none with 5: None), empty (None), outside the calendar (raises, both ends).
- **Plants (each run against the test file):** `>=` to `>`: caught; `is_session` instead of regular only: caught;
  `[day, e)` instead of `(day, e]`: caught (after a test was added for it); no sorting: caught; a farther expiry as a
  fallback: caught; the first-day lookup removed: caught. **Survivor, equivalent:** `e > day` to `e >= day` (the day's
  own and past expiries hold 0 sessions, so they can never qualify; the filter is kept for clarity, the test says so).
- **Self-review (an independent review agent on the two files):** 1 should-fix, fixed: a day outside the calendar with
  nothing listed after it returned None instead of raising (now looked up first; two tests). 2 minors fixed: a comment's
  wording, and 24 Nov 2026 (a holiday) replaced by 23 Nov in the test listing. 1 noted: the filter test above.
  **Operations note (with a date):** the calendar has no 2027 rows. From Tue 22 Dec 2026 the 29 Dec weekly holds 4
  sessions (25 Dec holiday), so the next candidate is in January 2027 and the function raises every day until NSE's
  2027 holiday rows are in `research/data/calendar/nse_sessions.csv` (needed by about 21 Dec 2026; reported to the
  orchestrator).
- **Real output sample** (committed code, committed calendar; the listing is the test's, Tuesday weeklies):
  `2026-10-26 -> 2026-11-03 (6 sessions)`, `2026-10-27 -> 2026-11-03 (5)`, `2026-10-28 -> 2026-11-09 (8)`,
  `2026-11-03 -> 2026-11-17 (9)`.
- **Not in the method hash yet:** no G7 record uses it, so `wiring.METHOD_FILES` is unchanged (no back-fill
  regeneration now); it joins the hash in the step that builds V4's terms.
- **Gates:** see the commit message.

**Known limits:** V2's r is unmeasured (protocol 11 D) and the back-fill (b1) gives its first exploratory measure;
V4's and V5's base rates need about two years of live outcomes, so those comparisons do not exist until then; the
premium ratio is fitted on the EOD proxy and applied to the 14:30 pack's IV30 (the mismatch is the drift criterion 14
reports); `v4_ewma_chi2` mixes a close-proxy variance with an intraday outcome; all back-fill is spent data and
exploratory (protocol 8).

**Depends:** G7 and G7b part a (merged); G10's pack builder and release (live parts only); A16 (V4, V1's ratio); O9's
`DataStore` (merged); E7's `NseFinalSettlement` (merged); O1 (the step) · **Size:** L · **Status:** story text for the judge (rule 1);
no code before its PASS

---

## G8. Protocol v4 scoring, comparisons and the two looks

**Repository:** trading

**Description:** As the statistician, I want every v4 forecast scored against its outcome and its primary baseline
exactly as protocol v4 says, with the two confirmatory looks run by the frozen rules, so that the stop-rule review
reads a verdict nobody tuned, and every verdict states the market regime it was measured in.

**Context and why:** REPLAN slice A item 9; `REPLAN_new_stories.md` (G8); `research/forecasts/PROTOCOL_v4.md`
sections 4-7 and `PROTOCOL_v4_calibration.md`; G6 merged at 597487f (not frozen). The owner's G6 item E decision
(15 Oct 2026, `docs/DESK_DECISIONS.md`): option 2, windows with more than 10% 2% days give no verdict. Owner's rule
"Keep the design simple" (15 Oct 2026): real cases only. **Does this change a trade or stop decision?** Yes: Test A of
the stop rule (protocol section 6) reads G8's look. Everything else G8 prints is descriptive.

**Scope.** In: outcome resolution for V1, V2, V3, V6a, V6b and V7; per-forecaster scores; each comparison with its
primary baseline (scored set, gate set, effect, reported sensitivities, regime, power report); the look command (the
family decision and Test A); the report files. Out: producing forecasts and baselines (G7, M1, the books); V4 and V5
outcomes (they need A16's weekly ATM quotes and the expiry settlement wiring: printed "not started" until a story
adds them; the protocol already says they start later); the freeze record (after the judge's freeze check); the
proxy-drift diagnostic (`diagnostics.proxy_drift`) until G7 phase 2 supplies V2's IV30 pairs; Test B (shadow
strategies, slice B).

**Uses exactly, never re-implements** (`fno/forecast_v4/`): `pairs.pair_point` / `pair_probability` (the two date
sets), `loss` (QLIKE ranking and textbook, Brier), `confirmatory.calibrated_p`, `futility_p`, `judgeable`,
`event_band`, `batch_means_p`, `studentized_bootstrap_p`, `bootstrap.one_sided_test` (the null-centred bootstrap,
reported), `bootstrap.effect_check` (the minimum effect), `bootstrap.hac_one_sided_p` (HAC, reported),
`family.judge_family` and `FamilyDecision.lines()`, `regime.window_regime`, `stop_rule.forecasting_test`,
`power.power_report`, `sessions.py`, and every number in `terms.py`. **Thresholds at a look come from the frozen
tools, called with the member's actual n:** V1 and V2 claim `tools/v4_claim_thresholds.claim_threshold(question, n,
look rate)` (the tool divides by 15 itself) and futility `tools/v4_futility_study.futility_threshold(question, n)`;
V6a and V6b `tools/v4_brier_bands.operative_thresholds(question, n, band)` (claim per look and futility, for the
window's band). Measured on this container: 17 s, 7 s and 56 s per call at n = 125 (some evidence: one run), so a look
takes a few minutes.

**The crash-share cut (owner, item E option 2).** A member's window is **crash-dominated** when its 2% days are more
than 10% of its scored outcomes (`big_days / n > 0.10`, strict). A crash-dominated window is not judgeable at that
look, exactly like a window with fewer than 5 2% days: p = 1 for claims and futility, verdict open, never "no".
Both gates apply to every member at every look. **Said plainly:** at n = 125 the cut caps a judgeable window at
12 2% days (13 / 125 = 10.4%), so V6's 13+ band is unused until n >= 130; at n = 250 the cap is 25. **The rule is
`crash_dominated(big_days, n)` in `fno/forecast_v4/confirmatory.py`, beside `judgeable`** (orchestrator decision 69),
so it is frozen with the protocol; it is added in this story's branch. The protocol line stating option 2 as decided
(section 11 E) is written by the G6 session in the freeze commit (G6 judge note 1), not by G8: **a dependency of the
freeze**.

**Expected design** (new package `fno/forecast_scoring/v4/`, each file well under 350 lines; composition root
`fno/forecast_scoring/v4/wiring.py`, added to CLAUDE.md's list):
- `V4ForecastSource` (interface) and its adapter for **G7's agreed layout**: `research/forecasts/v4/<forecaster>/
  <question>.csv`, one row per day, first four columns `day,value,status,label` (value a variance for V1-V3 or a
  probability, empty unless status is `ok`; status `ok`, `missing`, `not_eligible` or `not_started`; label `live` or
  `backfill_exploratory`); G7's audit columns after them are ignored. Folder names are forecaster ids; question names
  the constants in `fno/constants.py`. Any status but `ok` is "no forecast that day". The primary baseline is read the
  same way under its id (`terms.PRIMARY_BASELINE`: `base_rate`, `har_daily`, `har_intraday`; V1's switch to intraday
  HAR by `eligibility.py`).
- `V4Outcomes`: **imports G7's pure rules in `fno/forecast_v4_rules/series.py`** (one place per rule; G7 builds
  first): the regular-session closes and VIX closes of `warmup_closes.csv`, the close-proxy `RV_s`, the V6a and V6b
  outcome per day with its resolution session, and the A16 live `rv/` reader (live provenance only; A16b's
  `rv-candle` never, decision 56). From those G8 forms V2 and V3 (sums of `RV_s` over the horizon's regular
  sessions), V7 (`VIX(d+5) > VIX(d)`, strict) and V1 (an `ok` A16 row; a `void` row is a void outcome). A horizon
  whose last session is not yet in the data is unresolved. The regime inputs of each outcome: the closing VIX and the
  log return of its first session (`regime.py`'s definition).
- `scores.py`: per forecaster and question. Point: count, mean ranking QLIKE, mean textbook QLIKE on RV > 0, mean
  squared error on variance, Mincer-Zarnowitz `RV = a + b f` (OLS). Probability: mean Brier, mean log score (clipped
  to [0.01, 0.99]), the 10-bin reliability table (G4's bins, reused), calibration slope and intercept (the same OLS,
  outcome on probability), the Brier skill score against the base rate.
- `comparison.py`: each forecaster against its question's primary baseline: the pairing counts (unresolved, void,
  forecaster missing, baseline missing, zero RV left out of the gate), D, the relative improvement and the minimum
  effect, and the reported sensitivities: batch-means t p, studentized bootstrap p, null-centred bootstrap p, HAC p,
  the sign of D in each half (stability). Seed word k: the member's place in `terms.FAMILY`; any other comparison
  `16 + crc32("question/forecaster") mod 2^31`, stable and never used to choose a result. The scored window's regime
  line. The power report once 60 scored outcomes exist (`power_report`; planning only).
- `look.py`: at a named look (`terms.LOOK_STOP_REVIEW` or `LOOK_SETTLE_DATE`) with its timestamp (time zone
  required): for each member with a registered forecaster, the scored set and its 2%-day count; not judged unless
  `judgeable` and not crash-dominated; else its thresholds (above), `calibrated_p` on the scored set (step = look rate
  / 15), the minimum effect from `effect_check` on the gate set, futile when `futility_p` on the gate set (its own n)
  is at most 0.025. A member closed at look 1 (claim or futile) is not judged at look 2 (read from look 1's record).
  Then `judge_family`, Test A by `forecasting_test`, and the output: `FamilyDecision.lines()`, each member's regime
  line under its verdict, Test A with every counted member's regime.
- `report.py` and the CLI `python -m fno forecast-v4-scores report` (descriptive, any day) and `python -m fno forecast-v4-scores look
  --look <name>`: Markdown and JSON under `research/forecasts/v4_scores/`. **Before `research/forecasts/FREEZE_v4.md`
  exists every output says "EXPLORATORY: protocol v4 not frozen; nothing here counts"**, and `look` prints its result
  without writing a record. After the freeze, a look's record is written once and never overwritten; the report
  states which forecasts are back-fill (exploratory) and counts only live ones made after the freeze.
- Registration of slots (which forecaster holds `rules`, `hybrid`, `ai_team` per question): read from the ledger row
  the freeze writes (protocol 5.6); before it, none is registered, so Test A is "undecided" (zero counted members),
  and the report says so.

**Acceptance criteria** (real NIFTY data as fixtures where a real case exists):
1. **Outcomes:** V2, V3, V6a, V6b and V7 on real 2024 sessions from `warmup_closes.csv` match a hand rebuild
   (including horizons across a holiday, the 1 Nov 2024 muhurat session and the 20 Jan 2024 special session, both
   skipped: a return runs from one regular close to the next); the last sessions' horizons are
   unresolved, never scored; V1 from A16 `rv` rows, a void row giving a void outcome.
2. **Scores:** QLIKE (ranking and textbook), squared error, Mincer-Zarnowitz, Brier, log score, reliability bins,
   calibration slope and intercept and the Brier skill score match hand values on a small fixture; a zero-RV date stays
   in the scored set and out of the gate set, and is counted.
3. **A comparison** on a real 2024-25 V6b window (a base-rate forecaster against an EWMA-style forecaster built in
   the test from the closes): every count, D, the effect and the four reported p-values equal direct calls of the
   `fno/forecast_v4` functions; the regime line equals `window_regime` on the window's first-session VIX and returns.
4. **Gates at a look, boundaries:** 4 2% days not judged, 5 judged; at n = 125, 12 2% days judged and 13 not
   (crash-dominated); at n = 250, 25 judged and 26 not. A not-judged member enters with p = 1 and verdict open.
5. **Thresholds:** the look calls the frozen tool functions with the member's n (claim on the scored set's n,
   futility on the gate set's n) and the look's rate; a look-2 member closed at look 1 is not judged.
6. **The family output** lists all 15 members, judged or not, with the look, its rate and the timestamp; every
   judged or not-judged member prints its regime line; V7 stays at p = 1.
7. **Test A:** no registered slot gives "undecided"; with registrations it equals `forecasting_test` on the decision.
8. **Labels:** before `FREEZE_v4.md` exists, every report and look output carries the EXPLORATORY line and `look`
   writes nothing; after it (a test fixture), a look record is written once and a second write is refused.
9. **Empty and not started:** a question without forecasts, and V4 and V5, print "not enough data yet" / "not
   started"; nothing fails.
10. Broken-code proof: for criteria 1, 2, 4, 5 and 8, a planted change (an off-by-one horizon, a dropped zero-RV date,
    `>=` for the cut, the scored n for futility, a look record overwritten) makes a test fail.
11. Gates: pytest, ruff, imports, code size; the G7 and G8 files are kept stable for the freeze hash.

**Known limits:**
- Every claim threshold measured so far is far below anything a real window reaches (V1 at n = 125: 1.1e-12, this
  session's run), so V1, V2 and V6a will almost surely stay open; G8 reports it, it does not change it (protocol 11 D).
- Thresholds are computed from exposed 2019-26 data by the frozen tools; G8 adds no calibration of its own.

**Test plan:** known-answer and hand-rebuild tests in `tests/forecast_scoring_v4/`; real-data fixtures; the
boundary tests above; planted changes for criterion 10.

**Judge verifies:** rebuilds one V6b comparison by hand from the closes; runs one look on a fixture and checks every
gate and threshold call.

**Depends:** G6 (merged), G7 (its `series.py` and forecast files; built first), A7, A16 (V1 only); the freeze also
needs the G6 session's section 11 E line · **Size:** M · **Status:** text PASSED (judge 128); built on
`story/g8-scoring`, for the judge (claims `reviews/claude/response_126_g8-scoring.md`)

## G9. Missed forecasts in protocol v4 (revision 9)

**Repository:** trading

**Description:** As the statistician, I want a member that misses too many days, or any scarce 2% day, to be
"undecided, operations" instead of being judged, so that a missing forecaster can never be called futile and can never
gain by skipping hard days.

**Context and why:** owner decisions of 15 Oct 2026 (`docs/DESK_DECISIONS.md`: observed days with a miss cap; Test A
keeps undecided), from responses 144-147, judge 138-139 and ChatGPT review 112. Section 4 already scores observed days
only; it had no miss cap and no miss report. It must land before the v4 freeze.

**Scope.** In: the miss definition, the two caps, the miss report on every comparison and look, Test A, the protocol
text. Out: scoreboard A and B misses of desk decisions (S2/S3), EQ2's release time, and stopping or fixing a
failing book (BG1's operational and budget stop).

**Expected design:** `fno/forecast_v4/misses.py` (pure: `MissReport`, `miss_report`), two registered constants in
`terms.py`, a `misses` field on G8's `Comparison`, `look.member_result` returning "not judged" for an operations-
undecided member, and the miss line in `look.py`, `render.py` and the recorded look JSON.

**Acceptance criteria:**
1. A miss is a resolved, non-void day with a baseline and no forecast, counted from the first forecast; a day with
   neither is an input failure, counted apart; unresolved and void days are neither.
2. More than 10% of baseline days missed, or more than 10% of baseline 2% days missed (any miss below 10 such days),
   makes the member "undecided, operations": not judged, never a claim, never futile; Test A stays undecided.
3. Every comparison and look prints the miss counts; the protocol text and `terms.py` state the same numbers (test).

**Test plan:** `tests/forecast_v4/test_misses.py` (boundaries of both caps), `tests/forecast_scoring_v4/test_look.py`
(an operations-undecided member through a look), `tests/forecast_v4/test_protocol_text.py`.

**Judge verifies:** recounts one miss report by hand; checks both cap boundaries; confirms an operations-undecided
member never asks for thresholds and leaves Test A undecided.

**Depends:** G6, G8 · **Size:** S · **Status:** done: judge 150 addendum 1 PASS, merged f3835ab; judge 156 independent PASS

---

## G10. Protocol v4 timeline: the pack observed 14:30-14:40, one release, one 15:10 deadline (before the v4 freeze)

**Repository:** trading · **Lane:** 1 (a frozen-to-be rule document and the capture times) · **Name note:** REPLAN's
"AI books on the v4 questions" was also called G10; this story renames it G11 (`REPLAN.md` and
`REPLAN_new_stories.md`).

**Description:** As the statistician and the owner, I want protocol v4's day to run on one clock that every family
shares (one data cutoff, one release, one deadline, one common snapshot), written into the protocol before its freeze,
so that no family gets more data or more time than another and no late or rebuilt day is scored as if it were normal.

**Owner decisions (15 Oct 2026, `docs/DESK_DECISIONS.md`, rows "v4 timeline", "flagged, not blocked", "Lateness",
"V6b stays a scored member", "The 60-minute fill decides"):** the capture from 14:30 with retries to 14:40 (revision 2: honest times, every quote
received by 14:40) and A16's 14:30 snapshot as the fallback; one pack to every family at about 14:32 (at the latest 14:40); one 15:10 deadline; the
15:15 common snapshot; the 3 pm routine moves to 14:05 only at go-live; two scores per desk decision (skill at the
common snapshot, money at the 60-minute fill); "moved after cutoff" days flagged, never blocked; system-late days out
for every family, a late family charged a miss (G9's caps); EQ2 and EQ5 and the day-quality labels into v4; the
pack's values stand in for the close, labelled and scored separately. V6b stays a scored member (no V6 code change).

### The day at go-live (a regular session `d`, IST)

| Time | What happens | Who |
|---|---|---|
| 14:05 | The 3 pm routine starts (setup ends well before 14:30) | owner's routine |
| 14:30:00 | The NIFTY pack's capture starts (spot, near future, chains, IV30); an incomplete capture retries | 3 pm recorder (A4) |
| 14:40:00 | **The pack's cutoff: a quote is in if its answer was received by 14:40:00** (owner's "Honest times, window to 14:40"). Fallback: A16's 14:30 mark, when no complete capture exists | A16 |
| when the pack is complete, at the latest 14:40 | **One release (EQ2):** the one pack, with one SHA-256, goes to every family at the same moment; rule outputs are computed but not published before the deadline | capture job |
| 15:10:00 | **One deadline:** a family's forecast or decision counts only if GitHub received its push by then (GitHub's receipt time, never the commit's own author or committer time) | every family |
| 15:15 | **Common snapshot** (A16's 15:15 mark): the skill score of every desk decision; the money verdict uses the 60-minute fill (E8, about 10:15 next session) | desk (E3, S1) |

**Honest times (revision 2, ChatGPT review 113, owner's decision of 15 Oct):** every live field keeps its real
`observed_at`; no field and no day ever carries a label earlier than its `observed_at`. A field received after
14:40:00 is not in the pack. **What `observed_at` is (revision 3, judge 161 addendum 2):** the time our request's
answer was received, by this host's checked clock: the honest upper bound of when the quote existed. Groww gives no
quote timestamp (strong evidence: `fno/quotes/recorder.py:65-69`, "quote age unknown"; `fno/providers/groww.py:94-103`
has only `last_trade_time`), so `last_trade_time` stays its own field, used only for the "traded today" check, and is
never the observation time. A provider's own snapshot stamp is used only where one exists (NSE's page time). **Day-quality label (one per day, on every v4 record and report):** `A` the live capture,
every required field observed by 14:40:00; `system_late` no complete pack by 14:40:00, or no release record at all
(written after the fact by the next publisher run). The label carries the pack's latest `observed_at` (for example
"A, observed by 14:31:12"). Every report counts `A`, `system_late` and flagged days; a protocol v4 verdict uses `A`
days. **`A2` dropped (orchestrator's ruling, 16 Oct; judge 274 note at 90bc4565):** A16's 14:30 mark has no India VIX,
only one monthly beside the weekly, and no next monthly on a monthly expiry day (strong evidence:
`fno/intraday/groww_source.py`, `expiry_plan.py`), so it can never hold a complete pack; with A4e's 14:30 capture
the `A` path is the normal one. **One pack, one hash:** every family's record names the released pack's SHA-256; a record naming
any other pack is refused. (The earlier note on an `A2` day's flagged IV30 is moot: `A2` is dropped, above.)

**"Moved after cutoff" (flag, never a block):** a day with `abs(ln(S_15:15 / S_14:30)) > X` is flagged and reported
apart; nothing is dropped. **X** is frozen before go-live as the 95th percentile of that move over A16b's 2020-26
checked 15-minute levels (regular sessions; the closes of the candles ending at 14:30 and at 15:15, A16b's level
rule), so about 1 day in 20 is flagged
(reasoning only for 95th; the 99th is the alternative and would flag about 1 in 100). **Live S (revision 3):** A16's
checked levels at its 14:30 and 15:15 marks, by A16's own level rule, because X is calibrated on A16b's levels made by
the same rule; the pack's spot is not used (its `observed_at` varies within the window, so the flag would measure a
different interval each day). A day without either A16 level has no flag value and is counted as "flag not
computable". **Frozen with it:** X's value, the
sample count, the source revision (A16b's archive manifest commit) and the quantile convention (nearest rank:
the `ceil(0.95 n)`-th smallest move). History's 5% does not promise 5% of future days.

**Lateness (owner's row):** a `system_late` day is excluded for every family and counted ("system late"), like G9's
input failure but decided by the pack, not by the files: with no pack, no family had the same inputs. A family whose
commitment is after 15:10 has no forecast that day: a miss under G9's 10% caps.

**Pack values stand in for the close:** every input of `d` itself (spot, futures, IV30, quotes) is the pack's value,
received between 14:30:00 and 14:40:00 with its real time, labelled `live_pack`. The back-fill has no intraday implied-volatility history (strong evidence: the panel holds end-of-day
chains only; A16b holds index candles, no option quotes), so back-filled rows that use `d`'s level or IV use the close
and stay labelled `backfill_exploratory`: the live and the close-proxy cohorts are scored apart and never pooled.
**G1 v2's 15:00 records are never merged into v4** (a different protocol, pack and time). **For today's forecasters this
changes nothing:** G7's baselines and rule forecasters and M1's weather read only sessions up to `d-1` (strong
evidence: `fno/forecast_v4_rules/baselines.py:3`, `fno/weather/day.py:3`), so their back-fill content is the same under
either cutoff; only the capture time check moves. It matters for the implied baselines, V4, V5 and the AI books.

**Outcomes do not move:** V1-V3, V6 and V7 outcomes stay measured from official closes (and A16's session RV), as
protocol 1.1-1.2 define them.

### The exact PROTOCOL_v4.md changes (applied in this story's build, before the freeze)

1. Section 1.2, "the cutoff is 15:00:00 IST on `d`, as G1 v2" -> "the cutoff is **every field observed by 14:40:00 IST
   on `d`, captured from 14:30:00, each with its real `observed_at`** (section 1.6; G1 v2 keeps 15:00 for its own
   questions)".
2. Sections 1.4, 1.5 and 3.1: every "15:00" spot, quote, spread check, pack, future and IV30 -> "the pack's" (section
   1.6), with its `observed_at`. The spread limit (5%) is unchanged.
3. Section 3.1, premium-adjusted implied: add "live forecasts multiply the **pack's** raw implied by the ratio; no 14:30
   IV30 history exists, so the window stays the EOD proxy and the pack / EOD mismatch enters the ratio's noise
   (reasoning only)"; `diagnostics.proxy_drift` pairs the pack's IV30 with EOD.
4. New section **1.6 "The day's clock"**: the table above, honest times, the day-quality labels, the one pack hash, the
   moved-after-cutoff flag with X's rule (value, sample count, source revision and quantile convention added at the
   freeze), and the 15:10 deadline (GitHub's receipt time).
5. Section 4, after the miss rule: "**A `system_late` day** is excluded for every member and counted apart; **a
   commitment after 15:10** is no forecast that day (a miss). Every report states each label's day count and the
   flagged days."
6. Section 8, disclosure: "the back-fill uses closes where live uses the pack's values; no intraday IV history
   exists".
7. Section 10, freeze preconditions: X's number frozen; the go-live date stated in `FREEZE_v4.md` with its
   `Frozen on:` line (G8).
`tests/forecast_v4/test_protocol_text.py` gains the cutoff and deadline times so the text and `terms.py` cannot drift.

### What moves with it

| Item | Today | At v4 go-live |
|---|---|---|
| 3 pm routine (CLAUDE.md, A4, A7) | starts 14:33; `quotes record` window 14:55-15:10 (`fno/quotes/recorder.py:36`) | starts 14:05; window 14:30-14:40 (lane 1, A4 change, and the owner's schedule) |
| v2 forecast capture (`.github/workflows/forecast-capture.yml:86-92`, `fno/ai/timing.py`) | waits to 15:10, pulls to 15:13, deadline 15:15 | **unchanged**: v2 keeps its frozen times until v4 is live, then retires or runs beside it as v2 says (its late days reported) |
| v4 capture times | G7 `fno/forecast_v4_rules/capture.py:28` and M1 `fno/weather/capture.py:39` refuse at 15:00 | refuse at 14:30 (one `terms` constant both import) |
| A4c's other indices (15:01-15:13) | after A16's 15:00 mark, before 15:13 | **14:41-14:44 and 14:47-14:58**: after NIFTY's last retry, paused 14:44-14:47 around A16's 14:45 mark (about 216 quotes, about 50 s, same Groww key), stopped before A16's 15:00 mark; data only, not in the pack |
| Stock chains | | the stock-chain slot is decided by the owner separately |
| AI books' v4 prompt (G11) | v2: deadline 15:15, reveal 15:15:10 | v4: release about 14:32, deadline 15:10, reveal after 15:10 |
| G7, M1 back-fill labels | `backfill_exploratory` | unchanged label; a method note says "close stands in for 14:30" (no content change, above) |
| G8 scoring | counts live rows after the freeze | also: excludes `system_late` days, reports per label and the flagged days; reads the label from the record |
| E3 / S1 desk | 15:15 execution snapshot, 60-minute fill | skill score at 15:15, money verdict at the 60-minute fill (owner's row); E3's timetable moves its pack time to 14:32 |

**Acceptance criteria (for the build after this text passes):**
1. The protocol text carries changes 1-7; `test_protocol_text.py` checks 14:30, 14:40 and 15:10 against `terms.py`.
1a. **Honest-time fixture (ChatGPT review 113; revision 3):** a quote whose answer was received at 14:40:00 is in the
   pack with that time; one received at 14:40:01 is not (the field is missing; a required field missing makes the day
   `system_late`); a quote received at 14:31:05 whose last trade was at 14:29:59 carries 14:31:05, never 14:29:59; the
   real A16 14:30 row (sent at 14:30:00.0004, received at 14:30:00.753 on 16 Oct) passes the 14:30 lower bound
   (judge 277);
   no field ever carries a time earlier than its `observed_at`.
1b. Every family's record names the released pack's SHA-256; a record with another hash is refused. The deadline check
   reads GitHub's receipt time; a commit dated 15:09 but received at 15:10:01 is late.
2. `terms.py` holds the capture start, window end, deadline and common-snapshot times and X; G7's and M1's capture
   refuse at the capture start through one constant, `terms.V4_CAPTURE_START = time(14, 30)` (boundary: 14:29:59
   accepted, 14:30:00 refused).
3. Each v4 record and report carries the day label; every report counts `A`, `system_late` and flagged days; a
   `system_late` day is excluded for every member and counted; a commitment received at 15:10:01 is a miss, at
   15:10:00 on time (G9's caps then apply); live and close-proxy cohorts are reported apart; no v2 record is read.
4. X is computed by a committed tool from A16b's checked levels (sample count, source revision, nearest-rank 95th
   percentile and the flagged share printed); a
   day just above X is flagged, just below is not; nothing is dropped.
5. The back-fill's content is byte-identical before and after the change for G7 and M1 (proof that they read `d-1`
   only); the method note is added.
6. Gates; real-data run: one day's 14:30 capture end to end in a dry run, beside A16's 14:30 mark on the same key
   (counts, errors and finishing times only).

**Shared Groww key at 14:30 (said plainly):** A16's 14:30 mark (about 216 quotes at about 5 a second) runs in the
same minute as the new 14:30 NIFTY capture, on the same key (A16 paces itself; the 3 pm recorder's provider has no
pacer, response 144 item 7). Today they never overlap (14:55 capture, 15:00 mark). Criterion 6's dry run therefore
measures both together at 14:30 (request count, errors and the time each finishes); if they clash, the capture starts
after A16's mark (about 14:31), still inside the 14:40 window, and its fields carry their real times. Two sign-ins on
one key coexisted once, outside market hours (some evidence, checked 15 Oct); criterion 6's dry run is the real test.

**Known limits:** X rests on 2020-26 history, one crash included (some
evidence); a GitHub push delay near 15:10 counts as late (the push time is the only clock both sides trust).

**Depends:** G6 (merged), G9 (merged), G7, M1, G8 (merged); A4e's named 14:30 capture; the owner's routine change
at go-live · **Size:** M · **Status:** story text for judge A, then ChatGPT (rule 9) (`reviews/claude/response_152_g10-v4-timeline.md`)

---

### G10 part 2: the pack, its release record and the AI fire (build text, 16 Oct 2026)

**Owner of this part:** the A16/G8 builder. **Lane:** 1 (judge B). **Before the v4 freeze** (22-23 Oct): G11 (Books 2
and 3, the owner's top priority) builds on its interfaces. Part 1 (merged: clock, X, day-label reader, system_late
exclusion, counts, the stored flag, cohorts, the look reconciliation) is not repeated here.

**Agreed so far (cross-builder, 15-16 Oct):** R2/G7 (pack fields, the `pack_sha256` column in its records, the
back-fill regenerated in the same commit), G11 (the fire on the pack's push, `V4_LATEST_FIRE`, collect in
forecast-capture.yml's existing slot, no new cron), the orchestrator (the workflow and step edits are in this
builder's remit, lane 1; any cron change goes to the owner first).

**Storage follows O9 from day one (rule 5: nothing writes data into a checkout).** Every file this part writes goes
through O9's `DataStore.put` (`fno/storage/data_wiring.build_data_store`): bytes write-once in Drive's `data` area,
one receipt `receipts/<path>.sha256` committed by the A16f committer. Readers read through O9's `DriveCache`
(verified SHA). Part 1's day-label reader keeps its format; only its root becomes the cache folder.

**1. The pack** (`fno/v4_pack/`, a new package outside the frozen `fno/forecast_v4/`, so a later format change never
touches the frozen set). One JSON document per regular session at Drive path `v4/packs/<YYYY>/<date>.json`; its
SHA-256 (of the stored bytes, canonical JSON: sorted keys, UTF-8) is the pack's identity. Values stay in Drive only:
Groww quote values never enter a repository (CLAUDE.md, A4b); GitHub holds the receipt. Fields, each with its own
`observed_at` (this host's checked clock at the answer's receipt, protocol 1.6; `last_trade_time` only for the
"traded today" check, never a time of observation):
- `day`, `label` (`A`, the 14:30 capture; the only label a pack carries), `source`, `provider`, `captured_from`,
  `released_at`;
- `spot` (NIFTY index), `future` (the future of expiry `e`: last, bid, ask), where `e` is the nearest monthly expiry
  strictly after `d` (protocol 1.5, V5's expiry), and `india_vix` (NSE's value with NSE's own time where NSE gives
  one);
- `chain`: per contract `expiry`, `strike`, `kind`, `bid`, `ask`, `last`, `last_trade_time`, `observed_at`; `mid` =
  (bid + ask) / 2 only when both sides are present, else absent. It holds at least both monthlies A4 records (IV30's
  inputs; `e`'s chain includes the ATM call and put that V5's 5% spread rule reads) and, once V4 is built, the nearest
  weekly;
- `iv30`: `value`, `flagged` (single-expiry, protocol 1.6), `expiries`, `method` (the G1 estimator's name and file
  hash), `observed_by`.
A field received after 14:40:00 is not in the pack; a required field missing makes the day `system_late` (no pack).

**2. The release record** (`v4/days/<YYYY>/<date>.json` in Drive, receipt in GitHub): `day`, `label` (`A` or
`system_late`), `pack_path`, `pack_sha256`, `observed_by` (part 1's format plus `pack_path`). Written once, right after
the pack. G8 syncs `v4/days/` through the DriveCache before every report and look.

**3. The capture at 14:30.** The pack is built from the 3 pm recorder's NIFTY capture moved to a 14:30-14:40 window
(retries inside the window, every field with its time). That window is A4's recorder (`fno/quotes/`), not this
builder's: A4's owner (with O1, who owns the 3 pm routine's timing: register row "Handover / routines") adds a
`--window` setting so v2 keeps 14:55 until go-live; this part supplies the pack builder
that reads the capture's result and writes the pack and the release record. The capture is A4e's named window
(`python -m fno quotes record --window v4`, dataset `quote-snapshots-v4`; judge 281), an extra capture beside 14:55
(orchestrator's ruling (A), 16 Oct). Only a run whose sidecar says `clock_ok` (both clock readings, worst skew within
A16's 5 s) gives `A`; otherwise the day is `system_late`. No fallback: `A2` is dropped (section 1.6 above). Same
Groww key as A16's 14:30 mark: the dry run (criterion 6 of the text above) measures the load. **Every session gets a
record (G11, 16 Oct):** each publisher run first writes `system_late` for every earlier scored session from
`daily.live_from.forecasts_v4` to yesterday that has no record, so a day the routine never ran is settled (the look
never stays blocked); records are write-once.

**4. `pack_sha256` in the v4 records** (G7's `fno/forecast_v4_rules/records.py`, R2/G7's file; R2/G7 builds it).
The column sits right after `inputs_sha256`; `record()` takes it as a keyword, default empty; `records.py` checks
only its form (empty or 64 hex characters). `read()` accepts a row without the column as empty, so every committed G7
and M1 CSV (M1's two forecaster folders use G7's `Record` through `v4_writer`: 9,636 rows) reads unchanged and is never regenerated; a file's next write (it rewrites the whole file) adds the empty column, with no value changed, which keeps
the freeze clean (R2/G7, 16 Oct). The refusal lives in a small guard in `fno/v4_pack/` used by the pack readers'
writers (G11's first): fed the released SHA from the release record, it refuses a record naming another pack, and an
empty SHA from a forecaster that reads the pack. **Design point for the judge:** G7's and M1's forecasters commit before the 14:30 cutoff from
closes up to d-1 only (proved: part 1's IV and back-fill checks), before any pack exists; they carry `pack_sha256`
empty, and their method hash already proves they read no pack. Requiring a pack SHA from them would force them past
their own cutoff.

**5. The 15:10 deadline on GitHub's receipt time.** A live record counts only if GitHub received the commit that
added its receipt by 15:10:00 IST: O8's `file_pushed_at` (GitHub push receipts, `fno/health/evidence.py:46`) on the
receipt path, never the commit's own time. Behind an interface (`CommitmentTimes`), one adapter on O8's evidence. A
record received at 15:10:01 is no forecast that day (a miss under G9's caps).

**6. The AI fire.** `terms.V4_LATEST_FIRE = time(14, 55)` (G11's latest start: a later run is recorded `not_fired`).
A new workflow triggered by `push` of `receipts/data/v4/days/**` on `main` (O9 keeps every data file
under Drive's `data` area, so its receipt is `receipts/data/<path>.sha256`; corrected from `receipts/v4/days/**`, 16 Oct) runs `python -m fno ai fire` on the released
pack; no cron (orchestrator, 16 Oct). The release record's receipt is pushed by the owner's routine with its own
credentials, which starts workflows (strong evidence: 15 Oct, push bf16247a started forecast-capture run 38714143717
within the minute); never by an Actions run's `GITHUB_TOKEN`, which starts nothing. Collect stays in
forecast-capture.yml's existing slot; the v2 AI steps leave at the freeze (owner's choice A). Any cron change: owner.

**Acceptance criteria (part 2):**
1. A pack built from a fixture capture has every field above with its `observed_at`; a field received at 14:40:01 is
   absent; a missing required field gives `system_late` and no pack; the SHA is of the stored bytes.
2. Pack and release record go through `DataStore.put` (a test refuses any open-for-write under a checkout data
   folder); G8 reads the release record from the DriveCache folder.
3. `pack_sha256`: the guard refuses a pack-reading record with another SHA or an empty one; G7 and M1 rows carry it
   empty; every committed G7 and M1 CSV is unchanged until its next write, which adds the empty column; no value changes
   (a missing column reads as empty, equal to a new empty value, so `RecordConflict` is unaffected);
   `records.py` is not a G7 method file, so no method hash moves.
4. The deadline: received 15:10:00 counts, 15:10:01 is a miss, from GitHub's receipt time through the interface.
5. `V4_LATEST_FIRE` in terms; the workflow's trigger path equals the release record's receipt path (a test); no
   `schedule:` added to any workflow (a test).
6. Real runs: criterion 6 of the text above (the dry run beside A16's 14:30 mark) on a session before the freeze;
   and one dated day where the release record's push starts the fire run (run id, both times) in the claims. **Said
   plainly:** the second needs the owner's 3 pm routine to commit at 14:30, which today starts at 14:33 and records
   at 14:55; moving it earlier is the owner's schedule call. Without it, that proof comes after the freeze and G11
   counts from the first proven day.

### G10 completion: protocol v4's daily clock really runs (story text, 24 Oct 2026)

**Builder:** session_011hvvn9CahAD5dCPHS3kowN (orchestrator session_01Mt6dcBU5kp2htdPN2KmiZH assigned G10 on 24 Oct;
the earlier builder 01VK88LxJvV1Gi7Wbr3D4fzp is out of reach). **Branch:** `story/g10-completion`. **Lane:** 1
(forecast records, a rule document before its freeze, Groww, Drive, Slack and the daily routine's schedule; one judge,
judge B: no money, limits, fills or exits). **Owner's ruling:** "let's close v4 full first" (DESK_DECISIONS, 24 Oct).

**Why (the 24 Oct audit, each point checked again on `main` at 4016e28f):**
1. The 14:30-14:40 capture is never run. A4e's `quotes record --window v4` exists (`fno/quotes/window.py`, config
   `quotes.windows.v4`), but `QUOTE_PARTS` (`fno/daily/quote_parts.py:67-75`) holds only nifty, nse and indices, and no
   workflow or routine calls it. No `quote-snapshots-v4` folder exists in Drive or the receipts.
2. `fno/v4_pack/` is on `main` (format, codec, guard, release record, `ReleasedPacks`, `CommitmentTimes`), but nothing
   outside it imports it except G7's `records.py` (the guard). The pack builder, the capture reader, the release run
   and `python -m fno v4-pack release` exist only on `story/g10-part2b-pack` (unmerged, unjudged; 818 lines added and
   353 removed in its two-dot diff to `main` under `fno/`, `tests/`, the workflows and `CLAUDE.md`, most of the
   removals being `main`'s newer files; its own new code is about 600 lines with tests; a test merge conflicts only in
   `docs/WORK_REGISTER.md`).
3. Day labels are written to Drive `v4/days/<YYYY>/<date>.json` (`fno/v4_pack/paths.py`, `release.py:62-70`), but G8
   reads a checkout folder, `research/data/v4_days/` (`fno/forecast_scoring/v4/wiring.py:29`), which does not exist and
   would be flat, not by year. No label is ever read.
4. Text and code disagree: PROTOCOL_v4.md:115 calls a day with no release record `system_late`; G8 leaves it
   unlabelled (`fno/forecast_scoring/v4/days.py:5`, and `LateDaysOut` drops only labelled days).
5. The 15:10 deadline is checked nowhere live: `on_time` (`fno/v4_pack/commitment.py:30`) has no caller.
6. The v4 AI fire workflow (`v4-fire.yml`) is on no branch that can merge: its command `ai fire --protocol v4` is
   G11's round 2b and is not on `main`.

**What is already on `main` and stays as is (no change, cited so the judge can check it):** the clock constants
(`fno/forecast_v4/terms.py:85-89`); G7's and M1's capture refusal at 14:30; X and its tool; the stored moved-after-cutoff
flag in A16's rv rows (`moved_after_cutoff`: "no" on 19, 21 and 22 Oct; empty on 23 Oct, when A16's 14:15-14:45 marks
were missed because its routine was not running, conversations/2026-10-23.md:218); the live and close-proxy cohorts;
the pack format and SHA; the pack binding guard; the release record format and its verified reader.

#### Scope

1. **Schedule the 14:30 capture** as a fourth quote part of O1's daily run (`v4`), live only from its own date.
2. **Take over the pack builder, the capture reader and the release run** from `story/g10-part2b-pack`, finish and
   judge them, and run the release as an O1 step right after the capture ends.
3. **One rule for the day label**, the same in the protocol, the writer and G8's reader.
4. **G8 reads the labels from Drive** through the verified Drive cache, never a checkout folder.
5. **The 15:10 deadline checked live** for every record committed straight to G8's folder, as a write-once verdict
   that G8 applies (a late record is a miss).
6. The protocol 1.6 and section 4 wording that this needs (the protocol is not frozen: no `FREEZE_v4.md` exists).
7. **The pack's interface for G7b and G11** (their asks, relayed by the orchestrator on 24 Oct; answered below): the
   `v4` window also records V4's expiry and the future's bid and ask.

#### The pack's interface for G7b and G11 (answers to their asks)

| Ask | Answer | Reason | Groww load added at 14:30-14:40 |
|---|---|---|---|
| G7b 1: chains for `e` and every expiry up to and including the first with at least 5 scored sessions | **Changed:** `e` and the other monthly as today, plus **the first listed expiry with at least 5 scored sessions in `(d, expiry]`** when it is not already one of them; not the nearer ones | V4 uses only that expiry (G7b's own rule picks the first with 5 sessions), so a nearer weekly adds requests and no input. The rule is one pure function in G7b's module, imported by A4e's `v4` window (G7b's offer 2: one rule, one place); **the pack names the chosen expiry as `v4_expiry`** (`None` when the function returns `None`; G7b's second ask: yes, so a failed weekly is never read as "V4's expiry is the monthly") | about 90 contract quotes and one chain call, about 80 s, on days that expiry is a weekly (most days); none when it is a monthly |
| G7b 1: strikes within at least 3% of spot | **Yes, already:** A4's band is 5% (`fno/quotes/recorder.py:49`, `SPOT_BAND`), used for the added expiry too (one band, DRY) | 5% covers 3% and the strikes either side of ATM | none beyond the row above |
| G7b 3: the future keeps bid and ask (and, asked later, what A4's `traded_today` needs) | **Yes:** the pack's `FutureQuote` gains `last_trade_time` (from Groww's quote) and `volume` (the day volume NSE's level read already gives; `7cab92b06` used it only for IV30's Black-76 and did not store it), so A4's `traded_today` can decide on the future like on any quote. One Groww quote of `e`'s future in the `v4` window, behind a new `FutureQuotes` interface with a Groww adapter (the `Provider` interface has no future quote; NSE's level read gives only last and volume) | V5 prices `F` at mid under the 5% spread rule (W2); without both sides V5 is void every day | one request, under 1 s |
| G7b 4: `iv30.flagged` as on `main` | **Yes**, unchanged | | none |
| G7b 5: an O1 step `forecasts_v4_pack` right after the release | **Yes**, the order is fixed below; G7b builds the step, its own live key and its own pathspec; **its V4 and V5 forecasters are pack readers: G7b adds them to `PACK_READERS` and calls `check_pack_binding` before writing** (judge 580 finding 3); their live records' receipts (`receipts/data/v4/records/live/`) are covered by the 15:10 check (criterion 7) | it reads the released pack, so it must follow `v4_release`, and it must commit before 15:10 | none (reads Drive) |
| G11 D1: the daily release and the names G11 reads | **Yes:** `ReleasedPacks` (`release`, `pack`, `pack_bytes`), `ReleaseRecord.pack_sha256`, `Pack`, `check_pack_binding`, `build_released_packs` keep their names and modules (`fno/v4_pack/release.py`, `model.py`, `guard.py`, `wiring.py`); a rename goes to G11 first | | none |
| G11 D2: `system_late` labels | **Yes, with a changed path:** the label is the release record in Drive `v4/days/<YYYY>/<date>.json`, read through `ReleasedPacks.release(day)`; **not** `research/data/v4_days/<d>.json` (that folder is retired here, criterion 6). Every scored session from the live date gets a record, `system_late` included (criterion 4's catch-up); criterion 5's function answers a day with no record yet | O9: data lives in Drive, GitHub holds receipts | none |
| G11 D3: the release push starts workflows | **Yes:** the receipts `receipts/data/v4/days/<YYYY>/<date>.json.sha256` (its `paths:` filter: `receipts/data/v4/days/**`) and `receipts/data/v4/packs/<YYYY>/<date>.json.sha256` go in one commit, pushed by the daily run's committer with the owner's routine credentials, never an Actions token (15 Oct: such a push started forecast-capture run 38714143717 within the minute). Catch-up records land on the same path, so the workflow fires only for today's record (as the held `v4-fire.yml` already checks). The deadline verdicts (`receipts/data/v4/deadlines/`) never match. G11 lands `v4-fire.yml` | | none |

**Total per `v4` attempt:** about 180 + 90 = 270 contract quotes, 3 chain calls and 1 future quote, about 4 min at the
measured pace (180 quotes in 2 min 38 s on 23 Oct), so about 14:30:00-14:34:00. A retry after an incomplete first
attempt has about 6 minutes, enough for one full attempt. These A4e changes (V4's expiry and the future quote, only in
the named window; the default 14:55 capture byte for byte as today) touch A4's `fno/quotes/`. A4e's builder
01MKtUHByHsR9cNwaP5KhFYH is out of reach, so the orchestrator assigned these `v4`-window changes to this story's
builder (24 Oct; register row G10); A4's other behaviour stays as it is (criterion 3a).

#### The daily-run steps (O1)

The routine time stays **14:05 IST** (owner, 21 Oct). `DAILY_RUN_STEPS` (`fno/constants_operations.py:49`) becomes:

`quotes` (now also starts the `v4` part), `owner_timing_fills`, `margin_check`, `weather`, `forecasts_v4`,
**`v4_release`**, `forecasts_v4_pack` (G7b's step, added by G7b), `versions`, `pack`, `book1`, `decisions`, `snapshot`, `fills`, `exits`, `trade_marks`, `reviews`,
`quotes_done`, `card`, `price_distribution`, `premium_ranges`, `price_distribution_scores`, `price_ranges`,
`price_range_scores`, `premium_range_scores`, **`v4_deadline`**, `candles`, `close_read`, `close_recheck` (code
round 1: before `candles`, so A4h's two reads stay last).

| Piece | When (IST) | What it runs | Commits (its own paths only) |
|---|---|---|---|
| `v4` quote part | opened by `quotes` at routine start, started at 14:27 (O1's 3-minute margin before the window; code round: not 14:03, A4e's early limit, so a rehearsal never runs 25 minutes at real speed), records 14:30:00-14:40:00, retries inside the window | `python -m fno quotes record --window v4` (A4e, unchanged) | `':(glob)research/data/quotes/groww/derivatives/quote-snapshots-v4/**'` (sidecars and the `.canonical` marker; raw rows Drive only) as soon as it ends, **not after NIFTY** |
| `v4_release` | after `forecasts_v4`; waits for the `v4` part to end, never runs while it records; a part still running at 14:45:00 (it sends no request after 14:40:00, so it is hung) is stopped, its files are not committed, and the release writes `system_late` ("capture still running at 14:45") | `python -m fno v4-pack release` (taken over; catch-up, then today) | `receipts/data/v4/days/`, `receipts/data/v4/packs/` (the receipt push is what will start G11's fire later) |
| `v4_deadline` | before `candles` (code round: A4h's two close reads stay the run's last steps), not before 15:12:00 | `python -m fno v4-pack deadline` (new) | `receipts/data/v4/deadlines/` |

`forecasts_v4` and `weather` keep their place: they must commit before 14:30, when their capture refuses. `v4_release`
sits before E3's `versions` and `pack` (14:58), so it adds no wait before the desk. G7b's `forecasts_v4_pack` comes
right after `v4_release` (it reads the released pack) and before `versions`; it commits before 15:10. **Live switch:** one new key,
`daily.live_from.v4_pack`, gates the `v4` part, `v4_release` and `v4_deadline` together (null on the branch; a not-live
day records `not_live` for each and starts no capture). Each new step gets its reason codes in O1's closed set
(`fno/daily/reason_codes.py`) and appears in O8's health window like every step. CLAUDE.md's "Daily desk routine"
gains one line for the `v4` part and its hand-fix `git add` line; NIFTY's hand-fix line is narrowed with it (criterion
2).

#### The Groww load at 14:30, beside A16's marks (said plainly)

- **The `v4` capture:** NIFTY's two monthly chains plus 180 contract quotes on the routine's Groww key take about 2 min
  40 s (measured: 23 Oct 14:55:00-14:57:38, 180 of 180; 22 Oct 14:58:58-15:01:30, 180 of 180); with G7b's V4 expiry
  and the future quote (interface table above) about 4 min, so about 14:30:00-14:34:00 when the first attempt is
  complete. India VIX and the futures' last prices come from NSE, not Groww.
- **A16's 14:30 mark:** 220 contracts on its own routine's sign-in to the same Groww account, sent at 14:30:00 and done
  in about 85 s (22 Oct 15:00 mark: sent 15:00:00.0003, finished 15:01:23, 220 of 220). So the two overlap from 14:30:00
  to about 14:31:25; G7b's additions make the capture longer, not the overlap. They do not overlap A16's 14:45 mark (the capture's last request is at 14:40:00 at the latest),
  the 14:55 NIFTY part, the 15:01-15:13 indices or A16's 15:00 mark.
- **Evidence on overlaps so far (mixed; some evidence, three overlaps; revised after judge 580 finding 2):**

  | Overlap | NIFTY capture (sidecar in `research/data/quotes/groww/derivatives/quote-snapshots/2026/10/`) | A16's mark (row in `research/data/intraday/slots/2026/10/<dd>/`) |
  |---|---|---|
  | 22 Oct, 15:00 mark | `nifty_20261022_145858.meta.json`: 14:58:58-15:01:30, 180 of 180, no failures | `nifty_20261022_1500.csv`: good, 220 of 220, sent 15:00:00, first seen 15:01:23 |
  | 22 Oct, 15:15 mark (desk's 15:15 capture) | `nifty_20261022_151500.meta.json`: 15:15:00-15:18:15, **176 of 180, incomplete: four `GrowwAPIException` failures (22450 and 22500 call and put of 27 Oct, the ATM strikes)** and one `RawFileConflict` | `nifty_20261022_1515.csv`: good, 216 of 216 |
  | 23 Oct, 15:15 mark | `nifty_20261023_151500.meta.json`: 15:15:00-15:17:34, 180 of 180, no failures | `nifty_20261023_1515.csv`: good, 216 of 216 |

  So one of three overlaps lost four quotes on our side while A16's mark stayed whole. Groww withholds its messages, so
  the cause (a rate limit or something else) cannot be read; a 22 Oct retry (15:18:24) was complete. The `v4` capture
  retries inside its window, so one such loss costs a retry, not the day, if the retry ends by 14:40.
- **The fallback trigger, observable (criterion 11):** any failure in either job during the overlap (the `v4` sidecar's
  `failures` not empty, or A16's 14:30 row not `good` or with failures) is reported with the counts in one #fno-desk
  line by `v4_deadline` at the day's end (A16's row is committed by then), and in the builder's evening report to the
  orchestrator. On such a day, the orchestrator decides the fallback (the part starts at 14:31:30, after the mark,
  still inside the window, every field with its real time): a one-value config change, not built in advance. A16
  alerts a bad mark itself; nothing in this story mutes it.

#### Merge order with `story/g10-part2b-pack`: taken over, not merged

The three code commits (`1fe605bd1` pack builder and capture reader, `7cab92b06` the future's traded volume,
`f313ae15f` release run, CLI and wiring) are cherry-picked with `-x` onto `story/g10-completion` (their history and
authorship stay traceable), without their `docs/` hunks; then this story's commits finish them (orchestrator, 24 Oct:
accepted). Where each lands:

| Commit | Files it brings (on `story/g10-completion`) | Finished by |
|---|---|---|
| `1fe605bd1` | `fno/v4_pack/builder.py`, `fno/v4_pack/capture.py` (new); `codec.py` (`capture_window`), `model.py` (one field); `tests/v4_pack/capture_fixture.py`, `test_pack_builder.py` (new), `test_pack_format.py` | criteria 3 and 3a |
| `7cab92b06` | `fno/v4_pack/builder.py` (the future's traded volume for Black-76) | criterion 3 |
| `f313ae15f` | `fno/v4_pack/release_run.py`, `cli.py` (new); `wiring.py` (`build_release_run`, merged with `main`'s REH1b receipts line); `fno/cli.py` (the `v4-pack` command); `tests/v4_pack/test_release_run.py` (new), `test_release.py`; its `docs/WORK_REGISTER.md` and `docs/stories/G-forecasts.md` hunks are dropped (this text replaces them) | criteria 4, 5 and 7 | **Not merged** because a
merge would also bring `.github/workflows/v4-fire.yml`, its `capture-watch.yml` line and its test: that workflow runs
`python -m fno ai fire --protocol v4`, which is not on `main` (G11 round 2b, parked), so every release push would start
a job that fails and alerts #fno-desk each session day. A merge would also bring a stale handover file and a second
copy of the register row. `v4-fire.yml` stays on `story/g10-part2b-pack` for G11 to take when its fire lands
(out-of-scope item 1). After this story merges, `story/g10-part2b-pack` is closed, with nothing left that is not on
`main` or held for G11. Expected conflict: `fno/v4_pack/wiring.py` (on `main`, REH1b's `rehearsed_receipts` was added
to `build_commitment_times`), resolved by keeping both.

#### Acceptance criteria (each with its code, its tests and the plant that must break a test)

1. **The `v4` part is scheduled.** `QUOTE_PARTS` gains `v4`: arguments `quotes record --window v4`, its own pathspec,
   its window end 14:40 and its early limit taken from A4e's window (never a copied number), its canonical marker
   (`quote-snapshots-v4`, `nifty`), and a live key `v4_pack` that `QuotePart` gains (no key: always live, as today).
   Good: live today, it starts at routine start. Bad: not live (null, or a later date), it is `not_live` and no process
   starts. Boundary: `live_from` equal to today starts it; a rerun after 14:40 without its marker fails it with one
   alert (`NOT_IN_THIS_RUN`, F1's rule), with its marker takes the earlier run's result. Empty: a closed day records
   only `skipped` (A7). Plants: drop the part; pass the default window; ignore the live key.
2. **The `v4` part commits alone, and no other part can commit its files.** A non-lead part commits after NIFTY
   (`quote_parts.py`, `name == LEAD or LEAD in self.results`); the `v4` part is exempt (it ends about 25 minutes before
   NIFTY starts and shares no file). NIFTY's pathspec `groww/**/nifty_*` today also matches
   `groww/derivatives/quote-snapshots-v4/.../nifty_*`, so it is narrowed to
   `':(glob)research/data/quotes/groww/derivatives/quote-snapshots/**/nifty_*'`. Good: `v4` ended at 14:34 with NIFTY
   not started is committed at once. Bad: a `v4` file left uncommitted is never in NIFTY's commit (pathspec test on
   real path strings of each dataset). Boundary: the weekly (`niftyweekly_*`) and the three indices' globs match exactly
   what they match today. Empty: `v4` ended "none" commits only its sidecar and marker. Plants: restore the wide
   glob; put the `v4` part back under the lead rule.
3. **The pack builder (taken over, finished).** `fno/v4_pack/builder.py` and `capture.py` build the pack only from a
   canonical `clock_ok` capture: each field in the pack only if received from 14:30:00 to 14:40:00 inclusive; required
   fields spot, the future of `e` (nearest monthly expiry strictly after `d`), India VIX, `e`'s ATM call and put, IV30;
   `last_trade_time` never an observation time. Good: the fixture capture gives every field with its `observed_at`.
   Bad: no marker, a `none` marker, a missing sidecar or quote file, a clock status other than `clock_ok`, no India VIX,
   no ATM pair: no pack, `system_late` with the reasons named. Boundary: 14:40:00 in, 14:40:01 out, 14:29:59 out; the
   day before a monthly expiry (`e` has 1 day left; IV30 from the other monthly alone, flagged: Monday 26 Oct's case);
   a monthly expiry day (`e` is the next monthly). Empty: a capture with zero valid rows. Plants: `<=` to `<` at the
   window end; drop the clock check; read `last_trade_time` as the observation time.
3a. **The pack holds G7b's inputs.** A4e's `v4` window records, beside the two monthlies, the first listed expiry with at
   least 5 scored sessions in `(d, expiry]` (G7b's pure function `first_v4_expiry(day, listed_expiries, calendar)` in
   `fno/forecast_v4_rules/v4_expiry.py`, imported with that exact signature from G7b's first commit, which merges
   first; special and muhurat sessions not counted) when it is not a monthly, at the same 5% band, and one quote of
   `e`'s future with bid, ask, `last_trade_time` and its `observed_at`, plus NSE's day volume already read; the pack
   carries them (`future.bid`, `future.ask`, `future.last_trade_time`, `future.volume`; the added
   expiry's rows in `chain`) and **a field `v4_expiry`**: the expiry the function chose (a monthly or the added one),
   `None` when it returned `None` (G7b's ask, 24 Oct: without it G7b cannot tell "the chosen weekly's quotes failed"
   from "V4's expiry is the monthly" and would score another question). The capture's sidecar records the same value,
   and the pack copies it from there (never recomputed at release). A chosen expiry whose quotes failed keeps
   `v4_expiry` set with no rows for it: V4 voids itself, the day is not `system_late`. The default 14:55 capture's
   sidecar and rows are byte-identical to today's (a golden test). **Only the `v4` window changes** (orchestrator's
   assignment, 24 Oct): A4's 14:55-15:10 window, A4c's indices and A4f's weeklies, and A4c-2's index alert (merging now)
   keep their code paths and outputs; their existing tests pass unchanged, none edited. Good: a Monday with Tuesday's weekly (1 session)
   takes the next weekly (6 sessions). Bad: the future quote fails: the pack keeps the future without bid and ask
   (V5 then voids itself by its spread rule; the pack is not `system_late`, because V1-V3, V6 and V7 do not need it).
   Boundary: exactly 5 sessions taken, 4 not; that expiry is a monthly: no extra chain, `v4_expiry` the monthly. Empty:
   no listed expiry with 5 sessions: no extra chain, `v4_expiry` `None`. Plants: count sessions in calendar days; the
   expiry rule copied instead of imported; the default capture gaining the future quote; `v4_expiry` dropped when its
   quotes fail; `v4_expiry` recomputed at release.
4. **The release step.** `v4_release` waits for the `v4` part to end, then runs the release: the catch-up writes
   `system_late` for every scored session from `daily.live_from.forecasts_v4` to yesterday with no release record in
   Drive (decision D2); today's pack and record are written once. **Release by 14:45:00** (`V4_RELEASE_BY` in `fno/v4_pack/release_run.py`; code round: not in `terms.py`, which M1's method hash reads,
   decision D1): a record written later is `system_late` ("released late"), so a pack reader always has 10 minutes
   before G11's 14:55 latest fire. The daily run commits the receipts; `v4-pack release` commits them itself only with
   `--commit` (by-hand use), so the run keeps one committer (O1's G4). Today `system_late` is the step's failure with
   one #fno-desk alert naming the reasons (decision D3); a write-once refusal is named, never overwritten. Good: `A`
   released at about 14:35 from a capture that ended about 14:34. Bad: no capture by 14:45, `system_late`. Boundary: a record due exactly at 14:45:00 is `A`, at 14:45:01
   `system_late`; a rerun the same day prints "already released"; a rerun after a failed write retries it. Empty: not
   a scored session, nothing written, ok. Plants: run the release while the part still records; drop the catch-up;
   release at 14:46 as `A`; leave a part running at 14:45 unstopped.
5. **One label rule, one place.** A function in `fno/forecast_scoring/v4/days.py` decides a day's label from its
   record, the live date and the report's date: a record gives its label; a scored session from
   `daily.live_from.forecasts_v4` up to the day before the report with no record is `system_late` ("no release
   record"); today with no record is pending (counted apart, never scored); a day before the live date has no label
   (the close-proxy cohort). The writer's catch-up and the reader use it (DRY), so a missed catch-up changes nothing.
   PROTOCOL_v4.md 1.6 and `days.py`'s docstring say the same; `test_protocol_text.py` checks the label words and
   `V4_RELEASE_BY`. Good, bad, boundary (the live date itself; yesterday; today), empty (no record at all). Plants:
   treat a missing live record as unlabelled; count today as late.
6. **G8 reads the labels from Drive: all three readers re-pointed in this story** (G7b's part e relies on it and does
   not do it again; orchestrator, 24 Oct). `fno/forecast_scoring/v4/wiring.py`'s `build_scoring` (`LateDaysOut`),
   `build_ai_slot_days` (`sessions_not_late`) and `build_day_counts` each read the release records through O9's
   verified Drive cache (`v4/days/<YYYY>/`, synced before every report and look) and criterion 5's label rule, through
   one shared day source built once in the wiring; `V4_DAYS_FOLDER` and `research/data/v4_days/` are deleted (a test
   finds no reference left in `fno/`). A test per reader feeds a `system_late` release record from a fake Drive cache
   and shows the day is out of the scored forecasts and outcomes (`build_scoring`), not an AI slot-day to settle, so
   never an AI miss (`build_ai_slot_days`), and counted as `system_late` (`build_day_counts`). A receipt whose bytes are missing or fail verification stops the report or look with the
   day named, never a report with fewer labels. `postmortem-weekly.yml`, which runs the G8 report, gets the four
   `FNO_GDRIVE_*` settings. Good: two records read. Bad: a tampered record stops it. Boundary: a year folder change
   (31 Dec to 1 Jan). Empty: no receipts yet, no labels, every live day before the report `system_late` by criterion
   5. Plants: swallow a sync problem; read the old folder; re-point only two of the three readers.
7. **The 15:10 deadline verdict.** `python -m fno v4-pack deadline` (the `v4_deadline` step, not before 15:12:00) reads,
   for each scored session from the live date to today without a verdict, every live commitment made by its forecaster
   itself: (i) each row of the CSV records in `research/forecasts/v4/` (G7's rules, M1's weather), GitHub's receipt
   time of the commit that added the row (`CommitmentTimes.row_received_at`); (ii) each receipt under
   `receipts/data/v4/records/live/` (G7b's Drive-stored live records, `v4/records/live/<forecaster>/<question>/<YYYY>/<date>.json`,
   G7b's ask), GitHub's receipt time of the commit that added that receipt (`CommitmentTimes.file_received_at`). Never
   the commit's own time. Which forecasters are excluded is its own set, `SEALED_COMMITMENTS` in `fno/v4_pack/`
   (the two AI books, whose commitment is their sealed submission: out of scope 2), **not** `PACK_READERS`: G7b's V4
   and V5 forecasters read the pack and are checked here like G7's (judge 580 finding 3). It writes one
   write-once verdict file per day, Drive `v4/deadlines/<YYYY>/<date>.json` (forecaster, question, received time,
   `on_time` or `late`). Any unknown time: no file for that day, the step fails with one alert, and the next run retries
   it (never a guessed time). Good: a row received at 14:12 is on time. Bad: received 15:10:01 is late. Boundary:
   15:10:00 on time; a run before 15:12 waits. Empty: a day with no live rows gets a file with no rows. Plants: `<=` to
   `<`; the commit's own date instead of the receipt; an unknown time written as on time; skip the `records/live/`
   receipts; key the exclusion on `PACK_READERS`. **Rehearsal:** the rehearsal's push log (REH1b's
   `rehearsed_receipts`) holds only the rehearsal's own pushes, so in a rehearsal the step checks the replayed day
   only, never the catch-up days (their times are not in that log; checking them would fail every rehearsal).
8. **G8 applies the verdicts.** A `late` row is no forecast that day (a miss under G9's caps); a live row whose day has
   no verdict file is counted "deadline not checked" in the report's counts line, and a confirmatory look refuses while
   one exists (the reconciliation's pattern, response 213). Back-fill rows are never checked. Good, bad (late), boundary
   (exactly at the deadline), empty (no live rows). Plants: score a late row; let a look pass with an unchecked day.
9. **Alerts, settings and the record scan.** Every new alert goes through `AlertSender` to #fno-desk only; no Groww value
   in any repository file, alert or log line (the record scan stays on; the pack and the capture rows are Drive only);
   `daily.live_from.v4_pack` is an allowed key (`fno/config.py`); the CLAUDE.md lines equal the pathspecs in
   `QUOTE_PARTS` (a test). Plants: a pathspec changed in code only; NIFTY's glob widened again in CLAUDE.md only.
10. **Gates and real output.** The full gates; no file or class over 350 lines; independent code-review agents on the
   diff, their findings in Claims; a real output sample made by the committed code (a dry run of the release and the
   deadline on a test store: the lines, labels and counts only, no prices). After merge (quality rule 8): one dry run of
   `v4-pack release` on real data; and the first live day's evidence (the `v4` sidecar beside A16's 14:30 row, the
   release line, the deadline line, the run's last line) in `conversations/<date>.md` and a report to the orchestrator.
11. **The overlap watch (judge 580 finding 2).** `v4_deadline` also reads the day's `v4` sidecar (failures, recorded of
   expected) and A16's 14:30 row (status, failures) and posts one #fno-desk line when either shows any failure, with
   the counts (never a quote value); no line on a clean day. Good: both clean, no line. Bad: two `v4` failures, a line
   naming 2 and A16 good. Boundary: A16's row missing (its routine did not run, as 23 Oct's 14:30): a line "A16 14:30
   mark missing", not a clash. Empty: no `v4` capture (not live): nothing. Plants: post only on A16's failures; drop the
   counts.
12. **Rehearsal (judge 580 finding 1; REH1c: every report runs in a rehearsal).** `v4_pack` goes through
   `rehearsed_live` like every key (it is not in `KEPT_REAL`: no fills or money), so in a rehearsal all three pieces
   run, labelled by `NotLiveInRealRuns` when the replayed day is before the real live date. Each piece's outcome:
   - `v4` part: A4e's recorder is replaced by REH1b's `rehearsed_recorder` (`fno/quotes/window_wiring.py:31`), which
     replays only recorded attempts of `quote-snapshots-v4`. With none (every day before the first live day), it ends
     "window closed" with "rehearsal: no recorded in-window attempt of nifty on <day>" and a `none` marker in the
     dryrun store; with a recorded attempt, it republishes it at its own times.
   - `v4_release`: writes into the dryrun Drive (REH1's `DryrunDrive`, the real record read-only behind it), so its
     catch-up sees the real release records visible at the replay time and writes `system_late` only into `dryrun/`.
     **D3 in a rehearsal:** on a replayed day with no recorded `v4` attempt the outcome is `system_late` but the step
     is **ok** with the line "v4 release <day>: system_late (rehearsal: no v4 capture recorded for this day)", because
     nothing failed: the record has no capture to replay. On a replayed day with a recorded attempt, D3 applies as in
     a real run (a replayed failure is a real one).
   - `v4_deadline`: the replayed day only (criterion 7), against the rehearsal's push log.
   Tests with the mode on (`ENV_FNO_REHEARSAL` set, as REH1's tests): a day with no recorded `v4` attempt ends the
   part "window closed", the release ok with the rehearsal line and nothing outside `dryrun/`; a day with a recorded
   `A` attempt replays `A`; the deadline checks one day. Plants: D3's failure on a rehearsal with no recorded capture;
   the catch-up writing outside `dryrun/`; the deadline checking catch-up days in a rehearsal.

#### Gap list: every requirement of protocol v4 section 1.6

| # | Requirement (PROTOCOL_v4.md 1.6) | Where it is met |
|---|---|---|
| 1 | 14:30:00 the pack's capture starts (spot, future of `e`, India VIX, chains, IV30); an incomplete capture retries | criterion 1 (scheduled); A4e (retries, merged a8e0d2a2); criterion 3 (fields) |
| 2 | 14:40:00 cutoff: a field is in only if received by 14:40:00 | criterion 3; A4e stops requests after the end (`capture_log.py`) |
| 3 | One release, one pack, one SHA-256, every family at the same moment, at the latest 14:40 | criterion 4 (one write-once record per day; release by 14:45:00, decision D1, with the text changed to match) |
| 4 | 15:10:00 deadline on GitHub's receipt time | criteria 7 and 8 for records committed directly; the AI books' commitment is G11's (out of scope 2) |
| 5 | 15:15 common snapshot: the desk's skill yardstick and the flag's end level | flag: on `main` (A16's 15:15 level, stored flag); desk yardstick: E8/E4 (out of scope 5) |
| 6 | Honest times: real `observed_at`, `last_trade_time` apart | criterion 3 (A4e records the times) |
| 7 | A capture whose clock was not checked ok before and after is not used | criterion 3 |
| 8 | Day label `A` / `system_late` (no complete pack by 14:40, or no release record at all), written once after the fact | criteria 4 and 5 |
| 9 | The label on every v4 record and report; a verdict uses `A` days; every report counts both labels and the flagged days | reports: criteria 5, 6 and 8 (counts line); records: joined by day from the release record (decision D4); `A` days only: `LateDaysOut` on `main`, fed by criterion 6 |
| 10 | One pack, one hash: a pack reader names the released SHA; another or an empty one refused; a pre-pack forecaster names none | guard on `main` (`fno/v4_pack/guard.py`, judge 277); **its first pack reader is G7b's `forecasts_v4_pack` (V4 and V5)**: G7b adds its forecaster ids to `PACK_READERS` and calls `check_pack_binding` in its writer, with a test per writer (the guard's opt-in rule, judge 274 add. 1; interface row G7b 5); G11's books are already in the set |
| 11 | Moved after cutoff: flag, never a block; X frozen; not computable without either level | on `main` (A16's rv rows, `RecordedCutoffMoves`); counted per criterion 6's labels |
| 12 | Pack values stand in for the close; live and close-proxy cohorts apart | cohorts on `main` (`story/g10-cohorts` merged); the implied baselines, V4 and V5 that read the pack: G7b (out of scope 3) |
| 13 | Outcomes do not move | no outcome code or file is in this story's diff (the judge checks the diff) |
| 14 | Section 4: a `system_late` day out for every member; a commitment after 15:10 a miss; each label's count reported | criteria 5, 6 and 8 |

#### Out of scope (with reasons)

1. **`v4-fire.yml` and the AI fire on the release push:** its command is G11's round 2b, not on `main`; merging the
   workflow now gives a failing job each day. It stays on `story/g10-part2b-pack`; G11 takes it with its fire.
2. **The AI books' 15:10 deadline:** their record row is written by the collect after the reveal (after 15:10 by
   design), so a row-receipt check would call every AI row late. Their commitment is the sealed submission's push;
   its check is G11's and F8c's timing (`fno/ai/timing.py` still holds v2's 15:15), told to them in the report.
3. **V2's and V3's premium-adjusted baselines, the implied baselines, V4 and V5:** G7b parts b-d; they read this
   story's pack once built.
4. **Slot registrations, `FREEZE_v4.md`, the go-live count:** the freeze commit after the owner's sign-off (response
   157), not code here.
5. **The desk's skill score at 15:15 and money verdict at the 60-minute fill:** E8 and E4 own them.
6. **S1's timetable still saying 15:00 and 15:12** (judge 161 add. 3 note 3): S1's.
7. **A day-label column in G7's record files:** decision D4; adding a column would rewrite 9,636 committed rows for
   no new fact.
8. **A prebuilt fallback start after A16's 14:30 mark:** no evidence of a clash (Groww load section); a one-value
   change if the first live day shows one.

#### Decisions (orchestrator, 24 Oct: D1 and D3 to the owner, D2 accepted, D4 for the builder and the judge)

- **D1 (owner decided 24 Oct (DESK_DECISIONS): "1 - Option A", release by 14:45:00):** "at the latest 14:40" cannot be met literally: the last retry
  may send its request at 14:40:00 and the pack is built after it. Recommend `V4_RELEASE_BY = 14:45:00`, a later
  record `system_late` (reasoning only: the content cutoff stays 14:40:00, no one gets more data, and pack readers keep
  10 minutes to 14:55). Alternative: 14:41:00, which a slow Drive upload can miss on a good day.
- **D2 (accepted by the orchestrator, 24 Oct):** the catch-up and the reader start at `daily.live_from.forecasts_v4` (22 Oct), so 22 and 23 Oct (and Monday
  if this is not live then) are `system_late`. Recommend yes: those days had no pack, which is exactly the
  protocol's definition; all are before the freeze, so nothing counted changes.
- **D3 (owner decided 24 Oct (DESK_DECISIONS): "2 - Option A", a `system_late` day fails `v4_release`):** a `system_late` today makes `v4_release` a failed step (the day ends "day done with problems: v4_release" and
  the card warns, owner's 24 Oct row). Recommend yes: it is a system failure by definition.
- **D4:** the day label reaches each record by its day from the release record, not as a record column; the 1.6 text
  says "on every v4 report, and joined to every record by its day". The builder's design choice, for the judge: one
  source of truth.
- **D1 and D3: owner decided 24 Oct (DESK_DECISIONS)**, both as recommended and as built; the merge no longer waits
  for them. D1 lives in one constant (`V4_RELEASE_BY`, `fno/v4_pack/release_run.py`) and D3 in the
  release step's status mapping, each with its test, so another answer changes only those two places and their tests.

#### Monday 26 Oct: what the live run would and would not do

**Said plainly first:** this text goes to judge B now; code, self-review and judge B's code round follow; no merges
14:00-16:15 IST on session days. A merge before Monday 14:00 is possible only if both judge rounds pass by then, which
is unlikely. So the likely Monday is today's run: no `v4` capture, no release, no deadline check, G7's and M1's
forecasts as on 22-23 Oct. **No `quote-snapshots-v4` capture exists for any day, so nothing can be rehearsed from
recorded data:** the first live day is the first real run, so it is record-only and alerting.

**If merged before Monday 14:00 with `daily.live_from.v4_pack: "2026-10-26"`, the run would:**
- start the `v4` part at about 14:07; it waits, records from 14:30:00 (about 270 Groww quote requests, 3 chain calls
  and 1 future quote, overlapping A16's 14:30 mark until about 14:31:25), commits its sidecar and marker by about 14:35;
- run `v4_release` at about 14:35: write `system_late` for 22 and 23 Oct (catch-up, D2), then Monday's pack and record
  (`A` if complete and `clock_ok`; IV30 from November's monthly alone, flagged, because October's has 1 day left), and
  push the receipts;
- at its end (about 16:00), run `v4_deadline`: verdicts for G7's and M1's live rows of 22, 23 and 26 Oct (they commit at
  about 14:10, so all should be on time);
- alert #fno-desk on a `system_late` Monday, a refused write, an unknown receipt time or a failed capture (A4e's own
  alerts).

**It would not:** fire any AI book (no `v4-fire.yml`); change any G7 or M1 forecast, the desk, Book 1, fills, exits,
the card's content or any order (none exist); count anything (no `FREEZE_v4.md`: every v4 row is uncounted); post to
#fno-forecast or #fno-intraday; change A16's marks, the 14:55 NIFTY, NSE or indices parts, or any 3 pm reader (the
`v4` dataset is apart; criterion 2 keeps the commits apart).

**Depends:** A4e (merged), O9's data store and Drive cache (merged), F1's push receipts (merged), O1 (merged);
**G7b's first commit, `first_v4_expiry(day, listed_expiries, calendar)` in `fno/forecast_v4_rules/v4_expiry.py`, not yet
on any branch (judge 580's re-read at d4e72f20d): it must be pushed, judged and merged before criterion 3a's code; until
then criterion 3a cannot be built, and the other criteria do not wait for it.**
**Touches:** `fno/daily/` (quote_parts, wiring, reason_codes), `fno/constants_operations.py`, `fno/v4_pack/`,
`fno/forecast_scoring/v4/` (days, wiring, a new verdict reader), `fno/v4_pack/release_run.py` (D1's and D3's constants;
`fno/forecast_v4/terms.py` unchanged, code round 1),
`fno/config.py`, `config.yaml`, `CLAUDE.md` (daily routine lines), `.github/workflows/postmortem-weekly.yml`,
`research/forecasts/PROTOCOL_v4.md` (1.6 and section 4), tests. G8's files are touched by this story with the
orchestrator's assignment (G8's builder is out of reach). **Size:** L, built in one branch, judged as one story.
**Status:** story text for judge B.

#### Round 2: answers to judge 580 (read at c876ede53), by number

| Judge 580 | Agreed? | Fix (and where) |
|---|---|---|
| Should-fix 1: rehearsal behaviour | **Yes**, checked: `rehearsed_live` makes every key but `KEPT_REAL` live in a rehearsal (`fno/rehearsal/live_wiring.py:23-30`); `rehearsed_recorder` replays recorded attempts only (`recorded_quotes.py:49-60`); with D3 every rehearsal would end with problems | new criterion 12: each piece's outcome and line; `v4_pack` goes through `rehearsed_live`; D3's failure does not apply to a replayed day with no recorded `v4` capture (step ok, with its line), and does apply when an attempt was recorded; the deadline checks the replayed day only (criterion 7); tests with the mode on; plants listed |
| Should-fix 2: Groww overlap evidence | **Yes**, checked: `nifty_20261022_151500.meta.json` is 176 of 180, four `GrowwAPIException` (ATM strikes) and one `RawFileConflict`; 23 Oct 15:15 clean; A16's rows are good on all three. The 22 Oct 15:00 row is in the repository, `research/data/intraday/slots/2026/10/22/nifty_20261022_1500.csv` (its raw file in Drive, `raw_sha256` in the row), so A16 did run on 22 Oct (the older routine, `conversations/2026-10-22.md:319`); "names a rate limit" was unobservable, removed | Groww load section: all three overlaps in a table, one failing; the trigger is any failure in either job, reported with counts by new criterion 11 |
| Should-fix 3: pack readers | **Yes**: G7b's V4 and V5 read the pack, so they must be bound; keying the 15:10 exclusion on `PACK_READERS` would have exempted them | gap row 10 and interface row G7b 5 name `forecasts_v4_pack` as the first pack reader, brought under `check_pack_binding` by G7b; criterion 7 excludes only `SEALED_COMMITMENTS` (the AI books), its own set |
| Minor 1: 14:45 with the part running | **Yes** | step table: a part still running at 14:45 is stopped (it is hung: no request after 14:40), its files not committed, the day `system_late`; criterion 4 adds the plant |
| Minor 2: build with D1 and D3 recommended | **Yes** (orchestrator's answer, 24 Oct) | Decisions: built and judged with the recommended values; only the merge waits for the owner |
| Minor 3: criterion 4's 14:33 | **Yes** | criterion 4: `A` released at about 14:35 from a capture ended about 14:34 |
| Minor (re-read at d4e72f20d): `first_v4_expiry` defined on no branch yet | **Yes**, checked: no `def first_v4_expiry` on `story/g7b-completion` | "Depends" names it as G7b's first commit, merged before criterion 3a's code |
| Plants to add | **Yes** | criterion 9 (NIFTY glob widened in CLAUDE.md only), criterion 12 (rehearsal) |

**Covered by my commits after c876ede53 (not read by judge 580):** 2f508ae15 (the `v4`-window changes in `fno/quotes`
assigned to this builder, A4's other behaviour unchanged, criterion 3a); e5626aabf (criterion 6 re-points all three G8
readers, a test each); d4e72f20d (`v4_expiry` in the pack). **Also in this round, from G7b (relayed by the
orchestrator):** (a) the 15:10 verdict covers `receipts/data/v4/records/live/` (criterion 7 (ii)); (b) the pack's
future carries `last_trade_time` and `volume` for A4's `traded_today` (interface row G7b 3, criterion 3a): correct,
`FutureQuote` on `main` (`fno/v4_pack/model.py:27-34`) has neither, and `7cab92b06` passes volume only to IV30.

**Claims (code round 1, 24 Oct 2026; builder session_011hvvn9CahAD5dCPHS3kowN).**

*Changes against the passed text (said plainly; each checked by its test):*
1. `V4_RELEASE_BY` lives in `fno/v4_pack/release_run.py` beside D3's `SYSTEM_LATE_FAILS`, not in
   `fno/forecast_v4/terms.py`: that file is in M1's `METHOD_FILES` (`fno/weather/wiring.py:31`), so a constant there
   moved every committed weather record's method hash (`tests/weather/test_method_hash_gate.py` failed; `terms.py` is
   now byte-identical to `main`: `git diff origin/main -- fno/forecast_v4/terms.py` prints nothing, and that gate
   passes again).
2. `v4_deadline` runs right before `candles`, not last: A4h's reads stay the run's last two steps
   (`tests/close_read/test_daily_steps.py`, unchanged); 15:12 is before 15:33.
3. The `v4` part starts at 14:27 (O1's 3-minute margin before 14:30), never before A4e's early limit (14:03): a
   rehearsal runs at real speed while a recorder runs (REH1), so 14:03 cost about 25 minutes per rehearsal.
4. A part not live on the day is not a part of that day (no result, no start); the steps sharing its key record
   `not_live`. So every reader of the parts' results, and the e2e suite, is unchanged.
5. The release waits for an ended capture until 14:45 (not 14:40): a hand run while the recorder may still write its
   marker never settles the day; a capture not ended by 14:45 is `system_late` ("capture still running at 14:45").
6. The future's quote is a `FUT` row in the attempt's Drive-only quote file (a Groww value never enters the committed
   sidecar, A4b); the sidecar names only `v4_expiry`, `v4_expiry_note`, `v4_failures` and `future_quote` (no value).
7. The deadline's catch-up starts at `daily.live_from.forecasts_v4` (as the release's), and a look is refused only by
   unchecked days after the freeze that are not `system_late` (self-review finding, below).

*Criteria (code, tests; the planted break each test catches):*
| # | Code | Tests | Plants caught |
|---|---|---|---|
| 1 | `fno/daily/v4_part.py`, `quote_parts.py` (`live_key`, `_open`), `v4_wiring.day_parts` | `tests/daily/test_v4_part.py` | default window; live key ignored |
| 2 | `quote_parts.py` (`apart`, `NIFTY_QUOTES`), CLAUDE.md 3 and 3c | `test_v4_part.py` (real git), `tests/quotes/test_routine_commit_paths.py` | wide glob in code; wide glob in CLAUDE.md only; lead rule |
| 3 | `fno/v4_pack/builder.py`, `capture.py` (taken over) | `test_pack_builder.py`, `test_pack_builder_cases.py`, `test_stored_capture.py` | `<` at 14:40; clock check dropped |
| 3a | `fno/quotes/capture_extras.py`, `v4_extras.py`, `future_quotes.py`, `window_wiring.py`, `recorder.py` (3 lines); `model.py`, `codec.py`, `builder.py` | `tests/quotes/test_v4_extras.py`, `tests/v4_pack/test_pack_g7b_fields.py`, `test_cli.py` | `v4_expiry` dropped; CalendarError raised; extras counted; a monthly fetched twice; recomputed at release; FUT in chain; late quote used; note not alerted; window without extras |
| 4 | `release_run.py`, `cli.py`, `quote_steps.AfterPart`, `quote_parts.await_part` | `test_release_run.py`, `test_release_rules.py`, `test_v4_part.py`, `test_cli.py` | release at 14:46 as `A`; no catch-up; hung part not stopped; D3 ignored |
| 5 | `days.missing_label`, `LiveDayLabels`, release catch-up; PROTOCOL_v4 1.6 | `tests/forecast_scoring_v4/test_release_days.py`, `tests/forecast_v4/test_protocol_text.py` | missing live day unlabelled; today counted late |
| 6 | `drive_records.py`, `release_days.py`, G8 `wiring.py`; `postmortem-weekly.yml` | `test_release_days.py`, `tests/learning/test_boundaries.py` | sync problem swallowed; two of three readers |
| 7 | `commitments.py`, `deadline.py`, `cli.py` | `tests/v4_pack/test_deadline.py` | `<` at 15:10; unknown time not handled; live receipts skipped; exemption keyed on `PACK_READERS` |
| 8 | `deadlines.py`, G8 `cli._look` | `tests/forecast_scoring_v4/test_deadlines.py`, `test_release_days.py` | late row scored; look passes unchecked |
| 9 | `reason_codes.py`, `constants_operations.py`, `config.yaml`, CLAUDE.md | `tests/daily/test_v4_steps.py`, `test_v4_part.py`, the reason-code tests | (with 2) |
| 11 | `overlap.py`, `cli._deadline` | `tests/v4_pack/test_overlap.py` (fixtures and the real 23 Oct `missed` row; a missing row) | only A16's failures |
| 12 | `fno/rehearsal/v4_pack.py`, `v4_wiring.step_notes/part_notes` | `tests/rehearsal/test_v4_pack.py`, `test_not_live_reports.py`, `test_rehearsed_day.py` | excuse always; catch-up in a rehearsal |

34 planted breaks, all caught (one first survived each in criteria 7 and 3a; their tests were strengthened).

*Existing tests edited, and why (none loosened):* `tests/daily/test_day_run.py`, `test_steps.py`,
`tests/health/test_desk_and_data_checks.py` (the step tuple and live dates now hold the two steps and the key);
`tests/quotes/test_routine_commit_paths.py` (NIFTY's narrowed glob, criterion 2); `tests/learning/test_boundaries.py`
(the four Drive settings, criterion 6); `tests/rehearsal/test_not_live_reports.py`, `test_rehearsed_day.py` (one key's
note on two steps); `tests/e2e/harness.py` (the `v4` part scripted for a rehearsal), `tests/e2e/test_hangs.py` (its hang
now starts after `v4_release`, the last step before the desk waits); the taken-over `tests/v4_pack/test_release_run.py`
(the fake capture's `ended`, the 14:45 wording).

*Self-review (two independent review agents, 24 Oct):* pack and G8 side: two blocking findings, both real and fixed
with tests (a row committed after its day's check was scored and blocked looks for good: now late; rows before the
release's live date never got a verdict: the catch-up starts with the labels, `system_late` and pre-freeze days never
block a look); fixed: an unreadable record line names the file and the day is retried; a hand release waits until
14:45. Rejected with evidence: "two rows, one verdict key" (G7's `records.py:90` refuses a second row for a day).
Daily side: nothing blocking; fixed: the wait for the part is announced (O1-day-lock), another step's rehearsal note
never reaches NIFTY or NSE, an adopted part is held (F1's `STILL_HELD`), the part starts at 14:27 (rehearsal speed);
left as is: a stopped capture's files taken by a same-day rerun's marker check, NIFTY's existing behaviour (low risk).

*Real output sample* (the committed code on fixture stores, no Groww or Drive; lines and counts only):
```
$ python -m fno v4-pack release   (22 Oct 14:35, live from 22 Oct, labels from 19 Oct)
v4 release 2026-10-19: system_late (catch-up: no release record in Drive)
v4 release 2026-10-20: system_late (catch-up: no release record in Drive)
v4 release 2026-10-21: system_late (catch-up: no release record in Drive)
v4 release 2026-10-22: A [exit 0]
$ python -m fno v4-pack deadline  (22 Oct 15:15; checks from 21 Oct; one row pushed 15:10:01)
v4 deadline 2026-10-21: 2 on time, 0 late
v4 deadline 2026-10-22: 0 on time, 2 late [exit 0]
$ G8 report counts line (as of 23 Oct)
days (live pack): A 1, system_late 3 (out for every family), pending 1; moved after cutoff 0, flag not computable 4; deadline not checked 0
```

*Open:* D1 and D3: owner decided 24 Oct (DESK_DECISIONS), as built. After merge: one dry run
of `v4-pack release` on real data, and the first live day's evidence (criterion 10).

**Claims, round 2 (judge 584, the last round; builder session_011hvvn9CahAD5dCPHS3kowN).** Every finding fixed, each
with its test and a planted break that the test catches (10 planted, 10 caught; one first survived, B1, its test made
stronger).

| Judge 584 | Fix | Test | Plant caught |
|---|---|---|---|
| B1 merge conflict | `origin/main` merged (3782758b8): the scheduler keeps main's O1 DRY2 (`earliest_start(window_start)` over A4's shared `earliest_waiting_start`, `INDEX_EARLIEST_START`, `_waited_for`/`_due`, `service()` calling `start_due()`) together with this story's `_open`/`_live` (a not-live part is no part of the day), `apart`, `await_part` and `waits_for`. **The resolved scheduler (`fno/daily/quote_parts.py`) is new lane-1 code, for judging.** The `v4` part's early limit is A4's one early-limit rule (`earliest_waiting_moment`, the function main's `earliest_waiting_start` is built on) with the window's own 30-minute wait plus O1's margin (`fno/daily/v4_part.py` `_shortly_before`: the later of 14:27 and that limit, 14:03 today; no second early-wait rule). Not main's 20-minute `earliest_start`: that is A4's default window's wait, not this window's (self-review: a window with a 2-minute wait would have started too early and recorded nothing) | `tests/daily/test_v4_part.py` (the start stays 14:27; a 1-minute wait moves it to 14:32), the merged O1 tests | the part's own rule instead of the shared one |
| SF1 overlap misses the extras | `fno/v4_pack/overlap.py` `_failures`: A4's `failures`, the extras' `v4_failures` and a `future_quote` other than `recorded` or `no monthly after the day` | `tests/v4_pack/test_overlap.py` (the judge's case: 30 `v4_failures`, a failed future quote, A16's row good: an alert naming 31 failures; all recorded: no line) | extras' failures ignored; future failure ignored |
| SF2 extras before the required fields | `fno/quotes/recorder.py`: the extras run after NSE's levels and every monthly quote (`found` holds the expiries; asked only when the monthlies' chains came) | `tests/quotes/test_v4_extras.py` (extras taking 15 minutes: levels first, every monthly quote answered before the extras start, the attempt complete) | extras asked first |
| SF3 "last, v4's deadline check" | CLAUDE.md "Daily desk routine" step 2 and the story's step list now give the code's order (the check from 15:12, before the candles; A4h's reads last). CLAUDE.md is a rule document: this only corrects its step order to match the code and narrows nothing, so it stays in G10's lane-1 change | `tests/daily/test_v4_steps.py` (CLAUDE.md's order equals the code's) | CLAUDE.md saying "last" again |
| m1 stale text | the story's decisions bullet and Touches line name `fno/v4_pack/release_run.py`; `release_run.py`'s D1 and D3 comments say "owner, 24 Oct 2026, DESK_DECISIONS" | read | |
| m2 release-by before the write | `fno/v4_pack/release.py` `publish(..., in_time)`: the release-by time is asked after the pack's upload, right before the small record; an upload ending after 14:45:00 writes `system_late` ("released late") and leaves the pack unreleased (write-once, named by no record). Said plainly: the record's own write (a few hundred bytes) can still end just after 14:45:00; that residue is not checked | `tests/v4_pack/test_release_rules.py` (an upload started 14:44:59, ended 14:45:30: `system_late`, no pack path, the step failed) | the check before the upload only |
| m3 a row from another session | stated plainly in `fno/v4_pack/commitments.py` and `fno/forecast_scoring/v4/deadlines.py`: the check reads this run's checkout at 15:12 or later; every G7, M1 and G7b live record is committed from that checkout today; a forecaster committing from another session must be in it by then or its row counts late. G7b and G11 are told; reading `origin/main` instead is a later change | read | |
| NIFTY-glob plant caught only by literals | a test with git alone: NIFTY's part's own pathspec stages a `quote-snapshots/` sidecar and never a `quote-snapshots-v4/` one | `tests/daily/test_v4_steps.py` | glob widened in code |
| Round-2 self-review (an independent agent) | (a) the early limit above; (b) `found` is set before the chain calls, so a later chain failing never hands the extras empty expiries (it wrote "no monthly after the day", which the overlap watch read as no failure); (c) the extras' sidecar keys come only from an attempt that asked them (an attempt with no chain carried the previous attempt's `future_quote` and `v4_failures`) | `tests/quotes/test_v4_extras.py`, `tests/daily/test_v4_part.py` | `found` after the loop; an earlier attempt's keys; the window's wait ignored |

---

## G11. AI books on the v4 questions: books 2 and 3 forecast like the rules and are scored by G8 the same way

**Repository:** trading · **Lane:** 1 (forecast records, a new registered prompt version, the AI books' fire) · **Name
note:** called G10 in REPLAN until story G10 (the v4 timeline) took the name.

**Description:** As the statistician and the owner, I want the Hybrid book (Book 2) and the AI team (Book 3) to answer
the same protocol v4 questions as the rule forecaster on the same day, the same pack and the same deadline, scored by
G8 with the same metrics and miss rule, so that the AI team builds an honest record before it may trade, and a failed
AI run shows as a miss, never as a gap.

**Context and why:**
- Design v2 7 (`docs/design_v2/07_ai_team.md:10-12`): "there is no evidence yet that the AI books forecast better than
  the baselines"; every AI role earns its cost on the record. Books 2-3 trade only from the first approved strategy or
  rung-2 idea; until then they forecast and are scored (`docs/DESK_DECISIONS.md`, 15 Oct).
- Protocol v4 already names them: the family has a `hybrid` (Book 2) and an `ai_team` (Book 3) slot beside `rules` on
  each member question (`research/forecasts/PROTOCOL_v4.md:225-228`); each slot holds "the first forecaster version
  registered in the ledger for it before its first counted v4 forecast".
- Today the books answer only v2 (Q1-Q5, prompt v1, `fno/ai/versions.py:90-95`) and write
  `research/forecasts/ai_v1/`, which G8 does not read. No v4 path exists for them.
- Real record so far (strong evidence, the audit files): 14 Oct both books `no_submission` (fired at 19:27 IST);
  15 Oct both `late` (commitments received about 12 s after v2's 15:15 deadline). No on-time AI day yet.
- Decision row 16 Oct (`DESK_DECISIONS.md`, "R3, G11, O2 ... start in parallel"): story text now, code after the v4
  freeze (about 22-23 Oct), within BG1's budget cap.

**Scope.** In: a v4 prompt version per book; the books' v4 answers as G7-schema records in G8's folder; their slot
registration; the outcome-to-status mapping (every failure a miss); the audit gate on v4 rows; the self-timing record
BG1 asks for. Out: any trading by the AI books (full F1 isolation, F1); G8's scoring code, including the look's refusal below
(the A16/G8 builder, before the freeze, agreed 16 Oct); the
v4 pack and its 14:30 capture (G10); any workflow schedule (its owner); new questions.

**Expected design** (reuse, no second version of anything):
1. **Questions:** each book answers exactly the questions the `rules` slot answers that day, read from G8's started
   set: at the freeze V6a and V6b (decision 16 Oct: "v4 freezes with V6a/V6b"); V1 when A16 is ready; V2-V5 when G7
   phase 2 builds them. One list, never a separate AI list.
2. **Prompt versions:** `agents/forecast/book2_hybrid_v2.md` and `book3_ai_v2.md`, registered in `fno/ai/versions.py`
   as new versions (a prompt "changes only as a new version"); same model; same label form
   `book/v2/sha256:.../isolation:sealed_same_day`. Book 2 keeps the rules' numbers in its pointer, Book 3 does not.
   BG1's self-timing record (`fno/budget/self_timed.py`, the change `BG-budget.md:102-104` left open) is written by
   `brief` and `reveal` themselves (story F8c, its owner's; response 258 addendum 1), so no prompt step is needed.
3. **Fire and collect:** F1/G5's existing firer, seal, reveal and outcome code (`fno/ai/fire.py`, `seal.py`,
   `outcome.py`, `scoring_gate.py`), pointed at the v4 pack: fired after the pack's release (about 14:32, at the latest
   14:40); the commitment must be **received by GitHub by 15:10** (G10, `fno/forecast_v4/terms.py` `V4_DEADLINE`);
   reveal after 15:10. Fired once, never retried (as today). The timing constants come from `terms.py`, not a copy.
4. **Records:** G11's own writer (G7's `records.record()` stamps G7's version, so it is not reused) writes
   `research/forecasts/v4/book2_hybrid_v2/<question>.csv` and `research/forecasts/v4/book3_ai_v2/<question>.csv`
   (one folder per registered version, named as item 6 registers it, because G8's reader and the look's
   reconciliation find a slot's rows by its registered forecaster's folder; a later version writes its own folder and
   never fills the slot of the first, response 272 addendum 1) in G7's
   schema (`fno/forecast_v4_rules/records.py`: `day, value, status, label, forecaster_version, kind, slot,
   method_sha256, inputs_sha256, made_at`), `label=live` always (AI answers have no back-fill; G10's cohorts), `slot`
   `hybrid` or `ai_team` (`fno/constants.py` `V4_SLOT_HYBRID`, `V4_SLOT_AI`), `kind=ai`, `method_sha256` the prompt's
   hash, `inputs_sha256` the hash of the book's own inputs (the pointer it was given), and the released pack's hash in
   the `pack_sha256` column G10 part 2 adds for every family, with its "another pack is refused" check (the exact name
   comes from G10). Written once (`records.write` raises `RecordConflict` on a different row). G8 finds the folders
   itself (`fno/forecast_scoring/v4/inputs.py:106-107`) and reads a value only when `status == ok`.
5. **Every failure is a miss:** each session day from the slot's `effective_start`, each book writes one row per
   question, once its scoring gate has settled (a written row can never change, so a row is never written while its
   transcript audit is pending; until then the day has no row and G8's reports show it as a provisional miss, which
   disappears when the row lands, because G8 recomputes every report from the files). G11's output prints "N days
   awaiting audit". On `on_time` with no breach: `status=ok` and the value. Otherwise value empty and status one of
   `late`, `not_fired`, `no_submission`, `not_revealed`, `invalid`, `model_mismatch`, `exposed`, `breach`,
   `stopped` (two breaches in 20 days, `stop_rule.py`). G8 counts any non-`ok` status as no forecast, so it is a miss
   under the 10% caps; past the caps the slot is "undecided, operations" (`PROTOCOL_v4.md:251-257`). A `system_late`
   day (G10's day label) is out for the AI slots as for every family.
6. **Registration:** FREEZE_v4's ledger row registers only `rules` for V6a and V6b (response 157). After the freeze,
   G11 appends its own rows: `book2_hybrid_v2` for `hybrid` and `book3_ai_v2` for `ai_team` on each started member
   question, each before the slot's first counted forecast and with an `effective_start` no later than the slot's
   first eligible session (the ledger adapter refuses a later one, judge 184); misses count from it (decision 16 Oct).
   V7, when it starts, is a member that is never judged (`terms.py` `DESCRIPTIVE_ONLY`).
7. **Looks: reconcile before a confirmatory look** (ChatGPT review 127, response 213; a look is recorded once,
   `LookRecords`, and would keep a false miss). G11 guarantees that collect writes exactly one v4 row for every
   scheduled session day of each registered AI slot and started question from `effective_start`, whatever the
   outcome (ok, or a definitive miss status: `not_fired`, including days the fire never ran and BG1 stops,
   `no_submission`, `late`, `not_revealed`, `invalid`, `model_mismatch`, `exposed`, `breach`, `stopped`), and only once
   the day's audit gate has settled. Before recording a look on date L, G8 checks every registered `hybrid` and
   `ai_team` slot: each scored session from its `effective_start` to L, `system_late` days excepted, has a row; any day
   without one refuses the look, naming the count and the earliest day. That covers an open audit, a sealed commitment
   never collected and a collect that never ran. Built by the A16/G8 builder in `fno/forecast_scoring/v4/` before the
   freeze (agreed 16 Oct, response 202 addendum 6); it replaces their earlier `open_audits.csv` gate, which this rule
   makes redundant, so G11 keeps no such file. G8 reads only the record files it already reads, never G11's code.
8. **Composition:** wired in `fno/ai/wiring.py` and `book_wiring.py` only.

**Settled before code (16 Oct; response 202):**
- With the A16/G8 builder: **agreed 16 Oct** (response 202, addendum 1): rows written after the gate settles (a
  `pending_audit` status cannot work, since a written row never changes); G11 adds its own registration rows after the
  freeze; its own writer; the pack hash in G10's new column.
- **The owner chose A** (`DESK_DECISIONS.md`, 16 Oct, "G11: at the v4 freeze the AI books' v4 run replaces the v2
  AI run"): one run cannot serve both (v2's pack lands after v4's 15:10 deadline), so from the freeze the books fire
  for v4 only and the v2 AI capture stops (its record, no on-time day, stays as it is).
- **`fno/ai`:** this builder owns `fno/ai`'s v4 changes for G11 (orchestrator, 16 Oct; its only earlier builder,
  session 01AGpndRQcLERm1xLMNb3Tmj, is not active).
- **Prerequisite, `forecast-capture.yml`:** moving the AI fire step after the v4 pack's release is a workflow change
  owned by G10's capture owner, the A16/G8/G10 builder (session 01VK88LxJvV1Gi7Wbr3D4fzp); G11's code does not run
  live until that change is merged. Agreed 16 Oct (response 202, addendum 4), with no new or moved schedule: the fire
  runs on the push that lands the released pack (`research/data/v4_days/<date>.json` and the pack's sidecar), with a
  latest start of 14:55 IST (`V4_LATEST_FIRE` in `fno/forecast_v4/terms.py`, G10 part 2; a later start is a recorded
  `not_fired` miss, never a late fire); collect and audits-due keep `forecast-capture.yml`'s existing slot, re-pointed
  to v4; the v2 AI steps are removed at the freeze. The CLI stays `ai fire` and `ai collect`. A push made with an
  Actions run's own token starts no workflow, so the pack's commit must come from the routine's own credentials.

**Claim scope (ChatGPT review 127, response 213):** a better Book 2 score means "the hybrid improves on its frozen
baseline", never "an independent AI found the same skill": Book 2 sees the rules' value, so Book 2 and the rules are
not independent observations when counting the family's sample size. Book 3, without the rules' value, is the
independent comparison.

**Daily AI cost against BG1's cap:**
- BG1's cap is minutes, not rupees: the books' and roles' minutes at most 50% of all measured session minutes in the
  month until December 2026 (`config.yaml` `budget`), then 50% of the owner's plan minutes; alert at 80%, stop at
  100%; the plan costs Rs 20,000 a month.
- No book run has been measured yet (`accounting/ai_usage.csv` has no book row). The one data point: on 15 Oct each
  book's commitment came about 5 minutes after the fire (15:10:20 to 15:15:12-15). Some evidence, one day.
- Estimate (reasoning only): 2 books x 5-10 minutes = 10-20 minutes a session day, about 220-440 minutes in a
  22-session month, the same number of runs as today's v2 run (option A: v4 replaces v2).
- This story makes the number real: the v2 prompts write BG1's timing record, so BG1 measures it from the first day.
  G11's output reports runtime p50 and p95 by question set from day one; a run past 15:10 is late; no second runtime
  cap (BG1's cap is enough, ChatGPT review 127).
  At BG1's `stop`, AI forecasters stop last (design 7.6); a stopped day is written as `not_fired`, so it is a miss.

**Acceptance criteria:**
1. The books answer exactly the `rules` slot's questions for the day (same list); a question the rules do not answer
   is never asked.
2. A fixture day with both books on time writes one `ok` row per question in G7's schema, `label=live`, the right
   slot, the prompt hash and the released pack's hash; G8 scores them with the rules' metric.
3. Each failure outcome (late, not fired, no submission, not revealed, invalid, model mismatch, exposed, breach,
   stopped) writes a non-`ok` row and G8 counts it a miss; a day past 10% makes the slot "undecided, operations".
   No outcome leaves the day without a row.
4. A commitment received at 15:10:01 is `late`; at 15:09:59 it is on time, decided by G10's receipt-time check
   (reused, not copied).
5. A pack hash other than the released one is refused; a `system_late` day is out for the AI slots.
6. A day whose audit is pending has no v4 row and is printed in "N days awaiting audit"; once settled, its v4 row
   lands and G8's recomputed report shows it scored or missed. Every settled AI slot-day has exactly one v4 row per
   started question, including `not_fired` days. (The look's refusal on a slot-day without a row, for example a sealed
   commitment never collected, is the A16/G8 builder's test.)
7. Each run writes BG1's timing record; BG1's meter shows the book minutes; G11's output shows runtime p50 and p95
   by question set.
8. No AI answer ever gets `label=backfill_exploratory`; no AI row exists before the slot's `effective_start`.
9. Gates: pytest, ruff, ruff format, the import check; no file or class over 350 lines.

**Test plan:** fixture days for each outcome; a G8 run over the fixture rows (score and miss counts); the 15:10
boundary; the pack-hash refusal; a dry run of one real day's fire and collect after the freeze.

**Judge verifies:** a failed-run fixture shows as a miss in G8's report, not a gap; the AI rows use the same pack and
deadline as the rules; no second firer, sealer or record format.

**Known limits:** the routines still have the repository and the network, so the label stays "sealed same day (not
full F1)" and these forecasts never decide a trade (owner's condition 3, 14 Oct); with no on-time day yet, the 10%
miss cap may make an AI slot "undecided, operations" early, which is an honest result, not a fault.

**Depends:** G6 freeze, G8 (merged), G9 (merged), G10 (the v4 pack and clock, and the `forecast-capture.yml` fire
step), the A16/G8 builder's look reconciliation, G5, BG1 · **Size:** S-M ·
**Status:** story text for the judge (`reviews/claude/response_202_g11-ai-books-v4.md`); code after the v4 freeze

### G11 completion (stage 1 text, 24 Oct 2026; round 2 after judge 579; builder session_01Rga1fe3C4rmnrmmE1p3diE)

**Why now:** the owner, 24 Oct: "let's close v4 full first ... no partial implementation" (`DESK_DECISIONS.md` row
"Close v4 in full first"). The 24 Oct audit found the AI books missing from v4. G11 makes Book 2 (Hybrid) and Book 3
(AI team) answer v4's questions as scored records: **10 of the family's 15 slots** (`terms.FAMILY`: V1, V2, V6a, V6b,
V7, each with `rules`, `hybrid`, `ai_team`). The earlier builder (013xqaNT) is out of reach; the orchestrator gave G11
to this session, and with it step 7 and round 2c (F1t's owner out of reach; register row, fee2fd8e). **Lane 1**
(forecast records, a registered prompt version, outside services: the routines' triggers, Drive, a workflow). **Not
a money piece** (one judge; judge 579 note 1 agrees): no G11 output is read by any decider; C15 pins that, and C8
can only stop AI runs, never enlarge a trade.

**What is done** (strong evidence: the commits and tests named; nothing of it runs live):
- On `main`: round 1, `fno/ai/v4_rows.py` (judge 275 PASS, 7c1a9734), switched off (no caller).
- On `story/g11-ai-books-v4` (312eb791; 16 own commits, round 2b, **never judged**; conflicts with `main` only in
  `docs/WORK_REGISTER.md`): the v4 input (`v4_input.py`, `v4_book_inputs.py`), the 64 KiB pointer (`v4_pointer.py`),
  prompts v2 registered as protocol-v4 versions (`agents/forecast/book*_v2.md`, `versions.py`), `ai fire --protocol
  v4` (`v4_fire.py`), `ai collect --protocol v4` (`v4_collect.py`, `v4_settle.py`, which already prints "N day(s)
  awaiting audit"), one `RunTerms` per protocol threaded through F1/G5's chain (`run_terms.py`, v2 the default), rows
  in `v4/book2_hybrid_v2/` and `v4/book3_ai_v2/` checked by `check_pack_binding`, the stop rule as a structured flag,
  the own go-live key `daily.live_from.ai_books_v4` (null) and the v2 AI fire stopping on the same date. Claims:
  `reviews/claude/response_282_g11-round-2b-v4-fire-collect.md`.

**What is left** (each a criterion below):
1. **All five questions.** Prompt v2 defines only V6a and V6b (`versions.V4_AI_QUESTIONS`), but the rules slot answers
   all five (`research/forecasts/v4/`: `v1_close_blend`, `v2_close_blend`, `v6_ewma_t4`, `v7_vix_vs_mean20`). Story
   item 1 says one list, so prompt v2 gains V1, V2 and V7 (v2 is not on `main`, so its hash changes in the same
   commit; after merge any change, `w` included, is a v3 and never a member, protocol 5.6).
2. **Point answers (V1, V2)** in each question's own measure (C2): today's answer check, envelope and prompt are
   probability-only (`envelope.py` bounds inside [0, 1]).
3. **Inputs for V1 and V2** in their own measures (C4).
4. **Hybrid's envelope** (C3). Measured on `main`'s back-fill (strong evidence, 1,908-1,912 days, 2019-01-14 to
   2026-10-23): the built rule "primary baseline +-0.10" holds the rules slot's own value on 94.4% of days for V6a,
   **55.5% for V6b** and 96.7% for V7 (p95 of the gap 0.113, 0.438, 0.091). So as built, Hybrid could not even repeat
   the rules' V6b answer on almost half the days. The envelope is redesigned in C3.
5. **Step 7, the book side:** `brief` reads the v4 pointer; `seal` and `reveal` use `V4_TERMS` (the code still waits
   for 15:15:10, `timing.py:13`).
6. **The reveal wait.** Fired at about 14:41, a book's commitment reaches GitHub 35-309 s after its fire (the v2
   record: fire log `fired_at` against the audit's GitHub `commitment_received_at`, 9 book-days 16-23 Oct), so about
   14:42-14:46, and `reveal` then waits until 15:10:10, about 24-28 minutes, in one call (`book.py:94-97`) under the
   prompt's 600,000 ms (10-minute) Bash timeout (`book*_v2.md:64`). Every day would end `not_revealed`, a miss (C6).
7. **Round 2c:** the stop rule and the weekly audit draw count v2 days only; until fixed every on-time v4 day stays
   "awaiting audit" (never scored) and a v4 book can never be stopped.
8. **`pack_sha256` in every row** (R2/G7's column is on `main`: `records.py:44`).
9. **BG1's stop:** nothing reads BG1's signal before a fire (`grep stop_ai_roles fno`: written `budget/signal.py:53`,
   read only by `learning/writer.py:49`), yet story item "Daily AI cost" says a stopped day is `not_fired`.
10. **Slot registration:** 10 rows in `research/forecasts/v4_slots.csv` (the file does not exist yet), in the order
    of C13.
11. **O11's replay check:** the strict xfail
    `tests/e2e_acceptance/test_expected_missing.py::test_the_ai_books_answer_the_v4_questions_on_the_recorded_day`
    becomes a real check.
12. **Workflows:** `v4-fire.yml` (held on `story/g10-part2b-release` and `story/g10-part2b-pack`, judge 282.3) lands
    with G11's fire; `forecast-capture.yml`'s collect gains `--protocol v4`.
13. **The routines' stored prompt** says "sealed by 15:15:00 IST" (`docs/stories/F1-G5-owner-checklist.md:48`);
    v4's deadline is 15:10:00. The owner owns the routines; exact text under "Owner step".
14. Merge `main` into the branch (first code commit; `main` is 2,743 commits ahead of 312eb791 on 24 Oct).

**Acceptance criteria.** Each names its code, a test that fails when that code is broken, and its good (G), bad (B),
boundary (Bd) and empty (E) cases; P is the planned plant the judge can reuse.
- **C1 Same questions.** Each book is asked exactly the rules slot's started questions of the day (`v4_slots.csv`'s
  rules rows and G8's started set: one list); prompt v2 defines all five. G: five asked. B: a registered question
  the prompt does not define is a logged `not_fired` with one alert. Bd: a question started on `d` is asked from `d`,
  not before. E: no started question, nothing fired, one line. P: drop V7 from prompt v2's list.
- **C2 Answer form, by measure** (protocol 1.1-1.2; named the same way in prompt v2). V1: the intraday `RV_s` of
  `d+1` (A16's squared overnight log return plus the 25 intraday squared log returns, "quote-snapshot realised
  variance"). V2: the sum of `close_proxy` `RV_s` over `d+1..d+5` (squared close-to-close log returns of the official
  closes). Both are variances (dimensionless, not volatility points), finite and strictly positive. V6a, V6b, V7: a
  probability in [0, 1]. `null` is "no forecast" (a miss, never imputed). G: V1 0.00008, V2 0.0004, V6a 0.12. B: 0,
  a negative, NaN, a probability for V7 above 1; a V1 or V2 value above 1 (a 100% log move squared) is refused as a
  unit error (volatility points given for a variance). Bd: V1 exactly 1 accepted, 1.000001 refused; probabilities
  exactly 0 and 1 accepted. E: a question with no answer is `invalid` for that question only. P: accept 0 for V1.
- **C3 Hybrid's envelope** (redesigned, reasoning only, fixed in prompt v2 and `versions.py` before merge, so no
  value is set after merge). The day's span is from the lower to the higher of the rules slot's value and the
  primary baseline's (either alone when the other has none), widened by `w`: probability questions (V6a, V6b, V7)
  `w = 0.10` absolute, clipped to [0, 1], the built width; point questions (V1, V2) `w = 0.25` relative (low x 0.75 to
  high x 1.25). So Hybrid can always repeat either number, which item 4 shows the built rule cannot. The primary
  baseline is the one G8 uses for that day, `eligibility.primary_baseline(question, eligible, intraday_started)`
  (V1: HAR daily, then HAR intraday one way from its first eligible date), never `terms.PRIMARY_BASELINE` directly.
  V2's primary (premium-adjusted implied, G7b part b) needs no measurement for `w`, so its path is the same rule;
  until G7b's baseline exists the V2 day is not baseline-observable (protocol 4: no score, no miss), and Hybrid's
  span is the rules' value alone. No rules value and no baseline: no envelope, Hybrid answers "no forecast", no miss.
  G: an answer at the span's widened edge accepted. B: outside, refused for that question. Bd: V6b with rules 0.30,
  baseline 0.70: bounds 0.20-0.80; V1 after HAR intraday's first eligible day uses HAR intraday, and a later day
  without it has no primary (never falls back to HAR daily). E: neither value, no envelope. P: build the span from
  `PRIMARY_BASELINE` (V1's switch lost).
- **C4 Inputs, by measure, no look-ahead.** Book 3 gets no rule or baseline value (key test). V1's history: A16's
  committed intraday `RV_s` of the sessions before `d`, a void session shown as void (never filled). V2's history:
  the `close_proxy` `RV_s` of the last 260 sessions before `d`, computed by the code from the official closes it
  already sends (the test recomputes them as squared log returns). Nothing dated `d` except the released 14:30-14:40
  pack. Hybrid's rules value for V6 is whatever forecaster the rules row of `v4_slots.csv` names (G7's `v6_ewma_t4`
  or M1's weather), never hard-coded. The pointer stays under `ROUTINE_POINTER_MAX_BYTES`; the five-question input is
  measured and stated in Claims. G: full input under the cap. B: over the cap, not fired (never truncated). Bd: an
  `RV_s` row dated `d` is left out. E: no A16 row yet: V1 not started, nothing sent for it. P: let day `d`'s `RV_s` in.
- **C5 Book side (step 7).** `brief` accepts the v4 pointer and prints prompt v2 (hash-checked) and the input; `seal`
  writes the v4 commitment under `V4_TERMS`; `reveal` never publishes before 15:10:10; labels and envelope come from
  the input. The v1 path is unchanged (v1 tests untouched). G: v4 brief, seal, reveal in a fixture day. B: a v1
  pointer read as v4 (or the reverse) is refused. Bd: `reveal` at 15:10:09 waits, at 15:10:10 publishes. E: `seal`
  with no brief this session is refused (`BookStepRefused`). P: `reveal` with v2's 15:15:10.
- **C6 Reveal wait.** One `reveal` call waits at most 9 minutes; still early, it prints "waiting until 15:10:10 IST:
  run reveal again" and exits 0; prompt v2 says to run it again until it publishes. G: a seal at 14:45 publishes on
  the third call. B: a reveal with no seal is refused. Bd: called at 15:01:10, it waits exactly 9 minutes and
  publishes at 15:10:10 in that call. E: called after 15:10:10, it publishes at once (collect judges the receipt). P:
  one call that waits the whole 24 minutes.
- **C7 Fire.** Today only, from `ai_books_v4`'s date, only after today's release record exists, latest start 14:55
  (`V4_LATEST_FIRE`), once per book and day, never retried; each failure a logged `not_fired` and one #fno-desk line;
  the v2 AI fire stops on the same date. G: a release at 14:40, both fired. B: a day other than today refused,
  touching no Drive. Bd: start at 14:55:00 fires, 14:55:01 is `not_fired`. E: no release record, nothing fired, one
  line. Re-verified after the merge of `main`. P: fire at 14:55:01.
- **C8 Budget: forecasters stop last** (`BG-budget.md:46-48`, design 7.6). BG1's signal is one flag
  (`signal.py:53`); the post-mortem writer already stops on it (`learning/writer.py:49`). So the fire
  stops the books only when stopping every other role cannot help: the signal's level is `stop` **and** the books'
  own minutes of the month (BG1's ledger rows with a `book`) are by themselves at or above the cap; then every
  question is `not_fired` (reason "BG1 stop"), a miss. `ok`, `alert`, `unknown`, or `stop` with the books under the
  cap: fire. **A missing signal file** for the month: fire, with one #fno-desk line "no BG1 signal for <month>"
  (fail open, because a miss costs the slot under the 10% cap and the cost is bounded by C17's numbers). This reading
  of "last" and the fail-open choice are reasoning only; the orchestrator puts both to the owner, and C8 follows the
  ruling. G: `alert`, fired. B: `stop` with books at 100% of the cap, `not_fired`. Bd: books at 99.9%, fired. E: no
  file, fired and one line. P: stop the books on any `stop`.
- **C9 Rows.** One row per book, started question and settled session from `effective_start`, in G7's schema,
  `label=live`, `kind=ai`, the right slot, the prompt hash, the input hash, and `pack_sha256` = the release record's
  SHA (an empty or other SHA refused by `check_pack_binding` before any write); written once (`RecordConflict`). G:
  an on-time day, one `ok` row per question with all fields. B: the pointer's SHA differs from the release record's,
  refused, nothing written. Bd: the same row written twice is a no-op; a different second row raises. E: a day before
  `effective_start` writes nothing. P: write the pointer's SHA instead of the release record's.
- **C10 The 15:10 deadline.** GitHub's receipt decided by G10's `commitment.on_time` (reused, not copied). G: 15:09:59
  on time. B: a commit dated 15:05 but received 15:10:01 is `late` (receipt time, never commit time). Bd: 15:10:00 on
  time, 15:10:01 `late`. E: no commitment, `no_submission`. P: compare commit time instead of receipt time.
- **C11 Every failure a miss.** Each outcome (late, not fired, no submission, not revealed, invalid, model mismatch,
  exposed, breach, stopped, BG1 stop) writes a non-`ok` row; a session the fire never ran is `not_fired`. Day labels
  come from the release record (`ReleasedPacks.release(day)`, D2): a `system_late` day has no AI row and is excused;
  a day with no release record yet is neither collected nor written. Over a fixture month G8's `AiSlotDays` finds no
  slot-day without a row, and a slot past 10% misses is "undecided, operations". G: a month of mixed outcomes, all
  rows. B: a never-fired day left without a row fails the test. Bd: a `system_late` day, no row and not counted. E: no
  release record yet, no row, counted as waiting. P: skip a never-fired day.
- **C12 Round 2c.** `stop_rule.breached_days` takes the window's session days and the v4 audit folder;
  `audit_plan.fired_sessions` and `TranscriptAudits` take the v4 folder; `scoring_gate.scoring_status` passes
  `V4_TERMS`. Defaults keep v2's behaviour (its tests unchanged). G: a drawn, clean v4 day becomes `ok`. B: two
  breaches in 20 v4 sessions stop the book. Bd: the second breach on the 21st session back does not stop it. E: no
  fired v4 session draws nothing. P: drop `terms` in the gate.
- **C13 Registration, in the protocol's order** (`slot_file.py:62-69`: a start on or before the freeze's day, or after
  the slot's first eligible session, raises, and `registered()` then refuses the whole file, which stops every v4
  score). The required order: (1) `FREEZE_v4.md` and the rules rows (the freeze builder, D5); (2) G11's 10 rows,
  `book2_hybrid_v2` for `hybrid` and `book3_ai_v2` for `ai_team` on each of the five questions, `effective_start` =
  the first scored session after the freeze's day (NSE calendar), which is never after any slot's first eligible
  session (the earliest a primary-baseline value can exist; V6 and V7's base rate is eligible on that very day),
  `registered_on` = the day written, on or before it, `decision` citing the owner's row; (3) `ai_books_v4` set by the
  owner to that same session. G11 builds `python -m fno ai register-v4-slots`: it refuses, writing nothing, while
  `FREEZE_v4.md` does not exist or the rules rows are missing, and after `effective_start` has begun (09:15 IST);
  otherwise it appends the rows (or prints them with `--print` for the freeze builder to put in the freeze commit).
  If the owner sets `ai_books_v4` later than `effective_start`, the sessions between are `not_fired` rows (collect's
  back-fill, C11), honest misses; `ai fire` prints that count every day. G: rows written on the freeze's day, read
  clean by `SlotFile`. B: before `FREEZE_v4.md`, refused, nothing written. Bd: a start one session later than the
  first eligible session is refused by `SlotFile` (its test, here with G11's rows); writing at 09:14:59 of the
  start day works, 09:15:00 is refused. E: no rules rows, refused. P: an `effective_start` one session late.
- **C14 Replay.** O11's xfail becomes a real check: the recorded day, replayed with a fixture released pack and
  scripted routine answers, writes 10 rows (5 per book) that G8 scores; the marker is deleted in the same branch. G:
  10 `ok` rows scored. B: one book scripted late writes 5 `late` rows, scored as misses. Bd: a `system_late` replay
  day writes none. E: no scripted answers, 10 `no_submission` rows.
- **C15 Not a money piece.** A test over every module of the deciding packages `fno/desk`, `fno/books`, `fno/book3`,
  `fno/risk`, `fno/factory` and `fno/playbook` (an AST walk of imports, and a text search): none imports `fno.ai` or
  any `fno.ai.v4_*` module, and none holds the strings `research/forecasts/v4/book` or `book2_hybrid_v2` /
  `book3_ai_v2`. A later package that decides trades (F1t's `fno/ai_trading`) is added to the list by its builder.
  G: today's tree passes. B: a fixture module importing `fno.ai.v4_rows` fails it. Bd: a string inside a comment
  counts (text search). E: an empty package passes. Note: O1's steps stage all of `research/forecasts/v4/`
  (`daily/wiring.py:18`), which commits files but decides nothing.
- **C16 Workflows.** `v4-fire.yml` runs `ai fire --protocol v4 --day <today>` on the release receipt's push
  (`receipts/data/v4/days/**`, D3), fires nothing for a catch-up record of an earlier day, and commits only
  `research/forecasts/ai_v4/` (judge 282.1's test kept); `forecast-capture.yml` runs `ai collect --protocol v4` after
  the 15:10:10 reveal; before `ai_books_v4`'s date both refuse and change nothing. No schedule is created or moved.
  G: today's receipt push fires. B: a push touching only `receipts/data/v4/deadlines/` starts nothing. Bd: a catch-up
  push of yesterday's record fires nothing. E: no `ai_books_v4` date, refused, nothing committed.
- **C17 Cost report.** G11's output prints, per book, p50 and p95 of working minutes (brief to seal), waiting minutes
  (seal to reveal) and model turns, from BG1's ledger and the routine's timing file; a run not captured is named
  (F8c's alert). G: a fixture week's numbers. B: a timing file with no seal time shows "working unknown", never 0. Bd:
  one run, p50 = p95. E: no runs, "no runs yet".
- **C18 Gates.** pytest, ruff, ruff format, `check_imports`, `check_numbers` on `main`; no file or class over 350
  lines (`fno/constants.py` is 349 lines on `main` and 350 on the branch: new constants go elsewhere).

- **C19 Pending days and unknown receipts** (earlier criterion 6, restored). A day whose transcript audit is pending
  has no v4 row and is printed in "N day(s) awaiting audit" with each day and book (`v4_settle.py`); once settled its
  row lands and G8's recomputed report shows it scored or missed. A day whose GitHub receipt cannot be found
  (`CommitmentTimeUnknown`, `fno/v4_pack/commitment.py:16`) gets no verdict and no row (never a guessed time), is
  printed as "N day(s) awaiting GitHub's receipt", and is retried by every later collect; while it waits, G8's look
  refuses (its reconciliation), the safe direction. G: a pending day lands after its audit. B: a receipt lookup that
  fails writes nothing. Bd: the audit settling on the day of the look lets the look run. E: nothing pending, "0 days
  awaiting audit". P: write a `late` row when the receipt is unknown.

**Gap list** (each requirement: its criterion, or out of scope with the reason):
| Requirement (source) | Covered by |
|---|---|
| Item 1, same questions | C1 |
| Item 2, prompt v2 per book, same model, label form | C1, C2, C3, C5 |
| Item 3, fire after release, 15:10 receipt, reveal after, once | C5, C6, C7, C10 |
| Item 4, G7 schema, folders, `pack_sha256`, write once | C9 |
| Item 5, every failure a miss | C11 |
| Earlier criterion 6, "N days awaiting audit", no row while pending | C19 |
| Item 6, registration after the freeze | C13 (D5) |
| Item 7, one row per slot-day for the look | C11, C19 (the look's refusal is G8's, merged) |
| Item 8, wiring only in `fno/ai/wiring.py`, `book_wiring.py` | C18 (judge reads the diff) |
| Protocol 1.1-1.2, each question's measure and unit | C2, C4 |
| Protocol 3.2, V1's one-way baseline switch | C3 |
| Daily AI cost, BG1 stop last, p50/p95 | C8, C17 |
| Claim scope (Book 2 not independent) | prose only: G8's report wording, unchanged |
| Judge 275 conditions (pack guard; freeze list) | C9; the freeze list is the freeze builder's (D5) |
| Judge 282.1/282.3 (fire log folder; fire workflow with G11) | C16 |
| Handover risk 6, 64 KiB vs the routine API's real limit | C4 measures; the first live fire is the real check |
| Handover risk 1, M1's stale method hash | out: M1 and the freeze's, not G11's (no G11 file) |
| Round 1's behaviour kept | the existing `test_v4_rows.py`, unchanged in meaning |

**Dependencies on G10** (`story/g10-completion`, session_011hvvn9). Agreed (G10's answers, c876ede5, "The pack's
interface for G7b and G11"):
- **D1 The daily release:** O1's new `v4_release` step releases the 14:30-14:40 pack every session. G11 reads only
  `ReleasedPacks` (`release`, `pack`, `pack_bytes`), `ReleaseRecord.pack_sha256`, `Pack`, `check_pack_binding` and
  `build_released_packs` (`fno/v4_pack/release.py`, `model.py`, `guard.py`, `wiring.py`); G10 tells G11 before any
  rename.
- **D2 Day labels:** the label is the release record in Drive `v4/days/<YYYY>/<date>.json`, read through
  `ReleasedPacks.release(day)`; every scored session from G10's live date gets one, `system_late` included (catch-up).
  `research/data/v4_days/` is retired by G10, so G11 reads no file there (G8's reads of it are G10's to re-point).
- **D3 The trigger:** the daily run's committer pushes `receipts/data/v4/days/<YYYY>/<date>.json.sha256` and the pack
  receipt in one commit with the owner's routine credentials (never an Actions token), so `v4-fire.yml` starts on
  the `paths:` filter `receipts/data/v4/days/**`. Catch-up records land on the same path, so `v4-fire.yml` fires only
  for today's record (C16). G11 lands `v4-fire.yml` (judge 282.3's preferred path).
- **D4 Times:** `V4_LATEST_FIRE` 14:55, `V4_DEADLINE` 15:10, read from `fno/forecast_v4/terms.py`, never copied.
- **D5 Freeze and the rules rows:** a separate freeze builder writes `FREEZE_v4.md` and the rules rows of
  `v4_slots.csv` (orchestrator, 24 Oct); G11's rows follow in C13's order.
- **Not G10's, also needed:** V2's primary baseline (premium-adjusted implied; G7b's builder, `story/g7b-completion`).
  Until it exists no V2 day is baseline-observable, so the V2 AI slots can neither score nor miss (C3).

**AI cost limits (BG1):**
- Measured (strong evidence): 6 v2 book runs, 19-23 Oct, 4.21-4.51 minutes start to end (`accounting/ai_usage.csv`);
  they run from about 15:11 to 15:15:13-40 (`research/forecasts/ai_v1/timing/`), so they include v2's short reveal
  wait. The commitment reached GitHub 35-309 s after the fire on the 9 book-days with one (fire log against the
  audit's receipt time), so the working part is about 0.6-5 minutes. Two runs were not captured (22 Oct Book 3, 23 Oct
  Book 2). v2 record: 7 of 14 book-days on time (3 `no_submission`, 4 `late`; the 22-23 Oct late seals had a root
  cause fixed on 23 Oct).
- v4 estimate (reasoning only): about 1-8 working minutes per run (a bigger input, five questions), plus a wait to
  15:10:10 of about 24-28 minutes, so 25-35 minutes start to end, and 3-4 extra `reveal` turns (C6; judge 579 note 2).
  Two books, 22 sessions: about 1,100-1,540 minutes a month if the waiting counts, 44-350 if only working minutes
  count. Firing later (for example 14:50) would cut the wait but shrink the margin to 15:10; recommended: keep the
  fire at release, because a miss costs the slot (10% cap) and the cap counts minutes, not answers.
- Today's meter (`python -m fno budget meter --month 2026-10`): "level unknown", because development and
  data-routine minutes are not recorded, so the cap cannot be judged now; C8 fires on `unknown`. Whether the wait
  counts goes to the owner (orchestrator, 24 Oct); C17 reports working and waiting minutes and turns apart.
- Limits G11 keeps: one fire per book and session, never retried; no second runtime cap; C8's stop; the weekly
  transcript audit draw stays as it is (its auditor minutes are BG1's roles).

**Owner step (text for the orchestrator to put to the owner when G11 is ready to go live; G11 changes no routine):**
in both books' routines, replace step 4 of the stored prompt (`F1-G5-owner-checklist.md:48-50`) with:
> 4. Your answer must be sealed by the deadline your versioned instructions give. Never use `--no-verify`. If `seal`
>    prints a line starting with "refused", do what your instructions say (fix what it names and run it again)
>    while it is before that deadline. If it fails in any other way, or still refuses at that deadline, stop; final
>    message: its last line.

Version 1's instructions say 15:15:00 and version 2's 15:10:00, so this text is right for both; the checklist file is
updated in the same branch (lane 1, a routine's prompt).

**Out of scope:** any trading by the AI books (F1t, F5); G8's scoring and the look (merged); the v4 pack, its
capture, release and day labels, and G8's re-pointing from `research/data/v4_days/` (G10); the freeze record and the
rules rows (D5); V2's primary baseline (G7b); creating, changing or deleting any scheduled routine or trigger (the
owner's); setting `ai_books_v4`'s date (the owner's, after merge and the rule-8 end-to-end run); M1's method hash; v5.

**Order:** this text to the judge; then merge `main`, C12 and C5-C6 (the book side), C1-C4 (five questions),
C8-C9, C19, C13, C16, C14 last; self-review by independent code-review agents; Claims with a real output sample;
judge.

**Round 2 (judge 579, round 1 FAIL at acacf5c7f), each finding:**
- S1 (D2, D3 vs G10's answers): fixed in a3de25b6, before the verdict reached me; C11 and C16 now also read the
  label through `ReleasedPacks.release(day)` and name `receipts/data/v4/days/**`.
- S2 (freeze order): C13 states the order, what G11 does in each case (refuse before the freeze or without rules
  rows, refuse once the start has begun, `not_fired` back-fill for a late go-live) and tests both sides.
- S3 (baseline and `w`): C3 uses `eligibility.primary_baseline` (V1's one-way switch) and redesigns the envelope as
  the rules-and-baseline span widened by a declared `w` per kind (0.10 absolute, 0.25 relative), fixed before merge;
  the measurement (V6b 55.5% inside the built rule) is in item 4. V2 needs no measured `w`, so nothing is set after
  merge.
- S4 (measures): C2 and prompt v2 name each measure (V1 intraday `RV_s` with the overnight return; V2 `close_proxy`),
  variances, with the unit-error bound; C4 gives V2 its close-proxy history and tests it.
- S5: C19 restores "N days awaiting audit" and adds the `CommitmentTimeUnknown` case and its retry.
- S6: C15 lists the six deciding packages and checks both imports and path strings.
- S7: C8 defines "last" (books stop only when their own minutes alone reach the cap) and the missing-file case
  (fail open, one line); both are put to the owner by the orchestrator.
- m1: every criterion now has G, B, Bd and E cases.
- m2: `fno/constants.py` 349/350; the v2 minutes include the reveal wait; 2,743 commits (counted 24 Oct, after more
  merges to `main`); the fire-to-receipt times are now taken from the audit files' GitHub receipts (35-309 s).

**Claims** (stage 2, builder session_01Rga1fe3C4rmnrmmE1p3diE; branch `story/g11-ai-books-v4`, head given in the
message to the judge). Lane 1, one judge (not a money piece: C15). Nothing runs live: `daily.live_from.ai_books_v4`
stays null.

*Commits on top of the merge of `main` (7334ec2b; full suite there 15,215 passed):* 85df1067 C12; e3c6cb35 C5-C6;
881ba676 C1-C4; 2c69136a C8, C9, C17, C19; dfb26381 C13-C16; then the self-review's fixes 8e34b29a (A), 8d896bf3 (B),
99a916f2 (C) and, after a second review, 251b65de (D); 562718c5 merges `main` (REH1i's receipts check passes).

*Per criterion (code; tests; the builder's plants, every one caught):*
- C1 `versions.py` (`V4_AI_QUESTIONS` = the family), prompts v2; `test_v4_versions.py`, `test_v4_fire.py`; plant: V7
  dropped (20 failures).
- C2 `answer.py` (`VARIANCE_CAP` per question); `test_v4_five_questions.py`; plants: 0 accepted, caps at 1.
- C3 `envelope.py` (`Envelope.span`), `v4_book_inputs.py` (G8's `primary_values`), `v4_input_check.py` (recomputed);
  `test_v4_input.py`, `test_v4_five_questions.py`, `test_v4_pointer.py`; plants: no point branch, static primary
  baseline, envelope not recomputed.
- C4 `v4_book_inputs._history`, `v4_input.py`; plants: day d's `RV_s` let in, free-text label.
- C5-C6 `book.py`, `book_run.py`, `run_timing.py`; `test_v4_book_side.py`; plants: no cap, v2 reveal time, v2
  path, no sealed-day check.
- C7 `v4_fire.py`; `test_v4_fire.py` (whole-second 14:55, no log on no pack); plants: 14:55:01, log on no pack.
- C8 `budget_stop.py`; `test_v4_budget_stop.py`; plant: stop on any `stop`.
- C9 `v4_rows.py`; `test_v4_rows.py`; plant: rows without the release SHA.
- C10 `run_terms.V4_TERMS` and `outcome.judge`, the same constant as G10's `commitment.on_time`, pinned equal at
  15:09:59, 15:10:00, 15:10:01 (`test_v4s_deadline_is_g10s_receipt_rule`). It is not the same function because
  F1/G5's judging chain takes one `RunTerms` for both protocols (v2's deadline is not G10's), so the rule stays in
  the terms and the pin proves the two agree (judge 586 m3 corrected the earlier reason; ruled the pin enough).
- C11 `v4_collect.py`, `v4_settle.py`; `test_v4_collect.py`; plants: never-fired day skipped, no catch-up, lost log
  as `not_fired`, no too-early check, no containment.
- C12 `run_terms.py`, `stop_rule.py`, `audit_plan.py`, `transcript_audit.py`, `scoring_gate.py`, `cli.py`;
  `test_v4_round_2c.py`, `test_v4_wiring.py`; plants: gate, stop rule, fire-log shape, settler glob, v4 weeks
  dropped, audits-due v2 only.
- C13 `v4_register.py`, `ai register-v4-slots`; `test_v4_register.py`; plants: after 09:15, a later start, exit 0
  on refusal, a conflicting forecaster.
- C14 `tests/e2e_acceptance/ai_v4_day.py`, O11's marker deleted; see the sample.
- C15 `tests/ai/test_v4_not_a_money_piece.py` (imports by AST and path strings; planted import found).
- C16 `v4-fire.yml` (from `story/g10-part2b-release`), `forecast-capture.yml`, `capture-watch.yml`;
  `tests/v4_pack/test_fire_workflow.py` (the day step and the commit step run as GitHub runs them, offline);
  plants: fire on any receipt, no pipefail, no alert.
- C17 `v4_cost.py`; `test_v4_cost.py`; plants: missing seal as 0, uncounted calls.
- C18 gates below; largest file in `fno/ai` 171 lines.
- C19 `v4_collect.py` (`Waiting`, `ReceiptUnknown`); plants: unknown receipt judged late.

*Changes from the passed text, each for a reason found while building or by the self-review:*
1. C2's caps are per question, not "at most 1": V1 0.01, V2 0.05. Strong evidence: NIFTY's closes 2017-2026, the
   largest realised one-session close-proxy variance 0.0193 (23 Mar 2020), five sessions 0.0287, median 2.6e-5.
   Percent squared, annualised figures and volatility points are refused; a standard deviation for V1 (about 0.008)
   still passes, a known gap.
2. C8 reads BG1's own meter, not the signal file: no schedule writes `accounting/budget/<month>_signal.json`.
3. C14 replays 22 Oct 2026, not O11's 16 Oct: v4's rule rows are live only from 22 Oct (the back-fill ends 15 Oct).
4. C4: the input is written as columns (closes, histories, the chain), not one object per row, and each `RV_s` to 6
   significant digits: 33 KB became 18-19 KB, because the routine's model retypes the text into `brief`.
5. The pointer carries its input's SHA-256; `brief` refuses a mis-copied text ("copy it again exactly"). The owner's
   step 3 must let the model retry that one refusal: the exact text is in `F1-G5-owner-checklist.md` (the
   orchestrator puts it to the owner with step 4).
6. Collect no longer rebuilds the input: the fire log keeps the labels and Hybrid's envelope (rule numbers only),
   because the files an input is built from can still change after the fire (the self-review's blocking finding).
7. v4's first 10 fired days need a recorded transcript audit before they score, as v2's did (before round 2c the
   gate read v2's fire logs only). Someone must record them: `ai audit-record --protocol v4`.
8. `register-v4-slots` registers per rules row (a question whose rules row lands later is added by a later run).
9. A commitment without a fire log waits 3 sessions (the fire keeps its log as a run artifact when its push fails),
   then that book is `invalid`; the fire log is read as first committed; a Hybrid entry without an envelope is
   `invalid`; the firer runs `brief`'s own pointer check before firing (each from the second review).

*Self-review (quality rule 3):* three independent agents on dfb26381 (protocol logic, book side and prompts,
workflows and wiring), then a fourth on the fixes. Accepted and fixed, each with a test: collect's rebuild from
changing files (blocking); `v4-fire.yml` failing every session before go-live on `git add` of a missing folder
(blocking); a fire step whose failure `tee` hid (blocking); the pointer retyped with no copy check; unchecked fields
shown by `brief`, an editable envelope; weak variance caps; tracebacks on odd values; v2 collect writing
`no_submission` after go-live; a refused question crashing settle; a lost fire log becoming `not_fired`; a failed
pack read unalerted; v4 runs missing from BG1's capture coverage; the alert step's name cut by YAML at ` #`; ten
mutations that survived. The second review (of 99a916f2) found, all fixed in 251b65de with a plant each: a
`system_late` day collected as AI misses (blocking: the real `ReleasedPacks.release` returns a `system_late` record
without raising, and the test fake had raised there, so the fake now behaves like the real class); the fire log
trusted as it stood in the checkout; a lost log waiting forever; a pointer `brief` would refuse fired anyway. Not
changed: C10's pin (above). Residual (reasoning only): a routine's own push credentials could add a file such as a
forged fire log before the Actions push; the transcript audit names any push beyond `seal` and `reveal` a breach.

*Real output sample* (`tests/e2e_acceptance/ai_v4_day.py` on 22 Oct 2026: the committed closes, rule and baseline
rows and A16 rows; a fixture pack, scripted routines, recorded receipts):

```
Omenix F&O AI forecasts v4 (GitHub Actions): 2026-10-22: fired book2_hybrid, book3_ai of book2_hybrid, book3_ai
Omenix F&O AI forecasts v4 (GitHub Actions): 2026-10-22: book2_hybrid on_time: collected; its rows land once its audit settles
Omenix F&O AI forecasts v4 (GitHub Actions): 2026-10-22: book3_ai on_time: collected; its rows land once its audit settles
Omenix F&O AI forecasts v4: 10 v4 row(s) added; 0 day(s) awaiting audit
book2_hybrid_v2 v1_rv_next_session: invalid (no rules value and no baseline that day: no envelope, null; no miss)
book2_hybrid_v2 v6_abs_move_2pct_next_session: ok 0.064 / book3_ai_v2 ...: ok 0.04
G8, V6a, live cohort, n 1: Brier book2_hybrid_v2 0.004096, book3_ai_v2 0.0016, weather_vix_v1 0.000784, base_rate 0.000711
Omenix F&O AI v4 slots: refused, nothing written: FREEZE_v4.md does not exist: the AI slots are registered after the freeze
```

*Waiting on others (none of these tests fail now; they use fakes of the agreed interfaces):* G10's real daily
release (`ReleasedPacks`, the receipt push that starts `v4-fire.yml`) and G8's move from `research/data/v4_days/`;
the freeze builder's `FREEZE_v4.md` and rules rows (then `register-v4-slots`); G7b's V2 primary baseline. The
rule-8 end-to-end run needs G10's release on a live day.

*Owner decided 24 Oct:* BG1 "forecasters last" and fail open, as built (C8; DESK_DECISIONS c63eb7e0b); the reveal
wait does not count in BG1's cap (owner: "Waiting minutes - Option A"): BG1's reader change is its own story, not
G11's (C17 already reports working and waiting minutes apart). *Still open:* steps 3 and 4 of both routines' stored
prompt, at go-live (exact text in `F1-G5-owner-checklist.md`, with who records v4's first 10 transcript audits).

*Round 2 (judge 586, round 1 FAIL at d8aabba4c), each finding:*
- Merge of `main` (G10 completion at 3ee1b8ae and later): `config.yaml` keeps both adjacent keys; G8's v4 wiring
  keeps G10's body with G11's `build_slot_registry` name (judge J's resolution). REH1i's receipts test passes.
- F1 (C13's late go-live): `v4_go_live.py`. Collect starts at the earlier of the go-live date and the AI slots'
  earliest `effective_start`; a session before go-live is `not_fired` ("before the AI books' v4 go-live"); `ai fire`
  prints the count every day. Tests: judge J's probe (start one session early, go-live on DAY) writes the early
  session's audit, and G8's `AiSlotDays` finds no slot-day missing; the count line; the wiring passes the calendar's
  sessions. Plant: collect from the go-live date only, caught. Note: a registered AI slot is collected from its start
  even while `ai_books_v4` is null, so registration and the go-live date should land on the same session (C13's order).
- F2: P18 (`mark_exposures` dropped), P23 (`released_sha256` from the fire log) and P25 (the firer's stop rule without
  v4's sessions) each now fail a test through the collector or the firer; the three plants caught.
- m1: both docstrings corrected. m2: the claim now says what holds: an annualised V1 is refused, an annualised V2
  below a VIX of about 22.4 and a standard deviation for V1 pass (a test pins all three). m3: C10's reason corrected.
- Change 7: who records v4's first 10 transcript audits and how, in the go-live checklist.

*Gates* on the merged head 562718c5 (a clean copy, `env -u FNO_SLACK_BOT_TOKEN` for pytest only): 15,550 passed,
1 skipped, 14 xfailed (O11's G11 marker gone); ruff and ruff format clean; `check_imports` clean (2,619 files);
`check_records` clean (9,070 files). `check_numbers` runs on `main` at merge (no number was claimed by this story).
Every later commit on the branch is Markdown only.
