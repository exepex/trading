# Response 79: P8 flows filed by the session they cover (judge 66 follow-up): builder's claims

Builder session, 14 Oct 2026. Branch `story/p8-flows-by-session`, started from `story/p8-flows-first-day` a20e315 (the
judge passes the two separately). Orchestrator's GO: losing 14 Oct's flows is not acceptable. Judge first; nothing on
`main`.

**Verdict in one line:** every new flows copy is filed under the session it covers, in a new series. Tonight's 21:10 IST
take of 14 Oct therefore lands in `.../by-session/2026/10/14/` and is no longer blocked by the run-dated `14/` copy
(which covers 13 Oct). No existing Drive copy or manifest row is touched.

## 1. Why (strong evidence, response 78)

The run-dated `14/` already holds 13 Oct's values. `SnapshotTaker` keeps an existing copy and never fetches again. NSE
serves only the latest session, so session 14 Oct could never have been archived.

## 2. The design

| Part | What |
|---|---|
| New series (`fno/storage/snapshot_source.py`) | `FiiDiiCashBySessionSource` (`nse/flows/fii-dii-cash-by-session`) and `NsdlFpiDailyBySessionSource` (`nsdl/fpi/fpi-daily-by-session`): the same publishers and URLs, but a folder means the session covered. `first_day` is 13 Oct, the first session the flows history covers. |
| `SessionFiledTaker` (`fno/storage/session_filed_taker.py`) | Fetches, checks, reads the covered session from the copy itself, and files the copy there. It **refuses** a copy covering a session after the run's day (it cannot exist yet), and **keeps the first copy** of a session. |
| Wiring (`fno/storage/wiring.py`) | The two new series replace the old ones in `SNAPSHOT_SOURCES` (what gets taken; the commands are `data-snapshot fii-dii-cash-by-session` and `fpi-daily-by-session`). The old run-dated series stay in `RAW_SOURCES` as `RUN_DATED_FLOWS`: kept, manifested, never taken again. `COVERED_SESSION` (`content_checks.py`) holds each series' session reader. `build_snapshot_taker` returns a `SessionFiledTaker` for these two. |
| Jobs | `flows-download.yml` and the publish run's `DAILY_SNAPSHOTS` call the new names. |
| `FlowsReader` | Reads both series for folders up to D and merges them per session, run-dated first and then by-session, **so a session held by both comes from the by-session series and is counted once**. |

**How the old run-dated series is treated (the orchestrator's question):** it is read only for sessions the by-session
series lacks.
- Today that means 13 Oct. It has no by-session copy because the new series starts tonight, so 13 Oct publishes from
  the run-dated `13/` copy (taken by its own publish run). For later sessions in that series, the latest copy filed on or
  before D wins, as before.
- Its `14/` copy covers 13 Oct, so it can never stand in for 14 Oct. Session 14 Oct comes only from the by-session
  series.

**No look-ahead:** a by-session folder S holds only session S's values, and the reader reads folders up to D only.
Nothing from a session after D can be read. A run-dated copy filed after D is never read for D (unchanged).

## 3. Evidence (`tests/market_read_models/test_flows_by_session.py`, 7 tests; flows-files tests updated)

- **Tonight's case:** with the run-dated `14/` holding 13 Oct's values, a take on 14 Oct of NSE's 14 Oct copy is filed
  under `fii-dii-cash-by-session/2026/10/14/`. The line is "archived", and the old copy is unchanged.
- A copy taken on 14 Oct before NSE's release (still 13 Oct's values) is filed under 13, and leaves 14's folder free.
- A copy covering 14 Oct taken with run day 13 Oct is refused, and nothing is written.
- A session keeps its first copy: a later revised copy is "already archived" and the bytes are unchanged.
- The reader, with both series as archived plus tonight's copy:
  - for 13 Oct it reads 13 Oct only, from the run-dated series, with no problem named;
  - for 14 Oct it reads each session once (13 Oct -1,305.13, 14 Oct -900.00);
  - the by-session NSDL copy of 13 Oct wins over the two run-dated ones.
- A by-session copy gets its row in its own manifest (`fii-dii-cash-by-session.csv`), never in the run-dated one.
- The composition root hands out `SessionFiledTaker` for the two flows datasets and `SnapshotTaker` for the
  reference lists.
- Mutations (`python -B`, caches cleared): **12 of 12 caught**:
  - filed under the run's day again; a later session accepted; the first copy overwritten;
  - the run-dated series winning; either series not read;
  - flows taken by day again in the wiring; the old series dropped from the manifests;
  - a one-day look-ahead; `first_day` back to 14 Oct;
  - the missing-cash check off; problems not stopping the build.

## 4. What the owner or orchestrator should know

- **Deploy timing:** the fix works only if it is on `main` before 21:10 IST today, because the workflow runs from
  `main`. If it is not, run `flows-download` by hand after the merge, before NSE replaces 14 Oct's values (next
  evening).
- **13 Oct's re-publication** (`market-publish` for 2026-10-13) reads the run-dated `13/` copy. That works with
  response 78's branch alone, and with both branches together.
- The run-dated series' two folders stay as they are (owner's rule: never delete in Drive). Its `14/` copy is a
  duplicate of 13 Oct's values, and the reader never uses it for 14 Oct.

## 5. Gates

Full suite, `ruff check fno tests tools`, `ruff format`, `python tools/check_imports.py` and the 350-line limit: in the
commit message and the message to the orchestrator.
