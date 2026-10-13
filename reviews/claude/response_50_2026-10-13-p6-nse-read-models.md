# Response 50: P6 NSE market read models for the Screener and Markets (builder's claims)

Status: **built; awaiting judge** (criterion 4 blocked: this cloud container cannot open a connection to Postgres port 5432; see Addendum 2). Story:
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
- Demergers (judge 42's INDIAGLYCO and DCMSRIND; orchestrator rule: NSE's ex-date special pre-open price ÷ previous
  close, never guessed). The named test is `test_judge_42s_demergers_on_nses_ex_date_open`, and it uses NSE's own bars:
  - INDIAGLYCO, ex-date 2 Sep 2026: previous close 1,111.70, ex-date open 225.00. 1Y is +75.32%; unadjusted it would be −64.52%.
  - DCMSRIND, ex-date 26 Dec 2025: previous close 172.16, ex-date open 51.00. 1Y is −20.05%; unadjusted it would be −76.31%.
  Both figures are the ones the real build of 12 Oct published. Neither stock is on an example page; their rows are
  among the 2,920 that equal the dashboard's data.json.
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

---

## Addendum 1 (13 Oct 2026): judge 49 fixes

Judge 49 gave **FAIL** with 1 should-fix and minors; criterion 4 is blocked by the owner. Every finding is fixed below. One of them (TMPV) turned out to be a general problem: **renamed stocks**. Its fix makes 54 of our stock rows *correctly* differ from the dashboard's examples. The proof is below, and design needs to apply the same fix.

### Should-fix: read NSE's latest version through A11 (accepted; strong evidence)

- `fno/composition.py` `build_session_rows_builder` now reads through `build_versioned_reader()`, which is A11's `VersionedRawStore` with `as_of=None` (NSE's latest version). This is a one-line change in the composition root.
- **Root-cause bug found on the way:** A11's revision index listed only the dated datasets. Reading a reference-list path (for example `corporate-actions-equities.json`) through the versioned reader raised "no dataset with a manifest". The fix is in the composition root (`build_revision_index` now covers `RAW_SOURCES`, every dataset with a manifest). A dataset with no revision file reads as "no revisions", so A11's code is unchanged.
- `market daily` now sweeps the session's four dated files for newer NSE versions before it publishes (`_archive_revisions`).
- The rule is written into P6's story: publishing reads the latest version; research reads point in time.
- Test: `test_latest_versions_and_renames.py::test_the_sectors_come_from_nses_latest_version_of_the_index_file`. It uses A11's real fixtures of NSE's first and rewritten 12 Oct files: Nifty Capital Goods and Nifty Telecommunications come only from the latest version. A second test, `test_publishing_is_wired_to_the_latest_reader`, checks the wiring.
- Real rebuild: `getIndiaSectors_india` has **0 differences in `.indices`**. The 826 differences are gone. The 5 that remain are in `.industries` and are explained under "renamed stocks" below.

### Minor 1: pin moved forward, and every India example compared by its own query (accepted)

- **New pin:** dashboard `b2c92ee` (main, 13 Oct; contract version still 2.4.0). Only `api/examples/blocks-33-34.json` changed; every schema is byte-identical.
- `market compare` now covers **all 21 India examples of the blocks we publish**: the 8 earlier ones plus the 13 new ones.
- A paged example is served from our stored table by **its own `x-query`**, through `screener_route.py`. That file is a port of the dashboard's reference `tools/api/screener_route.py`, covering filters, screens, sorts, missing-last ordering, ties and pages. My hand-made views are removed.
- Tests: `test_screener_route.py` (6).

Real rebuild of 12 Oct against the new pin (`python -m fno market compare --day 2026-10-12`):
```
getScreenerSummaryIndia_india: 7    getScreenerStocksIndia_india: 0     ..._high: 0       ..._gainers: 0
..._ours: 0      ..._year: 0        ..._volume: 0       ..._oversold: 1     ..._picks: 0      ..._results: 0
..._filters: 1   ..._losers: 0      ..._active: 0
getFnoScreenerSummary_india: 0      getFnoScreenerRows_india: 0  ..._index_options: 0  ..._short: 0
..._ivhigh: 0    ..._index: 0       getOverviewIndicesIndia_india: 0    getIndiaSectors_india: 5
```
**Proof that the 14 remaining differences come only from renamed stocks** (strong evidence):
- I put the dashboard's own row values back for the stocks renamed since 2025 and rebuilt the blocks.
- **Every example then equals ours, except one row:** ZFCVINDIA's low is 2,050.33 against the example's 2,050.34. That is the known factor rounding from before.
- The summary counts (`near_low`, `fall`, `oversold`, `trend`, `up_1m`), the industries' averages, `oversold` row 9 (ZFCVINDIA) and `filters` row 18 (HALEOSLABS, renamed from SMSLIFE) all move only because of the renamed rows.

