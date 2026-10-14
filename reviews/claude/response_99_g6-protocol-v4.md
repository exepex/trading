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
