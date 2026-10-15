# Epic P: publishing F&O results (dashboard data and Slack)

Roles: data engineer, head of desk, risk manager. Goal: after every daily run, code turns the committed records into
versioned dashboard pages published atomically to the shared Azure database, and posts one Slack message, so that
the owner sees the day without the dashboard ever becoming a second source of truth (design 13.2-13.4, 13.8).
Story template, definition of done and the full story index: `docs/IMPLEMENTATION_PLAN.md`.

---

## P1. F&O data catalog (shared mock data and the read-model contract of the five F&O screens)

**Repository:** both: omenix-dashboard (the catalog lives in the dashboard's API contract) and trading (the pinned copy
and the backend tests).

**Description:** As the owner, I want a data catalog, "which is nothing but mock data that could be shared between
front-end and back-end, so that they could decide how the data looks like for each screen, what kind of data do we
need, and what kind of API contract will be needed, and how UI will consume and use that mock data on its screens, so
that both backend and frontend could keep working on their own parts ... and then later on they integrate" (owner,
15 Oct 2026).

**Context and why:** Owner decisions of 15 Oct 2026 (`docs/DESK_DECISIONS.md`): P1 moves into slice A ("2 Yes"); it is
a shared mock-data catalog and its first screens are the daily card, the weather, the Forecast lab, the Strategy lab
(with its honest empty state) and paper trades ("1 Yes"); it starts now as a third builder ("2 B"). Design v2 defines
what each screen shows: the card (`docs/design_v2/04_layers_card_monitor_learning.md` 4.1 and 4.4), the weather (02,
2.3), the forecasts V1-V7 and their scores (05), the factory and the paper desk (03). Without one written contract the
engine (P2, T1, M1, G8) and the screens (W3) would drift apart; the dashboard's contract already carries the F&O blocks
(W10, W11, W13) and this repository already validates against a pinned copy of it (P6). Cards are kept in Google Drive
only (owner, 15 Oct 2026), and strategy internals never reach a screen or an API (owner, 13 Oct 2026).

**Scope.** In: per screen, a schema in the dashboard's contract (one home: `api/schemas/fno-*.yaml`, endpoints in
`api/paths/fno-screens.yaml`, contract version 2.7.0, additions only); Mock examples in the positive, negative and
empty cases (`api/examples/fno-screens.json`); a plain-words field table generated from the schemas
(`api/catalog/fno-screens.md`: field, meaning, unit, source record in the backend, freshness, visibility public or
owner, and whether the backend can fill it today); checks in the dashboard; mockups for the card (39) and the weather
(40) built from the catalog; the pinned copy here with tests that the catalog's examples, the record fields it names and
fixtures built from this repository's records validate. Out: building or publishing the pages (P2, P3), the screens in
the app (W3), the card's Slack text (T1), rebuilding mockups 37 and 38 on the new contract (W3), the stock tool's half
of the Strategy lab.

**Design:**
- Five India-only endpoints under `/api/v1/markets/india/fno/` (absent in the US), tag `fno-screens`, each answering 501
  until built: `card`, `weather`, `forecast-lab`, `strategy-lab`, `paper-trades`; the F&O block envelope (`FnoBlockMeta`:
  ReadModelMeta plus publisher, freshness, Paper, `product`, `publication_id`), one page per screen per publication.
- Catalog keys on the schemas, inherited downward: `x-visibility` (`public`, or `owner`: the owner's signed-in dashboard
  only, never a public repository: live legs, entry ranges, exit plans, objections), `x-fill` (`built` with `x-record`
  naming `<record>:<field>` of a record that exists here today, or `not_built` with the story that builds it), and
  `x-never-sent` on each page (the strategy internals the backend must never send). Every object is closed; every money
  unit is "INR (Paper)"; the card's `label` is the constant PAPER ONLY; `real_money_eligible` and the Strategy lab's
  `real_money.eligible` can only be false in this version.
