# Response 315: G13c code, each contract's market-implied ITM chance and its calibration (builder's claims, for Judge B)

**From:** G13/G13b builder, session_01UkTaDeTRF9ksDgQB9cTU5C · **Branch:** `story/g13c-itm-chance` at 108faff8 ·
**Story text:** `docs/stories/G13c-itm-chance.md` (judges 452 and 452.1 PASS) · **Lane:** 1.

## What is built

New package `fno/itm_chance/`, 13 files, the largest 101 lines. Its composition root `fno/itm_chance/wiring.py` is
added to CLAUDE.md's list. Nothing in `fno/price_distribution/`, `fno/price_ranges/` or `fno/desk/` is edited.

| File | What it does |
|---|---|
| `chances.py` | `ContractChance` and `ExpiryChances`. G13's stored CDF points and tail anchors are rebuilt into G13's own `Distribution` (so the arithmetic is `Distribution.cdf`, not a copy). PE = F(K), CE = 1 - F(K); `region` is body or tail; `measure` is always "risk-neutral (market-implied), not a forecast"; `source` is 3pm or backfill_eod. |
| `records.py` | G13's own record-file reader over the verified Drive cache. It keeps only records of G13's current method (d3980df7; the older 2c7d8a43 back-fill is in Drive and is skipped), each (underlying, day, source) once, live before back-fill. |
| `settlement.py` | `LegacyFileSettlement` behind E7's `SettlementPrices` (the expiring FUTIDX row's SETTLE_PR; option rows must equal it or be 0, else refused). `FirstSettlement` asks E7 first, the legacy reader second. `settle()` cross-checks against G13b's official close (less than half a paisa apart, else left out with both values; no close: kept and flagged). |
| `rows.py` | Calibration rows: body strikes once per (record, expiry), p = P(S_T > K), y = settlement > K (equal is not above). Bucket and bin rules. `all` = per day and expiry the 3pm rows when present, else the end-of-day rows, never both. |
| `calibration.py` | Per bucket and bin: rows, expiries, mean chance, frequency. Per bucket: Brier and reliability. Every 95% interval comes from one cluster bootstrap over expiries (sums per expiry, 2,000 draws, seed 20261022). |
| `report.py` | One report per underlying: settled expiries and their outcome source, the left-out expiries (with reason and the issue days lost), the expiry-day change read from the records, the no-distribution reasons by kind, and the slices (all, 3pm, backfill_eod, before and from the change). Header: measure, exploratory note, tail note, unit note. No `made_at`. |
| `publish.py` | Write-once to Drive (O9 receipt), named by the last settled expiry and the content's SHA-256. Nothing is written while nothing is settled, or when Drive already holds a report for that last expiry. |
| `reader.py` | `ItmChances.for_day / for_contract` and `ItmCalibration.latest`, as sent to FL1 and the designer. One addition: `for_contract(..., source=None)` picks a source when a day has both (default: the 3 pm chain). |
| `cli.py` | `python -m fno itmchance calibrate [--underlying U]` and `chances --day D --underlying U` (prints only). |

## Judge 452.1's check, on real files (22 Oct)

- E7 alone covers only the UDiFF library (from 2024). For 2019-2023 expiries it returns None ("not published"), so
  those expiries would silently look unsettled.
- The legacy reader fills them. Of the 93 settled NIFTY expiries, 60 settle from the FUTIDX row and 33 through E7.
  **All 93 equal G13b's official close to the paisa; there is no mismatch.**
- Option rows read 0 on 31 Jan 2019 and carry the future's price in 2021, 2023 and 2024 (my probe of
  the real files, 22 Oct). I did not count the 0-row expiries one by one: the reader accepts both, so the count changes nothing;
  I can add it if you want it.

## Real-data run (dry: nothing written to Drive until your PASS)

Through the verified Drive cache: 1,933 current-method records, 233 s.
- **NIFTY:** 93 settled expiries, 2019-01-31 to 2026-09-29. 92 give rows: the 28 Jun 2023 expiry appears in the
  records only on its own expiry day, which is not eligible. 280,778 rows. The 3 pm slice is empty, because the
  3 pm records (from 1 Oct 2026) have no settled expiry yet.
