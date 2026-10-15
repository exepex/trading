# Response 99: story G6, forecast protocol v4 (draft for the judge, then ChatGPT)

**Builder:** Claude, 15 Oct 2026 IST, branch `story/g6-protocol-v4`. **Lane 1.** Not frozen: the freeze record comes only
after the judge's PASS and ChatGPT's review. G1 v3 and its files are untouched. This file also answers ChatGPT review
98's G6 caveat (cumulative Holm, p = 1 for hypotheses not yet judged, membership and timestamp on every report).

## What changed

- `research/forecasts/PROTOCOL_v4.md` (draft protocol, 286 lines).
- `fno/forecast_v4/` (new package, pure functions, no I/O; largest file 103 lines): `terms.py`, `loss.py`, `pairs.py`,
  `bootstrap.py`, `family.py`, `eligibility.py`, `units.py`, `settlement.py`, `sessions.py`, `stop_rule.py`, `power.py`.
- `fno/constants.py`: v4 question, slot, baseline, verdict and stop-rule names (+23 lines).
- `tests/forecast_v4/` (6 files, 91 tests) and `tests/fixtures/forecast_v4/v4_golden.json`.
- `docs/stories/G-forecasts.md`: the G6 story with its 11 acceptance criteria.

## Claims

| # | Claim | Evidence | Label |
|---|---|---|---|
| 1 | Ranking loss `ln f + RV / f` is defined at RV = 0, finite near zero, never floors RV; non-positive forecasts and negative or non-finite RV are refused | `test_loss_and_pairs.py` | strong evidence |
| 2 | Paired differences equal the textbook QLIKE's whenever RV > 0 (2,000 random cases, and the per-forecast gap is exactly `ln RV + 1`) | same file | strong evidence |
| 3 | Scored set keeps zero-RV dates and zero differences; gate set is the same dates with RV > 0; zero-RV exclusions, missing forecasts, missing baselines, void and unresolved dates are counted, never imputed | `pairs.py`, tests | strong evidence |
| 4 | The bootstrap is exactly p = (1 + #{D*-D <= D}) / (B+1), B = 10,000, ceil(n/L) starts from 0..n-L, seed `SeedSequence([20261015, k])`; a plain-loop rebuild matches; committed values reproduce; under 2L pairs p = 1 | `test_bootstrap.py` | strong evidence |
| 5 | HAC (Newey-West, lag L-1) matches a hand computation and is reported only, never used to choose | `test_hac_matches...`; protocol 5.3 | strong evidence |
| 6 | Minimum-effect gate = relative improvement on the gate set; 3% of mean textbook QLIKE (point), 0.02 Brier skill (probability) | `test_gate_is_three_percent...`, `test_brier_gate...` | strong evidence |
| 7 | Futility = nearest-rank 95% upper bound of the improvement below the effect; never declared without 2L gate pairs | `test_futility_...` | strong evidence (code); the 5%-per-member IUT validity cites Berger 1982 |
| 8 | Holm over a fixed 15-member family with p = 1 for unjudged members; every decision prints the look, its rate, a time-zoned timestamp and all 15 members | `test_family_and_stop_rule.py` | strong evidence |
| 9 | Primary baselines as predeclared (premium-adjusted implied for V2/V3; option-implied probability by Brier for V5); an ineligible primary leaves the pair missing; V1's HAR switch is one way | `test_eligibility_and_power.py` | strong evidence |
| 10 | V4 golden example: 13.656% session RV against 13.567% session-clock IV gives "no", while raw 13.8% would wrongly give "yes"; 9 calendar days gives 15.384% and "yes"; both sides integrate back to 0.00037 and 0.000365 | fixture computed with 30-digit decimals; `test_units_settlement_sessions.py` | strong evidence |
| 11 | V5's outcome only from the frozen expiry's final settlement (E7's expiry-day F&O file), with path, SHA-256 and first-seen time; another expiry, another day's file or a level seen before 15:30 IST on expiry is refused | same file | strong evidence (code); that `SttlmPric` is the final settlement rests on E7's check of 25 Jan 2024 |
| 12 | Session set = A7 regular sessions; muhurat and special excluded; the calendar's classification equals the closes file's `session` column on every row to 14 Oct 2026 | `test_session_set...`, `test_disclosed_base_rates...` | strong evidence |
| 13 | Disclosed base rates reproduced from the committed closes: 100 of 2,409 = 4.15%; 331 of 2,405 windows = 13.76% | same test | strong evidence |
| 14 | Stop rule: zero counted forecasters gives A undecided; zero shadows gives B `undecided/no_economic_test`; "no" needs futility everywhere; the full outcome table | `test_the_review_table` and neighbours | strong evidence (code matches design 8.2) |
| 15 | Power report: design table reproduced (114, 316, 1,264 at 0.05/15); refused before 60 outcomes; overlapping outcomes counted as n / horizon | `test_eligibility_and_power.py` | strong evidence (arithmetic) |
| 16 | Protocol text and `terms.py` state the same names and numbers | `test_protocol_text.py` | strong evidence |
| 17 | 13 planted mutations (inequality, +1s, block range, percentile rank, p = 1, gate set, RV floor, clock, V5 boundary, zero shadows, empty A, one-way switch, session set) each fail a test | run before the commit | strong evidence |

## Judge 98 fixes (one commit)

- **Must-fix 1, the premium-adjusted window's source.** Yes, a point-in-time EOD IV30 exists: G1 v1's frozen
  `PanelAtmIv30` on the A3 panel's first-archived end-of-day chains. The panel has 685 regular sessions from 2 Jan 2024
  to 14 Oct 2026 (strong evidence: manifest count). The window is now limited to 2024 onwards, labelled
  `iv30_eod_close_proxy`, with the rule `eligibility.premium_ratio_window` (at least 500, at most 750, resolved before
  the refit) and two tests. About 620-680 rows remain after the horizon's tail and flagged days (some evidence: G1's
  published flag rates, not recomputed). It is point in time by content, not by archive time, said in the protocol.
- **Must-fix 2.** Section 11 now lists A (Holm at 0.02 at the review: 134 outcomes against 114 at r = 3), B (no power
  report means option 2) and C (the EOD proxy) "for the owner's confirmation before the freeze". Section 10 makes
  that confirmation a freeze precondition.
- **Follow-up.** `test_a_tiny_positive_rv_stays_in_the_gate_set` (1e-13 and 1e-300 stay in the gate set).

## Choices made in this draft (open to the judge and ChatGPT; protocol section 11)

Items 2 and 6 below, and the EOD proxy, need the owner's confirmation before the freeze (protocol section 11, A-C).

1. **Family of 15** (V1, V2, V6a, V6b, V7 x rules, hybrid, AI team). V3, V5 and V4 are tested the same way but never
   members, because 20-session questions cannot settle in useful time and would tighten every other claim. Reasoning
   only.
2. **Two looks with an alpha split, 0.02 at the stop review and 0.03 at the settle date.** Design 5.5 says Holm at 5%
   but 8.2 already has two looks (review, then the re-run on the projected date), so a single 5% per look would not
   control the error. Cost, said plainly: at r = 3, look 1 needs 134 outcomes instead of 114. Reasoning only; the bound
   itself is strong evidence (Bonferroni).
3. **Special sessions excluded**, unlike G1 v1-v3, so outcomes and the disclosed base rates use one set. 4 of the 6
   special sessions had normal timings; their moves stay inside the next regular return. Reasoning only.
4. **V2 and V3 confirmatory on the close proxy** for all of v4; intraday versions reported apart. Reasoning only.
5. **5% spread limit and a put-call-parity forward for weekly IV** (weekly expiries have no future). Some evidence
   (one session of monthly spreads, 0.14-0.99%).
6. **No power report yet leads to option 2** at the stop review. Reasoning only.
7. **V5 "inside" is strict** (break-even counts as outside). Reasoning only.
8. **The freeze waits for G7 and G8's code** (as S1's option A), so the code is hashed with the rules. Orchestrator's
   call.

