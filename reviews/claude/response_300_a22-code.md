# Response 300: A22 code, the morning capture (GIFT Nifty, NSE's pre-open list, NIFTY and BANKNIFTY 09:09 candles)

Builder session_013u1Ac2N9eRQ8XCYPjwpaat, for Judge F (session_01QLDqmpqUA7gAi7vcijnj5Y). Branch `story/a22-preopen`.
Text: `docs/stories/A22-preopen-data.md` (judge 407 PASS, add. 1 and 2). O8's owner (session_012eM7Ti) reviews the
`fno/health/` diff before the judge, as agreed.

## What is built

| Criterion | Where | Evidence |
|---|---|---|
| 1 GIFT Nifty | `fno/preopen/answers.py` `read_gift_nifty` | level, NSE time, contracts, expiry; 15 min old fresh, 16 stale, yesterday stale, before midnight stale, a minute "ahead" accepted (NSE's minute resolution), 2 ahead stale; HTML, a list, no block, missing fields refused (`tests/preopen/test_answers.py`) |
| 2 F&O pre-open list | `read_preopen_list` | stock count and stocks with an IEP; another day's time, a time before 09:08:00 and an empty `data` are incomplete, never complete; 09:08:00 exactly is final |
| 3 Index pre-open | `read_index_preopen`, Groww through A16b's `GrowwCandleSource` over `ReadOnlyGroww` | the 09:09 candle's close, `source_time` 09:10:00; candles stopping before 09:09 "no 09:09 candle yet" (retried to 09:10:59); candles only from 09:15 "no pre-open value"; a time with an offset refused |
| 4 Windows | `fno/preopen/run.py` | exact boundaries on an injected clock (`tests/preopen/test_run.py`): GIFT waits at 08:39:59, reads at 08:40:00, 08:44:59 `ok`, 08:45:00 `late`; the list reads 09:08:30, 09:09:00 ... 09:10:30, 09:10:59, then `incomplete`; the candles 09:10:00, 09:10:30, 09:10:59; stale then fresh is `ok`; a read seen after the close is `late` even if it started inside |
| 5 Storage, records | `fno/preopen/record.py`, `day_row.py` | raw answers and the day row write-once through O9's `DataStore` (receipts); one O10 row per problem; one alert per run; the second run finds the day row taken and the first row stands; Drive down names each unsaved file and writes no receipt; no value in any committed file, O10 row or alert (`tests/preopen/test_record.py`) |
| 6 Routine | CLAUDE.md "Pre-open capture (story A22)"; `python -m fno preopen record` | end to end with the real adapters over a fake NSE session and fake Groww candles (`test_record.py`) |
| 7 Real output | after the owner creates the 08:36 routine | **pending** (first two live mornings) |
| 8 Witness | `fno/health/preopen_checks.py`, one `Expectation` row (`live_from` None) | receipt pushed at 09:20:00 ok, 09:20:01 late; absent 09:19:59 not due, 09:20:00 missed (O8's shared rule); unknown push time is `unknown`; regular and special expected, holiday and muhurat not (`tests/health/test_preopen_check.py`). FL1's 09:15 line "pre-open data: missing" is FL1-2's code (not built); its contract is `day_file(day)` and `receipt_path(day)` in `fno/preopen/day_row.py` |

Safety: `tests/preopen/test_safety.py` (no trading call in the package; `GrowwProvider` only in `wiring.py`, held
through `ReadOnlyGroww`).

## Real checks from this container (22 Oct 2026, about 03:00 IST) [strong: direct reads]

- The readers on NSE's real answers kept in my scratchpad (not committed): GIFT Nifty (NSE time 22 Oct 02:44) complete;
  the F&O list of 21 Oct: 213 stocks, 213 with an IEP, NSE time 09:08:43, complete.
- The production adapters live on 21 Oct (Groww, read-only): NIFTY and BANKNIFTY both complete, source time 09:10:00.
  Groww's BANKNIFTY symbol `NSE-BANKNIFTY` probed the same night (17 one-minute candles 09:00-09:16).
- Step 0b again, through the production reader (judge 407 add. 2 asked for the output). It compares the 09:09 close
  with NSE's `ind_close_all` Open Index Value, printing differences only:

```
2026-09-21  nifty diff +0.00  banknifty diff +0.00
2026-09-22  nifty diff +0.00  banknifty diff +0.00
2026-09-23  nifty diff +0.00  banknifty diff +0.00
2026-09-24  nifty diff +0.00  banknifty diff +0.00
2026-09-25  nifty diff +0.00  banknifty diff +0.00
2026-09-28  nifty diff +0.00  banknifty diff +0.00
2026-09-29  nifty diff +0.00  banknifty diff +0.00
2026-09-30  nifty diff +0.00  banknifty diff +0.00
2026-10-01  nifty diff +0.00  banknifty diff +0.00
2026-10-05  nifty diff +0.00  banknifty diff +0.00
2026-10-06  nifty diff +0.00  banknifty diff +0.00
2026-10-07  nifty diff +0.00  banknifty diff +0.00
2026-10-08  nifty diff +0.00  banknifty diff +0.00
2026-10-09  nifty diff +0.00  banknifty diff +0.00
2026-10-12  nifty diff +0.00  banknifty diff +0.00
2026-10-13  nifty diff +0.00  banknifty diff +0.00
2026-10-14  nifty diff +0.00  banknifty diff +0.00
2026-10-15  nifty diff +0.00  banknifty diff +0.00
2026-10-16  nifty diff +0.00  banknifty diff +0.00
2026-10-19  nifty diff +0.00  banknifty diff +0.00
2026-10-21  nifty diff +0.00  banknifty diff +0.00
sessions 21 equal {'nifty': 21, 'banknifty': 21} largest abs diff {'nifty': 0.0, 'banknifty': 0.0}
```

## Choices beyond the text, each with its reason (the judge decides)

1. **Raw answers kept: the one each part ends on** (its complete answer, or its last usable one), not every retry.
   Writing up to 6 Drive files per part inside a 60-second candle window would delay the retries. `<part>_reads` in
   the day row counts every read. [reasoning]
2. **NSE's `key=NIFTY`/`key=BANKNIFTY` lists not read.** The text kept them only "if they answer at 09:08" and said
   no criterion needs them. The F&O list already holds every NIFTY 50 and BANKNIFTY constituent (all are F&O stocks)
   [some evidence: the F&O list of 21 Oct has 213 stocks; I have not matched them name by name].
3. **The F&O list is complete only from NSE's 09:08:00.** That is stricter than the text's "today's": order entry
   closes at random between 09:07 and 09:08, so an earlier time is not the final result.
4. **A run started after a window reads once.** Complete then is `late` (seen time in the detail), else
   `incomplete`, matching the text's GIFT rule for every part.
5. **Values only for `ok` or `late` parts.** An incomplete part keeps its status and the reason; its raw answer
   stays in Drive. So a stale GIFT level can never be read as today's.
6. **A16's checked clock is asked once at the start** (08:36-08:40 has time to spare). A skew or an unchecked clock is
   a problem line, and the day row's `clock` column records it.
7. **Commit order:** the O10 error log first, then `receipts/`. The receipts are new files and never block the log's
   pull; the receipts committer carries a log commit whose own push failed (`run_paths`).
8. **A16b's `GrowwCandleSource` gained `symbol=`** (default `NSE-NIFTY`, unchanged for A16b). This reuses it, as
   the design says, instead of a copy. I'll tell its builder (01MBnbVU4sundxNjs5u4xCsP).

## Gates

`pytest -n auto`: 9,023 passed, 17 xfailed. `ruff check`, `ruff format --check`, `check_imports` and
`check_records` are clean. Every file is under 350 lines (largest 98). A22's tests: 49 in `tests/preopen/` and 7 in
`tests/health/test_preopen_check.py`. **Mutations: 11 of 11 caught**: GIFT 15 to 16 min; 09:08 to 09:07; the 09:09
candle to 09:08; the last read 09:10:59 to 09:11:00; `late` from `<` to `<=`; values for every status; 09:20 to
09:21; part problems dropped; BANKNIFTY's symbol. The same-day GIFT rule survived at first, so I added a
before-midnight test, which now catches it.

## Open

- The owner creates the 08:36 IST routine (prompt in CLAUDE.md). Then `live_from` is set in its own commit, and
  criterion 7 and the first week's miss rate are reported here.
- Judge 407 add. 2: measure Groww's serving delay for the 09:09 candle (`nifty_seen_at` minus 09:10:00 against the
  09:10:59 limit) on the first live week; widen toward 09:11:30 if near the limit.
- Text open question 2 (the owner's personal-research rule covering NSE's GIFT Nifty and pre-open pages) is not answered
  in DESK_DECISIONS as far as I found.
