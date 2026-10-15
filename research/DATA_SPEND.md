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
| NIFTY monthly options | NSE daily closes | 2024-2026 | `spent` | 1-21 (desk meeting 1, review 9-10), 22-31 (experiment 1, discovery) | Discovery data; never out-of-sample again |
| NIFTY monthly options | NSE daily closes | 2019-2023 | `spent` | 22-31 (experiment 1, challenge holdout), 42 (desk meeting 2, one more look at the windows) | Used up by experiment 1's holdout (judge 53, ChatGPT review 30) |
| NIFTY weekly options | NSE daily closes | Feb 2019 - 9 Oct 2026 | `spent` | 43-52 (weekly-weather study, frozen `650dd8f`) | Used once, there |
| NIFTY 50 index | daily closes | 2017-2026 | `exposed` | many: experiment 1 features (F1), 42, 43-52 | Predictor and holding-window moves seen |
| India VIX | daily closes | 2017-2026 | `exposed` | experiment 1 (F2), 43-52 | Predictor |
| Event calendar (A6) | dates | 2019-2026 | `exposed` | experiment 1 (F3), 43-52 | Predictor |
| NIFTY options 15:00 bid/ask (A4) | Groww quotes | from 13 Oct 2026 | `forward` | 37-41 (forecast protocol v2, live inputs) | Each day after a test's registration is fresh for that test |
| NIFTY 15-minute quotes (A16) | Groww quotes | not yet recorded | `fresh` | none | Starts with A16 |
| Participant open interest (A8) | NSE daily files | history | `fresh` | none | Idea O1 waits for 20 measured release days |
| F&O stock options around results | NSE F&O bhavcopy: volume, open interest, lot size, strikes, closes | 2019 - 9 Oct 2026 | `registered` | 53 (R2 feasibility, `research/2026-10-15-r2-stock-options-results/`) | R2 reads volume, open interest, lot values, strike steps and entry-day prices only; it reads **no option P&L** and no implied-vs-realised comparison. It does read event moves of **2019-2021 only**, for their within-week correlation (section 7 of the R2 protocol): after R2 runs, 2019-21 stock event moves become `exposed` (correlation only), 2022-26 moves stay `fresh` |
| F&O stock option bid/ask | one Groww snapshot | one session in the Oct-Nov 2026 results season | `registered` | 53 (R2) | Spreads only; used as a cost input, never as an outcome |
| Company results dates (A12) | NSE board meetings (A12's daily `board-meetings_YYYYMMDD.json` lists, filled from 1 Dec 2018 through A12's own classes before the R2 run, R2 amendment 1 D1), results filings' `filed_at` (A12 `results-xbrl.csv`) | 2019-2026 | `registered` | 53 (R2) | Event dates only; filed numbers are not read |

## Update rule

- A new registration adds a row for each data set it will read (status `registered`, the quantity it reads) in the
  commit that adds its ledger rows.
- When the test runs, the row's status becomes what the test actually read (`spent` for tested outcomes, `exposed`
  for predictors and analysed quantities), with the run commit.
- A row is never deleted; a period split (as above for 2019-21 vs 2022-26) is a new row, with the reason.
