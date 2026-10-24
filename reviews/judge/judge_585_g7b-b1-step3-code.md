# Judge 585: G7b completion code, part b1 and step 3, `story/g7b-completion` at bde56bbe2 (round 1 of 2, judge K)

**FAIL, lane 1.** 1 should-fix (three untested rules), 3 minor. The code itself matches the passed text (judge 578.1).
A trial merge into origin/main (56bb0f05e) is clean. Gates on that merge: `pytest -n auto` 15,356 passed, 1 skipped,
15 xfailed, exit 0; ruff check and format clean; `check_imports`, `check_records` and `check_numbers` clean.

## Criteria (this slice)

| # | Criterion | Verdict | Own evidence |
|---|---|---|---|
| 1 | EOD IV30 proxy from 2024, flagged kept with their flag | MET | `eod_iv30.py`; the panel's 100-day filter changes no IV30 value or flag: 249 sessions of 2025, filtered against unfiltered, 0 differ (my script) |
| 2 | Raw implied over calendar days to `d+h`; flagged, past-calendar and 0 give missing | MET | `implied.py:83-87`; plants "one session short" and "flagged kept" caught |
| 3 | Ratio window, median, monthly refit (the stored ratio is b2, not this slice) | MET | `PremiumRatio` calls `premium_ratio_window`; plants "resolved one session early" and "ratio at `d`" caught |
| 4, 5 | V2/V3 premium-adjusted; back-fill exploratory, before the first live day, write-once per hash and last day | MET | `implied_backfill.py`; the closes-against-sessions guard (`wiring.py`) stops row misalignment; plant "first live day included" caught. The reader and the hash gate are part e, and the Claims say so |
| 6 | Live quote (A4's `traded_today` imported), 5% in exact decimals, V5 `e` from listed monthlies | PARTLY | rules right (`live_quotes.py`, `option_terms.py:96-110`); "first monthly" is not proven by a test (SF1c) |
| 7 | V5 option-implied probability | MET | I recomputed `v5_golden.json` independently (60-digit decimals, erf series): 0.5068528873171638536...; plant "drift sign" caught |
| 8 | V5 outcome: expiry-day file, strict inside, `CreationTimes` then A8's log | PARTLY | `option_outcomes.py:48-67` right; the order is untested (SF1b) |
| 9, 10 | V4 terms from `v4_expiry`, 5-session re-check, parity forward, session clock; outcome on live A16 rows | MET | plants "parity sign", "4 sessions accepted", "resolved by first row" caught; `v4_golden` reproduced in the suite |
| 11 | Base-rate inputs known only when first seen | PARTLY | V4 uses the latest row's first-seen date (`option_outcomes.py:89`); V5's dating is untested (SF1a) |
| 12 | `v5_ewma_lognormal`, `v4_ewma_chi2`, chi-square(5) | MET | formulas as the text; plant "calendar IV in chi2" caught |
| 19 | Size, design, no re-implementation | MET | largest file 145 lines; `settlement.v5_outcome`, `units.v4_outcome` and `premium_ratio_window` are called, not copied |

## Findings

1. **Should fix: three stated rules survive a planted break.** Each needs one test that fails when the rule is broken.
   - **a. V5's base-rate outcome dated by the expiry, not the IST date of `first_seen_at`, survives** (`v5_base_outcome`). The only test has the file first seen 5 hours after the close, the same date. A file first seen days later would then enter the base rate before it was seen: a point-in-time break. Fix: a case where the file is first seen on a later IST date, and `resolved_on` must equal that date.
   - **b. A8's log before Drive's `createdTime` survives** (criterion 8's order). Fix: a case with both times present and different; Drive's time must win.
   - **c. A pack future on the second monthly is accepted as V5's `e`** (planted `future_expiry not in after`). Fix: a case where the future is the next-but-one monthly, expecting `future_not_monthly`.

## Plants

- **The builder's:** step 2's 13 and step 3's 21 are in the Claims; 9 of them overlap with my own plants (all caught); the rest I did not re-run.
- **My 20:** 16 caught. The 4 survivors are SF1a, SF1b and SF1c above, and minor m1.

## Minor

- **m1:** the inputs hash without the refit ratio survives. It is an audit field, so this is not blocking.
- **m2:** `IMPLIED_METHOD_FILES` leaves out `fno/forecast_v4/eligibility.py`. It is hashed only at the v4 freeze, which is response 250 item 10's accepted reasoning. A change of config rate or panel data under the same hash and last day ends in a write-once refusal: loud, never silent.
- **m3:** V5 terms are void (`calendar`) for days whose monthly is in 2027 until the 2027 calendar rows land. Counted; the operations note covers it.

## Rulings asked for

- **`v4_expiry.py` in phase 1's `METHOD_FILES`: pushback accepted.** None of the five hashed files imports it (grep). Adding it would move the hash of 9,636 rows with no value changed. **Condition, now a criterion for the live-capture step:** every V4 and V5 row carries its own method hash over `v4_expiry.py`, `live_quotes.py`, `option_terms.py`, `option_probabilities.py`, `option_outcomes.py`, `implied.py`, `series.py`, `baselines.py` and `records.py`. A gate test fails when any committed or Drive row's hash differs from the tree's.
- **Deferring the HAR fold: accepted as minor.** `first_session_of_month` and `Har.refit_day` are the same rule on the same scored sessions today. Until the step that regenerates phase 1's back-fill folds them, a test (outside `baselines.py`) should assert that both give the same day for every month of the calendar, so a drift cannot slip in.

## Notes

- No look-ahead found otherwise: the window points are resolved before the refit day; V4's resolution date is the latest A16 row's first-seen date; base rates count only outcomes resolved strictly before `d`.