- The examples are the one copy of the mock data: mockups 39 and 40 build their `data.json` from them; the dashboard
  check fails if a mockup's data differs. Mockups 37 and 38 keep their signed-off draft data; their notes say the
  catalog supersedes their proposed F&O contracts.
- **Where the contract lives (owner, 15 Oct 2026: "contract A"):** the dashboard's `api/` is the single master contract
  for both stock and F&O; this repository keeps the pinned copy with its hashes and drift check (`pin.json`, `python -m fno
  market contract-check`), as W11 and P6 do. It supersedes the reading of DESK_DECISIONS' 13 Oct "API design kept" row
  that this repository owns the F&O contract.
- **A missing weather blocks new trades** (owner, 15 Oct 2026, DESK_DECISIONS row "Missing weather blocks new trades" (owner:
  "4 A"; asked: "A: If the weather reading is missing, block new trades. B: ... allow trades and just show 'weather
  unknown'."): "Fails closed, like RED"). The weather schema requires `blocks_new_entries: true` when `status` is
  `not_published`, and a TRADE card needs GREEN or AMBER.
- Drift fails a test on both sides: `tools/api/check_fno_screens.py` in the dashboard (CI job api-contract);
  `tests/market_read_models/test_p1_data_catalog.py` here against the pinned copy (`pin.json` names the dashboard commit,
  version 2.7.0).

**Acceptance criteria:**
1. Each of the five screens has a schema, an endpoint and Mock examples covering its positive, negative and empty cases
   (at least: card TRADE, NO TRADE for RED, NO TRADE with a missing input named, NO TRADE because no strategy has passed;
   weather RED; Forecast lab "not enough data yet" with V1's missing input named; Strategy lab "no strategy has passed";
   paper trades with a loss).
2. Every example validates against its schema in both repositories, is labelled Mock, carries contract version 2.7.0,
   its page key and the SHA-256 of its payload by this repository's canonical JSON.
3. Every leaf field has its meaning, unit, source record, freshness, visibility and whether the backend can fill it
   today; every built field names a record field that exists in this repository, with a matching type where the record
   is typed (a test reads each one); no field the
   backend cannot fill is filled with a made-up value outside a Mock example.
4. Every money field says Paper; the card says PAPER ONLY; no example or schema property is named like a strategy
   internal (rule, threshold, filter, parameter, prompt, weight, feature, coefficient), and each page lists what is never
   sent.
5. Mockups 39 (card) and 40 (weather) read their data from the catalog only, each with data.json, template.html, a
   deterministic build.py, notes.md, rationale.md and screenshots at 1280 and 390 px with no console errors, no external
   requests and no overflow.
6. Planted breaks are caught (21 in the dashboard check: an extra or missing field, an open object, RED without the block,
   NO TRADE without a reason, a TRADE card at rung 0 or in RED, real money eligible, a label without Mock, a stale hash, a
   missing empty case, money without Paper, the card not PAPER ONLY, a built field without or with an unknown record, no
   visibility, a private key or property, no never-sent list, net not gross minus costs, mockup drift); here a renamed or
   retyped backend record field fails a test.
7. Gates: dashboard code size, typecheck, tests and build, its api-contract checks; here pytest, ruff, ruff format and
   the import check; no file or class over 350 lines.

**Test plan:** the dashboard check with its rule probes (its 28 planted breaks were removed on 15 Oct 2026 under the
owner's simplicity rule, dashboard f617139) and the generated-table currency check; the backend test file (every example,
every named record field, fixtures from the trial ledger, a fresh paper account and the 14 Oct 2026 live forecasts, a
renamed field); page checks of every mockup state.

**Judge verifies:** reads the five schemas against design v2 (4.1, 2.3, 5, 3.1-3.2) for missing or wrong fields; plants a
field rename in a backend record and sees the test fail; checks that no public example carries a strategy threshold or a
live card detail; rebuilds mockups 39 and 40 and compares data.json with the examples.

**Depends:** W10, W11 (the block envelope), P6 (the pin) · **Size:** M · **Status:** built on branches
`story/p1-data-catalog` (both repositories); awaiting the judge (claims: `reviews/claude/response_102_p1-data-catalog.md`)

### History: the original P1 (12 Oct 2026, design 13.2), superseded by the owner's decisions of 15 Oct 2026

Kept for the record. Its version policy (a breaking change is a new major version; the envelope with `product` and
`publication_id`) is kept by the dashboard contract; its page list (today, positions, risk, scoreboards, ledgers, judge,
evidence, health) returns with P2 and W3 where design v2 still needs it.

> **Repository:** trading
>
> **Description:** As the dashboard developer, I want a versioned JSON schema for every F&O page, owned and tested in this
> repository, so that the dashboard knows exactly what it reads and a backend change can never silently break a screen.
>
> **Context and why:** Design 13.2: each backend owns a versioned data contract; the dashboard checks the version it
> expects; a breaking change is a new version. The stock dashboard already uses the read-model envelope `market,
> page_key, as_of, cutoff, built_at, schema_version, source_commit, payload_sha256, payload`
> (`agentic-stock-prediction/web/lib/data/serve.ts`, read only); F&O uses the same envelope with `product = fno`.
>
> **Scope.** In: page list and JSON schemas, the envelope, contract tests, the version policy. Out: building or
> publishing pages (P2, P3).
>
> **Expected design:** `contracts/fno/v1/*.schema.json` for pages: `today` (per book: decision, reasons, Book 2's rule
> default vs AI action), `positions` (per book: legs, marks, pending exits, days left), `risk` (per book: each owner limit
> used vs allowed, brake distance, stress, exposure), `scoreboard_b` and `scoreboard_a` (every detail of 12.5, per segment,
> pilot apart; `scoreboard_a` is added as a minor version when S3 lands), `forecasts`, `ledgers` (cash spend and allocated AI cost labelled apart), `judge` (approvals,
> rejections, abstentions, overrides, hard-validity failures), `evidence` (hashes and commits of packs, decisions,
> snapshots, versions), `health` (data and run status, alerts). `contracts/fno/CHANGELOG.md`; a compatibility test
> fails if a field is removed or retyped without a major version.
>
> **Acceptance criteria:**
> 1. Every page schema validates a fixture payload built from fixture records.
> 2. Removing or retyping a field without bumping the major version fails the compatibility test.
> 3. No schema field can hold a credential or broker identifier (a field-name and pattern check).
> 4. The envelope matches the stock read-model envelope field for field, plus `product` and `publication_id`.
>
> **Test plan:** schema validation and compatibility tests.
>
> **Judge verifies:** validates one real day's payloads against the schemas.
>
> **Depends:** D3, S2 (S3 for the scoreboard A page) · **Size:** M · **Status:** later

---

## P2. Read-model builder

**Superseded (16 Oct 2026):** the owner's decision "F&O screens start now ... through the existing Azure path" replaces
this text with `docs/stories/W3-fno-screens.md`, part 1 (pages in the existing daily publish). The text below is history.

**Repository:** trading

**Description:** As the owner, I want the F&O pages built by code only from committed records, so that every number on
the dashboard traces to a file and a commit and no AI ever writes a number.

**Context and why:** Design 13.2: payloads generated by code from committed repository records (decision records,
ledgers, scoreboards, forecasts, data-health records); every screen shows built-at time and source commit; "paper
trading only, not advice"; never a real-order instruction.

**Scope.** In: the builder, determinism, the evidence links. Out: publishing (P3).

**Expected design:** `fno/publish/builder.py`: `build_publication(commit) -> Publication` with one payload per P1 page,
each with `source_commit`, `payload_sha256`, `as_of`, `cutoff`; a local copy written to
`reports/dashboard/<date>/` (committed) so the record exists even if publishing fails. Command
`python -m fno publish build [--date]`.

**Acceptance criteria:**
1. Building twice from the same commit gives byte-identical payloads.
2. Every number in the payloads equals its source record (a test re-reads sources for a fixture day).
3. Every payload validates against P1 and carries the "paper trading only, not advice" notice.
4. The builder never calls an AI or a network service (test with fakes that fail on any call).

**Test plan:** fixture-day build tests; determinism test.

**Judge verifies:** rebuilds one day's payloads and compares hashes.

**Depends:** P1, E3, S2, G4 (S3 for the scoreboard A page) · **Size:** M · **Status:** later

---

## P3. Atomic publisher to Azure

**Repository:** trading

**Description:** As the owner, I want each day's pages published to the shared database all at once, with a
current-publication pointer and a run status, so that the dashboard never mixes two days and shows clearly when F&O
data is publishing or stale.

**Context and why:** Design 13.2 (ChatGPT review 25): a `publication_id` per run tied to the source commit and the
cutoff; all pages written and validated in **one transaction** into a history table with unique (`product`,
`page_key`, `publication_id`); `fno.current_publication` advanced in the same transaction; a failed run leaves the
previous publication current with the failed run ID and reason; F&O freshness by the session calendar and run status
("publishing", "stale"), not the stock app's age limit. 13.3: this repository writes only the `fno` schema with its
runtime role (no DDL); the schema is a derived copy, rebuildable from the repository.

**Scope.** In: the `fno` schema's table definitions (migrations run by the migration role, X1), the publisher, run
status, rebuild command. Out: platform roles (X1), the dashboard (W).

**Expected design:** `db/fno/migrations/*.sql` (tables `fno.pages_history`, `fno.current_publication`,
`fno.run_status`; constraints and the unique key); `fno/publish/azure.py` using a Postgres driver with verified TLS
and parameterised queries; credential `FNO_DB_URL` (runtime role) only from the environment (name added to
`fno/constants.py`); command `python -m fno publish push [--date]` and `python -m fno publish rebuild --from <date>`.
Run status rows: `publishing` at start, `published` or `failed (reason)` at the end.

**Acceptance criteria:**
1. A failure injected after half the pages are written leaves the previous publication current and no partial
   publication visible (test against a local Postgres in CI or a container).
2. Two publications of the same commit are idempotent (same `publication_id`, no duplicate rows).
3. The runtime role cannot create, drop or alter tables (test, together with X1).
4. `rebuild` recreates the schema's contents from the repository records with identical payload hashes.
5. Freshness: on a session day after the scheduled publication time without a `published` row, the status reads
   `stale` with the failed run's reason (calendar-aware test).

**Test plan:** integration tests against a disposable Postgres; failure-injection tests.

**Judge verifies:** kills a publish half-way on a test database and checks what the dashboard query returns.

**Depends:** P2, X1, A1 · **Size:** M · **Status:** later

---

## P4. Slack daily message and alerts

**Repository:** trading

**Description:** As the owner, I want one short #fno-desk message after each run and a same-day alert on any failure,
so that I can follow the desk from my phone without reading code.

**Context and why:** Design 13.4: one message per trading day after the run (one line per book: decision, account
value, brake distance; alerts; the dashboard link); a no-trade day still posts; failures post a short alert the same
day; monthly headline numbers. Only channel `C0C89E8QCCD`, only `FNO_SLACK_BOT_TOKEN` or the Slack connector, never
`SLACK_*` or #market-brief; text only; the poster refuses any other channel and any webhook. The old `notify.py`
allowed an environment variable to change the channel (clean-slate design 4b) and was removed. Slack is a summary,
never the record.

**Scope.** In: `DeskReportPoster` behind an interface, message text, alert messages, monthly headline. Out: the data
(P2), the dashboard (W).

**Expected design:** `fno/publish/slack.py`: `SlackPoster` interface; `BotTokenPoster` (Slack `chat.postMessage`, the
channel ID fixed in `config.yaml` `slack.channel_id` and checked against the constant `C0C89E8QCCD`); the token name
`FNO_SLACK_BOT_TOKEN` in `fno/constants.py`; errors redact the token. Message built from P2's `today` and `health`
payloads.

**Acceptance criteria:**
1. Any channel other than `C0C89E8QCCD`, and any webhook URL, is refused (tests).
2. No code path reads a `SLACK_*` variable (test scans the environment access).
3. A no-trade day still produces a message with the reasons; a failed run produces an alert naming the step.
4. Numbers in the message equal the day's payloads.
5. An error message never contains the token (test with a fake failing API).

**Test plan:** tests with a fake Slack API.

**Judge verifies:** compares one posted message with its payloads.

**Depends:** P2 · **Size:** S · **Status:** later

---

## P6. NSE market read models for the Screener and Markets

**Repository:** trading

**Description:** As the owner, I want the India Screener (33) and Markets (34) screens fed from NSE's own daily files,
published by this repository, so that the signed-off screens show real data instead of examples.

**Context and why:** Owner decision (13 Oct 2026, DESK_DECISIONS): exepex/trading publishes NSE's daily market files for
the dashboard. The blocks and their schemas are the dashboard's W11 contract (omenix-dashboard `api/`, catalog marks
them "publisher fno, not published today"). This repository already downloads, verifies and archives NSE files (A1, A9,
A10); it does not yet publish market read models.

**Scope.** In: the India blocks W11 assigns to publisher `fno` (screener summary and stock rows, F&O screener summary and
rows, indices and sectors overview, breadth, movers, index-option rows) built from archived NSE files, validated
against the W11 JSON schemas, and published through a `ReadModelPublisher` interface. Out: US blocks (stock tool),
stock-tool fields, the paper books (P2).

**Expected design:**
- New raw datasets as needed (equity bhavcopy, delivery, index file with P/E, P/B, yield) archived through the A9
  librarian with fingerprints (A10); coverage and manifests like the others.
- `fno/market_read_models/`: one small builder class per block, each a pure function of archived files for one
  session; no network in builders.
- `ReadModelPublisher` interface; first adapter writes the blocks to the Azure `fno` read-model tables with the X1
  publisher role (credential only in environment settings), atomically per session (all blocks or none); a local file
  adapter for tests. Wired only in the composition root.
- Every payload is validated against the W11 schema copied from omenix-dashboard (pinned by contract version and
  SHA-256; a test fails if the pinned copy differs from the dashboard's published version).
- A daily routine after NSE's evening files: fetch, verify, build, validate, publish; alerts to #fno-desk on any
  failure; never publishes a partial session.
- Which version of a file (judge 49, A11): publishing reads NSE's latest version of each archived file (A11's
  revisions); research reads the version available at its decision time (point in time, no look-ahead).

**Acceptance criteria:**
1. For 12 Oct 2026, every built block equals the W11 example payload for India field by field (the examples were made
   from the same NSE files), except fields W11 marks as derived elsewhere.
2. Every payload validates against the pinned W11 schema; a planted extra or missing field fails the run.
3. Publishing is atomic per session: a failure in any block leaves the previous session's blocks unchanged (test with
   a failing adapter).