### Minor 3 (TMPV) became a general fix: renamed stocks keep their history (accepted, widened)

- **The general problem:** NSE lists a corporate action under the stock's *current* symbol, but the sessions before a rename sit under the *old* symbol. Without joining the two:
  - a renamed stock loses that part of its year (no 1Y; a 52-week range over part of the year);
  - a demerger before the rename is never adjusted.
- **The fix:** NSE's `symbolchange.csv` is a new daily snapshot dataset (`nse/equities/symbol-change`, `SymbolChangeSource`, with a content check). Today's copy is archived in Drive with its SHA-256 manifest row. `symbol_changes.joined()` puts the old symbol's sessions before the new symbol's, in effective-date order (so chains join up), and moves actions filed under the old symbol to the new one.
- **TMPV:**
  - It was TATAMOTORS until 24 Oct 2025.
  - The demerger's ex-date was 14 Oct 2025: previous close 660.75, open 400.00, so the factor is 1.6519 (judge 42's numbers).
  - As published: `y1` **−32.69%** and `h` **424.97**, over a full year. The earlier `y1` was null and the high (419.00) covered 239 sessions.
- **HEGAM: judge 42 called it "a new listing (14 sessions)". That is not right.**
  - NSE's symbol-change file says HEG became HEGAM on 22 Sep 2026.
  - NSE's corporate-actions list files HEG's **demerger (ex-date 7 Sep 2026)** under HEGAM. HEG closed at 728.25 on 4 Sep and opened at 260.00 on 7 Sep, so the factor is 2.8010.
  - As published: `y1` **+26.84%**, `h` 273.00, `l` 168.09. The examples show `y1` null and a 14-session range (`h` 256.47, `l` 229.01).
- **The other 52 renamed stocks** are mostly ETF renames (for example UTI's "…ETF" symbols → "…BETA", Axis's ETFs → "…AXIS") and company renames such as LTIM → LTM, GUJGASLTD → GUJENERGY, AKZOINDIA → JSWDULUX and INFIBEAM → CCAVENUE. They now have their full year.
- **Guard:** every joined series still passes the jump check. Any one-session move outside 0.55–1.8 with no action in NSE's list stops the build until the symbol's own list is looked up. The 12 Oct build passed, so no join creates an unexplained price break.
- **Remaining risk (reasoning only):** a rename that comes with an unlisted price change *inside* the band would not be caught. I found none.
- **Stock rows equal to the dashboard's `data.json`:** now 2,866 of 2,924.
  - 54 rows differ because they are renamed stocks, where the dashboard's figures are null or cover part of the year.
  - 4 rows are the earlier sub-cent rounding (CUB, ZFCVINDIA, SKFINDIA, TEMBO).
- **For design (orchestrator to route):** the examples should follow `symbolchange.csv` the same way. Until they do, criterion 1 differs exactly in these rows, and each one is traced to the source.
- Tests:
  - `test_tmpv_keeps_its_tatamotors_sessions_and_its_demerger_uses_the_ex_date_open`
  - `test_a_rename_applies_old_symbol_actions_and_chains_in_date_order`
  - `test_nses_symbol_change_file_is_read_with_its_padded_header`

### Minor 2: no 52-week figure over a cut window (accepted, with one distinction)

- When a corporate action without a price cuts history inside the window, `stock_row(..., cut=True)` makes these null instead of computing them over fewer sessions:
  - `h` and `l` when fewer than 250 sessions remain;
  - `va` when 20 or fewer remain.
- The periods were already null.
- **A later listing is not a cut.** Its high since listing is its true 52-week high, because no earlier session exists. That is why a short series alone does not null `h` or `l`.
- On 12 Oct no row is cut any more: TMPV was the only case, and it is now joined.
- Test: `test_a_cut_window_has_no_52_week_high_low_or_volume_average_but_a_later_listing_keeps_them`.

### Minor 4: pre-open wording (accepted; judge 42's sources)

