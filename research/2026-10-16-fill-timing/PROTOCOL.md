# Protocol: FT1, the fill-timing study (story E8a)

Ledger trial 54, kind `prospective`, hypothesis `no` (as R2, trial 53). Story text: `docs/stories/E-paper-desk.md`,
section E8a (revision 3, judge 155 PASS on the text). Where this protocol and the story differ, this protocol governs
and the difference is listed in section 15.

**Status of every figure: exploratory measurement.** No edge, no verdict on a strategy, no pass mark. The option
prices of 2024-26 are spent data (`research/DATA_SPEND.md`); the study measures how far an entry price moves between
a decision and E8's fill, not whether any trade pays.

## 1. The question

For each structure family, for a 15:00 decision and for a 14:00 decision, and for each of E8's reaction times
(R = 5, 30 and 60 minutes): how far does the entry price move between the decision and the fill, and how often does a
trade that wins at the decision price lose at E8's price? The owner chooses the decision time from these numbers
(owner decision of 15 Oct 2026, `docs/DESK_DECISIONS.md`).

## 2. Data

| Input | Source | Use |
|---|---|---|
| NIFTY option and future 15-minute candles | Groww historical candles, read-only through A16's `ReadOnlyGroww`, segment FNO | Leg prices, the forward |
| NIFTY index 15-minute candles | A16b's archive in Drive (`research/data/manifests/groww-candles/nifty-15m.csv`) | Spot at the decision (strikes), gap band |
| Listed contracts, monthly expiries, final settlement | The daily panel (`research/data/nifty_panel`), years 2024-26 | Chains, expiry choice, flip share |
| NSE sessions | A7 calendar (`research/data/calendar/nse_sessions.csv`) | Decision days, nights, sessions to expiry |
| India VIX open | A15 (`research/data/vix/india_vix_daily.csv`) | VIX band |
| Lot size, charges, rate | `config.yaml` at run time: `lot_sizes` NIFTY, `charges`, `risk_free_rate` | Rupees, flip P&L, time part |
| 15:00 bid and ask | A4's canonical Groww snapshots held at run time (`python -m fno quotes report` logic) | Spread caveat only |

Monthly expiries are the expiry dates of the panel's futures rows (one future per month). An expiry on or before the
panel's last day without a final settlement in the panel is dropped as not a real expiry (see section 3).

## 3. Coverage probe (done before this freeze, 15 Oct 2026)

`python study.py --probe` (`ft1study/probe.py`): for each monthly expiry from 25 Jan 2024 to 27 Oct 2026 (34
expiries), one call for the ATM call 10 sessions before expiry (ATM from the panel's close that day; ATM + 50 if the
first gave nothing) and one for the same-expiry future. It records the symbol and candle count only, never a price
(`probe.csv`).

**Result: 68 of 68 answered** (options 24-27 candles, futures 25-27, for that one day). Two causes were found and fixed
before this result, both in the expiry list, not at Groww:
- A "last listed expiry of the month" rule picked the weekly of 30 Apr 2025 and a re-dated 31 Mar 2026. Fixed by taking
  monthly expiries from the futures files.
- 25 Sep 2025 was a re-dated expiry with no contracts on it (NSE moved monthly expiry to Tuesdays from Sep 2025; the
  real one is 30 Sep 2025). Fixed by dropping a past expiry with no settlement in the panel.

No month is left out by the probe.

## 4. Decision days

- Every A7 `regular` session from 2 Jan 2024 to 30 Sep 2026 whose next session is also `regular`. A special or
  muhurat decision day, or one whose next session is special or muhurat, is left out and counted (the next-session
  fills need a normal morning).
- Both decision times use the same days, so they can be paired.
- A day whose NIFTY index candle for the decision time is missing is left out for that decision time and counted.

## 5. Expiry, structures and strikes

- **Expiry:** the nearest monthly expiry more than 7 sessions after the decision day. Sessions to expiry = A7 sessions
  (any kind) after the decision day up to and including the expiry day. Bands: 8-15, 16-25, 26 and more.
- **Families:** SF, SC, BF (`fno/research_engine/structures.py`) and LC, LP, CDS, CCS, PDS, PCS
  (`fno/research_engine/one_side.py`), built exactly as `fno/composition.py` `build_tradable_structures`.
- **Spot:** the NIFTY index close of the candle ending at the decision time (A16b; the candle starting 14:45 for 15:00,
  13:45 for 14:00).
- **Chain:** the contracts of that expiry listed in the panel on the decision day. A structure whose leg is not listed
  is "width unavailable" for that day and counted as missing (section 11).
- **Width:** 200 points for SF, SC, BF and the four spreads; LC and LP at width 0 (ATM). Widths 100 and 300 are
  sensitivity checks for the seven width families, reported only for the mean of `|C|` and the three threshold shares
  at the 15:00 decision with R = 60.

## 6. Times and prices

Groww's candle rows are `[start time, open, high, low, close, volume, open interest]`; a row's time is its **start**.
The price "at" a time is the close of the candle that ends then (starts 15 minutes earlier), on that date.

