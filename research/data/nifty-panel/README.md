# NIFTY option-chain panel (story A3)

Every NIFTY index option on every NSE session from 1 Jan 2019, built from NSE's raw daily files by
`python -m fno nifty-panel --to YYYY-MM-DD [--from 2019-01-01] [--raw-folder FOLDER]`
(`fno/research_data/nifty_panel.py`, files written by `fno/research_data/panel_store.py`). Research data only.

## Files

- `options_<year>.csv.gz`: one row per contract per session, columns
  `date, expiry, strike, type, close, settle, volume, open_interest, underlying, vix, source_format`.
  - `close`, `settle`: NSE's closing and settlement price (rupees, two decimals). A contract that did not trade keeps
    NSE's close (often the previous close): check `volume` before treating `close` as a traded price.
  - `volume`: contracts traded (old format `CONTRACTS`, UDiFF `TtlTradgVol`); `open_interest`: open interest in units.
  - `underlying`: that day's **Nifty 50 close** and `vix` that day's **India VIX close**, both from NSE's
    index-close file (`ind_close_all_DDMMYYYY.csv`) for every row, whatever the F&O format.
  - `source_format`: `udiff` (current format, used whenever it exists: every day from 1 Jan 2024) or `legacy`
    (old format, 2019-2023).
  - Sorted by date, expiry, strike (numeric) and type; (date, expiry, strike, type) is unique.
- `manifest.json`: build range, calendar SHA-256, columns, each output file's SHA-256 (gzip and uncompressed CSV) and
  row count, and per session: session kind (`regular`, `special`, `muhurat`), status, the F&O file and index-close
  file used with their SHA-256, and the row count. A session left out says why (`no file` + the sourced exception).

## Rules the build enforces

- Days come from the NSE session calendar (`research/data/calendar/nse_sessions.csv`), never from weekdays or from
  which files exist; Saturday/Sunday special sessions and Diwali muhurat sessions are included.
- A session without its F&O file, its index-close file, a Nifty 50 close or an India VIX close fails the whole build
  (nothing is written, the days are named) unless `research/data/calendar/exceptions.csv` has a sourced row for it.
- Values are copied, not rounded: a price with more than two decimals or a fractional count fails the build.
- Same raw files, same bytes: fixed column order, gzip without file name or timestamp, sorted JSON without build time.
  The gzip bytes can differ under another zlib version; `csv_sha256` in the manifest checks the content regardless.
- Raw files are read through `RawFileLibrary` (local folder, then Drive, then NSE); Drive is never written.

## Build of 13 Oct 2026 (2019-01-01 to 2026-10-12)

1,928 sessions in the panel, 1 left out (2021-03-30: NSE never published its old-format F&O file; sourced exception).
4,058,698 rows, 45.6 MB compressed. Checks: `research/2026-10-13-nifty-panel/`.

| Year | Sessions | Rows | File size |
|---|---|---|---|
| 2019 | 245 | 773,364 | 7.8 MB |
| 2020 | 252 | 736,996 | 7.8 MB |
| 2021 | 247 | 510,565 | 5.7 MB |
| 2022 | 248 | 562,041 | 6.3 MB |
| 2023 | 246 | 340,423 | 4.1 MB |
| 2024 | 249 | 398,739 | 4.8 MB |
| 2025 | 249 | 395,866 | 4.9 MB |
| 2026 (to 12 Oct) | 192 | 340,704 | 4.3 MB |

Not included (out of the story's schema): NIFTY futures, other underlyings, open/high/low, previous close, lot size.