4. A real publish of 12 Oct to Azure succeeds with the publisher role, and a read with the dashboard role returns the
   same payloads (evidence redacted like X1).
5. New raw datasets are complete in Drive with fingerprints for 2025-10-13 to 2026-10-12 (one year, what the 1Y views
   need), coverage 0 missing, 0 damaged.
6. Code size, lint, imports, tests pass; no US block is built here.

**Judge verifies:** rebuilds 12 Oct from the raw files and compares with the W11 examples; plants a schema break; reads
the published rows with the dashboard role.

**Depends:** W11 (PASS), A9, A10, X1 · **Size:** L · **Status:** done: judge 49 PASS round 2 (13 Oct 2026); criterion 4 met (publish run 38438666957, dashboard-role read-back, response 50 addenda 4-5)

---

## P7. Run status for every publish run

**Repository:** trading

**Description:** As the owner, I want every publish run to leave a status row (started, finished, result, reason), so
that when the dashboard shows F&O data as "stale" it can say why the run failed, not only what is missing.

**Context and why:** Judge 57 (W2): "stale with the reason" names the missing data and when it was due, but not why a
run failed, because no publisher writes a run-status table. P3 named `fno.run_status`; the W11 catalog lists it as the
source of the dashboard's bell (W8). Orchestrator, 13 Oct 2026.

