# Response 65: stories P7, P8 and P9 (run status, FII/DII flows, option chain), claims

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
