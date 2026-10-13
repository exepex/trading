# Response 66: stories P7, P8 and P9 (run status, FII/DII flows, option chain), claims

Orchestrator request of 13 Oct 2026: three publishing follow-ups before the owner's pause, each story written first in
`docs/stories/P-publishing.md`, then built. The same rules as P6 apply: no AI at runtime, no secret printed,
contract-validated and idempotent. One addendum per story.

## Addendum P7: run status (built; awaiting judge)

**What:** every publish run now leaves one `fno.run_status` row per product and run. It is `running` at the start, then
`published`, `failed` with a reason code, or `skipped` on a closed day. This lets the dashboard's "stale" state say why
a run failed (judge 57's dependency gap).

- **Migration** `db/fno/migrations/002_run_status.sql`:
  - **Columns:** `product`, `run_id`, `session`, `started_at`, `finished_at`, `result`, `reason_code`, `reason`, `publication_id`; primary key `(product, run_id)`.
  - **Checks:** `result` and `reason_code` take only the listed values; a `running` row has no `finished_at` and a finished row has one; `failed` and `skipped` rows must carry a reason code.
  - **Index:** on `(product, started_at desc)`.
  - **Grants:** `select, insert, update` to `fno_writer`, with no delete (the history stays), and `select` to `dashboard_app`.
- **Code:**
  - `run_status.py`: the `RunStatusRecorder` interface, with a `PostgresRunStatus` adapter (same verified TLS connection as the publisher) and a `LocalRunStatus` adapter (JSON lines, used by local runs and tests).
  - `MarketRun` writes the row at the start and at the end of every run.
  - The archive step moved into the run (`run(day, prepare=…)`), so an archive failure also gets its row.
  - **A crash** is recorded as `crashed`, then re-raised.
  - **A status write that fails** adds one "run status NOT recorded (<class>)" line, and the run's own result and exit code stand.
  - **Run ID:** `gh-<GITHUB_RUN_ID>-<attempt>` in Actions (a re-run counts as its own run), else `local-<UTC time>`.
- **Reason codes:**

  | Code | When |
  |---|---|
  | `not_a_session` | the day is not an NSE session (`skipped`) |
  | `archive_incomplete` | the archive step failed, or an archived file is missing |
  | `contract_changed` | the pinned W11 copy differs from its pin |
  | `schema_invalid` | a payload fails the W11 schema |
  | `publish_refused` | the store refused the publication for a reason that is not a database error |
  | `read_back_mismatch` | the read-back hashes differ from the built ones |
  | `database_network` / `database_firewall` / `database_tls` / `database_authentication` / `database_privilege` / `database_other` | from the failure class (`db_errors.py`) |
  | `figures_not_computed` | a figure P10 does not compute yet (an open trade's risk used, an approved strategy's picks) |
| `crashed` | an unexpected error |

- **Wiring:** the market read models now have their own composition root, `fno/market_read_models/wiring.py`. `fno/composition.py` had reached 348 of its 350 lines; the code moved unchanged, and CLAUDE.md's list of composition roots now names it.

**Tests** (`tests/market_read_models/test_run_status.py`, 9 tests; plus every earlier run test, now with a status):
- each reason code from a real failing run, with `reason` equal to the alerted line;
- a closed day gives `skipped`/`not_a_session`, and a second run adds its own row;
- a crash is recorded, then raised;
- an unreachable status store never changes the result;
- the run-ID rule;
- **on a throwaway PostgreSQL 16 with the migration and X1's roles:**
  - rows are written as `fno_writer`, and a finished row never changes;
  - `fno_writer` cannot delete (`InsufficientPrivilege`);
  - `dashboard_app` can read but not insert;
  - an unknown code, or a failure without a code, is refused by the table's checks.

Full suite: 1,540 tests pass; ruff, imports and the record scan are clean.

**The owner's one step (as `fno_owner`, from the Mac, as for 001):**
```
psql "host=<server>.postgres.database.azure.com port=5432 dbname=<db> user=fno_owner sslmode=verify-full sslrootcert=system" -f db/fno/migrations/002_run_status.sql
```
- **Expected:** `CREATE TABLE`, `CREATE INDEX`, `GRANT`, `GRANT`.
- The Mac's `psql` uses its own OpenSSL, so `sslrootcert=system` works there (psql 16 or later). The psycopg-binary problem (response 50, addendum 4) affects only our Python publisher.
- **Until the migration runs:** each publish still publishes and reads back. It only adds a "run status NOT recorded (other (UndefinedTable, SQLSTATE 42P01))" line.

**For the dashboard's read side (a small W2 follow-up):** read the latest row of `fno.run_status` for `product = 'fno'`
(`order by started_at desc limit 1`). The fields:

| Field | Type | Meaning |
|---|---|---|
| `product` | text | `fno` |
| `run_id` | text | `gh-<run>-<attempt>` (links to the Actions run) or `local-<time>` |
| `session` | date | the NSE session the run published, or tried to |
| `started_at` | timestamptz | the run's start |
| `finished_at` | timestamptz or null | null while `running` |
| `result` | text | `running`, `published`, `failed` or `skipped` |
| `reason_code` | text or null | one of the codes above; set for `failed` and `skipped` |
| `reason` | text or null | the run's own one-line reason, as posted to #fno-desk; no credential, host or user (db_errors) |
| `publication_id` | text or null | set for `published`; equals `fno.current_publication.publication_id` after success |

Suggested dashboard rule (reasoning only; the dashboard's call):
- "stale" plus a `failed` row for the due session: show `reason_code` in words, with `reason` underneath.
- A `running` row older than the job's 60-minute limit: "the run did not report".

## Addendum P8: FII/DII flows (stopped before building: the contract assigns the block to the stock tool)

**What I checked:** W11's contract does have this block: `Flows`, endpoint `getFlows_india`, Markets 34's "What did big investors do?". But its catalog entry in `api/schemas/blocks-overview.yaml` reads:
```
x-catalog: {publisher: stock, source: "the stock tool's flows (NSE FII/DII, provisional) and fpi (NSDL) records",
            freshness: next morning, story: K5-proposed, status: published}
```
So the stock tool is the contract's publisher, and its status is already `published`.

**Why I stopped:**
- If this repository published the same block, it would have two publishers and two sources of truth. That breaks the contract's one-publisher-per-block rule.
- That is the same reason as the "no contract, don't invent one" rule you set.
- **Built:** nothing for P8 except the story text (status: blocked).

**The decision needed (orchestrator or owner); options, reasoning only:**
1. **W11 moves `Flows` to publisher `fno`** (a dashboard contract change). Then P8 builds what you described: the daily GitHub Actions download into Drive (A9 and A11 rules, revisions kept) and the published block.
2. **The block stays with the stock tool**, and this repository only archives NSE's FII/DII file for its own research (F&O positioning features). That needs no contract and is small.
3. **Nothing.**

My lean is option 2 if the desk wants FII/DII cash flows as a research input; otherwise option 3. I see no gain in moving a block the stock tool already publishes. This is reasoning only.

## Addendum P9: NIFTY option chain read models for screen 32 (built; awaiting judge)

**What:** the six India-only chain blocks of W13's frozen contract (`blocks-chain.yaml`, `blocks-chain-history.yaml`, W11 2.3), built from the archived NSE F&O and index files. They publish in the **same publication** as P6's blocks: one transaction, one pointer, one run status (P7). So screens 32, 33 and 34 always show the same session.

**Pages** (the route reads them by these keys; for the dashboard's W13 route follow-up):

| Page key | Endpoint | 12 Oct 2026 |
|---|---|---|
| `chain_underlying` | `/markets/india/fno/chain/underlying` | 1 |
| `chain_expiries` | `/markets/india/fno/chain/expiries` | 1 (7 expiries) |
| `chain_rows:<expiry>:<near\|band\|all>` | `/markets/india/fno/chain/rows?expiry=&strikes=` | 21 (7 × 3) |
| `chain_history` | `/markets/india/fno/chain/history` | 1 |
| `contract_history:<code>` | `/markets/india/fno/chain/contracts/{code}/history` | 1,246 (every contract in scope: W13 x-empty, owner default) |
| `chain_sources` | `/markets/india/fno/chain/sources` | 1 |

W13 defines no stored shape for the blocks asked for by a parameter (W11 2.4's `x-stored` covers only the screener). So I store one page per answer, and each page validates directly against the served schema (`ChainRowsResponse`, `ContractHistoryResponse`). That needs no new contract shape; the route only maps the parameter to the key.

**Method** (W13's examples, the mockup's `design/mockups/_platform/chain_data.py`, ported and tested):
- **Scope:**
  - NIFTY index options and futures, from NSE's UDiFF file;
  - expiries after the session up to the end of its second following month (on 12 Oct: through 31 Dec, the mockup's year-end cut; my rule stays sensible in December, when "the year's end" would leave nothing);
  - options within 10% of the day's NIFTY, with both legs per strike;
  - monthly = the last expiry of its month.
- **Per contract:**
  - close, change, OI and its change, volume;
  - IV by Black-Scholes from the close, only when the contract traded, searched within 1%–200% (outside that, the close is not a usable price: no IV, Greeks or chance);
  - prices and Greeks from `fno/analytics.py` (B1), using the repo's `risk_free_rate` of 0.065;
  - break-even, and the risk-neutral chance N(d2).
- **Per expiry:** put-call ratio, max pain, the ATM strike (a tie goes to the lower strike), ATM IV, straddle and range, call and put walls, and where OI was added.
- **History:**
  - from W13's extract day, 1 Jun 2026, keeping at most six months (bounded daily reads);
  - NIFTY and VIX closes, and each expiry's daily PCR;
  - coverage as W11's rule (a value only when the days cover the period);
  - each contract's own sessions, with the close null on a day without trades.
- **The F&O files are read once:** the session build reads the chain's longer window and parses each file once. P6's F&O rows still use only their own 95-day window, so their figures are unchanged (the comparison proves it).

**Criteria:**
1. **Every chain example equals ours field by field: MET (strong evidence).**
   - A real `python -m fno market compare --day 2026-10-12`, from the archived Drive files through the new session build (3 min 10 s), gives 0 differences for all 9 chain examples: `getChainUnderlying`, `getChainExpiries`, `getChainRows` (near, weekly band, all), `getChainHistory`, `getContractHistory` (near and long) and `getChainSources`.
   - `getChainHistory_india_short` is a view (the history cut to 30 sessions to show the nulls), not a page. A test rebuilds it from our series and gets it exactly.
   - The 33–34 differences are unchanged from response 50: renamed stocks plus one sub-cent rounding.
2. **Validation: MET.** All 1,271 chain pages validate against the pinned served schemas (2.4 s). The planted-break tests still refuse the whole publication.
3. **One transaction, one run status: MET.** The chain blocks are in `build_market_blocks()`, so they publish through the same `PostgresPublisher` transaction and the same run row. A re-run adds no rows (the content-named ID covers every page).
   - The read-back now prints one line per block: a single page's hash, or a multi-page block's page count and the SHA-256 of its pages' hashes. That keeps 1,277 pages to 14 log lines.
4. **Size, lint, imports, tests: MET.**
   - 1,558 tests pass; ruff, imports and the record scan are clean; the largest new file is under 150 lines.
   - **Pinned:** `api/examples/blocks-32.json` was added to the pin at dashboard b2c92ee. Nothing under `api/` changed since, and the chain schemas were already pinned.
   - **Fixture:** `tests/fixtures/nse/chain/` (307 KB) is our own cut of the archived files. It holds the 21,590 in-scope NIFTY rows (UDiFF columns) of 1 Jun to 12 Oct, plus NIFTY 50 and India VIX from the index files. The equality test therefore runs offline in CI.

**Doubts and costs (stated plainly):**
- **Storage (some evidence):**
  - The chain adds about 1.5 MB of JSON per session (1,271 pages); P6's pages are about 2–3 MB. `fno.pages_history` keeps every publication, so that is roughly 1 GB a year, before index overhead.
  - **Options (reasoning only):**
    - a retention job that keeps the last N publications (my lean: a small P-story);
    - contract histories only near the money (the mockup's 21 strikes: about 300 pages instead of 1,246);
    - accepting the growth.
  - The owner's call.
- **Fixed text (interim):** `chain_sources.books` is fixed text ("No F&O book holds a position…"). It is true today (no strategy has passed testing) but is not read from the books yet. When a book can hold a position, this must come from the books' state (C-stories). `quotes.status` is `not_published` until the 3 pm quotes are published.
- **Not checked from here:** the dashboard's route for the chain (W13 follow-up) must map its parameters to the page keys above.
- **Daily run:** the job (`market-publish.yml`, 07:10 IST) will publish the chain from its next run. Publish run time grows by about 30 s (the extra F&O files).

## Addendum P10: Home's F&O read models (built for the fields W10 gives fno; two items stopped)

**What W10 assigns to publisher `fno` for Home, checked against the contract** (omenix-dashboard `api/`, at 407ead2):

| Owner's item | W10 | Done |
|---|---|---|
| F&O book accounts for "Who trades" (Book 1 Rules, Book 2 Hybrid, Book 3 AI team, `pnl` each) | `FnoBooks`, `/markets/india/fno/books`, `x-publisher: fno` | **built**: page `fno_books` |
| F&O picks, empty with a reason | `FnoPicks`, `/markets/india/fno/picks`, `x-publisher: fno`; empty state is `fno_state.approved: false` plus `note` | **built**: page `fno_picks`; **no reason-code field exists** (only `note`) |
| India market band (indices and session) | `getIndices`, `getSession`: `x-publisher: stock` for every market (`api/paths/blocks-frame.yaml`) | **stopped**: not an fno field |
| Upcoming NIFTY expiries (`fno_expiry` events) | `Events`, `getEvents`: `x-publisher: stock`; the kind `fno_expiry` exists in its enum | **stopped**: not an fno field |

**What is published, from the F&O tool's own records (no example values):**
- **`fno_books`:** for each book (1 rule, 2 hybrid, 3 AI team), read from its own account (E1, `journal/<book>/account/`):
  - `value`: the latest marked equity on or before the session; before a book opened, its Rs 5,00,000 opening balance;
  - `pnl`: value − opening balance;
  - `approved`: the passing policies of the latest frozen experiment (`research/2026-10-12-experiment-1/results_challenge.json`, `overall.passing_policies`: none). That is the only route by which a strategy becomes approved;
  - `limit_used`: 0 with no open trade;
  - `limit_max`: C2's `max_stress_loss_rs` from `config.yaml` (Rs 30,000);
  - `as_of`: the session at 15:00 IST, when the books decide.

  **Today's truth:** all three books are at Rs 5,00,000 with `pnl` 0, no approved strategy and no risk used.
- **`fno_picks`:** `approved: false`, `rows: []`, `baskets: {}`, and the note "No F&O strategy has passed testing yet: Experiment 1 (the 2019-2023 challenge) passed no policy, so at 3 pm each F&O book records “no approved strategy”." The W10 example's note ("Experiment 1 has not run") is out of date; ours reads from the result file.
- **Both pages** are in the same publication, transaction and run status as P6 and P9 (1,279 pages for 12 Oct), and validate against the pinned W10 schemas (`FnoBooksResponse`, `FnoPicksResponse`).

**Figures this story does not compute stop the run** (new reason code `figures_not_computed`, added to migration 002 before the owner runs it):
- a book with an open trade: its risk used is C2's stress of the open trades, not computed here;
- an approved strategy: its picks are the books' decision records (D3).

Either case publishes nothing rather than a wrong figure or an empty panel that is no longer true. Today neither can happen: no strategy is approved, so no book can open a trade.

**Tests** (`test_home_blocks.py`, 6):
- each book read only from its own account, as of the session, with the before-opening case;
- the approvals read from the frozen result;
- the live wiring reads the repository's books and C2's limit (Rs 30,000);
- both payloads say the truth and validate;
- each not-computed case stops the run with its code.

All market tests pass (106).

**Decisions needed (orchestrator or owner):**
1. **India market band and `fno_expiry` events:** W10 gives them to the stock tool. Either the stock tool publishes them (it has the NSE session calendar and its events file), or W10 moves the India band and the India expiry events to publisher `fno`. In the second case, P6's index rows and the session calendar (A7) plus the listed expiries (A5) already hold the data, and a follow-up here builds them. **My lean (reasoning only):** split by market. The India band and India F&O expiries go to `fno`, because this repository already holds NSE's calendar, expiries and closes; the US stays with the stock tool. Not built here, by your rule.
2. **Reason code for the empty picks state:** W10's `FnoPicks` has no field for it; only `note` (text). If the dashboard needs a machine-readable code, W10 must add one (for example `fno_state.reason_code`, with values such as `no_strategy_passed`). I did not add it.
3. **Where `FnoBooks` is stored:** W10's `x-read-model` names P1's proposed pages `risk` and `scoreboard_b`. Those don't exist yet, so I store the block as one page, `fno_books`. The dashboard's route reads it by that key; please confirm, or W10 can change the read-model note.

**End-to-end check (all of P7, P9 and P10 together):** `python -m fno market publish --day 2026-10-12 --local <folder>` through the real wiring (Drive files, the repository's books, `config.yaml`) published 1,279 pages, with read-back equal and exit 0. The six P6 page hashes equal those published to Azure in run 38438666957 (for example `screener_stocks cfb0584223818102…`, `overview_sectors 2bf88cacb2b01f53…`), so P7–P10 left P6's output byte-identical. Full suite: 1,618 tests pass; ruff, imports and the record scan are clean.

## Addendum P8 and P10 (rest), after the owner's decision of 14 Oct: data side ready, blocks waiting for the contract

**The decision:** the owner said "yes" to moving the India market band (indices, session), India `fno_expiry` events and India FII/DII flows to publisher `fno`; the US stays with the stock API. The dashboard builder is changing W10/W11 to split the publisher by market, with no field-shape changes.

**Contract status when I checked (omenix-dashboard `main` at dca854d):** not pushed yet. `getFlows`, `getIndices`, `getSession` and `getEvents` still read `x-publisher: stock`. As instructed, I built only the downloader and the data side. The blocks wait for the contract commit that names the publisher split.

**Built (data side, P8):**
- **Two new archived datasets.** Both serve only their latest day, so each is archived as one copy per day fetched, and the session a copy covers is read from the copy itself:
  - `nse/flows/fii-dii-cash` (`FiiDiiCashSource`, NSE's `api/fiidiiTradeReact`, JSON): provisional FII/FPI and DII cash-market buy, sell and net, in Rs crore;
  - `nsdl/fpi/fpi-daily` (`NsdlFpiDailySource`, NSDL's `Reports/Latest.aspx`, HTML): the daily FPI report, from which the reader takes the **equity sub-total net over all routes** (the contract's `nsdl.net`). Bracketed amounts are negatives.
- **Readers:** `fno/market_read_models/flows_files.py`. They are also the archive's content checks, so a blocked or maintenance page is refused before it is saved.
- **First copies are in Drive, with SHA-256 manifest rows committed:**
  - `nse/flows/fii-dii-cash/2026/10/14/fii-dii-cash.json` (13 Oct: FII/FPI net −1,305.13 crore; DII +2,439.24);
  - `nsdl/fpi/fpi-daily/2026/10/14/fpi-daily-latest.html` (13 Oct: FPI equity net +2,000.73 crore).
- **Daily download:** `.github/workflows/flows-download.yml` runs at 21:10 IST, after NSE's evening release, with the same Drive and Slack secrets as the other jobs and one alert on failure. The 07:10 IST publish run also takes a copy (`DAILY_SNAPSHOTS`).
- **Versions:** a later NSE version of the same day is never written over the first. It lands as the next day's copy, and the reader takes the latest copy per session, so publishing reads the latest version while every copy stays.
- **Tests** (`test_flows_files.py`, 7): both readers on the real 13 Oct files, refusals, paths and URLs, the content checks, and the workflow.

**History (stated plainly):**
- Both sources give only the latest day, so our flow history starts on 13 Oct 2026.
- The contract's period totals are null until the days cover them: 1D now, 1W after 5 sessions, 1M after 21, 3M after 63, 1Y after 250. That is the contract's own rule (judge 27), so nothing is invented. The stock tool's example shows 5 days.
- Backfilling a year would need NSE's or NSDL's archive pages, which are date-range forms. That is not attempted. Ask if the owner wants it.

**Waiting for the contract, then built against it, through the same publisher, run status and validation:**
- **P8:** the India `Flows` block. It needs FII and DII per day, NSDL per day, and the period totals with coverage.
- **P10 rest:**
  - the India band: `Indices` from P6's index rows and `Session` from NSE's session calendar (A7);
  - India `fno_expiry` (and `weekly_expiry`) events: from the listed NIFTY expiries (A5) and the calendar.

## Addendum: judges 59-61 and 63 fixes

**P7, judge 59 FAIL: a finished row could be rewritten by a plain UPDATE.** Accepted; I checked the judge's plant before fixing it.
- **Fixed inside `002_run_status.sql`,** since the owner has not run it: a `before update` trigger (`fno.run_status_finished_never_changes`) raises `restrict_violation` when the old row is not `running`.
- **The adapter is unchanged.** Its `where result = 'running'` never touches a finished row, so the trigger never fires on the normal path.
- **Test:** `test_a_finished_row_cannot_be_rewritten_even_by_a_plain_update_as_the_publisher_role` connects as `fno_writer` and runs the judge's exact UPDATE. It is refused (`RestrictViolation`) and the row stays `published`.
- **Mutation check:** with the trigger removed from the migration the test fails; with it, it passes.
- **The owner's step is unchanged:** the same `psql … -f db/fno/migrations/002_run_status.sql` as `fno_owner`. It now also creates the function and trigger, which needs `fno_owner`'s CREATE on schema `fno`, the same right 001 used.

**P10, judges 61 and 63: page keys.** Accepted: the contract wins.
- **Picks:** `FnoPicks` → page **`today`**, exactly as W10 names it (`api/paths/blocks-fno.yaml:37`: `x-read-model: 'fno.pages_history page today (P1)'`).
- **Books:** `FnoBooks` → page **`risk`**. W10 is ambiguous here; it names two pages for one block:
  - `api/paths/blocks-fno.yaml:117`: `x-read-model: 'fno.pages_history pages risk and scoreboard_b (P1)'`
  - `api/schemas/blocks-home.yaml:71`: `source: "fno.pages_history pages 'risk' and 'scoreboard_b' (P1) over E1's paper accounts"`

  The dashboard's only reader of the block reads one page, `risk`: `web/lib/home/azure-source.ts:14`, `fnoBooks: () => payload("risk")` (W9-F&O). I followed that reader rather than guess a split, since `FnoBooks` is one closed object and nothing says which fields would go to `scoreboard_b`. **Contract owner:** please reduce line 117 and the catalog source to "page risk", or say which fields `scoreboard_b` holds.
- **Test:** `test_the_page_keys_are_the_ones_w10_names_in_the_pinned_schemas` reads both names from the pinned W10 schemas' catalog text. The payloads were already validated against `FnoBooksResponse` and `FnoPicksResponse`.

**P9, judge 60 minors.**
- **ATM tie test added:** `test_a_spot_exactly_between_two_strikes_takes_the_lower_as_atm` (spot 22,375 between 22,350 and 22,400 gives 22,350). The judge's plant (tie to the higher strike) now fails it; I checked by applying the plant.
- **Page keys against W13's proposal** (W13 calls them "proposed"; listed, not renamed twice):

  | Block | W13 (`api/paths/blocks-chain.yaml`) | P9 publishes |
  |---|---|---|
  | rows | line 63: `chain_rows:<expiry>` ("the route picks the strikes") | `chain_rows:<expiry>:<near\|band\|all>` (three pages per expiry, each a served answer) |
  | contract history | line 121: `chain_contract:<code>` | `contract_history:<code>` |
  | underlying, expiries, history, sources | lines 11, 37, 95, 150 | the same names |

  If W13 keeps its proposal, P9 changes two key formats. For rows that means storing the "all" strikes once per expiry, with the route filtering near and band (14 fewer pages on 12 Oct). Both are one-line changes in `chain_blocks.py`. Whoever owns W13 decides.

## Addendum: W13's page keys adopted (orchestrator decision); yearly size, measured

**Decision applied:** P9 now publishes W13's proposed keys exactly (`api/paths/blocks-chain.yaml` lines 63 and 121):
- **`chain_rows:<expiry>`:** one page per expiry with every strike in scope (`strikes: "all"`, 89 strikes for 27 Oct). The route serves "near" (the ATM strike and 10 either side) and "band" (within 5% of NIFTY) from it.
- **`chain_contract:<code>`:** replaces `contract_history:<code>`.

**The route's strike sets are code here** (`chain_route.strikes_view`). The comparison serves W13's near, weekly-band and all examples through it, from the stored page, NIFTY from the underlying block and the ATM strike from the expiries block. All 9 chain examples still equal ours field by field (`test_chain.py`, offline on the real-file fixture). Pages for 12 Oct: 1,265 in all (7 rows pages instead of 21).

**Yearly size (some evidence: payload sizes measured on 12 Oct as compact JSON; the disk factor is reasoning):**

| Pages | 12 Oct | Per session |
|---|---|---|
| Chain: 7 rows + 1,246 contracts + 4 single | 0.27 MB rows, 0.85 MB contracts, 0.01 MB others | 1.13 MB |
| Screener, Markets, Home (P6, P10): 8 pages | measured from the real local publish | 0.65 MB |
| **Total** | | **1.78 MB** |

- **Per year:** about 250 sessions × 1.78 MB ≈ **0.44 GB of payload a year** in `fno.pages_history`, which keeps every publication.
- **Saved by this change:** the dropped near and band pages were 0.21 MB a session, about 52 MB a year.
- **On disk:** Postgres compresses large JSONB values (TOAST), and this JSON repeats keys heavily, so the disk share is likely 2–4× smaller, roughly 0.1–0.2 GB a year plus indexes. That is reasoning, not measured on Azure.
- **Correction:** my earlier "about 1 GB a year" was too high. It assumed 2–3 MB for P6's pages; measured, they are 0.65 MB.
- **The largest part is the contract histories** (0.85 MB, 1,246 pages), each repeating up to six months of history every day. A retention job keeping the last N publications would bound the total; my lean is that is still worth a small story.

Tests:
- `test_the_pages_one_per_expiry_and_one_per_contract`: 7 rows pages, 1,246 contract pages, 89 stored strikes, and the route's near set of 21 around 22,350;
- the equality test through the route;
- the run and read-back tests (1,265 pages; read-back shows "chain_rows 7 pages").

## Addendum: judge 59 addendum 1, the runtime role's rights fixed at the design level

**Root cause (accepted; the judge's evidence matches X1's SQL):**
- X1's step 40 (`platform/sql/40_default_privileges.sql`) gives `fno_writer` SELECT, INSERT, UPDATE and DELETE on **every** table `fno_owner` creates in schema `fno`. On Azure that includes 001's tables and would include 002's.
- My fixture created the roles without step 40, so it never saw those rights.

**Fixed in `002_run_status.sql`** (the owner has not run it, so the file itself changed, not a new migration):
- **Rights narrowed to exactly what the publisher needs** (revoke, then grant, so it is idempotent):

  | Table | `fno_writer` keeps | Revoked | Why |
  |---|---|---|---|
  | `pages_history` | INSERT, SELECT | UPDATE, DELETE, TRUNCATE | history is append-only (insert … on conflict do nothing, then read back) |
  | `current_publication` | INSERT, UPDATE, SELECT | DELETE, TRUNCATE | a one-row pointer per product, upserted |
  | `run_status` | INSERT, UPDATE, SELECT | DELETE, TRUNCATE | one row per run, inserted then finished once |

  `dashboard_app` keeps SELECT only, on all three.
- **No job needs DELETE as the runtime role:** the publisher, the read-back and the run status only insert, update the pointer, and finish a run. A future retention or rebuild job would run as `fno_owner`, never `fno_writer`.
- **One guard trigger** (`fno.run_status_guard`, before insert or update) replaces the update-only one:
  - a row must be **born `running`** (no `finished_at`, result, reason or publication at insert);
  - a running row **keeps its product, run ID, session and start**;
  - a **finished row never changes**.

  It raises `restrict_violation`. On a server set up like Azure (functions executable by nobody but `fno_owner`), the trigger still fires for `fno_writer`, as the tests show.
- **The test fixture now mirrors Azure:**
  - `tests/market_read_models/x1_platform.sql` is a copy of X1 steps 00 (the 8 roles), 20 (schema `fno` owned by `fno_owner`), 30 (USAGE) and step 40's `fno_owner` default privileges, from omenix-dashboard at 407ead2;
  - the migrations run **as `fno_owner`**;
  - the publisher and run-status tests act **as `fno_writer`**.
- **New tests** (`test_runtime_privileges.py`, 13), as `fno_writer` on the Azure-like server:
  - delete and truncate refused on all three tables, and update refused on the history;
  - a row born `published` is refused;
  - changing a running row's identity is refused, and a finished row cannot be updated;
  - `dashboard_app` reads but cannot delete;
  - `fno_writer`'s exact grants per table.
- **Mutation check:** with the revokes removed, 5 of these fail.

All market tests pass (129). The owner's step is the same command as before (`psql … user=fno_owner … -f db/fno/migrations/002_run_status.sql`). It now also narrows `fno_writer`'s rights on 001's two live tables; nothing the publisher does needs what it removes.

## Addendum: contract 2.5 (publisher split), India's band, expiries and flows built

**Contract:** pinned omenix-dashboard `6cc6b7a`, contract **2.5.0**, which includes 13661c0, 715048a and 3501464.
- Changed: `openapi.yaml`, `blocks-frame.yaml`, `blocks-home.yaml`, `blocks-overview.yaml`, `blocks-responses.yaml` and the 33–34 examples.
- India's pages under publisher fno, built to exactly these names and schemas:

| Page | Endpoint (2.5) | Schema | Built from |
|---|---|---|---|
| `session` | `getSessionIndia` | `SessionIndiaResponse` (`Session`) | NSE's session calendar (A7) |
| `indices` | `getIndicesIndia` | `IndicesIndiaResponse` (`Indices`) | P6's index rows (NSE's index file) |
| `fno_events` | `getFnoEvents` | `FnoEventsResponse` (`Events`) | the NIFTY expiries NSE lists in the day's F&O file (P9's scope) |
| `flows` | `getFlows` | `FlowsResponse` (`Flows`) | the archived NSE FII/DII and NSDL copies (P8 data side) |

Books and picks stay `risk` and `today`; 2.5's catalog now says "page 'risk'" only.

**How each is computed:**
- **`session`** (the session being predicted is the next session after the published one, from the calendar, so a re-run is deterministic):
  - `exchange` "India (NSE)", `zone` IST;
  - open and close at NSE's regular 09:15–15:30 IST (03:45–10:00 UTC), and `next_open_utc` = that open;
  - `post_close_at` = 07:10 IST the next day, when the next market run brings the close;
  - `regime` null (the F&O tool records none; the catalog says so);
  - `major_event_names` = the session's major expiries (a monthly expiry day names it).
  - **Special sessions** keep regular hours: the calendar notes say "normal timings" for every future special session; the 2024 disaster-recovery switch days are past.
  - **A muhurat session stops the run** (`figures_not_computed`). Its hours exist only in the calendar's free text, and 2026's (8 Nov) are "not yet issued". **Owner action before 8 Nov 2026:** when NSE's timings circular is out, give the calendar the muhurat hours (A7), or the session page is not published that day.
- **`indices`:**
  - NIFTY 50 and INDIA VIX, with id, symbol, name and role as in the contract's example;
  - `last` = the close, `chg_pct` = change on the previous close, `chg_5d_pct` = change over 5 sessions (P6's d1 and w1, the same rounding);
  - `as_of` = the index's own close date at 15:30 IST, and `source` "close".
  - A missing index stops the run rather than publish a made-up level (the contract's x-empty).
  - 12 Oct: NIFTY 22,363.35 (−0.70%, 5-session −0.85%); INDIA VIX 15.25 (+6.05%, +3.18%).
- **`fno_events`:**
  - the NIFTY expiries NSE lists after the session, within the next three calendar months: monthly = `fno_expiry` (major), weekly = `weekly_expiry`;
  - title "NSE monthly F&O expiry (last Tuesday)", or "(moved for a holiday)" when a monthly is not the month's last Tuesday (23 Nov 2026), and "NIFTY weekly expiry";
  - the route applies `kinds`, `from` and `limit`.
  - 12 Oct: 7 events (13, 19 and 27 Oct, 3, 9 and 23 Nov, 29 Dec). **The first four equal the contract's `getFnoEvents_india_calendar` example field by field.** The example's horizon ends on 3 Nov; ours goes on to the expiries NSE already lists.
- **`flows`:**
  - per session, FII/FPI and DII buy, sell and net (NSE, `provisional: true`), plus NSDL's FPI equity net, for the last 250 sessions;
  - period totals only when the period's sessions all have data (else `complete: false` and null).
  - **Which copy is read:** NSE serves a session's values until the next release, so copies fetched up to the next session are read, the latest copy of each session wins, and values of a later session are never read (no look-ahead).
  - 12 Oct: `days` empty (our first copy covers 13 Oct), so the block is the contract's empty state: "no figures yet".

**Tests** (`test_frame_and_flows_blocks.py`, 6):
- the session's times and next-morning run; Friday → Monday; a monthly-expiry session names it; muhurat stops;
- the indices' values, and a missing index stops;
- the expiries, the moved monthly, and the equality with the contract's calendar;
- the flows' latest copy, no look-ahead, totals and validation against `Flows`;
- all four pages in the publication, validated as served against 2.5.

**Mutation check:** reading copies only up to the session day (missing the morning copy) fails the flows test.

Full suite and the real local publish: see the commit.

**Checks:**
- Full suite: 1,806 tests pass; ruff, imports and the record scan are clean.
- **Real local publish of 12 Oct** through the full wiring (Drive files, the repository's books and calendar, `config.yaml`): 1,269 pages in 18 blocks, read-back equal, exit 0. It includes `session` `8d812166…`, `indices` `3ce82445…`, `fno_events` `28949db2…` and `flows` `7e3bf91b…`. The six P6 pages keep their hashes from the Azure run 38438666957, so P6 is unchanged.

## Addendum: two design points before the judge (orchestrator, 14 Oct)

**1. A session with unknown hours is a block-level state, not a run failure.** Accepted: stopping the whole run was too wide. From 7 Nov every page would have failed, because the session after Friday 6 Nov is the muhurat Sunday 8 Nov.
- **Now:** when the next session is a muhurat session (its hours exist only in the calendar's free text), the `session` block **publishes no page**. Every other page publishes, and the route answers "page missing" for `session` alone.
- **Contract gap (stop and list, not invented):** 2.5's `Session` has **no field for a reason**. Its properties are `exchange`, `zone`, `session_date`, `open_utc`, `close_utc`, `next_open_utc`, `regime`, `post_close_at` and `major_event_names`. Its only empty form, `open_utc` and `close_utc` null, means "non-trading day" (path x-empty), which would be false for a muhurat session.
- **For the contract owner:** to publish a partial session with a machine-readable reason, `Session` needs a field such as `hours_status: known | not_issued` (or a reason code like `hours_not_issued`). I'll build to whatever is added.
- **Test,** with the real calendar row 8 Nov 2026 ("muhurat … timings circular not yet issued"): the frame for 6 Nov points at 8 Nov muhurat, the session block has no page, and a full run publishes with exit 0 and no alert. Indices, events, flows, books, picks and the chain are all present; only `session` is absent.

**2. Raw data never waits for the database** (G1 builder's point). Accepted: before, `market-publish.yml` archived inside the publish step, after the database check, so an outage would have left a gap in Drive, which A13's panel reads.
- **Now, in order:**
  1. **archive:** the new `python -m fno market archive [--day D]`. It needs no database and commits the manifest rows.
  2. **database check:** runs even when the archive failed (`if: !cancelled()`).
  3. **publish:** `market publish`, only when the check passed. It records `archive_incomplete` itself if files are missing.
  4. **one alert on failure,** naming the archive or database cause.
- `market publish --day` now defaults to the last session, like `market daily`. `market daily` (archive then publish in one step) stays for local use.
- **Tests:**
  - the workflow test checks archive < database check < publish, that the check runs after a failed archive, and that publish waits for the check;
  - `test_the_archive_command_needs_no_database_and_says_what_is_missing` checks the command's exit code and lines with no `FNO_DB_URL` set.

## Addendum: judge 66's minor, the flows window bounded by the publication's own moment

**Accepted, with evidence. My earlier claim was wrong.** I had said copies "fetched up to the next session" are read, to catch "the morning copy". The judge is right on both points:
- The upper bound was untested: their plant widening it by two sessions passed every test.
- The bound was too wide. Session D is published at 07:10 IST the next morning. A copy filed the next day may be taken after that moment (flows-download runs at 21:10 IST), so a re-run of D could read values the live run could not have seen.

My earlier mutation check ("reading only up to the session day fails the test") tested the opposite rule, so it proved the wrong thing.

**The rule now** (`FlowsReader`, `frame_inputs.py`):
- A copy is filed under the IST day it was fetched. The archive keeps no time of day, only the day folder.
- Session D publishes at 07:10 IST the day after D. So only copies **filed on or before D** are surely older than D's publication, and only those are read.
- The archive keeps one copy per day and refuses a different one, so a re-run of D reads exactly the same copies and builds the same pages.
- Within the window, the latest copy of each session still wins, and a copy covering a later session is still never read.

**Which copies each publication read is now recorded:**
- **Why not in the stored row:** the contract's stored row has no field for this, and I did not invent one.
- **Where it is recorded:** the run writes one row per publication, page and dataset to `research/data/publications/publication-inputs.csv`. The row gives the number of copies, the newest copy's filing day, and the SHA-256 of the full list (`<session> <filed on> <sha256>` lines, sorted). The publish run commits this file through the same git recorder as the manifests, with the record scan on and never bypassed. The run log prints the same lines.
- **How to check it:** the list itself is the reader's output for D, rebuilt from the append-only archive and checked against that SHA-256. Each copy's SHA-256 also equals its manifest row.
- **A re-run** that publishes the same ID adds no row ("already recorded").
- **Limit:** the judge asked for the fetch *time*. Only the fetch *day* exists, and the rule is designed around that.

**Tests:**
- `test_flows_read_only_copies_filed_by_the_session_itself_never_a_later_one`: NSE's revised 13 Oct values, filed 14 Oct, are not read for 13 Oct (net -1305.13, not -1300.00). They are read for 14 Oct, where they are the latest copy of 13 Oct. The test also checks each copy's dataset, session, filing day and SHA-256.
- `test_each_publication_records_the_copies_its_flows_read_once`: the run's lines, the CSV row, and a re-run adding nothing.

**Mutation checks** (each run on the flows test file, then restored):

| Plant | Result |
|---|---|
| Window widened by one session (`next_session(day)`) | caught (1 failed) |
| Window widened by one calendar day | caught (1 failed) |

**Real archive (some evidence; what the owner will see):**
- The only flows copies so far were filed on 14 Oct (02:18 IST, a hand run), so **13 Oct's publication has empty flows**. That copy was in fact taken before 13 Oct's 07:10 publish, but the day-level rule cannot prove it, so it is left out. That costs one day.
- 14 Oct's publication reads 13 Oct's values from those copies: FII net -1305.13 and NSDL 2000.73 crore. Their SHA-256s are `216a4b93…` and `0296e1dc…`, which equal the manifest rows.
- From then on, each session's 21:10 IST copy serves its own publication.
- The 07:10 run's own morning copy (filed the next day) is never read for D. It serves the next publication as the latest copy of D.

## Addendum: contract 2.6, India's session states `hours_status` (orchestrator, 14 Oct)

**The pin:** omenix-dashboard c6b4dc7 (`c6b4dc74…`), version 2.6.0.
- Three pinned files changed: `openapi.yaml`, `blocks-frame.yaml` and `blocks-responses.yaml`.
- The 2.6 example `getSessionIndia_india_hours_not_issued` is in `api/examples/blocks.json`. That file is now pinned as well. Its 48 example names share none with `blocks-33-34.json` or `blocks-32.json`.

**The block** (`SessionIndiaBlock`):
- The `session` page is always published and always states `hours_status`.
- For a muhurat next session, whose hours exist only in the calendar's notes, the page has:
  - `session_date` set;
  - `open_utc`, `close_utc` and `next_open_utc` null;
  - `hours_status: "not_issued"`.
- The 2.5 workaround is gone: the page is no longer left out.
- Every other session has `hours_status: "known"` and NSE's regular hours.

**One field differs from the example, on purpose (reasoning only):**
- **Our value:** `post_close_at` is `2026-11-09T01:40:00Z`, 07:10 IST on 9 Nov.
- **Why not the example's null:** 2.6 defines `post_close_at` as "when today's post-close run is due … null once it ran". The 07:10 IST market run on 9 Nov is still due, and it is what brings 8 Nov's close.
- **The contract owner can override:** if they want null while the hours are not issued, it is a one-line change.

**Tests:**
- `test_a_muhurat_session_without_issued_hours_publishes_as_not_issued_and_the_run_publishes`:
  - Uses the real calendar row for 8 Nov 2026.
  - The page equals the contract's example except for `post_close_at`.
  - A planted "guessed open time while not_issued" is refused by the 2.6 `Session` schema.
  - A full run publishes with exit 0 and no alert, and the stored page says `not_issued`.
- The regular session test now expects `hours_status: "known"`.
- The pin test expects version 2.6.0.

**Mutation checks:**

| Plant | Result |
|---|---|
| Muhurat treated as known hours | caught (1 failed) |
| `hours_status` dropped | caught (4 failed; `SessionIndiaResponse` requires it) |

**Owner action (unchanged):** when NSE issues the muhurat circular, add the hours to the calendar. The block then publishes them as `known`. That needs the calendar's hours fields, which A7 owns.