- **Left out: 29 Jun 2023, 40 issue days.** G13's end-of-day panel labels June 2023's contract as expiring 29 Jun,
  but NSE settled it on 28 Jun (29 Jun was a holiday). No file exists for 29 Jun, so G13c leaves it out and lists
  it, never re-mapping it [strong: files read]. This is a G13 panel label, not a G13c rule, and fixing it would be a
  new G13 method. It is in the work register's G13c row as an open question.
- **BANKNIFTY:** no settled expiry yet, so no report. Its first is 27 Oct 2026, if the 3 pm records hold.
- **Expiry-day change:** read as 30 Sep 2025, the first Tuesday monthly expiry after which no Thursday follows.

Brier by horizon, all sources, with the 95% interval and n expiries:

| Days to expiry | Rows | Expiries | Brier [95%] | Reliability |
|---|---|---|---|---|
| 1-7 | 37,955 | 92 | 0.0341 [0.0298, 0.0392] | 0.00028 |
| 8-21 | 79,222 | 92 | 0.0632 [0.0557, 0.0720] | 0.00056 |
| 22-45 | 115,452 | 92 | 0.1063 [0.0940, 0.1205] | 0.00009 |
| 46+ | 48,149 | 89 | 0.1497 [0.1276, 0.1748] | 0.00118 |

What the bins show (descriptive, exploratory, no multiplicity control):
- Up to 21 days, the realised frequency of "settled above K" sits below the market's chance in every middle bin.
  - 1-7 days, the 0.45-0.55 bin: chance 0.499, frequency 0.463 [0.379, 0.551].
  - 8-21 days, the same bin: chance 0.500, frequency 0.425 [0.340, 0.516]. This is the one middle bin whose
    interval leaves out its own chance.
  - Over 22-45 days the gap is gone (0.500 against 0.482).
- So, short-dated, NIFTY ended above near-the-money strikes about 4-7 points less often than the risk-neutral
  chance said. Equivalently, near-the-money puts finished in the money more often than priced [some evidence: 92
  expiries, wide intervals, end-of-day traded closes, spent data].
- Reliability looks tiny because the extreme bins hold most rows. The bins, not the reliability number, are what to
  read.

## Tests and checks

- `tests/itm_chance/`: 39 tests for criteria 1-5.
  - Hand chances: body, on a point, both tails; put plus call = 1.
  - Region and the missing-distribution reason.
  - Legacy, E7-first, mismatch, no close and refusal.
  - Hand frequencies, Brier and reliability; bin and bucket edges; equal is not above; as_of.
  - The bootstrap: one expiry has no spread however many rows it has; repeating every row leaves intervals
    unchanged; different expiries give a spread.
  - The source rule, the regime rule (with a stray Tuesday), byte-identical reruns, write-once and nothing-written,
    and the readers (current method only; 3 pm first; the latest report).
- 20 of 20 planted bugs are caught. They are: put/call swap, region edges, tail IV units, equal-is-above, tail strikes
  as rows, source preference, bin edge, bucket edge, row-level weights in the bootstrap, reliability weight, Brier
  term, the paisa check, option rows ignored, the reader order, as_of, the regime rule, publish's already-written
  check, the method filter, the reader's source default, and latest by as_of only.
- Full suite on the branch: 9,611 passed, 16 xfailed. Ruff, format, imports and the records scan are clean. Every
  file is under 350 lines.

## Deviations from the text

1. `for_contract` has an optional `source` argument (above).
2. The report also lists every expiry's settlement (price, source, close), not only the left-out ones, so the
   cross-check can be audited.
3. Criterion 6's first run is done dry. On your PASS I run `itmchance calibrate` once, commit the receipt, and merge
   with a merge commit.

## Open for the owner (unchanged)

- Q1: a corrected chance as a forecaster under a protocol?
- Q2: weeklies?
- New: should G13's panel back-fill map a holiday-moved expiry (June 2023) to its settlement day? That would be a
  new G13 method.
