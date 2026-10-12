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
writer, rollback of writes. Out: the stock backend's reads of the inbox (K1 criterion 3 follows this switch).

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

**Depends:** W1-W4, W6, W7, K1 · **Size:** S · **Status:** later

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
3. The stock backend's own reads of the inbox (`company.py import-inbox`, `portfolio.py import-inbox`) read the
   `app` schema after W7's switch (the dashboard-side write migration is W7).

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

**Depends:** W5, W7 · **Size:** S · **Status:** later
