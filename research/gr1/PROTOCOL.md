# Protocol: GR1, sharper price ranges

Ledger trials 56-70. Builder: session_01UkTaDeTRF9ksDgQB9cTU5C. Requested by the orchestrator for the owner on 21 Oct
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

## 3. Data (point in time: each input as known at the issue time)

| Input | Source | Known when |
|---|---|---|
| Implied ranges, N1 and N3, both indices | G13b's end-of-day back-fill, method `8d7d7301`, Drive `data/price_ranges/v1/backfill/backfill_eod_8d7d7301/` (receipts d6958a42), read through the verified Drive cache | d's close (CLOSE basis) |
| Outcomes | G13b's `Outcomes.close`: NIFTY from `warmup_closes.csv`, BANKNIFTY from its Drive close table (receipt 1ee30cee) | target close |
| India VIX | `research/data/vix/india_vix_daily.csv` (A15), close of d and d-1 | d's close |
| Event days | `research/data/events/events.csv` (A6): `rbi_policy`, `budget`, `election_result`, with `announced_on` before d | announced before d |
| Option expiries | the expiries of the index's options in d's archived F&O file (the same chain the record was built from) | d's close |
| Global cues | A17: S&P 500 close (Drive, private), US 10-year (`us10y.csv`), Brent (`brent.csv`) and USD/INR (`usdinr_rbi.csv`). Each read as its last value published before 15:30 IST on d: the US session that ended before d's Indian close, and RBI's rate of d-1 (RBI's rate is first usable on t+1, A17's README) | before 15:30 IST d |
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
| 57 | C2 | two constant scales: one for the 25/75 band, one for the 5/95 band (the shape, not only the width) | 2 |
| 58 | C3 | ln(VIX_d) minus ln(the train period's median VIX) | 2 |
| 59 | C4 | ln(VIX_d / VIX_{d-1}) | 2 |
| 60 | C5 | 1 if an RBI policy, budget or election-result day falls in (d, target] | 2 |
| 61 | C6 | 1 if an expiry of the index's options falls in (d, target] | 2 |
| 62 | C7 | the absolute last-published log moves of S&P 500, US 10-year (in points), Brent and USD/INR | 5 |
| 63 | C8 | ln(rv_session_d / implied's one-session variance at d); NIFTY only, 2020 on | 2 |
| 64 | C9 | the target session's weekday (4 dummies, Monday the base) | 5 |
| 65 | C10 | a separate constant scale per VIX tercile of d (terciles from the train period) | 3 |
| 66 | C11 | the combination: the two conditioners from C3-C10 whose 2024 score improves most on C1 and that each meet the calibration rule; fewer than two pass means C11 is not run (still counted) | up to 3 |

- **Combination rule (C11).** C11 uses C1's intercept plus the two chosen conditioners' columns together. The choice
  is made per cell on 2024, before the final period is read.
- **Count.** 11 candidates x 4 cells = 44 candidate-cells (C8 has no BANKNIFTY data: 42 fitted). Plus 3 N0 variants
  (section 11) and the 1 not-tested row: **46 counted tests**.

## 7. Periods

| Period | Dates (issue day d) | Use |
|---|---|---|
| Train | 2019-01-01 to 2023-12-31 (C8 from 2020-01-02) | fit each candidate's parameters |
| Select | 2024-01-01 to 2024-12-31 | choose at most one winner per cell (section 9) |
| Final | 2025-01-01 to 2026-10-20 | read **once**, after the selection is committed (section 12) |

Rows that are not `ok` for implied are dropped, as are rows with no outcome yet. The same days are used for the
candidate and the baseline (paired).

## 8. Scores

- **Quantile score (QS):** `(2/5) x sum of the pinball losses` over the levels 5, 25, 50, 75 and 95%, in log units.
  - This is G13b's own score, and the weighted interval score of the 50% and 90% bands plus the median, up to a
    constant.
  - It rewards narrow ranges and penalises misses: the Winkler/interval score the orchestrator asked for.
- **Coverage:** the share of outcomes inside the 25-75% band and inside the 5-95% band.
- **Width in points:** the median over days of `S_ref x (e^{q95} - e^{q05})` (the 90% band) and of `S_ref x (e^{q75} -
  e^{q25})` (the 50% band).
- **Comparison:** the mean daily QS difference against C0, by G4's block bootstrap (`fno/forecast_scoring/
  block_bootstrap.compare`, seed from the comparison's key as G13b).

## 9. Selection on 2024 (per cell)

1. A candidate is **eligible** when its 2024 coverage of the 5-95% band is within [0.87, 0.93] and of the 25-75% band
   within [0.45, 0.55]. This is the hard calibration constraint: "almost certainly" must still mean about 90%.
2. The **winner** is the eligible candidate with the lowest mean 2024 QS, if that QS is below C0's 2024 QS.
3. If no candidate is eligible and better, the cell's winner is C0: "no candidate beat implied".

## 10. Decision on the final period (read once)

A cell's winner is called **sharper** only if all four hold on the final period:

- its mean QS is below C0's, with the bootstrap p-value Holm-adjusted across the cells that have a winner (at most 4)
  below 0.05;
- its 5-95% coverage is within [0.87, 0.93];
- its 25-75% coverage is within [0.45, 0.55];
- its median 90% width in points is smaller than C0's.

Even then, the label is exploratory (section 2) and the next step is a live sealed shadow.

**Reported in full either way:**

- every candidate on every period: QS, both coverages and both widths;
- the selection table;
- the multiplicity count (46);
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
- **Periods.** Train 2020-01-02 to 2023-12-31, select 2024, final 2025 to 20 Oct 2026 once; the same selection rule
  as section 9.
- **Reported:** median 90% and 50% width in points for N1 and each N0 variant on the same days, their coverages and
  QS, and the width ratio N0/N1.
- **Measurement, not a hypothesis.** By construction alone N0-A is about 22% narrower: `sqrt(0.607 / 1)` = 0.78 on the
  CLOSE basis. The question is how much narrower the reliable N0 is, and whether overnight information adds anything
  beyond that.

## 12. Order of work and freeze

1. **Protocol and registration.** This protocol, the ledger rows 56-70 and the data-spend rows are committed. That
   commit is the protocol freeze (`FREEZE.md` names it and the file hashes). Judge B reviews it.
2. **Code.** The study code (`research/gr1/`) is written and tested on synthetic data only (`tests/research_gr1/`),
   with planted-bug proofs. Its hashes are frozen in `FREEZE.md` in their own commit. The run refuses to start if a
   file differs from its hash.
3. **Run 1, train and select.** It writes `selection.json`, which is committed before step 4. The run reads no row
   dated in 2025-26: the final rows are filtered out before any score is computed, and a test proves it.
4. **Run 2, the final period.** It reads the committed `selection.json` and computes the final period once. It
   refuses to run twice, by checking that `final.json` is absent at the committed head.
5. **Results.** A results file in `reviews/claude/` (number claimed), with plain conclusions. Then judge B reviews it.

## 13. What would make me stop and report instead

- A data input missing for more than 5% of a period's days in a cell: report the gap and do not impute it.
- A candidate whose fit does not converge (a grid edge is hit): report it as a failed fit, counted.
- Any sign of look-ahead found during the work: stop, report and re-freeze, counted as a protocol change.

## 14. Deviations

None yet. Any deviation is recorded here, dated, before the step it affects, and judge B is told.
