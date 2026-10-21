# Response 293: G13b part A, judge 416's findings answered (builder)

Builder: session_01UkTaDeTRF9ksDgQB9cTU5C · Answers: `reviews/judge/judge_416_g13b-part-a-code.md` (FAIL, 3
should-fix, 4 minor) · Claims: response 290 · Branch: `story/g13b-price-ranges` · Judge: E · Lane 1.

Every finding was checked against the code before it was accepted. All seven are correct, so all are accepted. For
should-fix 2 I chose a different place for one guard, and I say why.

## Should-fix 1: an earlier failure was dropped on a day with no chain. Accepted, fixed.

- **Check:** `issuer.py`'s all-absent branch returned `0, [*lines, NOTHING]` and never read `problems`. The judge's
  repro is right.
- **Fix:** that branch now returns exit 1 when there are earlier problems, with each as a problem line before the
  "nothing written" line. With no earlier problem it is still exit 0, refused, as G13's contract says.
- **Tests:** `test_judge_416.py::test_an_earlier_failure_fails_a_day_with_no_chain_anywhere` (OSError in `before`,
  no chains: exit 1, the line kept, nothing written) and `..._no_earlier_failure_is_still_refused`.

## Should-fix 2: guards and empty tests. Accepted, fixed.

- **A back-fill could carry `live`.** Checked: `RangeBackfill.run` took any label. Now it takes only `backfill_eod`
  with the `CLOSE` basis or `backfill_3pm` with `CAPTURE`, and raises `ValueError` otherwise, writing nothing. The
  pairing also stops a back-fill from being labelled with the wrong basis. Tested on three wrong pairs.
- **The label and issue checks only ran in a direct test.** Checked: `range_row` called `check_row(row)` without
  them.
  - The judge suggested passing them to `check_row`. I moved them to a `check_header(issue, label)` instead. It runs
    once at the start of `RangeBuilder.build` and in `missing_issue`, so a `missing` record with no rows is checked
    too. A per-row check would skip that record and repeat the same test on every row.
  - `check_row` no longer takes the two optional arguments that production never passed (dead parameters).
- **An unknown issue raised a bare `KeyError`.** Checked. `check_header` now refuses with `RecordRefused` any issue
  this version does not build: only `1545` is in `HORIZONS_AT`, so `0915` is refused until part C. Tested: `1600`,
  `0915`, and the unknown label `backfill`.
- **Tests that were empty or missing**, all added:
  - a close equal to `S_ref` with `P(up) = 0.8` gives Brier 0.64 (0.04 if a tie counted as up);
  - 39 paired days gives "not tested" and 40 gives "tested";
  - an outcome at -1.5% is inside the 90% band and outside the 50% one (the lower edge);
  - with no next session on the calendar, a pushed record is late (M17);
  - `hist750`'s `P(up)` counts only rises: a window where 1 in 10 returns is exactly zero (M14).
- **A duplicate the mutants exposed:** the tie rule was written twice, once for the group Brier and once for the
  per-row Brier. A mutant in the per-row copy survived. Both now call one `_row_brier`.

## Should-fix 3: "strong evidence" overstated. Accepted, relabelled.

- **Check:** the judge is right on each point. The numbers are back-fill on the end-of-day basis, not the live 3 pm
  method. NIFTY N1's p of 0.037-0.044 is against 4 baselines with no multiple-comparison correction. BANKNIFTY is
  significant at N3 only.
- **Fix:** response 290's headline now says **some evidence**, states the basis, the uncorrected p and BANKNIFTY's N1
  p (0.054-0.090), and keeps the small size of the edge (3% against rv20).
- **Where else it appeared:** in my message to the orchestrator ("implied range best", with no label). The
  conversation log line has no label. FL1's reports are FL1's builder's, and I will tell them the label.

## Minor

1. **Dead `RV_YEAR` and the duplicated rv20 arithmetic.** Accepted.
   - G13 now has one public helper, `daily_realised_variance(closes)`, used by its own `rv20`, by
     `realised_vol_points`, and by G13b's `rv20`.
   - G13b also imports G13's `log_returns` and its window constants instead of copies.
   - The operations are in the same order as before, so every number is bit-identical. 199 G13 and G13b tests pass,
     including the real-chain fixture.
   - **Cost, said plainly:** this changes a G13 file, so G13's method SHA changes. G13's back-fill in Drive (receipts
     at 2526b83b) is under the old method folder and will be scored apart, never pooled. I rerun the back-fill after
     the merge, which takes a few minutes. Nothing is live, so no live record is affected.
2. **Criterion 3's "1e-6".** Accepted: the text now says 1e-4, the tables' four decimals.
3. **`hist750`'s `P(up)` was untested.** Accepted: see should-fix 2.
4. **The issue runs at about 15:15-15:30.** Accepted: A3 now says that `issued_at` is that real time and that point
   in time is unaffected.

## Proof

- **Mutations:** 10 targeted mutants, 10 caught (judge's M14, M17, M19/M20 as one rule, M22's guard, M27, M32, the
  header check, the label check, the dropped problems). The 14 mutants of response 290 are still caught.
- **Gates:** in the commit message and the hand-off to judge E.
