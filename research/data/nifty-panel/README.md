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

## Warm-up closes (story A10)

`warmup_closes.csv`: the NIFTY 50 and India VIX close of every NSE session from 2017 (since 13 Oct 2026: to
12 Oct 2026, 2,423 sessions, including 2021-03-30 that the panel leaves out), columns
`date, session, underlying, vix, index_file, index_sha256`, from NSE's index-close files only, built by
`python -m fno nifty-warmup --from 2017-01-01 --to YYYY-MM-DD` (`fno/research_data/warmup_closes.py`). The panel
reader puts these days before the first session it reads as closes-only sessions (no option or future rows), so a run
that reads 2024 on (experiment 1's discovery) gets 2023's closes here, never from 2023's option file (judge 28); for
2019 on: F2 needs the previous 250 India VIX closes and 2018 has only 245 daily sessions,
hence 2017 too. 2017-18 F&O files are never opened. A session without its file or either close fails the build and
nothing is written. Muhurat sessions are kept with `session` = `muhurat` (the features leave them out).

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

## Daily closes after the panel (story O6, for G3)

From 13 Oct 2026 the GitHub Actions job `.github/workflows/index-closes.yml` (21:11 IST every day) archives NSE's
index-close file in Drive (A9, revisions kept per A11) and `python -m fno pipeline index-closes` appends each new
session's NIFTY 50 and India VIX close to `warmup_closes.csv`, from the version first archived in Drive (point in
time; a later NSE version never rewrites a row). Rows are only appended (`append_warmup_rows`). The reader gives
these days as closes-only sessions after the panel's last day whenever a read reaches that day, so live features and
base rates have closes through yesterday without rebuilding the panel.

## Build of 13 Oct 2026 (2019-01-01 to 2026-10-12)

1,928 sessions in the panel, 1 left out (2021-03-30: NSE never published its old-format F&O file; sourced exception).
The reader (`fno/research_data/panel_reader.py`) gives a left-out session the closes of `warmup_closes.csv` (NSE's
index-close file: NIFTY 50 14,845.10, India VIX 20.65 on 2021-03-30) and no option or future rows, so close series run
through it; a cycle entering on it is unfillable (no entry-day option data).
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

## Daily sessions after the build (story A13, waiting for G1 protocol v3)

Built, not yet active. `python -m fno pipeline panel-days` (GitHub Actions `.github/workflows/panel-days.yml`) appends
each new session's NIFTY option and future rows in place:
- each day is built with A3's own builder from the F&O and index-close files in Drive, using the newest version held at
  the run (A11);
- the day's closes must equal O6's `warmup_closes.csv` row;
- days are only appended after the manifest's `end`, never rewritten;
- a touched year file gets one more gzip member, so its old bytes stay a prefix;
- old manifest entries stay as they were, and new days carry `appended_at` and the calendar SHA-256 they used.

It appends nothing until `research/forecasts/FREEZE_v3.md` exists. Proposal: `reviews/claude/response_68_g1-v3-panel-extension.md`.
