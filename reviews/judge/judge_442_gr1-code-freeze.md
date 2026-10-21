# Judge 442: GR1's study code and hash freeze, before run 1 (story/gr1-sharper-ranges at d43877e7)

Judge B, 22 Oct 2026 (IST). Builder: G13b/GR1 (session_01UkTaDeTRF9ksDgQB9cTU5C). This follows judge 428 (the
protocol), as protocol section 12 step 2 requires. Number claimed with `tools/claim_number.py`.

## Verdict: FAIL (3 should-fix); deviation 3 is accepted

The code is careful:
- the seal comes first: final records are dropped before any outcome is looked up;
- cues are read by A17's own rule;
- events are counted only if announced before d;
- C11's pair is chosen on train;
- selection uses paired differences, Holm runs across winners only, and C0 is checked against the bands;
- the guard refuses on git state;
- 23 of 23 of the builder's planted bugs are caught.

Three things must change before run 1. Each would make a registered test mean something other than what the protocol
registers, or would push part of the final-period reading outside the frozen code.

## What I verified myself (on d43877e7)

| Item | Result |
|---|---|
| Code hashes | `sha256sum -c` on all 15 rows of `FREEZE.md` "Analysis code": all OK. `PROTOCOL.md` is `3293c2bf...` and `probe.csv` is `abeae36d...`, as the deviation-3 section records |
| Seal | `rows.implied_rows` applies `periods.sealed` before `close(...)`. `inputs.up_to` caps VIX, RV and the 09:15 opens at the last sealed day. `n0_pairs` is sealed by the target day. `run_final` takes C3's and C10's train statistics from `selection.json` |
| Cues | `cues.cue_move` uses `value_for(live_only=False)` with each source's `available_at` and `max_age_days`. USD/INR is read at 09:15, so it is d-1's rate. Never a raw value date |
| C5 | only events with `announced_on < d` count |
| C11 | chosen by the mean QS gain against C1 on each candidate's own train days |
| Selection | the most negative paired mean difference against C0 among eligible candidates. Eligible means: fitted, no crossing on a select day, no gap over 5% on train or on select, and both bands |
| Final | `final_cell` and `decide`: G4's `compare` (two-sided), Holm across the cells that have a winner, every check, `NOT_SHOWN`, and `known_before_the_study` for C1 and C2. C0's final bands are reported |
| N0 | the centre is the 09:15 open, the scale is sqrt(0.607) around implied's median, and the outcome is ln(close / open). N0-B and N0-C are chosen against N0-A under the bands. No Holm |
| Guard | refuses on a hash mismatch, an unhashed `.py`, an uncommitted study folder, a `selection.json` that is uncommitted or modified, and a `final.json` now or in any commit (`git log --all`) |
| Probe | its close is a constant, it computes no score, and it holds no 2025-26 row |
| Tests | `tests/research_gr1`: 34 passed. `mutation_proof.py`: 23 of 23 caught |

**Gates** (clean `__pycache__`):

| Gate | Result |
|---|---|
| `pytest -q -n auto` | 8,999 passed, 17 xfailed |
| `ruff check fno tests tools` | clean |
| `ruff format --check` | 1,667 files formatted |
| `check_imports` | clean |

## Deviation 3: accepted

1. The probe found C7 with inputs on 422 of 1,222 NIFTY N1 train days.
2. The cause is a hole in RBI's public USD/INR table from 24 Jul 2018 to 12 Apr 2022, when FBIL took over the
   benchmark.
3. The fix is to fill RBI's dates with FBIL's rows. A17's README records the two equal on all 1,086 dates both
   publish, and they are read under RBI's rule.

This is legitimate:
- it was found by counting inputs only, with no outcome read and no score computed;
- it was made before the code freeze;
- it changes no candidate, period, score or decision rule;
- it is recorded in section 14, and the protocol was re-frozen (23c9ce50, with the ledger rows updated).

FBIL's rows live in private Drive, which meets DESK_DECISIONS row 281 point (1). The section 13 gap rule now running
on train is as written.

## Should-fix 1: the fit's bound of |theta| <= 3 is in raw units, so small conditioners cannot express a real effect

`fit.py` bounds every coefficient at 3 and calls a parameter at the bound a failed fit (a grid-edge hit). The
conditioners differ in size by orders of magnitude. I measured them on train dates (conditioner data only, no
outcomes):