- The docstring (`corporate_actions.py`) and the README now say what the ex-date open is. For a stock with derivatives it is NSE's **special pre-open session** price, which NSE uses for index adjustment. For any other stock it is the **normal pre-open auction** price: exchange-discovered, but noisier.
- **Non-F&O demergers are tested:** INDIAGLYCO and DCMSRIND have no derivatives, and `test_judge_42s_demergers_on_nses_ex_date_open` uses NSE's real prices for both. Its docstring now says so.

### Checks
```
python -m pytest -q                     1316 passed
ruff check fno tests tools              All checks passed!   (ruff format --check: 284 files already formatted)
python tools/check_imports.py           clean: 292 files
python tools/check_records.py           record scan: clean (629 files)
largest P6 file: session_rows.py 174 lines
```
Criterion 4 is still blocked on `FNO_DB_URL`; the owner steps are above, unchanged. `market daily` is not scheduled, as the orchestrator instructed.

---

## Addendum 2 (13 Oct 2026): criterion 4 attempt, blocked by the container's network

The owner ran `001_read_models.sql` as `fno_owner` and set `FNO_DB_URL` (role `fno_writer`) in this environment.

- `FNO_DB_URL` is set. Parsed by name only: an Azure Postgres host (`*.postgres.database.azure.com`), port 5432,
  `sslmode=verify-full`, user `fno_writer`. Correct.
- **The connection fails: `psycopg.errors.ConnectionTimeout`.** This is not TLS or auth. Those errors can only happen
  after a TCP connection opens, and here none does.
  - DNS resolves (1 address). The TCP connect to port 5432 times out after 10 s.
- **Root cause (strong evidence): this cloud container cannot open a connection on any port except 443.**
  - Direct TCP tests: `portquiz.net:5432` timed out, `github.com:22` timed out, `portquiz.net:443` and `1.1.1.1:443`
    opened.
  - The container's proxy README lists "raw-TCP databases" as not supported through the proxy.
  - Azure Postgres listens on 5432 (6432 for PgBouncer), never on 443. So no setting in this repository can fix it.
- Not known from here: whether the Azure server's firewall would also refuse this container. That is untested, because
  the connection is blocked before it reaches Azure.
- **Not done, as instructed:**
  - privileges (`has_table_privilege`) and `current_user` were not read;
  - `python -m fno market publish --day 2026-10-12` was not run against Azure. It would fail at connect and post a
    false failure alert to #fno-desk.
  - Nothing was written to Azure.