## Checks run

- `env -u FNO_SLACK_BOT_TOKEN python -m pytest -q`: see the commit message for the count. In this container the clone was
  shallow at first: 8 freeze tests failed because frozen commits were missing; after `git fetch --unshallow` those 23
  tests pass. Not caused by this change.
- `ruff check fno tests tools`: clean. `ruff format --check`: clean. `python tools/check_imports.py`: clean.
- `pip install -r requirements-groww.txt` failed in this container (building `clint` and `args`); nothing here needs it.

## What this does not do

No freeze record, no ledger row, no G7 baselines or G8 scoring code, no v4 forecast or score. Nothing reads a v4
outcome. No order code.

## Revision 1: answer to ChatGPT review 99, item by item

Each item was checked before it was accepted.

1. **Bootstrap size (blocking): ACCEPTED. The simulation proves the defect (strong evidence).**
   - **The calibration.** `tools/v4_null_calibration.py` is seeded (SeedSequence([20261015, 99, cell])). Its output is
     committed as `research/forecasts/v4_null_calibration.{json,md}`.
     - 1,000 mean-zero series per cell.
     - Five kinds: i.i.d., overlapping horizon, AR(1) with phi 0.5, right-skewed and left-skewed.
     - L = 5, 10, 20, at n = 2L and n = 125.
     - Thresholds: 0.0013, 0.002, 0.004, 0.01, 0.02, 0.03, 0.05. Tolerance: nominal + 2 Monte Carlo SE.
     - Bootstrap B = 2,000 in the simulation (10,000 in scoring); the whole run takes about 70 seconds.
   - **Revision 0's centred bootstrap** over-rejects. On the Gaussian processes it rejected 22-28% at n = 2L and up to
     12% at 5% with n = 125. It is now a reported sensitivity only.
   - **The new confirmatory p** (`confirmatory.py`) is max(batch-means t against Student t with k - 1 df, studentized
     block bootstrap); both must pass.
   - **Its worst cases at Holm's first step (0.0013) and at 5%:**
     - Gaussian processes: 0.2% and 5.4% at n = 2L; 0.3% and 7.6% at n = 125. The 7.6% is the single AR(1) cell with
       L = 5 at n = 125; every other Gaussian cell is within tolerance.
     - Right-skewed: 0.7% and 10.1% at n = 2L; 0.7% and 7.2% at n = 125.
     - Left-skewed: at most 0.1% and 2.1%.
   - **Said plainly:** the switch fixes the dependence problem but not strong right skew. That is item D in protocol
     section 11, for ChatGPT and the owner before the freeze.
   - **Tests:** a small seeded version in `test_confirmatory.py` (i.i.d. and AR(1), 200 series, B = 500), a check that
     the committed calibration covers every cell, and committed p-values. Student t is written in the standard library
     (scipy is not a dependency) and is tested against known values.
