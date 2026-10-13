# Epics X, W and K: the shared platform, the shared dashboard and the stock backend's part

These stories are part of the finished product (design 13.1 item 8, 13.2, 13.3, 13.8) but are **built outside this
repository**. They are specified here so the plan lists every story the product needs; each is implemented and
judged in its own repository, whose rules also apply (the stock tool's CLAUDE.md for `agentic-stock-prediction`).
This repository never writes to another repository. Story template, definition of done and the full story index:
`docs/IMPLEMENTATION_PLAN.md`.

Repositories: `platform` (Azure setup, scripts kept in the dashboard repository under `platform/`), `dashboard`
(the new shared web app; name and GitHub account to be chosen by the owner), `agentic-stock-prediction` (the stock
tool, public, read only from here).

---

## X1. Azure Database for PostgreSQL: server, schemas, roles and tests

**Repository:** platform

**Description:** As the owner, I want one managed Azure Postgres server with a schema and least-privilege role per
backend and a read-only dashboard role, proven by tests, so that no tool can damage another tool's data and a leaked
runtime credential can do little harm.

**Context and why:** Owner decision (12 Oct 2026): Azure Database for PostgreSQL on the owner's subscription, backups
on, replacing MotherDuck (whose tokens cannot be limited to one database; the stock dashboard's inbox token is the
owner's all-privileges token). Design 13.3 (ChatGPT review 25): a migration/owner role per schema never used by
running processes; runtime writers with `CONNECT`, `USAGE` on their schema and only the row operations they need, no
`CREATE`/`DROP`/`ALTER`, no membership in owner or admin roles; dashboard runtime role `SELECT` on the backends'
read-model tables plus named `app` tables; `CREATE` revoked on the database and `public` for runtime roles and
`PUBLIC`; default privileges; verified TLS; one credential per deployment; network access limited where practical.

**Scope.** In: server provisioning (by the owner or a session with the owner's Azure access), schemas `stock`, `fno`,
`app`, roles, grants, default privileges, firewall policy, backups, the role test suite. Out: table contents (P3, K1,
W2).

**Expected design:** `platform/sql/00_roles.sql` ... `platform/sql/40_default_privileges.sql` (idempotent),
`platform/README.md` (server tier, region, backup retention, firewall rules, who holds which credential),
`platform/tests/role_matrix.*`: for each role, a table of allowed and forbidden operations executed against the
server (or a disposable copy), including DDL, cross-schema writes, reads it should not have, and object creation in
`public`. Credentials live in Vercel settings and the routine environments, never in files.

**Acceptance criteria:**
1. The role matrix passes: every allowed operation succeeds and every forbidden one fails, for every role.
2. A runtime role cannot create an object anywhere (tested in `public` and each schema).
3. TLS is required (a non-TLS connection is refused).
4. Backups are enabled with a stated retention; one restore is tested to a scratch server and recorded.
5. The firewall and public-access policy is written down and matches the server's settings (screenshot or CLI
   output recorded, no secrets).

**Test plan:** the role matrix run in CI against a disposable Postgres and once against the real server.

**Judge verifies:** runs the role matrix against the real server with each runtime credential.

**Depends:** owner's Azure access · **Size:** M · **Status:** later

---

## W1. Shared dashboard repository (copy of the stock dashboard)

**Repository:** dashboard

**Description:** As the owner, I want the stock tool's dashboard copied into its own repository and deployed beside
the current one, so that both tools' screens can be developed in one app without touching the live stock dashboard.

**Context and why:** Owner decision: one shared dashboard repository; both tool repositories are backends only. Today
the dashboard is `web/` in `agentic-stock-prediction` (Next.js 15 App Router, TypeScript, React 19, `pg`; Vercel;
owner-only Vercel Authentication; deploys not automatic: `web/vercel.json` sets `deploymentEnabled: false`; about 280
source files). Design 13.2 migration steps 1-8: the old dashboard stays live until parity (W5).

**Scope.** In: the new repository with the app's history if wanted, a new Vercel project, the same login, CI with the
existing tests. Out: changing screens (W2-W4), cutover (W5).

**Expected design:** copy `web/` (and `api/` OpenAPI contracts) into the new repository; keep the stock data path
working against MotherDuck initially; new Vercel project with owner-only authentication; repository-specific constants
(repository names, Slack channel) moved to configuration.

**Acceptance criteria:**
1. The new deployment serves every current stock screen with the same responses as production for a fixed set of
   pages and dates (recorded comparison).
2. The new deployment is reachable only after login (an unauthenticated request is refused: test).
3. The existing tests pass in the new repository's CI.
4. Production (the old dashboard) is unchanged.

**Test plan:** the copied test suite; a response comparison script.

**Judge verifies:** runs the comparison and the unauthenticated-request test.

**Depends:** - · **Size:** M · **Status:** later

---

## W2. Azure read path for F&O: publication-aware reads and contract checks

**Repository:** dashboard

**Description:** As the dashboard developer, I want the app to read each backend's current publication from Azure,
check the data contract version and show freshness per product, so that screens are always consistent, current or
clearly marked stale.

**Context and why:** Design 13.2-13.3: the dashboard reads only the database, never a backend repository; reads only
pages of the current publication (P3); checks the contract version (P1); F&O freshness by session calendar and run
status, not the stock app's fixed `FRESH_MINUTES = 1140`; the stock code today returns `rows[0]` of a keyed SELECT
with no stated uniqueness (`web/lib/data/store.ts`), which the history table's unique key fixes.

**Scope.** In: an Azure `RowStore` for the **F&O** product, publication-aware queries, contract version checks, F&O
freshness, error paths; the stock screens keep reading MotherDuck until W6. Out: F&O screens (W3), stock reads on
Azure (W6, after K1), dashboard writes (W7). Split after ChatGPT review 26 so the F&O launch never waits for the stock
migration.

**Expected design:** a `RowStore` implementation on Azure Postgres with the dashboard runtime role; F&O query: join
`fno.current_publication` to `fno.pages_history` by `publication_id` and `page_key`; contract major version check per
page with a clear "incompatible data version" screen; F&O freshness from `fno.run_status` and the calendar.

**Acceptance criteria:**
1. During a publication, screens show the previous complete publication with "publishing"; after a failed run, the
   previous one with "stale" and the reason (integration test with P3's test database).
2. A payload with an unexpected major version shows the incompatibility screen, never a broken page.
3. Database errors never leak driver text or credentials to the browser (test).

**Test plan:** integration tests against a disposable Postgres.

**Judge verifies:** runs the publishing/stale integration test.

**Depends:** W1, X1, P3 · **Size:** M · **Status:** later

---

## W3. F&O screens

**Repository:** dashboard

**Description:** As the owner, I want F&O screens for today, positions, risk, both scoreboards for all three books,
forecasts, costs, the judge and the evidence, so that I can compare the three strategies from every angle on my phone.

**Context and why:** Design 13.2 (screens list), 12.5 (all three books on both scoreboards with every detail; never
merged into one "AI beats rules" claim), 13.6 (allocated AI cost labelled "not a bill"), 7 (overrides scored apart).
Each screen shows built-at time and source commit and "paper trading only, not advice"; never a real-order
instruction.

**Scope.** In: `/fno` screens reading P1 pages via W2: Today, Positions, Risk, Scoreboard A, Scoreboard B, Forecasts,
Costs and ledgers, Judge and overrides, Evidence drill-down, Data health, Versions and segments. Out: any input that
changes F&O data (the dashboard writes only its `app` tables).

**Expected design:** pages under `app/(cockpit)/fno/...` reusing the shared components (charts, tables, shell);
phone-friendly; scoreboards A and B on separate screens with the labels of 12.5; pilot evidence shown apart.

**Acceptance criteria:**
1. Every field of every P1 page is shown somewhere (a test walks the schema and the rendered output for a fixture
   publication).
2. Scoreboards A and B are never combined in one figure or headline (test).
3. Every screen shows built-at time, source commit, the paper-only notice and the freshness status.
4. Screens render on a phone-width viewport without horizontal scrolling (visual test).

**Test plan:** component and page tests with fixture publications; a phone-width screenshot test.

**Judge verifies:** walks every screen with one real publication and spot-checks five numbers against the repository
records.

**Depends:** W2, P1 · **Size:** L · **Status:** later

---

## W4. Access and freshness contract tests

**Repository:** dashboard

**Description:** As the owner, I want automated proof that F&O screens and data are reachable only after my login and
that stale data is always marked, so that privacy and freshness are tested facts, not assumptions.

**Context and why:** Design 13.2 access and freshness contract (ChatGPT reviews 24-25): an unauthenticated request is
refused (test); no secret, credential or broker identifier in any payload; built-at time and source commit shown;
stale marking; if access control cannot be verified, the screens are not published. The stock dashboard also exposes
`/slack/*`, `/mcp` (owner GitHub login) and a public token-hashed `/brief/...` page; F&O must add no public route.

**Scope.** In: tests run in CI and against the deployment after each release. Out: the login provider itself.

**Expected design:** a test suite that requests every F&O route and API without a session (expects refusal), scans
payloads for secret patterns, and checks the stale and publishing states on a test database; run after each deployment.

**Acceptance criteria:**
1. Every F&O route and API refuses an unauthenticated request.
2. No F&O route is public (the route list is compared with an allow-list containing none).
3. Secret-pattern scan of a full publication finds nothing.
4. A deployment whose access test fails is not promoted (CI gate).

**Test plan:** the suite itself, in CI and post-deploy.

**Judge verifies:** runs the suite against the live deployment.

**Depends:** W2, W3 · **Size:** S · **Status:** later

---

## W6. Stock reads on Azure and parity

**Repository:** dashboard

**Description:** As the owner, I want the stock screens to read the stock tool's Azure publications and be proven
equal to their MotherDuck versions, so that the stock dashboard can move to Azure without losing a screen.

**Context and why:** Design 13.2 migration steps 2-4; split from W2 after ChatGPT review 26 (W2's stock-parity check
needed K1, scheduled later). The stock app reads one JSON row per page (`web/lib/data/store.ts`, `rows[0]` of a keyed
SELECT); on Azure it reads the current publication (K1 uses P3's pattern).

**Scope.** In: the stock `RowStore` on Azure with the dashboard role, a switch per environment, the parity comparison.
Out: dashboard writes (W7), cutover (W5).

**Expected design:** an Azure `RowStore` for the stock product reading `stock` current publications; a configuration
switch so the private beside-production deployment reads Azure while production keeps MotherDuck; a parity script
comparing envelopes, payload hashes and API outputs over a fixed set of pages and dates.

**Acceptance criteria:**
1. For the comparison set, Azure and MotherDuck responses are identical (payload hashes and API outputs).
2. Stock freshness keeps its own rule (`FRESH_MINUTES` logic) unchanged.
3. A failed or partial stock publication shows the previous complete one (K1's atomic pattern).

**Test plan:** parity script; integration tests against a disposable Postgres.

**Judge verifies:** runs the parity script.

**Depends:** W2, K1 · **Size:** M · **Status:** later

---

## W7. Dashboard writes on Azure (inbox, assistant and control state)

**Repository:** dashboard

**Description:** As the owner, I want the dashboard's own writes (inbox requests, command log, assistant
conversations and any control state) moved from MotherDuck to the Azure `app` schema with their history, so that
nothing the dashboard writes is lost or split between two stores.

**Context and why:** ChatGPT review 26: the stock dashboard writes live data to MotherDuck's inbox database
(`web/lib/tools/motherduck.ts`, inbox writes; `web/lib/assistant/store.ts` and `web/lib/assistant/sql.ts`, assistant
conversations), which is **not** derived from any repository and cannot be rebuilt (`docs/ARCHITECTURE.md` of the
stock tool). The read-model migration (K1, W6) does not cover these writers. K2 later requires no MotherDuck
reference.

**Scope.** In: Azure write adapters for every dashboard writer, the `app` schema tables (migrations by its owner role,
X1), SQL dialect changes, history migration, identity and authorisation of writes, idempotency, the switch to one
writer, rollback of writes. Out: the stock backend's reads of the inbox (K3, after this switch).

**Expected design:** `app` tables mirroring the inbox and assistant stores; Azure implementations of the inbox and
conversation stores behind their existing interfaces; a migration script copying history with counts and hashes; a
cutover flag so exactly one store accepts writes at any time; dual-read during verification; a rollback procedure that
copies writes made after the switch back if the cutover is reversed.

**Acceptance criteria:**
1. History copied: row counts and content hashes match per table.
2. At any time exactly one store accepts writes (test toggling the flag under concurrent writes; no write lost or
   duplicated, idempotency keys).
3. Every writer in the dashboard code uses the Azure implementation after the switch (search for MotherDuck writers
   finds none).
4. A rollback rehearsal returns post-switch writes to the old store with matching counts.
5. The dashboard role can write only the named `app` tables (X1 matrix).

**Test plan:** migration and concurrency tests against a disposable Postgres; rollback rehearsal.

**Judge verifies:** runs the count and hash comparison and reads the rollback rehearsal record.

**Depends:** W1, X1 · **Size:** M · **Status:** later

---

## W5. Cutover and rollback

**Repository:** dashboard (with `agentic-stock-prediction`)

**Description:** As the owner, I want my login and domain moved to the shared dashboard only after every stock screen
matches and the tests pass, with a fixed rollback period, so that the stock dashboard never breaks during the move.

**Context and why:** Design 13.2 migration steps 5-8: run privately beside production; switch login and domain only
after parity, freshness and error-path tests; rollback to the old dashboard and MotherDuck available for a fixed
period; then remove `web/` from the stock repository and retire MotherDuck later. No F&O launch depends on this
cutover (F&O screens can run on the new deployment before it).

**Scope.** In: the cutover checklist, the switch, the rollback period, the removal of `web/`. Out: MotherDuck
retirement (K2).

**Expected design:** `platform/CUTOVER.md` checklist with recorded evidence per step; rollback = switching the domain
back (tested once before the real switch); rollback period fixed in the checklist (proposed 14 days).

**Acceptance criteria:**
1. Every checklist item has recorded evidence before the switch (parity comparison, W4 suite, error-path tests).
2. A rollback rehearsal is recorded before the switch.
3. `web/` is removed from the stock repository only after the rollback period ends without a rollback.

**Test plan:** the checklist; the rehearsal.

**Judge verifies:** reads the checklist evidence and the rehearsal record.

**Depends:** W1-W4, W6, W7, K1, K3 · **Size:** S · **Status:** later

---

## K1. Stock backend publishes to Azure (dual publication and parity)

**Repository:** agentic-stock-prediction

**Description:** As the owner, I want the stock tool to publish its read models to Azure as well as MotherDuck, with
an automated parity check, so that the shared dashboard can switch to Azure without losing a single stock screen.

**Context and why:** Design 13.2 migration step 2 and 4; 13.3. Today `scripts/warehouse_sync.py` writes MotherDuck's
`rm` tables (one JSON payload per page) from the committed `data/` folder, which stays the source of truth
(`config/warehouse.yaml`, `docs/ARCHITECTURE.md`). The dashboard's inbox and assistant log (`market_brief_inbox`) are
not derived and must be migrated to the `app` schema with their history.

**Scope.** In: an Azure writer for the `stock` schema using the stock runtime role, the publication pattern (P3's
design: atomic publication, current pointer), parity comparison, inbox migration plan. Out: removing MotherDuck (K2).

**Expected design:** decided in the stock repository under its own rules; this specification requires only:
publication in one transaction with a current pointer; parity of payload hashes between MotherDuck and Azure for every
page on a set of dates; the inbox copied with row counts and hashes matched.

**Acceptance criteria:**
1. For a comparison set of pages and dates, Azure and MotherDuck payload hashes are identical.
2. The stock runtime role can write only the `stock` schema (X1 matrix).
(The stock backend's own inbox readers move in K3, after W7.)

**Test plan:** parity script; role matrix.

**Judge verifies:** runs the parity script.

**Depends:** X1 · **Size:** M · **Status:** later

---

## K2. Retire MotherDuck

**Repository:** agentic-stock-prediction

**Description:** As the owner, I want MotherDuck switched off after the rollback period, so that one data store
remains and no unused credential stays alive.

**Context and why:** Design 13.2 step 8; MotherDuck's broad tokens are a security weakness; keeping two stores in sync
indefinitely is a reliability risk.

**Scope.** In: removing MotherDuck writes, reads, tokens and docs from the stock tool; revoking tokens. Out: data
(the repository stays the source of truth).

**Acceptance criteria:**
1. No code or routine references MotherDuck (search) and the tests pass.
2. All MotherDuck tokens are revoked (recorded by the owner, no secrets in files).
3. The Azure data can be rebuilt from the repository (rebuild run recorded).

**Test plan:** search and test run; rebuild run.

**Judge verifies:** searches the repository and reads the revocation record.

**Depends:** W5, W7, K3 · **Size:** S · **Status:** later

---

## K3. Stock backend's inbox readers switch to Azure

**Repository:** agentic-stock-prediction

**Description:** As the owner, I want the stock tool's routines that read the dashboard inbox to read the Azure `app`
schema after the dashboard's write switch, so that requests I make on the dashboard keep reaching the stock tool.

**Context and why:** The stock tool's post-close routine imports inbox requests and paper-portfolio changes
(`company.py import-inbox`, `portfolio.py import-inbox`, per `routine/POSTCLOSE_PROMPT.md`) from MotherDuck's inbox
database today. W7 moves the dashboard's writes to Azure; without this story the stock tool would read an inbox that no
longer receives anything. Split out of K1 after ChatGPT review 27 (K1 is the read-model publisher; this is app state).

**Scope.** In: the stock tool's inbox readers on Azure with a read-only grant on the named `app` tables (X1), the switch
timed with W7, rollback. Out: the dashboard's writers (W7).

**Expected design:** decided in the stock repository under its own rules; this specification requires: the readers
use a dedicated least-privilege credential (read on the inbox tables, plus the "imported" marking if the design keeps
one, granted explicitly in X1); they switch in the same window as W7's one-writer switch; a rehearsal shows no request
lost or imported twice.

**Acceptance criteria:**
1. A request written on the dashboard after W7's switch is imported exactly once by the next stock routine (test on
   the disposable server and once for real).
2. The reader credential cannot write anything else (X1 matrix row).
3. A rollback rehearsal (W7's) also returns the readers to the old store without loss or duplicates.

**Test plan:** integration test on the disposable server; the rehearsal.

**Judge verifies:** reads the rehearsal record and the exactly-once test.

**Depends:** W7, X1 · **Size:** S · **Status:** later


---

## W8. The signed-off app frame in the real app

**Repository:** dashboard

**Description:** As the owner, I want the app frame I signed off (mockup `design/mockups/30-shell`, 13 Oct 2026) to be the
real frame of the Omenix app, so that every screen, old and new, sits inside it and the platform looks and behaves
the way I approved.

**Context and why:** The owner signed off 30-shell on 13 Oct 2026; its `notes.md` is the frozen data contract (fields,
units, freshness, publisher per element). The frame comprises the top bar with the one search box, the India/US switch,
the market open/closed chip and the manual trading lock, the navigation rail, the "Today's buy picks" panel, the right
drawer with the order window, and the phone bottom tabs. The app today (`web/`, Next.js 15) still has the old
cockpit navigation. Backends do not publish the new read models yet (W2, W6, P stories), so the frame reads through
an interface with a fixture adapter built from the same example records the mockup uses; real adapters plug in later
without touching components (design for change).

**Scope.** In:
- the frame components in `web/`, built from the design system only;
- typed contract types for 30's elements and a `ShellData` interface, with a fixture adapter;
- search over the fixture instruments, including option codes;
- the market status chip and the lock rule (the session times come through the interface);
- the order window as a preview (estimates, checks, the lock), with no order submission;
- the existing pages working inside the frame.

Out:
- submitting paper orders (it needs the Manual account and its store, a later story);
- real backend reads (W2, W6);
- new screens.

**Expected design:** small components (each file under 350 lines); `web/lib/shell/contract.ts` (types from 30's
`notes.md`), `web/lib/shell/source.ts` (interface), `web/lib/shell/fixture-source.ts` (adapter), wiring in one place;
no SQL or vendor SDK in components; Buy always green and Sell always red, words always shown; F&O absent in the US
market.

**Acceptance criteria:**
1. Every page of the app renders inside the frame at 390, 768, 1280 and 1680 px; the running-app harness
   (`web/tests/ui/harness.mjs`, the same checks as `design/system/check_page.js`, which only opens files) reports no
   console errors, no request off the app's origin and no horizontal overflow (corrected 13 Oct 2026, W8 builder's
   finding).
2. The frame matches the signed-off mockup: a side-by-side screenshot comparison at 1280 and 390 px for the
   default, dark, US and closed-market states, committed with the claims; any visible difference is listed and
   explained.
3. Search finds a stock by name, by ticker and an option by its NSE code (e.g. `NIFTY26OCT22800CE`), and in the US
   market finds no F&O instrument (tests).
4. While the market is closed every manual Buy and Sell control is disabled with the reason, by one rule (test over
   search results, picks, hover card and order window).
5. Components import only the `ShellData` interface, never the fixture adapter or a data client (an import-graph
   test enforces it); swapping the adapter is one line in the wiring.
6. The order window shows estimates labelled as estimates, names the snapshot or price check the fill would use,
   and has no submit path to any backend (test).
7. `node tools/check_code_size.mjs`, typecheck, all existing tests (303 or more) and the build pass; no regression in
   the existing pages' tests.

**Test plan:** unit tests for search, the lock rule, the contract adapter; an import-graph test; the screenshot
comparison; check_page on the running app.

**Judge verifies:** runs the app, opens three old pages and Home inside the frame at 390 and 1280 px, compares with
the mockup screenshots, plants a component import of the fixture adapter and confirms the test fails.

**Depends:** W1 (done in practice: the repository exists and builds) · **Size:** L · **Status:** next

---

## W9. The signed-off Home screen in the real app

**Repository:** dashboard

**Description:** As the owner, I want the Home screen I signed off (mockup `design/mockups/31-dashboard`, 13 Oct 2026)
in the real app, reading through the same kind of interface, so that the backends can later fill it with real data
without any change to the screen.

**Context and why:** 31's `notes.md` is the frozen Home contract (signed off as of commit e8cd360). W8 provides the
frame.

**Scope.** In: Home's sections in the signed-off order; typed contract and `HomeData` interface with a fixture adapter;
honest empty states ("no approved strategy yet", "no hybrid strategy yet"); group totals per the owner's exception
(never across groups, markets or currencies). Out: real reads (W2, W6), paper order submission.

**Acceptance criteria:**
1. Home renders every state of the mockup's gallery that the fixture data covers, at 390 to 1680 px, with
   check_page clean.
2. The screen matches the signed-off mockup (side-by-side screenshots, differences listed).
3. Components depend only on `HomeData`; an import-graph test enforces it.
4. No figure adds numbers across groups, markets or currencies, except the owner's per-group totals (test over the
   rendered numbers against the fixture).
5. No screen names an AI model (owner rule): one dashboard display-name rule maps backend strategy names to their
   approach (Rule-based, Hybrid, AI team); a test renders every fixture state and finds no model name (e.g. Opus,
   Sonnet, Haiku, GPT, Gemini). Added 13 Oct 2026 after W8 judge 19 found "AI combined (Opus)" in stock payload data.
6. Code size, typecheck, tests and build pass.

**Test plan:** contract and rendering tests; screenshot comparison; check_page.

**Judge verifies:** compares screenshots with the mockup; checks the no-merge test with a planted cross-currency sum.

**Depends:** W8 · **Size:** M · **Status:** later

---

## W10. API contract and data catalog for the frame and Home (small independent endpoints)

**Repository:** dashboard

**Description:** As the owner, I want the signed-off frame (30-shell) and Home (31-dashboard) turned into a fixed API
contract made of many small endpoints, one per independent block, plus a data catalog naming where every field comes
from, so that the screen loads its blocks in parallel and both backends know exactly what to publish.

**Context and why:** Owner, 13 Oct 2026: "we don't need to build one single API ... multiple small APIs which could
populate the screen in parallel instead of a big bulky API call. many blocks and sections are independent". The
signed-off contracts are the two mockups' `notes.md` (frozen). The repository's `api/` already holds an OpenAPI 3.1
contract with a per-page layout (`api/paths/<page>.yaml`, `api/schemas/<page>.yaml`, shared parts in `openapi.yaml`,
`api/README.md`); the old Home payload (`api/paths/home.yaml`) predates the new design.

**Scope.** In: one endpoint per independent block of the frame (for example search, market status, index strip,
notifications, picks panel) and of Home (each section), each with its own schema, `ReadModelMeta` (as-of, source,
freshness), error and empty states, cache and freshness rules; a data catalog (`api/catalog/home.md` or similar)
mapping every field to its publisher (stock tool, F&O tool, dashboard), its read model or table, its unit, freshness
and the story that will publish it; the old Home endpoint marked superseded. Out: implementing endpoints (W8, W9,
W2, W6, P stories); changing the signed-off mockups.

**Acceptance criteria:**
1. Every element in the two signed-off `notes.md` contracts maps to exactly one endpoint field; a check lists any
   element without an endpoint or any endpoint field without an element (zero both ways).
2. Blocks that the screen shows independently have independent endpoints; no endpoint returns data for two
   independent sections; each endpoint states which blocks it feeds.
3. The bundled OpenAPI document validates, and every schema has an example taken from the mockups' data.
4. The data catalog names, for every field, publisher, source read model or table, unit, freshness and the story
   that publishes it; fields no backend publishes yet are marked `x-status: planned` with that story.
5. The contract honours the screen rules: F&O fields absent for the US market (not null), no field sums across
   accounts or currencies except the owner's per-group totals, as-of time on every price.
6. The repository's checks pass (code size, typecheck, tests, build).

**Test plan:** a mapping check script (elements versus endpoint fields), OpenAPI validation, example validation.

**Judge verifies:** reviews the mockups, the contract and the catalog together: picks 10 random screen elements and
traces each to its endpoint field and its publisher; checks the independence of endpoints against the screen layout.

**Depends:** sign-off of 30-shell and 31-dashboard (13 Oct 2026) · **Size:** M · **Status:** done (judge passed, `reviews/judge/judge_17_w10_api_contract.md`; omenix-dashboard 7aa81a3)

---

## W11. API contract and data catalog for the Screener and Markets (small independent endpoints)

**Repository:** omenix-dashboard

**Description:** As the frontend engineer and the data engineer, I want every block of the signed-off Screener (33)
and Markets (34) screens served by a small independent endpoint with a validated example and a catalog row, so that
each backend knows exactly what to publish and the screens never invent data.

**Context and why:** The owner signed off 33 and 34 on 13 Oct 2026; their `notes.md` are frozen contracts. Same shape as
W10 (judge 17). Written 13 Oct 2026 after the build (judge 27 minor: no story text existed).

**Acceptance criteria:**
1. Every element of 33 and 34 `notes.md` maps to exactly one block endpoint (OpenAPI 3.1) with a validated Mock example;
   zero gaps both ways; `notes.md` unchanged.
2. Shared endpoints (e.g. `/events`) have ONE source fixture; each screen's example is derived from it by a documented
   query (kinds, limit), and a test fails if two examples disagree on the same dates.
3. F&O and India-only fields are absent in the US by schema (separate US variants, no extra properties), proven by
   plants for every F&O and India-only key.
4. Every figure that depends on history length states its coverage; a period total not fully covered is null and the
   screen rule shows "—" (plant: a 1M flows total from 5 days fails).
5. The catalog lists source, owner story, freshness and "Published today?" for every leaf; blocks no backend publishes
   are named plainly with the proposed publishing story.
6. Contract changes are additive only (Home's W9 fixture unchanged or regenerated by sync with tests green); code size,
   typecheck, tests, build and the api-contract CI pass.

**Judge verifies:** reviews mockups, contract and catalog together; plants an F&O key in a US payload and a conflicting
calendar example.

**Depends:** W10, owner sign-off of 33 and 34 · **Size:** M · **Status:** done: judge 35 PASS (13 Oct 2026)

---

## W12. Screener and Markets in the real app

**Repository:** omenix-dashboard

**Description:** As the owner, I want the signed-off Screener (33) and Markets (34) screens in the real app, reading only
their W11 blocks, so that they look exactly as signed off and switch from examples to real data with one wiring line.

**Acceptance criteria:**
1. Every gallery state of 33 and 34 that the W11 examples cover renders at 390 to 1680 px; side-by-side screenshots;
   differences listed.
2. Components depend only on the W11 typed block contracts; the import-graph test (W8 resolver, transitive) enforces it.
3. DOM assertions compare rendered rows and figures with their own source fields (data-src, as W9), incl. breadth
   counts, movers and flows; a flows period without full coverage shows "—" with the coverage text.
4. F&O and India-only elements are absent (not empty) in the US; a harness case proves it.
5. No model or vendor name on any screen (W9 detector gate); Buy/Sell only for followed companies, grey otherwise with
   the reason.
6. Code size, typecheck, tests, build and the UI harness pass in CI.

**Depends:** W8, W9, W11 · **Size:** L · **Status:** doing

---

## W13. API contract and data catalog for the option chain (32)

**Repository:** omenix-dashboard

**Description:** As in W10 and W11, for the signed-off option chain (32): small independent block endpoints, validated
examples from its data.json, catalog rows (publisher exepex/trading), India only.

**Acceptance criteria:** W11's criteria 1-6 applied to 32 (one fixture per shared endpoint, US absence by schema,
coverage on history-dependent fields, additive-only changes, checks green).

**Depends:** W11, owner sign-off of 32 · **Size:** M · **Status:** done: judge 38 PASS (13 Oct 2026); minors in progress

---

## K4. Stock backend publishes one read model per Home and frame block

**Repository:** agentic-stock-prediction (written there by the stock tool's own sessions; this repository never writes
to it)

**Description:** As the owner, I want the stock tool to publish one small read model per block of the signed-off frame
and Home, matching the dashboard's W10 contract, so that each block loads on its own.

**Context and why:** W10 (omenix-dashboard `api/`, commit 7aa81a3) fixed 23 small endpoints. Most of the stock-side
fields are `x-status: planned` with this story as their publisher (`api/catalog/stories.yaml`, "K4-proposed"). Until
it exists, the dashboard's stock routes project the same fields from today's rows (`x-read-model: interim`).

**Acceptance criteria:**
1. Every stock-published field of the W10 catalog is in a read model, with the contract's names, units and as-of time.
2. The dashboard's contract check runs green against the published rows.
3. The stock tool's new hybrid family and "AI team" (owner, 13 Oct 2026) appear under those names, never a model name.

**Depends:** W10 · **Size:** L · **Status:** later (the owner gives it to the stock tool's sessions)

---

## P5. F&O read models for the frame: contracts, quotes, order rules and books

**Repository:** trading

**Description:** As the owner, I want the F&O tool to publish the frame's F&O blocks (contract search, contract
details with quotes, order rules with charges and limits, books, picks), so that the order window and the Home F&O lines
show real F&O data.

**Context and why:** W10's contract puts these under `/api/v1/markets/india/fno/*` ("P1-extension-proposed"). P1's
page list has none of them.

**Acceptance criteria:**
1. Each F&O endpoint of the W10 catalog has its read model, with the contract's fields, units and as-of time;
   quotes come only from the 3 pm snapshot and are labelled as such.
2. The dashboard's contract check runs green on the published payloads.
3. US markets have no F&O payload at all.

**Depends:** W10, P1, A4 · **Size:** M · **Status:** later

---

## MA1. The Manual paper account (the owner's own paper trades)

**Repository:** dashboard (with an `app` table on Azure)

**Description:** As the owner, I want my own paper account (India Rs 5 lakh, US $5,000) to accept my paper orders from
the order window, fill them only from valid quotes, and keep cash, positions and history, so that my own trades sit
beside the strategy books and are never part of their scoreboards.

**Context and why:** PLATFORM_DESIGN.md's order window; W10 names this store "MA1-proposed"; W8 builds the order window
as a preview only. Fills follow the honest rules: stocks at the stock tool's next price check, F&O at the next valid
3 pm snapshot, refused where no executable quote exists, and every limit checked before confirming.

**Acceptance criteria:**
1. An order is accepted only while the market is open and every limit passes; otherwise it is refused with the
   reason (tests).
2. Fills use only the next valid quote named in the order window; an F&O order without an executable quote is
   refused (tests).
3. The account never mixes with strategy books or scoreboards, and INR and USD never sum (tests).
4. Every write is idempotent and only the dashboard role can write the account's `app` tables (X1 role matrix
   extended).

**Depends:** W8, X1, W7 · **Size:** L · **Status:** later