- **Ways forward (owner's choice):**
  1. Change the environment's **Network access** to a level that allows direct outbound TCP to the Azure host on 5432
     (cloud environment menu → Edit; docs: https://code.claude.com/docs/en/cloud-environments#network-access). Then
     allow this environment's outbound IP in the Azure server's firewall. *Doubt (reasoning only):* the docs describe
     allowed **domains**, which go through the HTTPS proxy. Adding the host to that list may still not carry raw TCP on
     5432. If it does not, this route is closed.
  2. **Run criterion 4 from the owner's Mac** (or a GitHub Actions runner, which can reach port 5432; the Azure firewall
     must allow it):
     - `FNO_DB_URL` is set in the shell only.
     - Run `python -m fno market publish --day 2026-10-12`, then run it again.
     - Count the `fno.pages_history` rows before and after the second run.
     - Read the pages back with the dashboard role (below).
  3. A small HTTPS endpoint in front of the database, for example an Azure Function. That is a design change and
     needs its own story; I do not recommend it for one acceptance check.
- Dashboard-role read-back (owner's Mac; `psql` asks for the password at a hidden prompt):
  `psql "host=<server>.postgres.database.azure.com port=5432 dbname=<db> user=dashboard_app sslmode=verify-full sslrootcert=system" -c "select h.page_key, h.payload_sha256 from fno.current_publication c join fno.pages_history h using (product, publication_id) order by h.page_key;"`
  Expected: 6 rows, one per block. `sslrootcert=system` needs psql 16 or later; on older psql, point `sslrootcert` at
  the server's CA file.

## Addendum 3 (13 Oct 2026): criterion 4 moves to GitHub Actions (orchestrator, O6)

Built: `.github/workflows/market-publish.yml`. It runs as a plain scheduled job, not an AI session, because Claude's cloud containers cannot open port 5432 (Addendum 2).

- **When it runs:**
  - daily at 07:10 IST (`cron 40 1 * * *` UTC). That is 20 minutes before the 07:30 target, because Actions often starts late, and after NSE's late-evening rewrites;
  - or on `workflow_dispatch` with a `day` input. Empty means the last session before today.
- **The session calendar decides:** `market daily` takes the previous session from NSE's session calendar, never from weekdays. A closed day publishes nothing. On a Sunday it re-checks Friday's session and adds nothing.
- **Steps:** archive the session's NSE files and NSE's later versions to Drive (with manifest and revision rows committed), build, validate against W11, publish in one transaction as `fno_writer`, then **read back** as `fno_writer`.
- **The read-back:**
  - `ReadModelPublisher.stored(publication_id)`, implemented by both adapters, returns each page's `payload_sha256` as the store holds it.
  - The run compares them with the records it built, then prints only `published 6 blocks as nse-<day>-<hash> (N rows added)`, `read back 6 pages … every payload SHA-256 equals the built records`, and one `page_key sha256` line per page.
  - A mismatch fails the run and alerts #fno-desk.
- **Secrets:**
  - `FNO_DB_URL` comes from the repository secret of that name. It is passed only as an environment variable and never pasted into a shell line or printed. A test checks that no `run:` line names it.
  - Drive: the owner's OAuth secrets the other jobs already use. The versioned reader now falls back to the owner's sign-in when no service account is set, so no new Drive secret is needed.
  - Slack: `FNO_SLACK_BOT_TOKEN`.
- **One line to #fno-desk on failure:** the run's own failures (missing file, schema, publish, read-back) already post their line. The workflow's failure step posts one only when the log has no such line, for a crash or an install failure, so a failure never posts twice.
- **A second run adds no rows (root-cause fix, strong evidence):**
  - The publication ID used to be `nse-<day>-<commit>`. But the job commits manifest rows, so every later run would check out a new commit, get a new ID, and add 6 rows of identical content.
  - It is now named by its content: `nse-<day>-<12 hex of the SHA-256 over the pages' hashes>`. The same pages always get the same ID; NSE's later version of a file gives a new one.
  - The pointer upsert no longer touches `published_at` when the publication is already current.
  - `source_commit` stays in each row as metadata.
- **O6 pipeline records** (`fno/pipeline`): not used, because they don't fit. They record "fired" and "processed" for AI routines started per batch, and this job fires no routine. Its record is the publication itself: `fno.pages_history` keyed by the content ID, plus the read-back lines in the Actions log.
- **Tests:**
  - `test_market_publish_read_back.py` (4): read-back lines are counts and hashes only, a second run adds 0 rows, a differing read-back alerts, and the workflow's schedule, input and secret handling.
  - `test_market_publishers.py` (real throwaway PostgreSQL 16): `publish` returns 3 then 0, a later re-run leaves `published_at` unchanged, and `stored` equals the built hashes.
  - `test_market_contract_and_run.py`: the ID ignores the commit and build time and changes when the content changes.

**The owner's one step:** in GitHub, exepex/trading → Settings → Secrets and variables → Actions → New repository secret. Name it `FNO_DB_URL`; the value is the `fno_writer` connection string already set here (with `sslmode=verify-full`). Then the orchestrator dispatches `market-publish` with `day = 2026-10-12`, and the owner runs the `dashboard_app` read-back above from their Mac.

**Likely next blocker (reasoning only, untested):** the Azure server's firewall. GitHub-hosted runners connect from changing Azure addresses.
- If the first run fails with `ConnectionTimeout` at publish, the firewall refused the runner.
- The usual Azure setting is "Allow public access from any Azure service within Azure to this server". It admits any Azure address, including GitHub's runners, so access then rests on the role's password and TLS.
- The tighter alternative is a self-hosted runner with a fixed address.
- That choice is the owner's, as a platform (X1) decision.

## Addendum 4 (13 Oct 2026): criterion 4 MET; the publish failure diagnosed and fixed

**Result:** GitHub Actions run 38438666957 (`market-publish`, day 2026-10-12) published and read back as `fno_writer`.
```
2026-10-12: published 6 blocks as nse-2026-10-12-40630e1cd4ec to Azure Postgres (fno schema) (6 rows added)
read back 6 pages of nse-2026-10-12-40630e1cd4ec: every payload SHA-256 equals the built records
    fno_screener_rows    2b472f047c22c5fc9a2b02e783782af77ddd32d16bba135ba1f7bea8ceb8d6d0
    fno_screener_summary 4c1121a66d8695cf86186ae6389d033dc1b3cd35d744a74e3ef114adb9743c53
    overview_indices     4ed3007055b26438b1887f0799fa4c064b056631a7c575fa2e9015d416d571ec
    overview_sectors     2bf88cacb2b01f53f1d7fa3f79a29bdfb2c0d354352fdb78b78c7a25999988fc
    screener_stocks      cfb0584223818102f3b0d80a20997106b909da06e64912bbd21201b401518edb
    screener_summary     e4d8d13b5e878af1541a4132a6fd7f59b9f8617df30eed2995a565c776dd2ad0
```
The owner's `dashboard_app` read-back (Addendum 2's command) should show these 6 page keys with these hashes.

### Why run 38436281593 failed: TLS (strong evidence)

- **The cause:** `psycopg[binary]` (3.3.6, libpq 18) bundles its own OpenSSL. That OpenSSL's default root store is a path from its build machine:
  ```
  OPENSSLDIR "/host/tmp/libpq.build"
  X509_get_default_cert_file -> /host/tmp/libpq.build/cert.pem   exists: False
  X509_get_default_cert_dir  -> /host/tmp/libpq.build/certs      exists: False
  ```
  `sslrootcert=system` asks libpq for those default roots, so it trusts **nothing** on any machine.
- **Reproduced:** on a throwaway TLS PostgreSQL with a test CA, `sslrootcert=system` gives "SSL error: certificate verify failed". It succeeds once `SSL_CERT_FILE` names the CA, which shows "system" means the bundled OpenSSL's defaults. The failed run's bare `OperationalError` (not `ConnectionTimeout`) fits a TLS failure.
- **Firewall caveat (reasoning only):** the owner says the Azure firewall rule may have been added just before. So run 1 might also have met the firewall, but it would have failed on TLS anyway.

### The fix (no weaker sslmode)

- **Pinned roots:** `db/fno/azure-postgres-roots.pem` holds the three Azure roots, with their SHA-256 written in the file:
  - DigiCert Global Root G2;
  - Microsoft RSA Root CA 2017;
  - DigiCert Global Root CA, for older servers. Mozilla dropped it, but it matches DigiCert's own download.

  The first two also match Mozilla's bundle (certifi).
- **The connection:** `VerifiedConnection` (`db_connection.py`, wired in `fno/composition.py`) always passes `sslmode=verify-full`, `sslrootcert=<that bundle>` and a 15 s `connect_timeout`. These override whatever the URL says.
- **Tested on real TLS:** with `sslrootcert=system` or even `sslmode=disable` in the URL, the connection is still TLS and verified. A server the Azure roots never signed is refused and named "TLS or certificate".

### No more blind failures

- **Failure classes:** `db_errors.py` names every database failure: network (TCP timeout or refused), firewall (server refused the address), TLS or certificate, authentication, permission denied, or other. It maps them from psycopg's type, the SQLSTATE (28000/28P01 authentication, 42501 privilege) and libpq's message.
- **What gets printed:** only the class, the exception type and the SQLSTATE, never the message (it names the host and user). `PublishFailed`, the read-back and the alert all use it. There are 11 parametrized mapping tests.
- **`market db-check`, the cheap diagnostic:** it connects as the publisher would, runs `select current_user = <the URL's user>` plus `has_table_privilege` for the five rights, and prints yes/no only. The workflow runs it first in every run, and the `check_only` input stops there.
- **Diagnostic run 38438592197:**
  ```
  database check: connected with TLS (verify-full, pinned Azure roots)
      current_user is the URL's user: yes
      pages_history INSERT: yes          pages_history SELECT: yes
      current_publication INSERT: yes    current_publication UPDATE: yes    current_publication SELECT: yes
  ```
- **The firewall** admits GitHub's runners now (the owner's rule). Nothing was changed on Azure from here. The trade-off of that rule is in Addendum 3: access then rests on the role's password and TLS, while a self-hosted runner with a fixed address would be tighter.
- **The failure step** now adds the `database check FAILED: <class>` line to its one #fno-desk alert.

Checks: 1,488 tests pass (more since), ruff, imports and the record scan are clean, and `fno/composition.py` is at 348 of its 350 lines. The next addition there needs a split.

**Second run of the same day, on the real database:** run 38439360415 started from a newer commit (e38eabd, other stories' work in between). It printed `published 6 blocks as nse-2026-10-12-40630e1cd4ec … (0 rows added)` and read back the same 6 hashes. So a second run adds no rows, and a code commit does not change the ID, which is named by content.
