# Data-spend register (story R1, gate G2)

One row per data set (instrument, period, price type): which trials have used it and for what. A test may count only
on data that is `fresh` for the quantity it measures; on `spent` or `exposed` data it is **exploratory** and cannot
pass (`research/FACTORY_RULES.md`, section 4). Source of the first rows: design v2, `03_layers_factory_desk.md`
section 3.1, checked against `research/LEDGER.md` on 15 Oct 2026. A change to this file is lane 1 (hand edit under
`research/`); every registration updates its rows **in the same commit as its ledger rows**.

## Status words

| Status | Meaning |
|---|---|
| `fresh` | No trial has read the quantity a test would measure (prices, outcomes or moves of the period) |
| `exposed` | Read as a predictor or seen in analysis; a new test that uses it as a predictor is weaker evidence, and a test of the same quantity is exploratory |
| `spent` | Its outcomes were tested; any further test on it is exploratory |
| `forward` | Recorded live from a date; each future day is fresh until a registered test reads it |
| `registered` | A frozen protocol will read it; status changes when the test runs, to what it actually read |

## Register

| Data set | Price type | Period | Status | Used by (ledger trials) | Notes |
|---|---|---|---|---|---|
| NIFTY monthly options | NSE daily closes | 2024-2026 | `spent` | 1-21 (desk meeting 1, review 9-10), 22-31 (experiment 1, discovery); 71-82, 95-96 (EDGE1, exploratory, protocol frozen `3152ed44`) | Discovery data; never out-of-sample again |
| NIFTY monthly options | NSE daily closes | 2019-2023 | `spent` | 22-31 (experiment 1, challenge holdout), 42 (desk meeting 2, one more look at the windows); 71-82, 95-96 (EDGE1, exploratory, protocol frozen `3152ed44`) | Used up by experiment 1's holdout (judge 53, ChatGPT review 30) |
| NIFTY weekly options | NSE daily closes | Feb 2019 - 9 Oct 2026 | `spent` | 43-52 (weekly-weather study, frozen `650dd8f`) | Used once, there |
| NIFTY 50 index | daily closes | 2017-2026 | `exposed` | many: experiment 1 features (F1), 42, 43-52 | Predictor and holding-window moves seen |
| India VIX | daily closes | 2017-2026 | `exposed` | experiment 1 (F2), 43-52; registered 58, 59, 65 (GR1, predictor) | Predictor |
| Event calendar (A6) | dates | 2019-2026 | `exposed` | experiment 1 (F3), 43-52; registered 60 (GR1, predictor) | Predictor |
| NIFTY options 15:00 bid/ask (A4) | Groww quotes | from 13 Oct 2026 | `forward` | 37-41 (forecast protocol v2, live inputs); 54 (FT1 spread caveat, registered); 99 (market school pilot P1, NIFTY monthly and weekly at 15:00) | Each day after a test's registration is fresh for that test. The market school simulator's spread model (MS-SIM-b) also reads every recorded session's bid and ask here, spreads only and never an outcome, as the cost input of practice runs (practice never counts toward a test, a card or the pilot) |
| BANKNIFTY, FINNIFTY and MIDCPNIFTY monthly option 15:00 bid/ask (A4c) and NIFTY weekly (A4f) | Groww quotes (raw in Drive only) | from 19 Oct 2026 (NIFTY weekly from 22 Oct) | `registered` | 99 (market school pilot P1, a measurement) | Each session after the first counted session (unset; set when P1's 10-session gate passes) is read by the pilot's decisions and counted; earlier recorded days are read only for the capture gate and the drivers' 20-session history windows (spots and volatility as inputs, never as outcomes). Becomes `forward`-used when a session is counted. The simulator's spread model (MS-SIM-b) also reads the bid and ask of every recorded session of these roads, counted sessions included, as a cost input for practice only: spreads, never an outcome |
| Bid-ask spreads of the 15:00 captures (A4, A4c, A4f) | Groww quotes (raw in Drive only) | from 13 Oct 2026 | `exposed` | read by the market school simulator's spread model (MS-SIM-b), run 23 Oct 2026 | Cost input for practice only, no outcome: bid and ask of each recorded session, counted ones included. Practice results are never used to choose, tune or rank a counted driver (orchestrator, 23 Oct 2026) |
| NIFTY monthly option and future candles | Groww 15-minute candles (last trades), read-only | 2 Jan 2024 - 1 Oct 2026 | `spent` | 54 (FT1 fill timing, protocol frozen `47d1598`, run 15 Oct 2026 at `1962610`) | Spent for the 14:00-to-next-10:15 windows of the sampled contracts (`C` is the P&L of selling at the decision and buying back at the fill); the flip share read held-to-expiry P&L of these entries; the probe before the freeze read candle counts only |
| NIFTY monthly option and future candles | Groww 15-minute candles (last trades) | 2019 - 2023 | `fresh` | none | Not read by FT1 |
| NIFTY 15-minute quotes (A16) | Groww quotes | not yet recorded | `fresh` | none | Starts with A16 |
| Participant open interest (A8) | NSE daily files | history | `fresh` | none | Idea O1 waits for 20 measured release days |
| F&O stock options around results | NSE F&O bhavcopy: volume, open interest, lot size, strikes, entry-day closes | 1 Jan 2019 - 14 Oct 2026 | `exposed` | 53 (R2 feasibility, run 15 Oct 2026 from the study folder of 02e84d0) | Read by R2 for fit, liquidity and cost only; **no option P&L**, no exit price, no implied-vs-realised comparison was read. A later P&L test of stock options around results is not exploratory on account of R2 for outcomes, but its entry prices, volumes and open interest were seen |
| F&O stock event moves | NSE stock-future closes, entry session to R | 2019 - 2021 | `exposed` | 53 (R2, within-week correlation only) | 1,870 market-adjusted moves read for their intra-cluster correlation; no mean, sign or hit rate computed |
| F&O stock event moves | NSE stock-future closes, entry session to R | 2022 - 2026 | `fresh` | none | R2 read no exit price of these years (split from the row above on 15 Oct 2026 after the R2 run, as registered) |
| F&O stock option bid/ask | one Groww snapshot, 15 Oct 2026 14:00-14:19 IST (raw in Drive only, SHA-256 `b83836e3...bb6c3f`) | 15 Oct 2026 | `exposed` | 53 (R2) | Spreads and best quantities used as a cost input, never as an outcome |
| Company results dates (A12) | NSE board meetings (A12's daily `board-meetings_YYYYMMDD.json` lists, filled from 1 Dec 2018 through A12's own classes before the R2 run, R2 amendment 1 D1), results filings' `filed_at` (A12 `results-xbrl.csv`) | 2019-2026 | `exposed` | 53 (R2) | Event dates and filing times only; filed numbers were not read |
| NIFTY and BANKNIFTY ranges from option daily closes (G13b's implied, end-of-day back-fill, method `8d7d7301`) | NSE F&O daily closes, ranges for N1 and N3 | 2019 - 20 Oct 2026 | `spent` | read before any trial: implied's back-fill scores for every year (responses 262, 290; scores receipt fc01f689); registered 56-70 (GR1) | GR1 is exploratory for this reason (its protocol, section 2) |
| BANKNIFTY monthly options | NSE daily closes | 2019 - 20 Oct 2026 | `exposed` | read by G13b's implied back-fill (row above); 83-94, 97-98 (EDGE1, exploratory, protocol frozen `3152ed44`) | First P&L use is EDGE1's; the 20 Oct 2026 file was not archived at the build, so the data ends 19 Oct |
| Global cues (A17): S&P 500, US 10-year, USD/INR (Brent dropped, judge 428) | publishers' daily closes | 2019 - 2026 | `exposed` | 62, 70 (GR1, predictor; run 22 Oct 2026, response 314) | First predictor use |
| NIFTY intraday realised variance (A16b candles) | Groww 15-minute index candles, `rv_session` and the 09:15 open | 2 Jan 2020 - 2026 | `exposed` | G13b's overnight share (39.3%, measured 2020-2025, not a ledger trial); registered 63, 68-70 (GR1) | The N0 share 0.607 comes from this measurement |

## Update rule

- A new registration adds a row for each data set it will read (status `registered`, the quantity it reads) in the
  commit that adds its ledger rows.
- When the test runs, the row's status becomes what the test actually read (`spent` for tested outcomes, `exposed`
  for predictors and analysed quantities), with the run commit.
- A row is never deleted; a period split (as above for 2019-21 vs 2022-26) is a new row, with the reason.
