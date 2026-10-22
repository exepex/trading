# G13c. Each contract's market-implied chance of expiring in the money, and how well that chance has matched

**Repository:** trading · **Lane:** 1 (new story; forecast and evaluation records; Drive) · **Judge:** B ·
**Builder:** session_01UkTaDeTRF9ksDgQB9cTU5C · **Orchestrator:** session_01VG1RqxLFUVdvvPuMRYZtDH · **Branch:**
`story/g13c-itm-chance` · **Depends on:** G13 (`fno/price_distribution/`, merged and live), G13b's close tables
(`fno/price_ranges/closes.py`) · **Status:** story text for the judge (no code yet)

**Description.** As the options strategist and the risk manager, I want, for every NIFTY and BANKNIFTY monthly
contract on the 3 pm chain, the chance the market's own prices give it of expiring in the money, labelled plainly as
the market's risk-neutral chance and not as a forecast; and one report of how well those chances have matched what
happened, over every settled expiry, counted with the expiry as the unit. Then the desk can read "the market says 18%"
next to "when the market said 15-25% in the past, it happened x% of the time (interval a-b, n expiries)".

**Does this change a trade or stop decision?** No. Descriptive only; nothing reads it to size, enter, exit or block a
trade; it is in no frozen protocol. A "real-world" corrected chance would be a forecaster and needs a protocol (Q1).

## Why, and what is already there

- The chance is already inside G13's record: each usable expiry carries the implied CDF `F(K) = P(S_T <= K)` under the
  risk-neutral measure for that expiry (`fno/price_distribution/density.py`, `Distribution.cdf`; Breeden- Litzenberger
  between quoted strikes, one fixed lognormal tail rule outside). So a put at strike K is in the money with chance
  `F(K)`, a call with `1 - F(K)`. No new model, no fitted parameter [strong: code read].
- What is missing: (a) nobody reads it per contract, so FL1 and the dashboard would each compute it again (DRY); (b)
  nothing checks it against outcomes. Known theory says it should be biased: index puts carry a premium (variance and
  crash risk premia), so the risk-neutral chance of a large fall is expected to be above its real frequency [reasoning
  only: literature, not yet our data]. That bias is exactly what the desk needs to see before trusting or fading a
  price.