| Decision | Price at decision | R = 5 | R = 30 | R = 60 |
|---|---|---|---|---|
| 15:00 (card about 15:08) | 15:00 | 15:15 same day | 09:45 next session | 10:15 next session |
| 14:00 (card about 14:08) | 14:00 | 14:15 same day | 14:45 same day | 15:15 same day |

This is E8's rule: the fill is the first 15-minute mark at or after card time + R; a mark after 15:25 moves to the next
session at 09:15 + R. **E4's 15:15 snapshot** is the same time as the 15:00/R = 5 and 14:00/R = 60 fills: those rows are
labelled "= E4's 15:15 snapshot", not computed apart.

All legs of a structure are priced at the same time. **Stale:** a leg's candle at that time has zero volume.
**Missing:** no candle at that time, or the contract was not fetched. Either removes the structure from that
time's figures and is counted; no other price stands in (no earlier candle, no other strike, no model).

## 7. The measure

`V = sum of side x price` over the legs (bought legs +1, sold legs -1): the debit paid per unit (negative for a
credit). `C = V_fill - V_decision`, in index points per unit. Positive `C` is worse for the trader (a buyer pays more,
a seller gets less credit). **Bad side:** `C > 0`. Bad-side size: `max(C, 0)`.

- **Risk scale:** the width (points) for SF, SC, BF and the four spreads; the decision debit `V_decision` for LC and LP.
  A long option whose decision price is not above zero is missing.
- **Rupees:** points x the NIFTY lot size of `config.yaml` at run time (65 on 15 Oct 2026), stated once; points carry
  the result.

By construction the families mirror each other: `C(BF) = -C(SF)`, `C(CDS) = -C(CCS)`, `C(PDS) = -C(PCS)` on the same
legs and day. So the mean of `C` is mostly drift (chiefly overnight time decay) and is never read as "the cost of
waiting".

## 8. Figures per family, decision time and R (width 200)

1. n (structures with a computed `C`) and the counts left out, by reason.
2. The 10th, 50th and 90th percentiles of `C` (points).
3. The mean of `|C|`, with its 95% interval (section 12).
4. The share of days with `C` above 5%, 10% and 20% of the risk scale (entry-range stand-ins, reasoning only);
   denominator n.
5. The mean of `C` and, beside it, the mean **time part** (section 9) over the structures whose time part is computed,
   with the count "not computed".
6. Rupee equivalents of the 50th percentile of `C` and of the mean of `|C|`.

## 9. The time part

Black-76 (`fno/research_engine/implied_vol.py` `Black76`) with only time moving:
- forward `F` = the same-expiry NIFTY future's close at the decision time (Groww 15-minute candle, fetched with the
  legs);
- each leg's IV from `F`, its strike and its decision price, time to expiry from the decision time;
- each leg re-priced at the same `F` and IV with the time to expiry from the fill time;
- time in calendar minutes to 15:30 IST on the expiry day, divided by 365 x 1440; rate = `risk_free_rate`;
- time part = `sum of side x (model price at fill - model price at decision)`, same sign as `C`.

A leg whose IV cannot be solved (`None`), or a stale or missing future, makes that structure's time part "not
computed": counted, never filled in.

## 10. Splits

For every cell of section 8: n, the 10th/50th/90th percentiles of `C`, the mean of `|C|` and the 10% threshold share
(no interval), by:
- **nights** = calendar days from the decision day to the fill day: 0 (same day), 1, 2, 3 or more;
- **gap band** = `|index at fill / index at decision - 1|`, from A16b's index candles at the same two times: below
  0.5%, 0.5-1%, 1% and more (an index candle missing at the fill time puts the day in "gap unknown", counted);
- **VIX band** = India VIX open of the decision day (known at the decision): below 13, 13-18, above 18 (13 is in the
  middle band, 18 in the middle band);
- **sessions to expiry**: 8-15, 16-25, 26 and more.

A split cell with fewer than 30 days prints "too few days", never a number.

## 11. Cells that cannot be read

Per family, decision time and R: if structures left out for a stale or missing leg (or width unavailable) exceed 10%
of the decision days eligible for that decision time (section 4), the cell prints "insufficient data", never a number.
A main cell with fewer than 30 days prints "too few days".

## 12. Bootstrap

- Stationary bootstrap (Politis and Romano) over the cell's sessions in date order, mean block length 5 sessions
  (10 and 20 as checks), B = 10,000, 95% percentile interval.
- Seed: 20261016. Each interval's generator is seeded from the seed and the cell's name (SHA-256 of the name, first
  8 bytes), so a cell's interval does not depend on the order cells are computed in. The same run twice gives the same
  intervals.
- `results.md` prints the 5-session interval; `results.json` carries all three.

## 13. The owner's choice, paired

