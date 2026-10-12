# Old and current NSE F&O formats: proof that one reader gives the same data (12 Oct 2026)

**Question:** can 2019-2024 research use NSE's old-format daily F&O files as if they were the current UDiFF files?

**Method:** NSE published both formats for every trading day from 1 Jan to 5 Jul 2024. For each such day,
`validate_overlap.py` reads the old file (with that day's index-close file) and the UDiFF file through
`fno/fo_bhavcopy.py` and compares them contract by contract.

**Result (`overlap.json`):** 128 days compared, **128 identical**; 5,793,044 contract rows. Every day had the same
contracts in both formats and equal values for open, high, low, close, settlement price, open interest, change in
open interest, contracts traded, traded value (within the old file's Rs 1,000 rounding) and trade date. For every
index option and future the underlying price taken from NSE's index close equals the one UDiFF reports.

**What the old format does not have (left empty, never guessed):** underlying price for stock options and futures,
last traded price, previous close, number of trades, lot size. Research uses the current lot size anyway.

Re-run: `python research/2026-10-12-legacy-format/validate_overlap.py` (needs NSE access; uses Drive if set up).
