# Protocol: GR1, sharper price ranges

Ledger trials 56-70. Revision 2 (before review, judge 428): see section 14. Builder: session_01UkTaDeTRF9ksDgQB9cTU5C. Requested by the orchestrator for the owner on 21 Oct
2026. Judge B reviews this protocol before any result is read, and the results after (orchestrator, 21 Oct).

Research only. Nothing here changes G13b's code, its live step or a frozen file. A candidate that wins is a new, judged
story.

## 1. The question

Can NIFTY's and BANKNIFTY's next-session (N1) and third-session (N3) price ranges be made narrower while staying as
reliable?

Owner: "having a way bigger range is not helpful ... one of the key reasons of this product is to find out that
correct and closer range with higher predictability ... we are consuming news, data from different sources ... so we
should do better."

A second question is in section 11: how much does a 09:15 forecast of the same day's close (N0) narrow the range,
compared with the 15:45 N1 forecast of that close made the evening before?

## 2. Status of every result: exploratory

This section is stated first, because it limits what any result can mean.

- **The data is spent.** `research/DATA_SPEND.md` marks NIFTY's option daily closes `spent` for 2019-2023 and for
  2024-2026. G13b's ranges are built from those closes.
- **The final period is not fresh either.** Implied's own back-fill scores for 2019 to 20 Oct 2026 were already read,
  in responses 262 and 290 and the 21 Oct scores file. So 2025-26 is not a fresh period for the baseline. Two things
  were also read on the full sample, final years included:
  - the overstated chance of a 2% move (5.9% against about 4.1% realised for NIFTY);
  - the 39.3% overnight share of variance.
  Both point to candidate C1 (a scale below 1), so C1 was suggested by data that includes the final period.
- **What a result can do.** Under `research/FACTORY_RULES.md` section 4, no GR1 result can pass a gate. A candidate
  that wins here can at most justify the next stage: a live sealed shadow of that one candidate, as its own registered
  trial and story.
- **What is fresh.** No candidate below has been fitted or scored on any period, and no conditioner has been read
  against an outcome.
- **Honest limit: the sealing is code plus process, not physical.** The 2025-26 back-fill records already sit in
  Drive, and I have seen implied's own 2025-26 aggregate scores. What is sealed is every candidate's 2025-26
  performance, which has never been computed; the data itself is not sealed (judge B, 21 Oct).

## 3. Data (point in time: each input as known at the issue time)

| Input | Source | Known when |
|---|---|---|
| Implied ranges, N1 and N3, both indices | G13b's end-of-day back-fill, method `8d7d7301`, Drive `data/price_ranges/v1/backfill/backfill_eod_8d7d7301/` (receipts d6958a42), read through the verified Drive cache | d's close (CLOSE basis) |
| Outcomes | G13b's `Outcomes.close`: NIFTY from `warmup_closes.csv`, BANKNIFTY from its Drive close table (receipt 1ee30cee) | target close |
| India VIX | `research/data/vix/india_vix_daily.csv` (A15), close of d and d-1 | d's close |
| Event days | `research/data/events/events.csv` (A6): `rbi_policy`, `budget`, `election_result`, with `announced_on` before d | announced before d |
| Option expiries | the expiries of the index's options in d's archived F&O file (the same chain the record was built from) | d's close |
| Global cues | A17: S&P 500 close (Drive, private), US 10-year (`us10y.csv`) and USD/INR (`usdinr_rbi.csv`). Each is read with A17's own point-in-time rule, `value_for(live_only=False)` with the source's `available_at`, at the cutoff 15:30 IST on d (C7) or 09:15 IST on d (N0-C). Never a raw `value_date < d`, which would be look-ahead against live. USD/INR is RBI's rate of d-1 at the latest, one day staler than A17 allows (safe). It is one reference rate: RBI's rows, and A17's FBIL rows (private, Drive) for the dates RBI lacks, read under RBI's rule (deviation 3, section 14). **Brent is dropped** (judge 428 SF2): A17's rule makes EIA's weekly Brent at least 10 days old at d (`EIA_WORST_LAG`), so for a 1- to 3-session range it would test nothing | at the cutoff |
| NIFTY intraday realised variance of d | A16b's `research/data/intraday/rv-candle/` (`rv_session`), from 2 Jan 2020, NIFTY only | d's close |
| NIFTY 09:15 price | A16b's 15-minute candles (`nifty-15m`), the first candle's open | 09:15 IST |
| Calendar | A7, `research/data/calendar/nse_sessions.csv` | always |