2. **Futility two-look budget (blocking): ACCEPTED (reasoning: Bonferroni over looks).**
   - The bound is a 97.5% upper bound at each look. The seed words now carry the look number. The nearest rank is the
     9,750th of 10,000.
   - Futility at look 1 is final; an open member uses its own 2.5% at look 2.
   - Golden values for both looks are in `test_bootstrap.py`.
3. **Family, 4 looks, 6 units and settlement, 7 session set, 8 QLIKE gate, 10 freeze:** no change asked.
4. **EOD proxy (5): ACCEPTED.**
   - `diagnostics.proxy_drift` reports the paired 15:00 / EOD ratio: its median over all live days and over the latest
     20, and their drift. It is descriptive only.
   - The protocol says the proxy is never claimed to be equivalent to 15:00 IV30.
5. **Power report (9): ACCEPTED.** It is now "a planning projection only; it promises no settle date".
6. **Judge follow-ups: DONE.**
   - A refit-day boundary test: a row resolved on the refit day is left out; the day before is kept.
   - The first session is 1 Jan 2024 (the earlier text said 2 Jan), with a test.
7. **A-C:** marked "confirmed by the owner, 15 Oct 2026", citing the `docs/DESK_DECISIONS.md` row on `main`.

## Revision 2: answer to judge 98 addendum 2 (owner decision "3 B")

