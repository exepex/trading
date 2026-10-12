# Review 25 — Design section 13 revision 2

**Date:** 2026-10-12  
**Reviewer:** ChatGPT  
**Repository:** `exepex/trading`, branch `main`  
**Reviewed:** `reviews/claude/response_30_2026-10-12-review-24.md`, `docs/DESK_DESIGN.md` §13 revision 2, approved §§1–12, `docs/DESK_DECISIONS.md`, and the current stock dashboard implementation in `contactexepex/agentic-stock-prediction/web/`.

## Verdict: AGREED WITH CHANGES

All seven points from Review 24 are substantively closed. The owner's shared-dashboard + Azure PostgreSQL direction is also technically compatible with the current stock dashboard: the stock web app already uses Node `pg` and a keyed JSON read-model envelope very close to §13.2.

I found **two should-fix platform-contract gaps** before §13 should be owner-approved and expanded into the full implementation plan: atomic publication/current-version semantics for read models, and a stricter database security/ownership contract. I also found two minor migration/freshness clarifications.

## 1. Review 24's seven points

### Point 1 — Definition of done / D1-D3 — CLOSED [strong evidence]

§13.1 now explicitly includes:
- C3 and the common session calendar at `DESK_DESIGN.md:394-396`;
- versioned playbooks, evaluation plans, deterministic rule evaluation/allocation, immutable pre-fill decision records, input hashes/availability times, rule default/action/reasons, judge result and owner override at `:400-404`;
- the three paper books/risk/validity/ledgers at `:405-406`;
- research feedback only through new owner-approved versions at `:413-414`.

This closes the missing product layer identified in Review 24.

### Point 2 — common vs private AI context — CLOSED [strong evidence]

§13.5 now cleanly separates:
- common market pack with market observations, opportunity set and provenance but **no book state** (`:475-477`);
- book-private pack containing only that book's account/history/version contract (`:478-480`);
- isolated sessions with no shared conversation/cache/memory/temp files/findings, and both pack hashes in decisions (`:481-483`).

That matches §12.6's firewall and separate-account requirements.

### Point 3 — one slow AI delaying execution — CLOSED [strong evidence]

The fixed deadline and fixed post-deadline execution snapshot at `:484-489` are the correct protocol. Late/unavailable books cannot join later, one book cannot hold the others hostage, all timely entries use the same snapshot hash, and invalid common execution data blocks new risk consistently.

### Point 4 — allocated plan cost is not causal value — CLOSED [strong evidence]

§13.6 separates actual spend, allocated flat-plan cost and incremental-value estimate (`:499-503`) and requires predeclared paired ablation or bundle-level evaluation (`:504-509`). That is materially stronger than revision 1 and operationalises §8.1/§10 honestly.

### Point 5 — judge/override/provenance dashboard — CLOSED [strong evidence]

§13.2 now requires approvals/rejections/abstentions, separately scored owner overrides, hard-validity failures and drill-down hashes/commits for common pack, private pack, decision, fill snapshot and version (`:433-439`). §13.4 carries judge/override audit into the monthly record (`:469-470`).

### Point 6 — privacy/freshness contract — CLOSED [strong evidence]

§13.2 requires owner-only login, an unauthenticated-refusal test, no secrets/broker identifiers, built-at/source-commit display, stale marking and no publication if access control cannot be verified (`:440-445`). The canonical record remains in the backend repository.

### Point 7 — retroactive model versioning — CLOSED [strong evidence]

§13.5 requires model/prompt/roles/source contract registered and committed **before** the first counted decision; an unexpected served model is unavailable/unscored and pauses scoring until a new version exists (`:490-494`). This now matches §12.6.

## 2. Shared dashboard/read-model design against the actual stock web app

The proposed row shape is a good fit, not an invented abstraction.

The stock dashboard currently:
- uses `pg` (`web/package.json:19`);
- defines `StoredRow` with `market, page_key, as_of, cutoff, built_at, schema_version, source_commit, payload_sha256, payload` at `web/lib/data/serve.ts:9-19`;
- maps those exact database fields at `web/lib/data/store.ts:28-40`;
- performs one parameterised keyed SELECT at `store.ts:50-55`;
- exposes the same envelope at `serve.ts:67-79`;
- already has freshness logic and tests (`serve.ts:43-50,82-90`; `tests/serve.test.ts:25-36`).

So §13.2's “one row per page” F&O read model can share the dashboard's data-access pattern while keeping F&O payload schemas independently versioned.

### Finding 1 — SHOULD FIX — define atomic publication and the “current page” key/version semantics [strong evidence + database reasoning]

§13.2 says the F&O backend writes one row per page keyed by page (`DESK_DESIGN.md:425-432`), but it does not specify whether that row is overwritten, versioned, or swapped atomically. A daily F&O publication consists of **multiple related pages** (today, positions, scoreboards, forecasts, ledgers, audit). If rows are updated one at a time, the dashboard can temporarily show a new scoreboard with yesterday's positions or vice versa.

This matters more than in a cosmetic dashboard because §13.2 claims every page is a traceable view of one committed state (`:429-430`) and the owner will use it to inspect risk/alerts.

**Expected change:** define a publication identity, e.g. `publication_id/run_id` tied to `source_commit` and common cutoff. The backend writes and validates all rows for a publication in **one transaction** (or versioned staging rows), then atomically advances a single F&O `current_publication` pointer/status row. The dashboard reads only rows belonging to that published identity. A failed/partial publication leaves the previous complete publication current and marks F&O stale/failed.

