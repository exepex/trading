# NSE market read models (story P6)

The India blocks of the dashboard's Screener (33) and Markets overview (34) that the W11 contract assigns to publisher
`fno` (exepex/trading), built from NSE's own daily files archived in Drive, validated against the pinned contract
(`contracts/omenix-dashboard/`) and published all at once per session.

| Page key | W11 endpoint | Stored as (W11 2.4) | Served by the route |
|---|---|---|---|
| `screener_summary` | `/markets/india/screener/summary` | the served payload (all, n500, fno, ours) | as stored |
| `screener_stocks` | `/markets/india/screener/stocks` | `ScreenerStocksTableIndia` (every row) | filtered, sorted, paged (Markets movers are pages) |
| `fno_screener_summary` | `/markets/india/fno/screener/summary` | the served payload | as stored |
| `fno_screener_rows` | `/markets/india/fno/screener/rows` | `FnoScreenerTable` (every row) | paged (Markets index options: four rows) |
| `overview_indices` | `/markets/india/overview/indices` | the served payload | as stored |
| `overview_sectors` | `/markets/india/overview/sectors` | the served payload | as stored |

"ours" (the companies the stock tool follows) is counted and tagged here over the NSE rows, from the stock tool's list
(W11 input `FollowedCompaniesIndia`, orchestrator decision of 13 Oct 2026, judge 40): a close uses the latest list dated
on or before it (`followed.py`). Until the stock tool publishes the list (K5-proposed), lists are recorded in
`research/data/followed-companies/india/<as_of>.json`; without a list for a close, the run stops.

How each figure is computed follows the contract's own examples (dashboard `design/mockups/33-screener/fetch_nse.py`,
`_platform/screener_data.py`, `_platform/markets_data.py`): one year and a week of capital-market and index files, three
months of F&O files, the same formulas (returns 1, 5, 21, 63, 250 sessions back; Wilder RSI 14; ATM IV by
Black-Scholes on the spot with the B1 solver, rate `risk_free_rate`). Two deliberate differences: sessions come from
NSE's calendar, never weekdays (the examples once skipped the 1 Feb 2026 Sunday Budget session), and an index absent
from a session's file carries its own last date in `as_of` instead of passing an older close off as the day's.

Modules: `nse_files.py` (readers, also the archive's content checks), `stock_rows.py`, `fno_rows.py`, `index_rows.py`,
`session_rows.py` (reads one session's archived files; a missing file stops the build), `blocks.py` (one builder class
per block, pure), `contract.py` (the pin, validation, drift), `publication.py` (stored rows, validated as stored and as
served), `publisher.py` (`ReadModelPublisher`), `local_publisher.py`, `postgres_publisher.py` (the Azure `fno` schema,
tables in `db/fno/migrations/`), `market_run.py` (one session, all or nothing, alerts), `cli.py`.

Commands:
- `python -m fno market daily [--day D]`: the routine. Archives the session's F&O, index, capital-market and delivery
  files and the two reference lists to Drive (with manifest rows, committed), then builds, validates and publishes to
  Azure (`FNO_DB_URL`, the fno publisher role; environment settings only). Run it the next morning (for example 07:30
  IST): NSE rewrites some evening files late (the 12 Oct 2026 index file gained two indices at 23:20 IST).
- `python -m fno market publish --day D [--local FOLDER]`: one session from the archived files.
- `python -m fno market compare --day 2026-10-12`: the built blocks against the pinned W11 examples, field by field.
- `python -m fno market contract-check`: the pinned contract against the dashboard's published files.

Any failure (a missing file, a schema break, a refused publish) stops the run before anything is visible, prints the
reason and alerts #fno-desk; the previous publication stays current. Never an order function; research data only.