| Conditioner | Median absolute value | 90th percentile | Largest scale at theta = 3 |
|---|---|---|---|
| USD/INR log move | 0.0012 | 0.0039 | x1.004 at the median, x1.012 at the 90th percentile |
| US 10-year move | 0.03 points | 0.10 points | x1.09, x1.35 |
| India VIX log change (C4) | 0.026 | 0.078 | x1.27 at the 90th percentile |

The S&P 500's daily log move is of the same order as USD/INR's (about 0.006 at the median, 0.017 at the 90th
percentile), so the bound caps it near 2-5%. The same holds for N0-C's two conditioners: the overnight gap
|ln(open / close)| and the S&P move.

**Why this is a normal path, not an imagined one:** a plausible true effect, for example a 2% S&P move making the next
range 20% wider, needs theta of about 9. The search then walks to 3 and reports "grid edge hit". C7 and N0-C would be
recorded as failed fits, counted, and never tested. The candidates the owner asked about most ("news, data from
different sources") would be the ones the code cannot test. Dummies and log-ratio conditioners (C3, C5, C6, C8, C9,
C10) are fine at 3.

**Fix (before run 1, recorded as deviation 4).** Standardise each non-intercept conditioner by its train-period
standard deviation, from the candidate's own train days, and store it in `selection.json` for run 2 as the VIX
statistics are. Then theta = 3 means "a one-SD move scales the range by e^3" for every candidate. Alternatively, set
per-conditioner bounds. Then:
- add a test that a planted large effect on a small-unit conditioner is recovered, not reported as an edge hit;
- re-freeze the hashes.

## Should-fix 2: C6 uses every file's expiries pooled, not d's own file

Protocol section 3 says C6 reads "the expiries of the index's options in d's archived F&O file". `inputs.expiries`
builds one union of every file's expiry dates, and `_expiry` tests that union, so an expiry date listed only in a
later file counts at d.

**Why this is normal running:** when NSE revises existing contracts' expiry dates, the union holds both the old and
the new date. Examples:
- BANKNIFTY weeklies moved from Thursday to Wednesday in Sep 2023, inside the train period;
- NIFTY moved to Tuesday in Sep 2025, inside the final period;
- ad hoc holiday reschedules.

In each case, a horizon can be flagged by a date that was not, or was no longer, an expiry at d. That is look-ahead
in one direction and stale data in the other, on the very regime breaks the protocol lists.

**Fix.** The cache already keeps each day's own list (`cached["files"][day]["expiries"]`). Make C6 read d's list,
with None when d's file is missing, then:
- add a test where a later file's revised date must not count at d;
- re-freeze.

## Should-fix 3: C9 "split at the regime breaks" is promised by the protocol but not produced by the frozen code

Protocol section 6 says: "C9's weekday effect may change at those dates; the results report C9 split at them". No
code splits C9: `selection.json` and `final.json` hold whole-period aggregates only.

So the split could only be made later by unfrozen analysis on the final period. That is exactly what section 12's
"read once, by frozen code" forbids.

**Fix.** Have runs 1 and 2 report C9's numbers (days, both coverages, mean QS difference) split at the stated dates:
- BANKNIFTY weeklies ended in Nov 2024 (state the exact last weekly expiry);
- NIFTY's expiry moved to Tuesday in Sep 2025 (state the exact first Tuesday).

This is descriptive only. Pin the dates in a test, and apply the same reasoning to any other per-subperiod number the
results will quote.

## Notes (one line each)

1. **The seal is by issue date, as frozen.** The last select-period N3 rows (30-31 Dec 2024) read early-January 2025
   closes as outcomes. No final-period candidate number is computed. Say so in the results.
2. **A cue's move after a gap is measured against the row before the gap.** For example, FBIL's 29 Jan - 16 Feb 2021
   gap gives a multi-week move. Rare; consider requiring the prior row within the age limit too.
3. **`dropped_reason` is one generic text.** The protocol asks for "why". Naming the missing input (VIX d-1, a cue, RV)
   would meet it better.
4. **The judge needs to be able to reproduce run 2 after the fact.** The guard refuses once `final.json` exists, and
   that is right for the CLI. Calling `run_final` with the committed `selection.json`, outside the CLI, lets the judge
   reproduce it; keep `run_final` side-effect free, as it is now.

## To pass

1. Should-fixes 1-3, with tests.
2. Deviation 4 recorded in section 14 before run 1. It is a code and parametrisation change with no rule change; say
   so.
3. New code hashes in `FREEZE.md`, and the ledger's `protocol_commit` updated if `PROTOCOL.md` changes.
4. Then I re-check.