**Scope.** In: the table (a migration the owner runs as `fno_owner`), one row per product and run written by the
publish run at its start and its end, a fixed set of reason codes, the field list for the dashboard's read side.
Out: the dashboard's read (a small W2 follow-up), the bell (W8).

**Expected design:** `db/fno/migrations/002_run_status.sql`; a `RunStatusRecorder` interface with a Postgres adapter
(same verified connection as the publisher) and a local one for tests; `MarketRun` records `running` at the start and
`published`, `failed` (with a reason code) or `skipped` (not a session) at the end. A status write that fails never
hides the run's own result.

**Acceptance criteria:**
1. A successful run leaves one row: `result = published`, `publication_id` set, `finished_at` after `started_at`.
2. Each failure class gives its own reason code (archive, contract, schema, read-back, each database class); a test per
   code.
3. A closed day leaves `result = skipped`, `reason_code = not_a_session`.
4. A second run of the same day adds its own row (one row per run), never changing an earlier one.
5. The runtime role can insert, update and read rows but never delete them, and a finished row never changes; the
   dashboard role can only read (grants in the migration, tested as each role).
6. Size, lint, imports, tests pass.

**Judge verifies:** runs the migration on a throwaway server, a successful and a failing run, and reads the rows.

**Depends:** P6 · **Size:** S · **Status:** done (judge 59 addendum 2 PASS; migration 002 run on Azure by the owner 14 Oct 2026, fno_writer grants read back as expected; claims: reviews/claude/response_66_2026-10-13-p7-p8-p9-publishing.md, addendum P7)