- History: G13's NIFTY back-fill from the end-of-day panel (label `backfill_eod`, 2019 onward, method d3980df7) has a
  CDF for the two nearest monthlies on each session; live 3 pm records from 14 Oct 2026 (NIFTY) and 19 Oct
  (BANKNIFTY). About 93 NIFTY monthly expiries (Jan 2019 to Sep 2026) are settled in that history; BANKNIFTY has none
  settled with a record yet (its first is 27 Oct 2026, if the 3 pm record holds) [some evidence: counts to be
  confirmed by the build's first run and stated in the report].

## Design

New package `fno/itm_chance/`, composition root `fno/itm_chance/wiring.py` (added to CLAUDE.md's list). Nothing in
`fno/price_distribution/` or `fno/price_ranges/` is edited; both are read through their existing readers.

### 1. Per-contract chance (read side, no new data file)

`ItmChances` (the reader FL1 and the dashboard use) derives, from one G13 record, one `ContractChance` per monthly
contract that G13 valued:

| Field | Meaning |
|---|---|
| `underlying`, `day`, `expiry`, `days` | as in G13's record |
| `strike`, `side` (CE/PE) | the contract |
| `itm_chance` | PE: `F(K)`; CE: `1 - F(K)`, from G13's stored CDF points and tail anchors, the same arithmetic as `Distribution.cdf` (one shared function, not a copy) |
| `region` | `body` (K inside the measured CDF) or `tail` (K outside: the lognormal tail rule decides; shown, never hidden) |
| `measure` | always the text `risk-neutral (market-implied), not a forecast` |
| `source` | `3pm` or `backfill_eod` (G13's label) |

- Weekly expiries are out (they go with A4's weekly chains, A4's builder).
- An expiry with no usable distribution gives no chances and its G13 reason, never a guessed number.
- No daily per-contract hit-or-miss mark: a single contract's outcome says nothing about calibration, and one expiry
  settles all its strikes together.

### 2. Calibration over settled expiries (one report file)

- **Rows.** For every record (live or back-fill) and every monthly expiry in it with a usable distribution, every
  strike in G13's CDF body, one row: predicted `p = P(S_T > K)` (the call's chance; the put's is `1 - p`, so the two
  sides are one test, counted once) and outcome `y = 1` if the expiry's settlement close is above K.
- **Outcome.** The index's official close on the expiry date (NSE's final settlement price for index options is the
  underlying's closing value on expiry day) from G13b's close tables (NIFTY panel closes; BANKNIFTY's close table). An
  expiry whose close is not yet in the table is not settled and is left out, counted.
- **Horizon buckets.** Days to expiry 1-7, 8-21, 22-45, over 45: the same strike means different things far from
  expiry.
- **Bins.** `p` in [0, 0.05), [0.05, 0.15), ..., [0.85, 0.95), [0.95, 1]: per bin and bucket the mean `p`, the
  observed frequency, rows, distinct expiries.
- **Unit = expiry.** All rows of one expiry share one settlement, and consecutive days of one expiry overlap, so the
  95% intervals come from a cluster bootstrap that resamples whole expiries (2,000 draws, fixed seed; a small function
  of its own, because G4's block bootstrap cuts date blocks, not clusters). Rows are never treated as independent.
  Effective sample is the number of expiries (about 93), so intervals will be wide; the report prints n expiries
  beside every number.
- **Summary scores.** Brier score per bucket and its reliability part (mean squared gap between bin mean `p` and bin
  frequency, weighted by rows), each with the expiry-bootstrap interval. No comparison baseline is claimed to win;
  this is a description of the market's chance, not a forecaster contest.
- **Split by source.** `backfill_eod` (traded closes, no bid/ask: noisier) and `3pm` are reported apart and together.
- **Regime check.** NIFTY's expiry weekday changed (Thursday to Tuesday from 1 Sep 2025, NSE's circular as recalled:
  reasoning only; the build reads the first Tuesday expiry from G13's records and uses that date): the report splits
  at that date too.
- **File.** `data/itm_chance/calibration/<underlying>_<last settled expiry>.json` in Drive, write-once, O9 receipt; a
  rerun with no new settled expiry writes nothing.
- **When.** A CLI `python -m fno itmchance calibrate`. Running it as an O1 step after a monthly expiry is a later
  change agreed with O1's owner (session_014zYLf18PgCzR7YoHs1X5Dp), not part of this story.

### 3. Reader names (shared with FL1 and the designer)

- `fno.itm_chance.reader.ItmChances.for_day(underlying, day) -> list[ContractChance]` and `.for_contract(underlying,
  day, expiry, strike, side) -> ContractChance | None`.
- `fno.itm_chance.reader.ItmCalibration.latest(underlying) -> CalibrationReport | None` (bins, buckets, Brier,
  reliability, intervals, n expiries, the settled-expiry list).
- Every display shows `measure` with the number, and the calibration line beside it shows n expiries; neither shows a
  per-day tick or cross.

## Acceptance criteria

1. `itm_chance` equals `F(K)` / `1 - F(K)` from `Distribution.cdf` on hand cases: inside the body, on a CDF point,
   below and above the tails; put plus call at one strike sum to 1.
2. `region` is `tail` exactly when K is outside the measured CDF; a missing distribution gives no chance and G13's
   reason.
3. Calibration rows on a synthetic history with known outcomes give the hand bin frequencies and Brier; an unsettled
   expiry is left out and counted; a close equal to K is not above.
4. The bootstrap resamples expiries, not rows: a test with one expiry duplicated across many rows gives the same
   interval as that expiry once.
5. Report file write-once with receipt; a rerun with no new settled expiry writes nothing.
6. Real-data run on NIFTY's back-fill: the report states the settled-expiry count, the rows per bucket, and the first
   and last expiry; the judge can rerun it.
7. Gates: full suite, ruff, format, imports, records scan; every file under 350 lines.

## Open questions for the owner

- Q1. If the report shows a steady bias (e.g. far puts' chance above their frequency), should a corrected chance be
  built as a forecaster under a protocol? Not in this story.
- Q2. Weekly contracts: wait for A4's weekly chains, or none?
