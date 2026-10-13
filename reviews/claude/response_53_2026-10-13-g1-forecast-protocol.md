# Response 53: G1 forecast protocol and the 30-day ATM implied-volatility estimator, builder's claims for the judge

Story: `docs/stories/G-forecasts.md` section G1 (issue #62).

**In short:** `research/forecasts/PROTOCOL.md` version 1 is written and frozen. The protocol commit is `f936156`, and
`research/forecasts/FREEZE.md` (the next commit) records it with the SHA-256 of 8 frozen files. The five questions'
targets have reference code (`fno/forecast/targets.py`), and so do the 30-day ATM IV estimator (`fno/forecast/iv30.py`),
the record schema (`fno/forecast/schema.py`) and the frozen 45-comparison family (`fno/forecast/comparisons.py`).
Ledger trials 32-36 were registered in the protocol commit. No forecast exists, and no real outcome was computed.
Evidence: strong for the code (tests with hand-worked values); reasoning only for the protocol's method choices
(section "Choices", below).

## How to check

```
python -m pytest -q tests/forecast tests/research/test_ledger_guard.py
git log --oneline -3 -- research/forecasts      # protocol commit f936156, then the freeze commit
ruff check fno tests tools && python tools/check_imports.py
```

## Acceptance criteria

| # | Criterion | Code | Test (`tests/forecast/`) |
|---|---|---|---|
| 1 | Each target matches hand-worked values on fixture data, all five questions, a holiday inside the window | `targets.py` `ForecastTargets` | `test_targets.py`: a fixture calendar with holidays on 26 Jan and 17 Feb and a muhurat session on 22 Feb. d = 2 Feb, d+10 = 16 Feb, d+20 = 3 Mar, counted by hand. Trailing RV 15.8745 and next RV 34.0470 by hand. All five outcomes, ties, an exact 3% move, a missing close (void), a target beyond the data (void) |
| 2 | IV30 matches a hand computation on two fixture days (bracketed and not) | `iv30.py` | `test_iv30.py`: bracketed 14.4937 points (w1 0.2704, w2 0.99, w30 0.6302); not bracketed (the far put did not trade) 13.0, flagged. Also: exactly 30 days, the 7-day minimum, the tie going to the longer expiry, and an expiry on its last day |
| 3 | Protocol frozen; its commit precedes the first scored forecast (checked by G4) | `freeze.py` `require_frozen_before` | `test_freeze.py`: in a temporary repository, a commit before the freeze record is refused, a frozen file edited after the freeze is refused, and a freeze naming another protocol version is refused. Also the repository's own freeze passes at HEAD |
| 4 | The multiplicity method (questions x book pairs) is named with its exact procedure before scoring | PROTOCOL.md section 8, `comparisons.py` | `test_schema_and_family.py`: 45 comparisons in the protocol's order, plus the protocol text naming Holm, 5%, L = 20, B = 10,000, the seed, and "Only Brier is tested" |

Look-ahead: `test_iv30.py::test_no_lookahead_on_10_random_real_days` runs B1's harness (`assert_no_lookahead`) on IV30 as
a feature on 10 random 2025-2026 days. Every panel value after the day's close is changed or removed, and IV30 does
not move. The targets are outcomes, so they read the future by definition; their "today" parts (trailing RV, IV30) use
only data up to `d`.

## Reuse (no second implementation)

- **IV:** B1's ATM IV code moved, unchanged in behaviour, into the shared function
  `fno/research_engine/volatility_features.atm_implied_vol_points`. F1, the IV30 estimator and (through B1's
  `ImpliedVolModel`) C2 now use one implementation. F1's and B1's tests pass unchanged.
- **Realised volatility:** B1's `realised_vol_points`.
- **Trading days:** A7's `SessionCalendar`.
- **Monthly expiries:** A5's futures rule.
- **Freeze check:** B4's `Git`.

## Choices I made (please challenge them; all reasoning only)

1. **Muhurat sessions are not trading days for the targets**, matching B1. Special weekend sessions count.
2. **Ties are "no"** (strict comparisons). The exception is question 2's "at least 3%", which uses the simple return, as
   the story says "return".
3. **IV30 bracket:** `e1` is the latest monthly expiry with 1 to 30 days left, so an expiry on its last day is never
   the near leg. **Fallback** to a single expiry is flagged: 13% of days in 2019-2026, mostly in 2019-2020 (84 and 80
   days), where the next month's ATM call or put often did not trade. Measured, protocol section 3.
4. **Baselines, written into the protocol so G2 cannot tune them later:**
   - (a) **Lognormal risk-neutral**, using IV30 and the carry from the near future. I did not use Breeden-Litzenberger:
     sparse, often untraded far strikes would make the smoothing choice decide the answer.
   - (b) **Base rate** over 750 resolved days, with at least 500 needed.
   - (c) **Statistical models with an empirical residual distribution**, refitted monthly: a HAR-type log-RV model on
     RV5, RV20 and RV60 (questions 3 and 5), and VIX mean reversion (question 4).
5. **Book 1** is the mean of the question's two baselines (G3 says "a fixed rule written in the protocol").
6. **Multiplicity:**
   - **Scope:** only Brier is tested. All 45 comparisons count from the start, and those not yet possible are given
     p = 1, so the correction never weakens.
   - **Test:** a moving-block bootstrap (L = 20, B = 10,000, a seed per comparison) gives a centred two-sided p-value.
     Holm's step-down is applied at 5% family-wise.
   - **Thresholds:** fewer than 40 paired dates is not tested. Nothing is called significant before the 6-month review.
7. **Freeze scope:** the checked files include B1's `implied_vol.py`, `volatility_features.py` and `close_series.py`,
   because IV30 and RV depend on them. **Consequence for other builders:** any later edit to those three files fails
   `test_freeze.py` and needs a new forecast-protocol version. The calendar, the panel manifest and `config.yaml` are
   recorded but not checked, because they grow with data.

## Open points and limits

- **The protocol is frozen before any outside review.** ChatGPT has not reviewed it. A change it asks for becomes
  version 2 (a new file and a new freeze) before any forecast is scored, so nothing is lost but the version number.
- **Live inputs come from the market pack (E2), which does not exist yet**, so there are no live forecasts until E2.
  History uses closes as a proxy for the 15:00 cutoff, and is labelled so.
- **Coverage:** the baselines need 750 earlier resolved days. Questions 1-4 can be back-filled from about 2020, and
  question 5 from about 2021-2022.
- **Previously seen:** the access attestation in FREEZE.md lists what touched these questions before the freeze: desk
  meeting 1's trend persistence and B1's F1 measurements.

## Addendum (judge 47: FAIL, one should-fix and one process point; both accepted)

**Should fix, accepted: the freeze locked the bytes of shared library files.** The judge is right. Forecasts are scored
for months, and checking B1's `implied_vol.py`, `volatility_features.py` and `close_series.py` byte for byte would turn
every unrelated refactor of code shared with F1, B7 and C2 into a failing test and a new protocol version. That breaks
the owner's "design for change" rule. Fix:
- **Golden file.** `research/forecasts/golden_iv30_rv20.csv` holds IV30 (value, flag, expiries) and trailing RV20 for
  all 1,921 panel trading days from 2019 to 12 Oct 2026; both are known at the forecast date. `fno/forecast/golden.py`
  computes it, `tools/forecast_golden.py` writes or checks it, and `fno/forecast/wiring.py` is a new composition root
  (added to CLAUDE.md; `fno/composition.py` stays at 320 lines).
- **Test.** `tests/forecast/test_golden.py` recomputes every day with the current code and requires equality within
  1e-12 points. It also proves that a changed value, a flipped flag and a missing day are each caught. The hand-worked
  values stay as fixture goldens in `test_iv30.py` and `test_targets.py`.
- **What the freeze will check.** `PROTOCOL.md` section 10: this file, `fno/forecast/*.py` and the golden file's hash.
  The shared library is recorded, not byte-checked. An A11 panel revision may move golden values only if it names the
  revision.

**Process, accepted (orchestrator decision): a G-protocol is frozen only after ChatGPT agrees.** I undid the freeze:
- `FREEZE.md` is removed.
- Ledger trials 32-36 have an empty `protocol_commit` again; they stay registered.
- The repository-level freeze test is removed. `require_frozen_before` and its unit tests stay for G4.
- `PROTOCOL.md` status is "draft version 1, awaiting ChatGPT review".

The review request is `reviews/claude/response_56_g1-protocol-for-review.md`. Criterion 3 (frozen before the first
scored forecast) is therefore not met until the agreed version is frozen. No forecast exists, so nothing is lost.