---

## P8. FII/DII cash-market flows for Markets 34

**Repository:** trading

**Description:** As the owner, I want NSE's daily FII/DII cash-market buy and sell values archived and shown in Markets
34's "What did big investors do?".

**Context and why:** Orchestrator, 13 Oct 2026. **Stopped before building (contract):** W11 has a contract for this
block (`Flows`, endpoint `getFlows_india`), but its catalog assigns it to **publisher `stock`, status published**
(`api/schemas/blocks-overview.yaml`: "the stock tool's flows (NSE FII/DII, provisional) and fpi (NSDL) records"). A
second publisher for the same block would make two sources of truth. Needs a decision by the orchestrator or owner:
either W11 moves the block to publisher `fno` (then this story builds the download and the block against it), or the
block stays with the stock tool and only a raw archive here is wanted (research use), or nothing is built.

**Status:** done for the built data and page: judge 66 items 1-3 and addenda 1-2 PASS (contract 2.5 page `flows`, filed-by-session window); live publish read-back at 07:10 IST 14 Oct pending (judge 66 item 4)

**Filing (judge 66 item 4, judge 79):** from 13 Oct each flows copy is archived in its own series
(`nse/flows/fii-dii-cash-by-session`, `nsdl/fpi/fpi-daily-by-session`) under the session it covers, read from the copy.
A session keeps its **first** copy: a later NSE revision of a provisional day is not kept (the price of point in time).
A copy covering a session after the run's day is refused by name; in the publish run's archive step that refusal skips
only that list. The run-dated series (`fii-dii-cash`, `fpi-daily`) is kept and read only for sessions the new series
lacks.

