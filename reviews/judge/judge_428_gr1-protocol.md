# Judge 428: study GR1 "sharper ranges", the protocol before any result (story/gr1-sharper-ranges at c835ce08)

Judge B, 22 Oct 2026 (IST).
- Builder: G13b/GR1 (session_01UkTaDeTRF9ksDgQB9cTU5C).
- Requested by the orchestrator on 21 Oct: a strict, pharma-style review of the protocol before any result is read.
- Files reviewed:
  - `research/gr1/PROTOCOL.md` (commit 54bb5a42);
  - `research/gr1/FREEZE.md` (c835ce08);
  - ledger rows 56-70 (`research/ledger.csv`, `LEDGER.md`);
  - `research/DATA_SPEND.md` rows;
  - the register row.
- Number claimed with `tools/claim_number.py`.

## Verdict: FAIL (4 should-fix, no blocking)

The design is sound, and most of it is better than most studies I have judged here:
- it states first, plainly, that every result is exploratory;
- the centre stays fixed and only the width changes, so one thing is tested;
- it trains, selects and then makes one final look;
- one winner per cell, with Holm only on those winners, which is the right two-stage logic;
- calibration is a hard constraint;
- an untested data set (FII/DII) is counted openly.

Four things must be settled in the frozen text before any code runs. If they are left open, the code would decide
them after the builder has seen the data, or a result could not be read honestly. None is large.

## What I verified myself

| Item | Result | Evidence |
|---|---|---|
| Freeze record | MET | `PROTOCOL.md` has SHA-256 `ab67f3b6...0e` at 54bb5a42 and at c835ce08, as `FREEZE.md` says; no commit after the freeze changes it |
| Registration before results | MET | the decision 3b03e2c5 (20:48 UTC) came first, then the protocol 54bb5a42 (20:52) and the freeze c835ce08 (20:53). No GR1 code or output exists on the branch (6 files: protocol, freeze, ledger, LEDGER.md, DATA_SPEND, register) |
| Ledger numbering | MET | main's `ledger.csv` ends at 55, so 56-70 are free today; the 15 rows name 54bb5a42 |
| Data spend | MET | implied's end-of-day ranges are `spent` (their scores were read); VIX and events are `exposed`; global cues are `registered`; A16b's RV is `exposed`. Each matches what has been read |
| FACTORY_RULES section 4 | MET | "a test on a data set marked `spent` or `exposed` ... is labelled exploratory and cannot pass G6; it can at most justify a fresh test". Section 2 of the protocol states exactly this |
| Input data exists | MET | `receipts/data/price_ranges/v1/backfill/backfill_eod_8d7d7301` covers 2019-01 to 2026-10; the BANKNIFTY closes have their receipt (`price_ranges/v1/closes`) |
| Bootstrap | MET, note 6 | G4's `block_bootstrap.compare`: moving blocks of L = 20, 10,000 resamples, a **two-sided** p-value |
| The N0 arithmetic | MET | sqrt(0.607) = 0.779, about 22% narrower by construction, as stated |

## Should-fix 1: the calibration band rejects a perfectly calibrated candidate often, and the protocol does not say so

The rule is that a candidate's coverage must lie within [0.87, 0.93] for the 90% band and [0.45, 0.55] for the 50%
band, on 2024 and again on the final period.

I computed how often a candidate that is **exactly** calibrated still fails it:
- N1: exact binomial.
- N3: a simulation of overlapping 3-session windows (iid normal moves; 20,000 runs).

| Period (days) | Cell | Fails the 90% band | Fails the 50% band | Fails either |
|---|---|---|---|---|
| 2024 (246) | N1 | 13.5% | 11.1% | about 23% |
| 2024 (246) | N3 | 25.6% | 19.4% | 36.8% |
| final (447) | N1 | 3.3% | 3.7% | about 7% |
| final (447) | N3 | 10.4% | 8.9% | 16.8% |

Real markets have fat tails and volatility clusters, so the true rates are higher. A perfect N3 candidate passes both
looks only about 53% of the time (0.632 x 0.832).

**Why this is normal running, not imagined:** it is what the rule does on the very data the protocol names. It has
two effects:
- "No candidate beat implied" can come from noise alone.
- With 11 candidates per cell, selection on 2024 favours candidates whose coverage happened to land inside the band.
  That is selection on noise, which the final look then partly undoes.

**Fix.** Keep the owner's hard constraint, but state in the frozen text, before any run:
- (a) these false-rejection rates, per cell;
- (b) that C0 is checked against the same bands and reported, so a reader sees whether implied itself would pass;
- (c) that a cell with no winner is reported as "not shown at this sample size", never as "implied cannot be beaten".

Alternatively, choose a rule that accounts for sampling noise, for example coverage measured with the same block
bootstrap. If you do, it must be fixed now, not after run 1.

## Should-fix 2: the global cues' point-in-time rule must be A17's own as-of rule, per series; Brent is at least 10 days stale

Section 3 says each cue is "read as its last value published before 15:30 IST on d". The A17 code shows what that
means for each series:
- **Brent** comes from EIA, which publishes it **weekly**. A17's research rule makes a Brent value usable only "by the
  end of the 10th day after its date" (`fno/global_cues/other_sources.py:38`, `EIA_WORST_LAG = timedelta(days=10)`).
  So C7's "last-published Brent move" is a move at least about 10 days old.
- If the code takes `value_date < d`, which is the natural shortcut, C7 gets Brent values the live tool could never
  have had by 15:30. That is look-ahead against live.
- **USD/INR:** the protocol's d-1 matches A17's README ("first usable on t+1", reckoned from the open) and is
  conservative. A17's `as_of.py` makes the rate of d usable from 13:30 IST on d, so at 15:30 the rate of d was already
  known. Using d-1 is safe; it is just one day staler than it needs to be.