1. **Must-fix 1, a measured option within tolerance for every L, n and look: DONE.**
   - **The study.** `tools/v4_size_study.py` uses 100,000 series per cell below 0.01 and 10,000 above, B = 10,000,
     with the judge's conditional bootstrap.
     - Processes: i.i.d., AR(1) 0.5, overlapping, lognormal, two QLIKE empirical nulls and two Brier empirical nulls.
     - Sizes: L = 5, 10, 20 at n = 2L and n = 125, plus n = 250 for the skewed processes.
     - Options measured: A (revision 1), B/2, B/4, B/10, C (Hall's skew-corrected t), D (at least 12 batches) and E
       (worst-case calibrated thresholds).
   - **Real skew, measured on exposed 2024-26 close-proxy data.** QLIKE differences of baseline pairs have a raw skew
     of -17 to +15. Their batch means have a skew of up to 7.5 at L = 5, 4.9 at L = 10 and 3.5 at L = 20; the
     lognormal case has 2.8, 2.0 and 1.4. **The lognormal case understates reality**, so the calibration targets the
     empirical nulls (some evidence: exposed data, a few pairs).
   - **Results at Holm's first step (0.0013), on the real nulls at n = 125:**
     - A: 6-18% at L = 5 and 10; still 7.5-10% at n = 250.
     - B/10: 2-13%.
     - C (Hall's correction) is no better than A.
     - The Brier V6a null fails A at n = 125 (0.8%) and badly at n = 10 (17%).
   - **The operative rule is E+D:** at least 12 batches, and a batch t p-value at or below the worst-case calibrated
     threshold for the member's question, n and look. The threshold is computed at the look by
     `tools/v4_claim_thresholds.py`, taken at the 95% lower confidence rank of the quantile.
   - **Held-out sizes** (fresh seeds, 100,000 series) are within nominal + 2 SE in all 30 cells (strong evidence for
     the measured processes).
   - **Power cost** (normal approximation, planning only), in outcomes at r = 3 / r = 5, against 134 / 316 for the
     plain first step:
     - V1: 426 / 1,183.
     - V2: 396 / 1,099.
     - V6a: 180 / 499.
     - V6b and V7: 151 / 419.
   - **Consequence, said plainly:** V1 and V2 (QLIKE) cannot be claimed in useful time.
   - **Code:**
     - `confirmatory.calibrated_p` and `MIN_CLAIM_BATCHES`.
     - `family.py` now uses Bonferroni at rate / 15, because only the first step is calibrated (Holm's later steps
       are dropped).
     - `hall_t` was measured and is kept as a reported option.
     - Tests: `test_claim_rule.py`, a `hall_t` test, and the family tests.
2. **Must-fix 2, thresholds below 0.01 at 50,000 or more series with B = 10,000: DONE.**
   - The thresholds below 0.01 now use 100,000 series.
   - Revision 1's 1,000-series figures are relabelled "superseded; some evidence only".
3. **Not tested:** futility's percentile bound under the same heavy-tailed nulls. It may give a false "no" too; this
   is disclosed in protocol section 11.

## Revision 3: false futility (orchestrator, after revision 2)

- **The test.** `tools/v4_futility_study.py` builds empirical nulls from exposed 2024-26 data (disclosed). Each one
  pairs the real daily loss difference with the real baseline loss: QLIKE for V1 and V2 (gate set RV > 0, textbook
  baseline loss) and Brier for V6a and V6b. The difference is shifted so the true relative improvement equals the
  registered minimum effect exactly (3% QLIKE, Brier skill 0.02). It is tested in both orientations, resampled jointly
  in circular 20-session blocks, at n = 125 and n = 250, at both looks.
- **Revision 1's rule (F0, the 97.5% bootstrap bound)** gives a false "no" far too often (10,000 series per cell,
  tolerance 2.81%). The target is at most 2.5% per look.
  - V1: 27% at n = 125, 23% at n = 250 (the rare-big-gain orientation).
  - V2: 32% and 23%.
  - V6a: 16-17%.
  - V6b: 7-12%.
- **The operative rule is now F+D** (`confirmatory.futility_p`). A member can be called futile only with at least 12
  batches and a batch-means t p-value for "improvement below the effect" at or below its worst-case calibrated
  threshold. That threshold is the 2.5% quantile at its 95% lower confidence rank, over both orientations, computed at
  the look for the member's n.
- **F+D's held-out false-futility rate** (100,000 series per cell) is 0.0-2.6% in all 16 cells, within the 2.60%
  tolerance (strong evidence for the measured nulls). The worst cell is V2 at n = 125: 2.58%.
- **Tests.** `test_futility_rule.py` checks the rule's mapping, the 12-batch minimum, that the fast bound equals
  `effect_check`, that the nulls sit exactly at the minimum effect, and the committed table.
