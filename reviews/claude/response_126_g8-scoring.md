# Response 126: story G8, protocol v4 scoring (story text)

Branch `story/g8-scoring`, from main 36d2db8. Text only: `docs/stories/G-forecasts.md` section G8. Code starts after
judge D's PASS.

## What I checked before writing (evidence labels as the project uses them)

- **Every rule G8 needs is already in `fno/forecast_v4/`** except the owner's crash-share cut (strong evidence: code
  reading). `confirmatory.judgeable` has only the 5-day gate; the cut exists only in `tools/v4_crash_cut.py` (a
  study), and the protocol's section 11 E still lists three options. The owner chose option 2 on 15 Oct
  (`DESK_DECISIONS.md`). Proposed to the orchestrator: one function beside `judgeable` and one protocol line, so it is
  frozen with the protocol.
- **The thresholds live in `tools/`, not `fno/`:** V1 and V2 use `claim_threshold` and `futility_threshold`, V6a and V6b
  use `v4_brier_bands.operative_thresholds` (the banded rule of revision 5; `v4_brier_regimes.operative_thresholds`
  is the superseded revision 4). `claim_threshold` takes the look's rate and divides by 15 itself (strong evidence:
  code; calling it with rate / 15 would square the correction).
- **Runtime** (some evidence, one run here): 17 s (V1 claim, n = 125), 7 s (V1 futility), 56 s (V6b, band 5-7), so a
  look of up to 12 judged members takes minutes. V1's claim threshold at n = 125 came out 1.1e-12, as the protocol
  says (effectively unreachable).
- **The 13+ band at n = 125:** 13 / 125 = 10.4% > 10%, so the cut makes it unreachable; usable from n = 130 (strong
  evidence: arithmetic).

## Choices, for the judge

1. **G8 resolves outcomes** for V1-V3, V6 and V7 (one place); asked the G7 builder through the orchestrator whether
   G7 does too. V4 and V5 are out: they need A16 ATM quotes and expiry-settlement wiring (reasoning: no real input
   exists yet).
2. **Calibration slope and intercept** are an OLS of the outcome on the probability, the same function as
   Mincer-Zarnowitz (DRY; reported only, never a verdict). A logistic recalibration is the textbook alternative;
   not chosen because it changes no decision (owner's rule).
3. **Seed words** of non-member comparisons: `16 + crc32(question/forecaster) mod 2^31`, stable when forecasters are
   added (reported sensitivities only).
4. **Futility uses the gate set and its own n** for the threshold (the protocol's 5.5 defines futility on the gate
   set; the tools calibrate at the n they are given). For Brier questions both sets are the same.
5. **Before the freeze nothing is written as a look record**; every output says EXPLORATORY.

## Revision 1 (orchestrator decisions 69 and the G7 agreement)

- The crash cut is `crash_dominated(big_days, n)` in `fno/forecast_v4/confirmatory.py`, added in this branch, with
  the boundary test 12 / 125 judged and 13 / 125 cut. The protocol's section 11 E line is the G6 session's, in the
  freeze commit; named as a freeze dependency, not edited here.
- Outcomes: G8 imports G7's `fno/forecast_v4_rules/series.py` (one place per rule); choice 1 above is withdrawn.
- Forecast files: G7's agreed layout, `research/forecasts/v4/<forecaster>/<question>.csv`, `day,value,status,label`
  first.
- Found while checking names (strong evidence: `fno/constants.py:168`): the EWMA baseline's constant is `ewma_094`,
  but G7's folder id is `ewma`. It is a reported baseline only (no primary uses it), but one name is needed; told
  the G7 builder.

## Build claims (text passed: judge 128, 02cb2b8)

Branch `story/g8-scoring`, merged with `story/g7-baselines` at be7f166 (G8 imports G7's `series.py`; merge, not
rebase). Code in `fno/forecast_scoring/v4/` (largest file 107 lines), `crash_dominated` in
`fno/forecast_v4/confirmatory.py`, tests in `tests/forecast_scoring_v4/` and `tests/forecast_v4/test_crash_cut.py`.

| Criterion | Where | Test |
|---|---|---|
| 1 outcomes | `outcomes.py`, `g7_series.py` | `test_outcomes.py` (V2 by hand across 1 Nov 2024 muhurat; V7 strict incl. a tie; V1 ok/void/unresolved), `test_g7_series.py` (all 2017-26 V6b outcomes through G7's rules equal the hand rebuild) |
| 2 scores | `scores.py` | `test_scores.py` (hand values; zero-RV day in QLIKE, out of textbook) |
| 3 comparison | `comparison.py` | `test_comparison.py` (real 2024-25 V6b: pairing, D, effect, 4 p-values and regime equal direct calls) |
| 4 gates | `look.py`, `confirmatory.crash_dominated` | 4/5 days, 12/13 of 125, 25/26 of 250; `test_crash_cut.py` |
| 5 thresholds | `thresholds.py` | fake tools record (q, n, look rate) and the Brier look names; real claim tool below 12 batches; futility asked with the gate set's n (V1 with 10 zero-RV days: 125 vs 115) |
| 6 family output | `look.py` | 15 members, header with look, rate, timestamp; a regime line under every member; V7 at p = 1 |
| 7 Test A | `look.py` | no registration: undecided; equals `forecasting_test` |
| 8 labels | `records.py`, `cli.py` | EXPLORATORY before the freeze and `look` writes nothing; after it recorded once, second write refused |
| 9 empty | `scoring.py` | V4, V5 "not started"; no forecasts "not enough data yet" |

**Broken-code proof (strong evidence; each run with `python -B` on the G8 tests): 10 of 10 caught.** M1 off-by-one
horizon; M2 zero-RV date dropped from the QLIKE mean; M3 `>=` for the crash cut; M4 the scored n for futility; M5 a
look record overwritten; M6 crash cut not applied at a look; M7 5-day gate not applied; M8 closed members judged
again; M9 regime from the wrong session; M10 V7 not strict.

**Real end-to-end (rule 8 style, scratch worktree, nothing committed):** G7's `forecast v4-backfill` (2,409 days,
9,636 rows, labelled exploratory), then `forecast-v4 report`, 3.5 s:
- V6a: G7's `v6_ewma_t4` against the base rate, 1,908 scored pairs: Brier skill 0.145, batch-means p 0.007; regime:
  mean VIX 17.1, 94 2% days.
- V6b: 1,900 pairs, Brier skill 0.171, batch-means p 0.006.
- **Exploratory only:** 2017-26 is spent data (protocol 8). The power report says 52,000-104,000 independent
  outcomes are needed (centuries). That is the protocol's own formula: it sizes detection of the 2% minimum effect,
  not the larger observed one, and r is 60-87 because Brier differences are dominated by rare 2% days (some evidence).
  It is G6's rule; G8 only prints it. Worth the owner knowing: as frozen, V6 can never settle in useful time by that
  projection.
- A demo look (a scratch script registering V6a and V6b `rules` to `v6_ewma_t4` on the last 255 back-fill days, real
  frozen thresholds): 2 judged, both p 1.0 (open), regime mean VIX 14.0, 8 2% days, band 8-12, Test A undecided;
  2 min 27 s.

**Not done (stated):** slot registrations are `NoRegistrations` until the freeze writes its ledger row (its adapter is
one class plus one line in `wiring.py`); V4 and V5 outcomes; the proxy-drift diagnostic (phase 2).
