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

**Depends:** A1, A3, B1, B4 · **Size:** M · **Status:** v1 frozen; awaiting judge re-check (protocol v1 with review 28 changes; freeze record research/forecasts/FREEZE.md). v2 (`research/forecasts/PROTOCOL_v2.md`, review 29's eight changes): judge 47 addendum 3 PASS; frozen (protocol commit ab2e811, freeze record research/forecasts/FREEZE_v2.md, ledger trials 37-41). v3 (`PROTOCOL_v3.md`, the panel extends daily, A13; ChatGPT review 30, response 69): judge 64 addenda 1-2 PASS; freeze record `FREEZE_v3.md` (c1bf97f, two sections), confirmed frozen 14 Oct 2026 (protocol commit 904c036; amended before confirmation in f67065a; `docs/DESK_DECISIONS.md`)

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

**Depends:** G1, G2 · **Size:** S · **Status:** done as built (judge 54 PASS; claims: response 62 and its v2 addendum; the job runs protocol v2's live capture from Wed 14 Oct 2026; first live run pending)

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
  wiring in `fno/forecast/baseline_wiring.py`.
- **Out:** V2-V5 and V7 (phase 2), the raw and premium-adjusted implied baselines (phase 2: they are V2's and V3's
  primary and only "also reported" for V1), scoring, pairs and reports (G8), adding the capture to the daily routine
  (at v4's freeze, a schedule change), the freeze record (G6), M1's weather model.

**Expected design** (pure calculations apart from I/O; G6's `fno/forecast_v4/` is called, never re-implemented):
- `fno/forecast_v4_rules/` (new package; every file under 350 lines):
  - `series.py`: regular-session closes (and India VIX closes) from `research/data/nifty-panel/warmup_closes.csv`
    (`session == regular`, `forecast_v4.sessions`), close-proxy `RV_s`, V6a and V6b outcomes with their resolution
    session, and A16's live intraday `RV_s` rows. **The one place for these rules:** G8 imports them to resolve
    outcomes; G7 writes no outcome files (agreed with G8, 15 Oct).
  - `baselines.py`: `Trailing`, `Ewma`, `HarDaily`, `HarIntraday`, `BaseRate` behind one interface (`PointBaseline`
    for variances, `ProbabilityBaseline` for probabilities), each returning a value or `None` (missing, never filled).
  - `rules.py`: the two rule forecasters below.
  - `records.py`: the v4 record and its CSV files; `capture.py`: one session's forecasts at the cutoff; `backfill.py`.
- Wiring: `fno/forecast/baseline_wiring.py` (G1's freeze pins `fno/forecast/wiring.py`). CLI: `python -m fno forecast
  v4-capture [--day D]` and `python -m fno forecast v4-backfill`.
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
  weather model in protocol 5.6, so `v6_ewma_t4` is registered as **reported only** unless the orchestrator decides
  otherwise before its first counted forecast. Registration itself (the ledger rows) happens at v4's freeze.

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
   `reported`), the method file's SHA-256, the inputs' SHA-256, `made_at`. Invalid values are refused, never written.
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
| Wiring in `baseline_wiring.py` | Expected design |
| V2-V5, V7 | out: phase 2 |

**Known limits:** `v6_ewma_t4`'s independence for V6b is an approximation (volatility clusters); V1 has no live data
until A16 runs; the back-fill uses spent 2017-26 data and is exploratory only (protocol 8).

**Depends:** G6 (merged, not frozen), O6 (closes), A16 (V1) · **Size:** M · **Status:** story text, awaiting the
judge (rule 1)
