# NIFTY option-chain panel (story A3)

Every NIFTY index option and every NIFTY index future on every NSE session from 1 Jan 2019, built from NSE's raw
daily files by
`python -m fno nifty-panel --to YYYY-MM-DD [--from 2019-01-01] [--raw-folder FOLDER]`
(`fno/research_data/nifty_panel.py`, files written by `fno/research_data/panel_store.py`). Research data only.

## Files

- `options_<year>.csv.gz`: one row per option contract per session, columns
  `date, expiry, strike, type, close, settle, volume, open_interest, underlying, vix, source_format, session`.
  - `close`, `settle`: NSE's closing and settlement price (rupees, two decimals). A contract that did not trade keeps
    NSE's close (often the previous close): check `volume` before treating `close` as a traded price.
  - **On its expiry day `settle` is not an option price.** For an expiring option NSE reports the index settlement
    value there: from 6 Feb 2020 on it equals that day's Nifty 50 close (`underlying`; e.g. every option expiring
    2026-09-01 has `settle` 24055.80), and up to 30 Jan 2020 it is 0.00 (measured on every expiry-day row of this
    build). Use `close`, or the payoff from the index settlement, on expiry days.
  - `volume`: contracts traded (old format `CONTRACTS`, UDiFF `TtlTradgVol`; equal on days with both formats);
    `open_interest`: open interest in units.
  - `underlying`: that day's **Nifty 50 close** and `vix` that day's **India VIX close**, both from NSE's
    index-close file (`ind_close_all_DDMMYYYY.csv`) for every row, whatever the F&O format.
  - `source_format`: `udiff` (current format, used whenever it exists: every day from 1 Jan 2024) or `legacy`
    (old format, 2019-2023).
  - `session`: the calendar's session kind, `regular`, `special` (weekend live sessions: Budget days, DR-site drills)
    or `muhurat` (Diwali's one-hour evening session: its closes are not normal daily closes; exclude them where that
    matters).
  - Sorted by date, expiry, strike (numeric) and type; (date, expiry, strike, type) is unique.
- `futures_<year>.csv.gz`: every listed NIFTY index future per session (near, next and far month), columns
  `date, expiry, close, settle, volume, open_interest, underlying, source_format, session`, same meanings; sorted by
  date and expiry, (date, expiry) unique. The near-month future is the market's forward (carry and dividends), which
  put-call parity and implied-volatility work need; the spot index ignores both.
- `manifest.json`: build range, calendar SHA-256, columns, each output file's SHA-256 (gzip and uncompressed CSV) and
  row count, and per session: session kind (`regular`, `special`, `muhurat`), status, the F&O file and index-close
  file used with their SHA-256, and the option and future row counts (`rows`, `futures_rows`). A session left out
  says why (`no file` + the sourced exception).

## Rules the build enforces

- Days come from the NSE session calendar (`research/data/calendar/nse_sessions.csv`), never from weekdays or from
  which files exist; Saturday/Sunday special sessions and Diwali muhurat sessions are included.
- A session without its F&O file, its index-close file, a Nifty 50 close, an India VIX close, NIFTY options or NIFTY
  futures fails the whole build (nothing is written, the days are named) unless `research/data/calendar/exceptions.csv` has a sourced row for it.
- Values are copied, not rounded: a price with more than two decimals or a fractional count fails the build.
- Same raw files, same bytes: fixed column order, gzip without file name or timestamp, sorted JSON without build time.
  The gzip bytes can differ under another zlib version; `csv_sha256` in the manifest checks the content regardless.
- A build never shrinks the panel: a range that starts later or ends earlier than the existing manifest's is refused
  before anything is read (delete `manifest.json` on purpose to start a smaller panel). Rebuild only when research
  needs new days: each rebuild rewrites the current year's files.
- Raw files are read through `RawFileLibrary` (local folder, then Drive, then NSE); Drive is never written.

## Build of 13 Oct 2026 (2019-01-01 to 2026-10-12)

1,928 sessions in the panel, 1 left out (2021-03-30: NSE never published its old-format F&O file; sourced exception).
4,058,698 option rows and 5,784 future rows (3 listed NIFTY futures every session); 46.7 MB compressed with the
manifest. Checks: `research/2026-10-13-nifty-panel/`.

| Year | Sessions | Option rows | Options file | Future rows | Futures file |
|---|---|---|---|---|---|
| 2019 | 245 | 773,364 | 7.9 MB | 735 | 13 KB |
| 2020 | 252 | 736,996 | 7.8 MB | 756 | 13 KB |
| 2021 | 247 | 510,565 | 5.7 MB | 741 | 13 KB |
| 2022 | 248 | 562,041 | 6.3 MB | 744 | 13 KB |
| 2023 | 246 | 340,423 | 4.1 MB | 738 | 13 KB |
| 2024 | 249 | 398,739 | 4.9 MB | 747 | 13 KB |
| 2025 | 249 | 395,866 | 4.9 MB | 747 | 13 KB |
| 2026 (to 12 Oct) | 192 | 340,704 | 4.3 MB | 576 | 10 KB |

Not included: other underlyings, open/high/low, previous close, lot size.
