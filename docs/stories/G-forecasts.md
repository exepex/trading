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
12 2% days (13 / 125 = 10.4%), so V6's 13+ band is unused until n >= 130; at n = 250 the cap is 25. The rule is one
function beside `judgeable` in `fno/forecast_v4/confirmatory.py` with one protocol line stating option 2 as decided,
so it is frozen with the protocol (proposed to the orchestrator; if refused, it is one G8 function instead, same test).

**Expected design** (new package `fno/forecast_scoring/v4/`, each file well under 350 lines; composition root
`fno/forecast_scoring/v4/wiring.py`, added to CLAUDE.md's list):
- `V4ForecastSource` (interface): one row per (question, forecaster, day) with a value or none, and a label
  (exploratory back-fill or live). Adapter for G7's committed files (layout agreed with the G7 builder through the
  orchestrator). The primary baseline is read from the same source under its name (`terms.PRIMARY_BASELINE`; V1's
  switch to intraday HAR by `eligibility.py`).
- `V4Outcomes`: from A7's regular sessions only (`sessions.py`) and the official closes and closing India VIX in
  `research/data/nifty-panel/warmup_closes.csv`: V2 and V3 the summed squared close-to-close log returns
  (`close_proxy`), V6a, V6b and V7 the events of protocol 1.2; V1 from A16's `rv/` rows (`ok` rows only; a `void` row
  is a void outcome). A horizon whose last session is not yet in the file is unresolved. The regime inputs of each
  outcome: the closing VIX and the log return of its first session (`regime.py`'s definition).
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
- `report.py` and the CLI `python -m fno forecast-v4 report` (descriptive, any day) and `python -m fno forecast-v4 look
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

**Depends:** G6 (merged), G7 (forecast files), A7, A16 (V1 only) · **Size:** M · **Status:** story text for the judge
(claims `reviews/claude/response_126_g8-scoring.md`)
