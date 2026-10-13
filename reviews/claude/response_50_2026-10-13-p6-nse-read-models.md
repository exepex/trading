# Response 50: P6 NSE market read models for the Screener and Markets (builder's claims)

Status: **built; awaiting judge** (criterion 4 blocked on the owner: one environment setting, below). Story:
`docs/stories/P-publishing.md`, section P6. Commits on `main` (oldest first): the P6 build, the followed-companies
decision (judge 40), the corporate-action adjustment (judge 42), per-symbol lookups and manifest keys, the A11 merge and
content-check move, the demerger method (last: `7fa847b`), and this claims commit.

## What was built

| Part | Where | What it does |
|---|---|---|
| New raw datasets | `fno/storage/raw_source.py` (`NseEquityBhavcopySource`, `NseDeliverySource`), `fno/storage/snapshot_source.py` (`EquityListSource`, `Nifty500ListSource`, `CorporateActionsSource`, `CorporateActionsBySymbolSource`) | NSE's capital-market (UDiFF) and delivery files from 1 Oct 2025; daily copies of NSE's company list, Nifty 500 list and corporate-actions list, filed `<dataset>/<YYYY>/<MM>/<DD>/<original name>`; per-symbol corporate-action lists for symbols NSE's range list leaves out (ETFs) |
| Readers | `fno/market_read_models/nse_files.py`, `corporate_actions.py` | Parse each file; the same functions are the archive's content checks (`fno/storage/content_checks.py`) |
| Rows | `stock_rows.py`, `fno_rows.py`, `index_rows.py`, `session_rows.py` | Computed as W11's examples are (returns 1/5/21/63/250 sessions back, Wilder RSI 14, 52-week range, ATM IV by Black-Scholes on the spot with B1's solver, build-up, PCR, priced-in move), with sessions from NSE's calendar and past prices on today's share basis |
| Corporate actions | `corporate_actions.py` | Splits and bonuses by NSE's stated ratio; demergers by previous close / ex-date open (NSE's special pre-open price); schemes without a ratio and demergers without an ex-date trade keep only later sessions (null, never a wrong figure); unexplained jumps get the symbol's own NSE list |
| "ours" | `followed.py` | The stock tool's followed India companies (W11 input `FollowedCompaniesIndia`), latest list on or before the close; interim source below |
| Blocks | `blocks.py` | `BlockBuilder` interface, six classes: `ScreenerSummaryBlock`, `ScreenerStocksBlock`, `FnoSummaryBlock`, `FnoRowsBlock`, `IndicesBlock`, `SectorsBlock`; pure functions of `SessionRows` |
| Contract | `contract.py`, `contracts/omenix-dashboard/` | W11 2.4.0 pinned as byte copies (`pin.json`: dashboard commit `e299534`, each file's SHA-256); validation as stored (W11 `x-stored`) and as served; `drift` against the dashboard's `main` |
| Publication | `publication.py` | Each block's stored row (read-model columns, `product`, `publication_id`, payload SHA-256), checked before anything may publish |
| Publishers | `publisher.py`, `local_publisher.py`, `postgres_publisher.py`, `db/fno/migrations/001_read_models.sql` | `ReadModelPublisher`; local folder (atomic rename + pointer); Azure Postgres `fno` schema (one transaction, completeness check, pointer moved last) |
| Run | `market_run.py`, `cli.py` | `python -m fno market daily | publish | compare | contract-check | look-up`; any failure alerts #fno-desk and publishes nothing |
| Wiring | `fno/composition.py` (`build_market_run`, `build_session_rows_builder`, `build_read_model_publisher`, ...), `fno/storage/wiring.py` | Concrete classes only in the composition roots |

## Criteria

**1. For 12 Oct 2026 every built block equals the W11 example field by field, except fields W11 marks as derived
elsewhere.** PARTLY MET, every remaining difference traced to its cause (strong evidence).

`python -m fno market compare --day 2026-10-12` against the pinned examples (dashboard `e299534`, split-, bonus- and
demerger-adjusted, on NSE's sessions):
```
getScreenerSummaryIndia_india: 0 difference(s)
getScreenerStocksIndia_india: 0 difference(s)
getScreenerStocksIndia_india_high: 0 difference(s)
getScreenerStocksIndia_india_gainers: 0 difference(s)
getFnoScreenerSummary_india: 0 difference(s)
getFnoScreenerRows_india: 0 difference(s)
getFnoScreenerRows_india_index_options: 0 difference(s)
getOverviewIndicesIndia_india: 0 difference(s)
getIndiaSectors_india: 826 difference(s)
```
- The sectors block: its industries are equal; all 826 differences are in `.indices`. Compared by name, only two
  indices differ: **Nifty Capital Goods and Nifty Telecommunications**. Cause: NSE rewrote `ind_close_all_12102026.csv`
  at 17:50 UTC (23:20 IST) on 12 Oct, adding those two rows (their open/high/low are "-"). Our archived copy (A1's
  download, SHA-256 `fc847998…`, 15,668 bytes) predates it and has neither. NSE's current file is `e8e8f6ec…`, and the
  examples used that later version. Since the two indices launched (mid-June 2026), 12 Oct is the only archived day
  without them. Raw files never change, so I did not overwrite. The orchestrator's decision: an append-only revisions
  area (story A11, built in parallel). Builder fix: an index row carries the date of its own last figure (`as_of`), so
  a missing index never shows an older close as the day's (`index_rows.py:51`; test
  `test_index_rows_put_broad_and_vix_first_and_date_an_index_by_its_own_last_figure`). These two rows are expected to
  match once the build reads A11's latest revision.
- The stock table beyond the compared pages: 2,920 of 2,924 rows equal the dashboard's own `data.json`. The other 4
  differ by 0.01 to 0.02 (CUB y1 40.29 vs 40.30, TEMBO y1 −1.05 vs −1.07, SKFINDIA h 2,330.13 vs 2,330.12, ZFCVINDIA l
  2,050.33 vs 2,050.34). The dashboard rounds each factor to 6 decimals (a 5:1 bonus becomes 0.166667); mine uses
  exact factors and rounds the price once. These rows sit on no example page.
- Proof that nothing else is hidden: with the dashboard's values substituted for those 4 rows (and earlier for the 19
  then differing), every example equals and only the two indices remain.

