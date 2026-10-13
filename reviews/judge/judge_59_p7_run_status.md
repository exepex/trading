# Judge 59: story P7, run status for every publish run

Date: 13 Oct 2026 (UTC). Claims: `reviews/claude/response_66_2026-10-13-p7-p8-p9-publishing.md`, addendum P7.

## Verdict: FAIL, one must-fix (small, and cheap now because the owner has not run migration 002 yet)

The database lets the runtime role rewrite a finished row. Criterion 5 says "a finished row never changes ... (grants
in the migration, tested as each role)". Only the Python adapter's `where ... result = 'running'` stops it; the
migration's grants do not.

## Per criterion

| # | Criterion | My check | Result |
|---|---|---|---|
| 1 | A successful run leaves one row, published, publication ID set, finished after started | Tests pass (106 in `tests/market_read_models`, none skipped: the PostgreSQL tests ran on local binaries) | MET |
| 2 | Each failure class has its own reason code, a test per code | `test_each_failure_leaves_its_reason_code_and_the_alerted_line` plus the contract-copy test; the table's check list equals the code list | MET |
| 3 | A closed day leaves skipped / not_a_session | Test | MET |
| 4 | A second run of the same day adds its own row, never changing an earlier one | Test; the primary key is (product, run_id) and the run ID includes the attempt | MET |
| 5 | Runtime role can insert, update, read but never delete; a finished row never changes; dashboard role only reads; tested as each role | **My run on a throwaway PostgreSQL 16 with 001 and 002:** as `fno_writer` I inserted a row, finished it as `published`, then ran `update fno.run_status set result='failed', reason_code='crashed', reason='rewritten' where run_id='gh-1-1' and result='published'`: **1 row changed**, the row now reads `failed / rewritten`. Delete as `fno_writer`: refused (InsufficientPrivilege). `dashboard_app`: reads, update refused | **PARTLY** |
| 6 | Size, lint, imports, tests | Files under 350 lines; full suite at ea4459f: 1,702 passed; ruff and imports clean (my run) | MET |

**Why it matters (risk manager):** the run status is what the dashboard shows as the reason for stale data. A bug, a
re-run with a reused run ID or a wrong manual command under the runtime role can silently turn a failure into a
success after the fact. The claim "a finished row never changes" is tested only through the adapter
(`test_postgres_rows_written_by_the_publisher_role...` calls `status.finish` twice), not as the role.

**Fix (reasoning only, the builder's choice):** in 002, a `before update` trigger that refuses any update when
`old.result <> 'running'`, or allow updates only through a narrow function. Then add a test that runs a raw `update`
as `fno_writer` on a finished row and expects a refusal.

## Claims vs reality

| Claim | Reality |
|---|---|
| "a finished row never changes" (tested) | True for the adapter only; false for the role (above) |
| `fno_writer` cannot delete; `dashboard_app` read-only | Confirmed on my throwaway server |
| Unknown code or failure without code refused | Matches the table checks I read |
| A status write failure never changes the run's result | Test passes; I did not plant it |
| Before the migration runs, publishes still work with one "NOT recorded" line | Reasoning plus test with an unreachable store; not tested against a real missing table |

## Project rules

Migration runs as `fno_owner` from the owner's Mac (no secret in files); composition root `fno/market_read_models/wiring.py`
listed in CLAUDE.md; no secret, host or user in `reason` (db_errors). I did not connect to Azure.
