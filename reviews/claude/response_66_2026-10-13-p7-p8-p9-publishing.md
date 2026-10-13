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