Fields "derived elsewhere": since judge 40 none apply. The "ours" universe and tag are computed here.

**2. Every payload validates against the pinned W11 schema; a planted extra or missing field fails the run.** MET
(strong evidence).
- Code: `PublicationBuilder.check` (`publication.py:55`) validates the stored payload against W11's `x-stored` schema
  (`ScreenerStocksTableIndia`, `FnoScreenerTable`) and the served response (envelope plus default page) against the
  response schema, for all six blocks. A real build of 12 Oct publishes all six
  (`2026-10-12: published 6 blocks as nse-2026-10-12-c1b7392f5bb3 to local folder`).
- Tests (`tests/market_read_models/test_market_contract_and_run.py`): an extra field in the F&O summary; a missing
  `close` in an index; a missing `dl` on row 41 of the stock table (beyond the first page); a missing "ours" universe.
  Each raises `ContractBroken`, nothing is published, and the run alerts. The pin is intact
  (`test_the_pinned_copy_matches_its_pin_and_names_the_contract_version`). Drift is detected
  (`test_the_pinned_copy_is_compared_with_the_dashboards_published_files`).
- "A test fails if the pinned copy differs from the dashboard's published version": the test checks the copy against
  its pin (no network in tests). `python -m fno market contract-check` compares with the dashboard's `main`, and the
  daily routine should run it. Today: `pinned W11 contract 2.4.0 (commit e29953456fb7): same as the dashboard's`.
  The contract changed six times during this build; each time I re-pinned and re-validated.

**3. Publishing is atomic per session.** MET (strong evidence).
- Local: `local_publisher.py:24`. The publication is written to a temporary folder, renamed into place, then the
  pointer moves. Test `test_a_local_failure_part_way_leaves_the_previous_session_current_and_unchanged`: a failing
  adapter breaks on the third block; the previous session stays current and unchanged, no partial folder is left, and
  a retry works.
- Azure Postgres: `postgres_publisher.py:49`, one transaction. Tests run against a real throwaway PostgreSQL 16 started
  by the test (`tests/market_read_models/postgres_server.py`):
  - `test_a_postgres_failure_in_any_block_leaves_the_previous_session_current_and_unchanged`: the third insert breaks
    a check constraint; the first two inserts roll back and the previous publication stays current.
  - `test_postgres_publishing_the_same_session_twice_adds_no_rows`.
  - A different payload under an existing publication ID is refused.
- Run level: `market_run.py`. A missing file, a schema break or a refused publish stops before anything is visible and
  alerts #fno-desk (`test_a_missing_file_or_a_schema_break_alerts_and_leaves_the_previous_publication`).