---

## P9. NIFTY option chain read models for screen 32

**Repository:** trading

**Description:** As the owner, I want the option chain screen (32) fed from NSE's daily F&O file, published by this
repository, so that the signed-off screen shows real end-of-day chains.

**Context and why:** W13 froze six India-only chain blocks for publisher exepex/trading (W11 contract 2.3,
`api/schemas/blocks-chain.yaml` and `blocks-chain-history.yaml`, examples `api/examples/blocks-32.json`), "not
published yet". The F&O file is already archived daily (A1, A9); the market run already publishes atomically (P6).

**Scope.** In: the chain blocks W13 defines (underlying, expiries, rows, history, contract history, sources) built from
the archived F&O and index files, validated against the pinned schemas, published in the same publication as P6's
blocks (one pointer, one run, one status). Out: bid and ask, 3 pm quotes (not published yet, as the contract says).

**Acceptance criteria:**
1. For 12 Oct 2026 every built chain block equals the W13 example field by field, or each difference is traced to its
   source.
2. Every payload validates against the pinned schemas; a planted break fails the run.
3. The chain pages publish in the same transaction as P6's, through the same publisher and run status.
4. Size, lint, imports, tests pass.

**Depends:** P6, P7, W13 · **Size:** M · **Status:** done (judge 60 and addendum 1 PASS; W13's page keys adopted, 409825f; claims: response 66, addendum P9)

---

## P10. Home's F&O read models

**Repository:** trading

**Description:** As the owner, I want Home to show the F&O tool's real state now (the three paper books' accounts and
the F&O picks panel), so that Home stops showing examples for F&O while the stock data waits for its own API.

