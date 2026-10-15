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
every required field observed by 14:40:00; `A2` A16's 14:30 mark (fallback), every required field observed by
14:40:00; `system_late` no complete pack by 14:40:00. The label carries the pack's latest `observed_at` (for example
"A, observed by 14:31:12"). Every report counts `A`, `A2`, `system_late` and flagged days; a protocol v4 verdict uses
`A` and `A2` days. **One pack, one hash:** every family's record names the released pack's SHA-256; a record naming
any other pack is refused. **Said plainly (strong evidence: `fno/intraday/expiry_plan.py`, `fno/forecast/iv30.py`):** A16 records the
nearest weekly and the nearest monthly chain only, while IV30 interpolates the two monthlies around 30 days, so an
`A2` day's IV30 is usually the protocol's flagged single-expiry value (or none when the monthly has under 7 days left).
The label carries it; adding the next monthly to A16 (about 70 more quotes a mark) is the alternative, not proposed.

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
   real shared-key fallback (A16's 14:30 mark, received about 14:30-14:31) keeps its own times and is labelled `A2`;
   no field ever carries a time earlier than its `observed_at`.
1b. Every family's record names the released pack's SHA-256; a record with another hash is refused. The deadline check
   reads GitHub's receipt time; a commit dated 15:09 but received at 15:10:01 is late.
2. `terms.py` holds the capture start, window end, deadline and common-snapshot times and X; G7's and M1's capture
   refuse at the capture start through one constant, `terms.V4_CAPTURE_START = time(14, 30)` (boundary: 14:29:59
   accepted, 14:30:00 refused).
3. Each v4 record and report carries the day label; every report counts `A`, `A2`, `system_late` and flagged days; a
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

**Known limits:** an `A2` day's IV30 is usually flagged (above); X rests on 2020-26 history, one crash included (some
evidence); a GitHub push delay near 15:10 counts as late (the push time is the only clock both sides trust).

**Depends:** G6 (merged), G9 (merged), G7, M1, G8 (merged); A16 live for the `A2` fallback; the owner's routine change
at go-live · **Size:** M · **Status:** story text for judge A, then ChatGPT (rule 9) (`reviews/claude/response_152_g10-v4-timeline.md`)

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
   Each version also writes BG1's self-timing record (`fno/budget/self_timed.py`), the prompt change
   `BG-budget.md:102-104` left open.
3. **Fire and collect:** F1/G5's existing firer, seal, reveal and outcome code (`fno/ai/fire.py`, `seal.py`,
   `outcome.py`, `scoring_gate.py`), pointed at the v4 pack: fired after the pack's release (about 14:32, at the latest
   14:40); the commitment must be **received by GitHub by 15:10** (G10, `fno/forecast_v4/terms.py` `V4_DEADLINE`);
   reveal after 15:10. Fired once, never retried (as today). The timing constants come from `terms.py`, not a copy.
4. **Records:** G11's own writer (G7's `records.record()` stamps G7's version, so it is not reused) writes
   `research/forecasts/v4/book2_hybrid/<question>.csv` and `research/forecasts/v4/book3_ai/<question>.csv` in G7's
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
7. **Looks:** every AI transcript audit up to a confirmatory look's date is settled before that look runs (a look is
   recorded once, `LookRecords`, and would keep a false miss). G11 keeps the committed file
   `research/forecasts/v4_audits/open_audits.csv` (header `day,forecaster,question`; one row per AI forecast whose
   audit is open; the row enters in the same commit as the book's collected submission (its sealed commitment and
   reveal), so an open audit is never missing from the file, and leaves when the audit settles, in the same commit as
   its v4 record row). From the books' first live day the file always exists, header-only when no audit is open,
   so a deleted file is never read as "nothing open". The look's
   refusal is built by the A16/G8 builder in `fno/forecast_scoring/v4/` before the freeze (their register row and a
   freeze-checklist line; built on `story/g8-look-audits` at 4b8912fc, constant `wiring.py` `OPEN_AUDITS_FILE`): a look on date L refuses while any row has `day <= L`, naming the count and the earliest
   open day; a missing file means no open audit; a bad header or date stops the look. G8 reads the file, never G11's
   code.
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

**Daily AI cost against BG1's cap:**
- BG1's cap is minutes, not rupees: the books' and roles' minutes at most 50% of all measured session minutes in the
  month until December 2026 (`config.yaml` `budget`), then 50% of the owner's plan minutes; alert at 80%, stop at
  100%; the plan costs Rs 20,000 a month.
- No book run has been measured yet (`accounting/ai_usage.csv` has no book row). The one data point: on 15 Oct each
  book's commitment came about 5 minutes after the fire (15:10:20 to 15:15:12-15). Some evidence, one day.
- Estimate (reasoning only): 2 books x 5-10 minutes = 10-20 minutes a session day, about 220-440 minutes in a
  22-session month, the same number of runs as today's v2 run (option A: v4 replaces v2).
- This story makes the number real: the v2 prompts write BG1's timing record, so BG1 measures it from the first day.
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
6. A day whose audit is pending has no v4 row, has its rows in `open_audits.csv` and is printed in "N days awaiting
   audit"; once settled, its v4 row lands and its `open_audits.csv` rows go in the same commit, and G8's recomputed
   report shows it scored or missed. (The look's refusal on that file is the A16/G8 builder's test.)
7. Each run writes BG1's timing record; BG1's meter shows the book minutes.
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
step), the A16/G8 builder's look refusal on `open_audits.csv`, G5, BG1 · **Size:** S-M ·
**Status:** story text for the judge (`reviews/claude/response_202_g11-ai-books-v4.md`); code after the v4 freeze