**4. A real publish of 12 Oct to Azure succeeds with the publisher role, and a dashboard-role read returns the same
payloads.** BLOCKED ON THE OWNER (not done here).
- This environment has no `FNO_DB_URL` (checked by name; no Azure credential of any kind is set).
- Owner steps:
  1. On the Azure Postgres server (X1), run `db/fno/migrations/001_read_models.sql` once with the `fno` migration role.
     It creates `fno.pages_history` and `fno.current_publication`.
  2. Grant the fno runtime publisher role `INSERT, SELECT` on `fno.pages_history` and `INSERT, UPDATE, SELECT` on
     `fno.current_publication`, and the dashboard role `SELECT` on both (X1's role matrix).
  3. Put the publisher role's connection string (with `sslmode=verify-full`) in this cloud environment's settings as
     **`FNO_DB_URL`** (the name P3 defines, in `fno/constants.py`). Never in a file.
  4. Run `python -m fno market publish --day 2026-10-12`. Then, with the dashboard role, select the rows of
     `fno.current_publication` joined to `fno.pages_history`, and compare `payload_sha256` and `payload` with the run's
     records.
- Doubt (reasoning only): P3 owns these tables. My migration follows P3's stated design (unique product, page key and
  publication; one pointer per product), and P3 may extend it with run status.

**5. New raw datasets complete in Drive with fingerprints for 2025-10-13 to 2026-10-12, coverage 0 missing, 0
damaged.** MET (strong evidence).
```
nse/equities/cm-bhavcopy             2025-10-01 2026-10-12      254     254       0       0      0
nse/equities/security-delivery       2025-10-01 2026-10-12      254     254       0       0      0
result: complete
```
(`python -m fno data-coverage --to 2026-10-12`. All datasets are complete, 0 without a fingerprint. The window starts
on 1 Oct 2025 because the examples' window is a year and a week: RSI and 1Y need it.) The reference lists and
corporate-action lists are snapshot datasets with manifest rows: `research/data/manifests/equity-list.csv`,
`nifty500-list.csv`, `corporate-actions.csv`, `corporate-actions-by-symbol.csv` (17 symbols for 12 Oct).

**6. Code size, lint, imports, tests pass; no US block is built here.** MET.
- `python -m pytest -q`: 1,213 passed. `ruff check fno tests tools`: all checks passed. `python tools/check_imports.py`:
  clean. `python tools/check_records.py`: clean.
- Largest P6 file: `session_rows.py`, 167 lines. `fno/storage/wiring.py` reached 348 after A11's and my additions; the
  content checks moved to `content_checks.py`, and it is now 321.
- Only the six India blocks are built. No US or stock-tool block.

## Judge 42: corporate actions (named acceptance: KOTAKBANK)

- `tests/market_read_models/test_corporate_actions.py::test_kotakbank_after_its_5_for_1_split_from_nses_corporate_actions_list`
  uses NSE's own subject text ("Face Value Split (Sub-Division) - From Rs 5/- Per Share To Re 1/- Per Share", ex-date
  14 Jan 2026) and the closes judge 42 cites (2,152.10 a year back, 2,132.60 before, 421.00 on the ex-date, 443.40 on
  12 Oct). Adjusted 1Y is +3.02%; unadjusted it would be −79.4%.
- Real build of 12 Oct, KOTAKBANK as published: `{'p': 443.4, 'y1': 4.24, 'h': 453.2, 'l': 345.5, 'u': ['n500', 'fno']}`.
  The 1Y is +4.24%, not judge 42's +3%, because the contract's 1Y is "250 sessions back". On NSE's calendar that is a
  slightly earlier session, raw close 2,126.85, not 13 Oct 2025. The high 453.20 is the raw 2,266 divided by 5.
- No "high > 3× price" heuristic. A one-session jump only chooses which symbols' own NSE lists to look up (ETFs NSE's
  range list leaves out); every adjustment comes from NSE's stated ratio or discovered price.

## Interim and open items (stated plainly)

- **"ours" source (interim):** `research/data/followed-companies/india/2026-10-12.json`, the stock tool's 20 India
  companies from its 12 Oct records. They were taken from the dashboard's copy (`design/mockups/33-screener/source/tracked.json`
  at `348fe34`), which `fetch_tracked.py` made from the stock tool's published records. I did not read the stock
  tool's repository directly. When the stock tool publishes `FollowedCompaniesIndia` (K5-proposed), a second adapter
  behind `FollowedCompaniesSource` reads it. Until then a new list must be added by hand when the stock tool's list
  changes; the run stops if a close has none.
- **Daily routine:** `python -m fno market daily` is built (archive, look-up, validate, publish, alerts). I have not
  scheduled it. Recommended: 07:30 IST the next morning, after NSE's late-evening rewrites. Scheduling is the
  orchestrator's or owner's call.
- **Rights issues** are not adjusted (NSE's list gives no factor; the effect is small), and neither are dividends
  (price returns, as the contract says).
- **Demerger without an ex-date trade:** I keep only later sessions (null). The dashboard leaves the prices
  unadjusted and marks them. No such case occurs on 12 Oct.
- **The example comparison copies the route's views** (first page, near-high, gainers, index options) exactly as
  W11's example builder makes them. The dashboard's real route is not in this repository.