Per family, over the days where both the 15:00/R = 60 and 14:00/R = 60 `C` exist: `D = max(C15, 0) - max(C14, 0)`
(positive: the 15:00 decision's bad-side move is larger). The report gives the mean of `D` with its stationary
bootstrap interval (section 12). What the 14:00 path gives up (the last hour's information) is not measured.

## 14. Flip share (exploratory: option P&L of spent data)

For each structure at R = 60, held to expiry and settled at intrinsic value against the panel's final settlement price:
`P&L = (terminal value - V) x lot - charges`, once with `V = V_decision` and once with `V = V_fill`. Charges (C1,
`fno/costs.py`, today's `charges` block for every year, reasoning only): each leg's order at its own entry price
(`order_charges`, buy for bought legs, sell for sold legs) plus its settlement (`settlement_charges_breakdown`, closing
side sell for a bought leg, buy for a sold leg). A P&L of exactly zero is not a win.

- **Bad flips:** wins at the decision price that do not win at the fill price, as a share of those wins.
- **Good flips:** losses at the decision price that win at the fill price, as a share of those losses.
- Interval: resample whole expiries with replacement (B = 10,000, seeded as section 12), ratio of pooled counts; a
  resample with a zero denominator is dropped and counted.
- Entries whose expiry has no settlement yet (27 Oct 2026) are left out of the flip share and counted.
- The report prints only these two shares, never a win rate or a mean P&L.

## 15. Spread caveat

Candle closes carry no spread. A4 has 15:00 bid and ask from 14 Oct 2026 only, and nothing at 09:45, 10:15 or
14:00-14:45, so **the spread at the fill times is not measured**. As an order of size only, the report gives, per
family, its number of legs x the median half-spread (Rs per unit) of A4's valid quotes in one distance band
(`fno/quotes/report.py` bands): the 0-1% band for every family except SC, which uses the 2-3% band (its legs sit about
2% and 3% from spot). It states the number of A4 days used.

## 16. Differences from the story text

1. Nights split: 0, 1, 2, 3 or more (the story names 1 against 3 or more; a midweek holiday gives 2 nights and would
   otherwise belong nowhere).
2. A decision day whose next session is special or muhurat is left out (the story leaves out only special and muhurat
   decision days).
3. The flip share leaves out entries into an expiry not yet settled (the 27 Oct 2026 expiry of late-September days).
4. The splits print no interval (the story names none).

## 17. Raw data and fetching

- **Plan:** for each needed contract (every leg of every family at widths 100, 200 and 300 on every decision day, and
  each expiry's future), one call covering the first decision day to the last fill day that uses it (at most 90 days;
  split if longer). Groww symbols: `NSE-NIFTY-{expiry:%d%b%y}-{strike}-{CE|PE}` and `NSE-NIFTY-{expiry:%d%b%y}-FUT`.
- **Calls:** only through `ReadOnlyGroww` behind `ContractCandles`, at least 0.5 s apart (at most 2 a second), outside
  market hours (not 09:00-15:45 IST on a session day).
- **Raw answers** go to Drive through `RawFileStore` at
  `raw/groww/options/nifty-candles-15m/<expiry year>/<expiry>/<symbol>_<start>_<end>_<sha16>.json.gz`
  (gzip with no time in its header, content-addressed), each with a manifest row (symbol, window, path, SHA-256, size, times; never a price) in
  `research/data/manifests/groww-candles/nifty-options-15m.csv`. Drive first, then the row. Nothing raw goes in the
  repository.
- A call that fails is retried once after the full plan; a contract still failing is missing (section 6) and listed.
- **Dry run first:** 5 decision days with real answers, giving the call count and duration, before the full fetch.
- The analysis reads only archived copies (checked against their manifest SHA-256), never a live answer.

## 18. Data spend

At registration: Groww 2024-26 NIFTY option and future 15-minute candles become `registered` (trial 54). After the
run: `spent` for the 14:00-to-next-10:15 windows of the sampled contracts (`C` is the P&L of "sell at the decision, buy
back at the fill"). Their 2019-23 candles stay `fresh`. The flip share reads 2024-26 final settlement prices, already
seen through the spent monthly data. A4's 15:00 spreads are read as a cost size (exposed for spread, not for price).

## 19. Run procedure

1. This protocol, the idea card (`research/ideas/FT1.md`), ledger row 54 and the DATA_SPEND rows are committed
   together; `FREEZE.md` records this file's SHA-256 and the commit.
2. The analysis code is built and tested on synthetic candles only (`tests/research_ft1/`); its file hashes go in
   `FREEZE.md` in their own commit before the full fetch.
3. `python study.py --dry-run`, then `python study.py --fetch`, then `python study.py --run` once. `--run` refuses to
   run unless every frozen file hashes to its row and the folder has no uncommitted change. It writes `results.json`
   and `results.md`.
4. A code judge (assigned by the orchestrator) recomputes two hand days from the archived answers before merge.

## 20. What the report says it cannot measure

- What waiting costs in the decision itself (an older signal): not measured.
- The spread at the fill times: not measured (section 15).
- What the 14:00 path gives up (the last hour's information): not measured.
- Candle closes are last trades, not the bid or ask the owner would get; only the live follow-up (after 20 A16
  sessions, the story's live rule) can confirm these figures.