**Context and why:** Owner request through the orchestrator, 13 Oct 2026. W10's contract (omenix-dashboard `api/`)
assigns two Home blocks to publisher `fno`: `FnoBooks` (`/markets/india/fno/books`, feeds "Who trades") and `FnoPicks`
(`/markets/india/fno/picks`, the picks panel). The truth today: every book holds its Rs 5 lakh opening balance with no
fill, and Experiment 1 passed no policy (`research/2026-10-12-experiment-1/results_challenge.json`:
`passing_policies: []`), so no book has an approved strategy and no pick exists.

**Scope.** In: `FnoBooks` (value, profit or loss, approved strategies, risk used and its limit, per book, from the
books' own accounts, E1, and C2's limit) and `FnoPicks` (the honest empty state: `approved` false, a note saying why,
no rows), published in the same publication and run status as P6 and P9. **Out, stopped (contract):** the India market
band (`getIndices`, `getSession`) and the coming-up events, including `fno_expiry` (`getEvents`): W10 marks all three
`x-publisher: stock` for every market. Publishing them here would make two publishers for one block. **Not in the
contract:** a reason code for the empty picks state (W10's `FnoPicks` has only `fno_state.note`).

**Acceptance criteria:**
1. `FnoBooks` shows each book's own account: value = its latest marked equity on or before the session (the books'
   `paper_account_rs` before it opened), `pnl` = value − the account's opening cash, `approved` = the policies the
   latest frozen experiment passed (none), `limit_used` = 0 with no open trade, `limit_max` = the books'
   `open_risk_cap_rs` (Rs 1,50,000; owner, 15 Oct 2026, "2 A": the books have no stress limit, story C5); never example
   values. Once P10 publishes open trades, `limit_used` is the sum of the open positions' maximum losses (C5). The
   dashboard owns the contract wording of `limit_used` and its examples (owner, "contract A"), changed there.
2. `FnoPicks` is the empty state with a note naming the reason (Experiment 1 passed no policy).
3. Both validate against the pinned W10 schemas and publish in the same transaction and run status as P6.
4. A book with an open trade stops the run rather than publish a risk figure this story does not compute.
5. Size, lint, imports, tests pass.

**Depends:** P6, P7, E1, C2 · **Size:** S · **Status:** built criteria PASS (judge 61 and addendum 1; page keys today and risk); contract 2.5/2.6 blocks (India band, expiries, session hours_status) PASS (judge 66 items 1-3, addendum 2); live publish read-back at 07:10 IST 14 Oct pending