**Not tested, counted.** Registered as trial 67 so the count stays honest:

- **FII/DII flows:** no history. The repository has 6 days from 13 Oct 2026, because NSE's API serves only the current
  day. A historical source (for example NSDL's FPI archive) would be a new data story; that is the owner's choice
  (orchestrator, 21 Oct).
- **Company results:** there is no results calendar, and they matter little for an index.

## 4. Basis and its limit

- **History is on the CLOSE basis.** The back-fill has only end-of-day chains: `S_ref` is d's official close and the
  rest-of-day tail is 0.
- **The live method differs.** It issues from the 3 pm chain (the CAPTURE basis, `S_ref` = 3 pm spot, tail 0.049).
  A conditioner that works on the CLOSE basis may work differently live. That is one more reason the next stage is a
  live shadow.

## 5. Baseline and candidate form

- **Baseline C0:** implied, unchanged.
- **Candidate form.** Every candidate rescales implied's log quantiles around implied's own median `m`:

  `q'_p = m + s(x) (q_p - m)`, with `s(x) = exp(theta . x)` and `x = (1, conditioners)`.

  The median, and so the centre, never moves. A candidate changes only the width.
- **Monotone.** `s > 0` always, so the quantiles stay increasing.
- **Fitting.** Each candidate is fitted separately per (index, horizon) on the train period, by minimising the mean
  quantile score (section 8).

## 6. Candidates (trials 56-66; each run on all four cells: NIFTY N1, NIFTY N3, BANKNIFTY N1, BANKNIFTY N3)

| Trial | Id | Conditioner(s) in `x` beyond the intercept | Parameters |
|---|---|---|---|
| 56 | C1 | none: one constant scale | 1 |
| 57 | C2 | two constant scales: one for the 25/75 band, one for the 5/95 band (the shape, not only the width). Parameters that make any quantiles cross on any train day are refused in the fit. On select and final days, a crossing on any scored day counts the cell as a failed fit for C2 (judge 428.1 note 1). The outer-to-inner scale ratio must keep q05 < q25 and q75 < q95 on every day: about 0.41 for a normal shape | 2 |
| 58 | C3 | ln(VIX_d) minus ln(the train period's median VIX) | 2 |
| 59 | C4 | ln(VIX_d / VIX_{d-1}) | 2 |
| 60 | C5 | 1 if an RBI policy, budget or election-result day falls in (d, target] | 2 |
| 61 | C6 | 1 if an expiry of the index's options falls in (d, target] | 2 |
| 62 | C7 | the absolute last-published moves of S&P 500 (log), US 10-year (points) and USD/INR (log), each by A17's rule at 15:30 IST on d | 4 |
| 63 | C8 | ln(rv_session_d / implied's one-session variance at d); NIFTY only, 2020 on | 2 |
| 64 | C9 | the target session's weekday (4 dummies, Monday the base) | 5 |
| 65 | C10 | a separate constant scale per VIX tercile of d (terciles from the train period) | 3 |
| 66 | C11 | the combination: the two conditioners from C3-C10 whose **train-period** fit improves most on C1's train QS (chosen on train, so 2024 is not used twice; judge 428); C11 is then selected on 2024 like any candidate | up to 3 |

- **Combination rule (C11).** C11 uses C1's intercept plus the two chosen conditioners' columns together, chosen per
  cell on train.
- **Count: every registered candidate-cell counts, whether it runs or not** (judge 428: the first count was not
  consistent). That is 12 conditioner candidates, C1-C11 plus FII/DII (trial 67), times 4 cells = 48. 4 of these
  cannot run: FII/DII's 4 cells (no history) and C8's 2 BANKNIFTY cells (no intraday data), so 42 are fitted. Plus the
  3 N0 variants: **51 counted tests**.
- **Regime breaks, stated now** (judge 428), because they touch C6 and C9:
  - BANKNIFTY weekly options ended in November 2024.
  - NIFTY's weekly and monthly expiry moved from Thursday to Tuesday in September 2025.
  - C6 reads the real expiries of each day's file, so it follows both changes. C9's weekday effect may change at
    those dates; the results report C9 split at them.

## 7. Periods

| Period | Dates (issue day d) | Use |
|---|---|---|
| Train | 2019-01-01 to 2023-12-31 (C8 from 2020-01-02) | fit each candidate's parameters |
| Select | 2024-01-01 to 2024-12-31 | choose at most one winner per cell (section 9) |
| Final | 2025-01-01 to 2026-10-20 | read **once**, after the selection is committed (section 12) |

Rows that are not `ok` for implied are dropped, as are rows with no outcome yet.

**Days.** Each candidate is compared with C0 on that candidate's own days, paired (judge 428 SF3). The candidates' day
sets differ: C8 has gaps, C4 needs VIX of d-1, and C7 needs the cues. So selection uses each candidate's paired mean
QS difference against C0, never raw means across different day sets. Every table reports the days each candidate
drops, and why.

## 8. Scores

- **Quantile score (QS):** `(2/5) x sum of the pinball losses` over the levels 5, 25, 50, 75 and 95%, in log units.
  - This is G13b's own score, and the weighted interval score of the 50% and 90% bands plus the median, up to a
    constant.
  - It rewards narrow ranges and penalises misses: the Winkler/interval score the orchestrator asked for.
- **Coverage:** the share of outcomes inside the 25-75% band and inside the 5-95% band.
- **Width in points:** the median over days of `S_ref x (e^{q95} - e^{q05})` (the 90% band) and of `S_ref x (e^{q75} -
  e^{q25})` (the 50% band).
- **Comparison:** the mean daily paired QS difference against C0, by G4's block bootstrap (`fno/forecast_scoring/
  block_bootstrap.compare`, seed from the comparison's key as G13b). Its p-value is **two-sided**; a win also needs
  the difference to favour the candidate.

## 9. Selection on 2024 (per cell)

1. A candidate is **eligible** when its 2024 coverage of the 5-95% band is within [0.87, 0.93] and of the 25-75% band
   within [0.45, 0.55]. This is the hard calibration constraint: "almost certainly" must still mean about 90%.
2. The **winner** is the eligible candidate with the most negative paired mean QS difference against C0 on 2024, if
   that difference is below 0.
3. If no candidate is eligible and better, there is no winner for the cell.

**What the bands cost, stated now** (judge 428 SF1, checked by exact binomial). The bands are kept as a hard rule,
but they are noisy at these sample sizes. Even an exactly calibrated candidate fails them:

| Look | N1 (about 246 days in 2024, about 440 in the final period) | N3 (overlapping outcomes; judge 428's simulation) |
|---|---|---|
| 2024 | about 23% of the time | about 37% |
| Final period | about 6-7% | about 17% |
| Both looks | about 72% pass | about 53% pass |

So a cell with no winner means **"not shown at this sample size"**, never "no candidate can be sharper". C0 itself is
checked against the same bands on both periods and reported. If implied fails its own band, that is reported as a
finding about implied.

## 10. Decision on the final period (read once)

A cell's winner is called **sharper** only if all four hold on the final period:

- its paired mean QS difference against C0 is negative, with the two-sided bootstrap p-value Holm-adjusted across the
  cells that have a winner (at most 4) below 0.05;
- its 5-95% coverage is within [0.87, 0.93];
- its 25-75% coverage is within [0.45, 0.55];
- its median 90% width in points is smaller than C0's.

Even then, the label is exploratory (section 2) and the next step is a live sealed shadow.

A **C1 or C2 winner is marked "known before the study"** (judge 428): its final look re-measures the full-sample finding
that suggested it (section 2). For C3-C10, the final period is fresh for the conditioning effect. A cell that fails is
reported as "not shown at this sample size" (section 9).

**Reported in full either way:**

- every candidate on every period: QS, both coverages and both widths;
- the selection table;
- the multiplicity count (51);
- the final-period numbers of every candidate, for transparency. Only the selected winner is decided on.

## 11. N0 at 09:15 against N1 at 15:45, the same target (trials 68-70; NIFTY only, 2020 on)

- **The comparison.** For target day d, N1 is the range G13b issued at d-1's close for d's close, from the record of
  d-1. N0 is a forecast of the same close made at 09:15 on d. So both forecast the same outcome and compare directly.
  No historical 09:15 chain exists, so N0 is built from the same implied distribution, moved forward:
- **Centre and spread.** The N0 centre is the 09:15 price (the first 15-minute candle's open). Implied's log
  deviations around its median are scaled by `sqrt(0.607)`, the variance share left at 09:15. 0.393 is the measured
  overnight share; it was measured on 2020-2025, so it is exposed (section 2).
- **The three variants:**
  - **N0-A** (trial 68): exactly that, with no fitted parameter.
  - **N0-B** (trial 69): N0-A times one constant scale, fitted on train.
  - **N0-C** (trial 70): N0-B with two conditioners known at 09:15: the absolute overnight gap, `|ln(open_d /
    close_{d-1})|`, and the absolute S&P 500 move of the US session that ended before 09:15 on d.
- **Periods.** Train 2020-01-02 to 2023-12-31, select 2024, final 2025 to 20 Oct 2026 once.
- **Rule** (judge 428 SF4; N0 is a measurement, so it gets no "sharper" label and does not join Holm):
  - on 2024, N0-B and N0-C are compared against N0-A (the baseline) by paired QS difference, under section 9's
    calibration bands;
  - the better eligible one, or N0-A if neither is eligible and better, is carried to the final period.
- **Reported:** all three variants against N1 on the same target days:
  - the median 90% and 50% widths in points;
  - coverages and QS;
  - the width ratio N0/N1, with a block-bootstrap 95% interval.
- **Measurement, not a hypothesis.** By construction alone N0-A is about 22% narrower: `sqrt(0.607 / 1)` = 0.78 on the
  CLOSE basis. The question is how much narrower the reliable N0 is, and whether overnight information adds anything
  beyond that.

## 12. Order of work and freeze

1. **Protocol and registration.** This protocol, the ledger rows 56-70 and the data-spend rows are committed. That
   commit is the protocol freeze (`FREEZE.md` names it and the file hashes). Judge B reviews it.
2. **Code.** The study code (`research/gr1/`) is written and tested on synthetic data only (`tests/research_gr1/`),
   with planted-bug proofs, among them a planted same-day value for each global cue that A17's rule must refuse and a
   planted 2025 row that must not change run 1's output. Its hashes are frozen in `FREEZE.md` in their own commit.
   The run refuses to start if a file differs from its hash.
3. **Run 1, train and select.**
   - (a) Run 1 filters every record by issue date < 2025-01-01 at load, before any score, conditioner or outcome is
     computed. A test plants a 2025 row whose outcome would change the selection and proves run 1's output does not
     change.
   - (b) Run 1 writes `selection.json` (winners, parameters and the 2024 table), and it is committed before run 2.
4. **Run 2, the final period.**
   - (c) Run 2 reads only the committed `selection.json`. It never refits. It refuses to start unless `selection.json`
     is committed and unchanged since its commit, and unless `final.json` does not exist at HEAD or in any earlier
     commit (git log). It writes `final.json` once; a second invocation refuses.
   - It is deterministic, so a judge can reproduce `final.json` from the committed `selection.json`: inputs sorted by
     day, seeds from the comparison keys (G4), no clock or random state. Its inputs' SHA-256 is recorded in
     `final.json`.
   - (d) Both runs refuse if any study file differs from its `FREEZE.md` hash or the folder has uncommitted changes
     (the FT1 pattern).
5. **Results.** A results file in `reviews/claude/` (number claimed), with plain conclusions. Then judge B reviews it.

## 13. What would make me stop and report instead

- A data input missing for more than 5% of a period's days in a cell: report the gap, do not impute it, and the cell
  is **not decided** (judge 428).
- A candidate whose fit does not converge (a grid edge is hit): report it as a failed fit, counted.
- Any sign of look-ahead found during the work: stop, report and re-freeze, counted as a protocol change.

## 14. Deviations

Any deviation is recorded here, dated, before the step it affects, and judge B is told.

- **22 Oct 2026, revision 2, before review (judge 428: FAIL, 4 should-fix; nothing had been fitted or scored).** All
  four should-fixes and the notes were checked and accepted:
  - **SF1:** the band costs are stated (section 9), confirmed by my own exact binomial: 23.1% at n = 246 and 6.2% at
    n = 440 for N1. C0 is checked against the same bands, and a cell with no winner means "not shown at this sample
    size".
  - **SF2:** every cue is read by A17's `value_for` and `available_at`. Brent is dropped: it is at least 10 days stale
    by A17's rule. A planted same-day test is added per series.
  - **SF3:** selection is by each candidate's paired difference against C0, with dropped days reported.
  - **SF4:** N0's rule is defined (section 11).
  - **Notes:** a consistent count of 51; C2 can no longer make quantiles cross; C11's pair is chosen on train; the
    regime breaks are listed; run 2 is deterministic; the p-value is two-sided; a gap means the cell is not decided;
    a C1 or C2 winner is marked "known before the study".
  - New freeze hash and the ledger rows' `protocol_commit` are updated in the same change.
  - Also in this revision, at judge B's request: section 12's (a)-(d) word for word as sent to the judge, run 2's
    determinism, and the "honest limit" in section 2.
- **22 Oct 2026, after judge 428.1's PASS of a7a1b28a, before any code:** its notes 1-3 applied.
- **22 Oct 2026, deviation 3, found by the input probe (counts only: no outcome read, no score computed), before the code
  freeze and run 1:**
  - **The problem:** C7 had its inputs on only 422 of 1,222 NIFTY N1 train days. RBI's public USD/INR table has no row
    from 24 Jul 2018 to 12 Apr 2022, after FBIL took the reference rate over. A17 holds FBIL's rates for that span, and
    A17's README records RBI and FBIL equal on all 1,086 dates both publish.
  - **The change:** C7's USD/INR is one reference rate. RBI's rows are used where they exist, and FBIL's for the dates
    RBI lacks. The series is read under RBI's rule (13:30 IST publication, 5-day age limit), at 09:15 on d, so the rate
    is of d-1 at the latest. With it, C7 has inputs on 1,213 of 1,222 train days. The 9 missing days are FBIL's own gap
    of 29 Jan - 16 Feb 2021, beyond the age limit.
  - **And:** section 13's gap rule ("over 5% of a period's days in a cell") now also applies to the train period in the
    code, as written. Each candidate's own train period counts, so C8's start on 2 Jan 2020 is a design date, not a gap.
  - **What this changes:** only C7's input and the code's check of section 13. No candidate, period, score or decision
    rule changes. Counted tests stay 51.
  - Note 1: C2's crossing check covers every scored day, and a crossing is a failed fit.
  - Note 2: DATA_SPEND's global-cues row no longer names Brent.
  - Note 3: the honest-limit sentence in section 2 (already in eb8d061a).