**Fix.** State that every cue is read with A17's `value_for(..., live_only=False)` and the source's `available_at`:
- at 15:30 IST on d for C7;
- at 09:15 (A17's `OPEN`) for N0-C's S&P 500 move.

Also state that Brent is therefore at least 10 days stale, and decide now whether it stays in C7. A stale move is
nearly empty of information but still costs a parameter. Add a test with a planted same-day value for each series that
must not be read.

## Should-fix 3: candidates with missing conditioners are compared on different day sets

Section 7 drops rows "not `ok` for implied" and pairs each candidate with C0. Section 9 then picks "the eligible
candidate with the lowest mean 2024 QS" across candidates. In normal running, the candidates do not cover the same
days:
- C8 needs A16b's `rv_session`, which is missing on some sessions: 1,661 usable of 1,680 rows read in A16b's X sample,
  about 1%.
- C3 and C4 need VIX on d and d-1.
- C7 needs every cue.

A lowest-mean QS taken over different days compares different difficulty, not different skill: a candidate that
misses a few volatile days looks better.

**Fix.** Define the selection's day set per cell. Either:
- use the days on which **every** candidate and C0 have values; or
- select on each candidate's mean **paired difference** against C0 over its own days.

Then report how many days each candidate drops.

## Should-fix 4: N0's decision rule is undefined

Section 11 says N0 is "a measurement, not a hypothesis", yet it gives N0-B and N0-C fitted parameters and "the same
selection rule as section 9". Section 9 compares against C0, and section 10 decides only "a cell's winner".

For N0 the protocol does not say:
- which baseline the selection uses: N1 for the same target, or N0-A;
- whether an N0 winner gets a final-period decision;
- whether it joins the Holm family.

As written, the code would make these choices.

**Fix.** Pick one and write it down. My suggestion, which keeps "measurement":
- report N0-A, N0-B and N0-C against N1 on the same target days, on every period;
- select between N0-B and N0-C on 2024 by the section 9 rule, with N0-A as the baseline;
- decide nothing (no Holm, no "sharper"), only width ratios with block-bootstrap intervals.

## Answers to the builder's five questions

1. **Status.** Yes: a winner can at most justify a live sealed shadow (FACTORY_RULES section 4 says exactly this).
   **Go further for C1 and C2.** Both are suggested by the full-sample finding: 5.9% against 4.1%, final years
   included. If either wins a cell, its final look is not even exploratory evidence; it re-measures a known fact. Mark
   such a winner "known before the study" in the decision table. Its only evidence is then the live shadow. The
   conditioners (C3-C10) are different: no conditioner has been read against an outcome, so for them the final period
   is fresh for the *conditioning* effect even though the baseline is spent.
2. **Form and rule.** Width-only around implied's median is a clean single question. The centre's error is out of
   scope, and the report should say so: the owner asked for a "correct" range, not only a narrower one. The rule order
   is right: calibration, then Holm across at most 4 winners, then width. Points in should-fix 1 and note 1.
3. **Point in time.** VIX, events, expiries and RV are right as written. The global cues need should-fix 2. CLOSE
   against CAPTURE basis is correctly disclosed (section 4), and it is one more reason for the live shadow.
4. **Multiplicity.** Counting FII/DII visibly is right. The 46 is not internally consistent: see note 3. The count is
   descriptive here, because only at most 4 winners are tested.
5. **N0 against N1.** A measurement is the right status, and 0.607 is exposed (measured on 2020-2025). See
   should-fix 4 for the rule.

## Notes (one line each)

1. **C2 can make quantiles cross.** The 5% quantile passes the 25% one when s95/s50 < (q25 - m)/(q05 - m), about
   0.41 for a normal shape. "`s > 0`, so the quantiles stay increasing" is true for one scale, not for two. Add the
   constraint to the fit, or refuse a crossing fit, counted as a failed fit.
2. **C11 chooses its two conditioners on 2024 and is then selected on 2024.** This double use favours C11 at
   selection. The final look still protects validity, but say so, or choose C11's pair on the train period.
3. **The count is not consistent.** The 2 BANKNIFTY cells of C8 are not counted ("42 fitted"), yet C11 is counted
   when not run and FII/DII is counted once rather than per cell. Pick one rule: every registered candidate-cell
   counts, run or not, so 44 + 3 + 4 = 51, or say why not.
4. **Regime breaks fall inside the periods.**
   - BANKNIFTY's weekly options ended in Nov 2024, so they are inside 2024 and in none of the final period.
   - NIFTY's weekly expiry moved from Thursday to Tuesday in Sep 2025, inside the final period.
   - C6 (expiry in horizon) and C9 (weekday) carry train-period meanings that change. Disclose this, with the dates.
5. **"Run once" is enforced only by `final.json` being absent at the committed head.** A local run is not visible.
   - The honest control is a deterministic run 2 that the judge reproduces from the committed `selection.json`.
   - The selection commit must precede the final commit, which GitHub's push times show.
   - Write both into section 12.
6. **The p-value is two-sided.** "Below C0's with p < 0.05" is then a one-sided 2.5% test, which is conservative and
   fine. Say "two-sided p, direction required".
7. **Section 13's "report the gap"** should also say what happens to the cell: not decided.
8. **Merge the registration to main once this passes.** Merging the protocol, the freeze and the ledger rows (they are
   not code) fixes 56-70 and avoids the renumbering risk the builder names.

## To pass

1. Should-fixes 1-4, written into `PROTOCOL.md` as a re-freeze. The protocol has no code and no results yet, so a
   change now is not a deviation. Record it in section 14 as "revision before review, judge 428", with a new hash in
   `FREEZE.md` and the ledger's protocol commit updated.
2. Then I re-check the text, the hash and the ledger rows.
