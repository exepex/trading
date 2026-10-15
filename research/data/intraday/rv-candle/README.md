# Candle-close realised variance, back-filled (story A16b)

**A back-filled row is history fetched later. It was never known at the time by this tool.** Each row was computed
from Groww's 15-minute NIFTY 50 candles, fetched long after the session (from 2026 for sessions since 1 Jan 2020). Its
`provenance` column says `backfilled` when the candles were first seen after the next session's 09:15 open (A17's
rule, `fno/global_cues/table.py`), and `live` only when they were seen before it. Decision 56: back-filled rows never
count as live forecast inputs; how a forecast built on them is labelled is G6's job.

Made by `python -m fno intraday backfill [--from YYYY-MM-DD] [--to YYYY-MM-DD]`; checked by
`python -m fno intraday backfill-verify` (every row recomputed from its Drive copies). Read-only towards Groww.

## Files

| Path | What |
|---|---|
| `<YYYY>/nifty_rv_candle_<YYYYMMDD>.csv` | one row per recorded session (regular or special), written once, never edited |
| `deferred.csv` | one row per run that put a session off (`deferred_at,session,reason`); a session's count is how many runs it has waited |

Raw candle answers stay in the owner's Drive (`raw/groww/indices/nifty-candles-<15m|1m>/<YYYY>/`), listed with their
SHA-256 in `research/data/manifests/groww-candles/nifty.csv`. No file here holds a price: only times, counts,
statuses, SHA-256 values, the realised variance and NSE gaps (differences).

## The row

A16's columns (`rv/` beside this folder, never mixed with it), with `measure` = `candle_close`, `method` =
`rv-candle-15m-v1` and `source` = `groww_candles`, plus:

- `provenance`: `backfilled` or `live` (above).
- `nse_check`: `checked`, or `unchecked` when NSE has no index-close file for the day.
- `nse_open_gap`: the last pre-open 1-minute close minus NSE's open (blank when no 1-minute check was made).
- `nse_high_gap`, `nse_low_gap`: NSE's high minus the highest used candle high; the lowest used candle low minus NSE's low.
- `outside_candles`: the day's candles that are not levels (09:00 pre-open, 15:30, after-hours).
- `copy_15m`, `copy_1m`: the Drive copies the row was computed from.

The 26 levels are the 09:15 candle's open and the closes of the 25 candles starting 09:15 to 15:15. Each is checked
against the session's 1-minute candles (within 0.05; decision 55) and against NSE's official open, high and low.

## Void reasons

| Reason | Meaning | Next session's overnight part |
|---|---|---|
| `missing_candles:N` | N of the 25 candles absent (short, halted or Groww's holes) | computed if the 15:30 candle exists |
| `no_1m_check:N` | the 1-minute answer lacks N needed minutes | void (levels untrusted) |
| `candle_mismatch:<marks>` | a level more than 0.05 from the 1-minute value | void |
| `outside_nse_range` | a level or a used candle's high or low outside NSE's range by more than 0.05 | void |
| `nse_unchecked` | NSE has no index-close file for the day | void |
| `no_previous_close` | the series' first session, or the previous session's 15:30 level is missing or untrusted | — |

A failed call or read (Groww, Drive, NSE) never writes a void row: the session is deferred and retried by the next run.