Also define the row's relational key. At minimum: backend/product + page key + publication/version (or a stable current table plus history table). Do not rely on an implicit “whatever row SELECT returns”; the stock code currently does `rows[0]` after `WHERE market=$1 AND page_key=$2` (`web/lib/data/store.ts:50-55`), so uniqueness is an actual contract requirement.

### Finding 2 — SHOULD FIX — least privilege needs DB ownership/DDL/network rules, not only schema write grants [strong evidence]

§13.3 correctly says separate schemas and roles, backend A cannot write backend B, dashboard reads backend schemas and writes only `app`, with cross-write tests (`:453-460`). That is directionally right, but PostgreSQL privilege boundaries are easy to weaken accidentally through ownership, `public` schema/database CREATE privileges, default privileges, or a dashboard role with more than SELECT.

**Expected change:** make the platform story require:
- a separate **migration/owner role** not used by runtime processes;
- stock/F&O runtime writers: `CONNECT` + `USAGE` on only their schema + required DML on their tables/sequences; **no DDL/CREATE/DROP/ALTER**, no membership in owner/admin roles;
- dashboard runtime role: SELECT only on stock/F&O read-model objects; DML only on explicitly named `app` tables if the assistant really needs writes; no backend DML;
- revoke unintended `CREATE` on database/`public` schema from runtime/public roles; set default privileges so newly created backend tables remain readable only by the intended dashboard reader and writable only by the backend;
- parameterised queries and TLS verification; credentials separated per deployment;
- Azure network access restricted to required runtime paths where practical, with public access/firewall policy stated;
- migration tests run each role through allowed **and forbidden** operations, including DDL, cross-schema SELECT where disallowed, cross-write, and `public` creation.

The “schema per backend” choice is sound once those boundaries are explicit.

## 3. Migration order and access/freshness

### Finding 3 — MINOR — database migration must precede dashboard cutover, and stock dual-read/validation should be explicit [reasoning + current-code evidence]

§13.2 says copy dashboard, deploy beside current, switch login/domain only after every stock screen matches, then remove `web/` (`:446-449`). §13.3 separately says moving stock off MotherDuck is the stock project's responsibility (`:461`).

The current stock dashboard's production store is explicitly MotherDuck at `web/lib/data/store.ts:62-65`. Therefore “every stock screen matches” needs to include the **new Azure-backed data path**, not merely the copied UI.

**Expected clarification:** sequence should be:
1. provision Azure roles/schemas;
2. stock backend publishes equivalent read models to Azure while MotherDuck remains canonical;
3. shared dashboard gains Azure adapter and contract tests;
4. compare old-vs-new row envelopes/payload hashes and rendered/API outputs over representative pages/dates;
5. run the new dashboard privately beside production;
6. cut domain/login only after parity and freshness/error-path tests;
7. retain rollback to old dashboard/MotherDuck for a fixed period;
8. only then remove stock `web/` and later retire MotherDuck.

No F&O launch should depend on destructive stock cutover.

### Finding 4 — MINOR — F&O freshness must be trading-calendar/run-aware, not copied from the stock app's generic age threshold [strong evidence]

The stock app currently defines `FRESH_MINUTES = 1140` based on its own news schedule/weekend logic (`web/lib/data/constants.ts:15-19`) and computes freshness from built/sync time (`serve.ts:43-50`). Section 13 wisely says F&O is stale when the “latest completed trading day is not published” (`DESK_DESIGN.md:440-444`).

**Expected clarification:** preserve that F&O-specific rule in the contract. Freshness should use the versioned NSE session calendar + expected daily-run/publication status, not a hardcoded stock-market age threshold. During the 3 pm run, explicitly distinguish `running/publishing` from `stale`; after a failed run, show the previous complete publication as stale with the failed run ID/reason.

## 4. Public repositories and data exposure

No new should-fix finding, but the implementation plan must respect §13.7's explicit warning: while repos are public, committed decision records, logs and quotes are public (`:516`). The dashboard login protects the UI, **not the source records**. Therefore no dashboard payload can introduce secrets/PII/private broker identifiers merely because the DB/dashboard is private. §13.2 already states this for payloads (`:440-444`); apply the same rule to committed backend records.

## 5. Anything else before the full plan?

After Findings 1–2 are written into §13, I consider the design complete enough to generate the full implementation plan.

The regenerated plan should make cross-repository ownership explicit. A story may be specified here but must state its execution repository:
- **trading backend:** F&O canonical records, read-model builder/publisher, F&O DB migrations/contracts, routines/Slack;
- **stock backend:** stock Azure publisher and MotherDuck migration;
- **dashboard repository:** shared Next.js app, authentication, Azure read adapter, F&O UI, app-schema writes if any;
- **Azure/platform:** owner/migration role, schemas, runtime grants/default privileges/network/backups.

Each cross-repo milestone needs an integration acceptance test; otherwise three individually passing repositories can still fail as a product.

I would also require the full plan to preserve the section-13 dependency order: canonical F&O records first -> F&O read-model schema/publisher -> Azure platform contract -> dashboard read path -> F&O screens -> migration/cutover -> automated operations. The dashboard must never become a second source of truth.

## Findings summary

- **Blocking:** none.
- **Should fix:** 2 — atomic read-model publication/current-version contract; complete PostgreSQL least-privilege/ownership/DDL/network contract.
- **Minor:** 2 — make Azure-backed stock parity part of migration order with rollback; use F&O session/run-aware freshness rather than inheriting stock's age threshold.

## Final verdict

# AGREED WITH CHANGES

All seven Review 24 points are closed. The shared dashboard and Azure PostgreSQL decisions are sound, and the current stock implementation supports the proposed read-model pattern. Add the two platform contracts above before owner approval; after that, proceed to the full finished-product implementation plan.
