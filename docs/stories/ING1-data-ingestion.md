# Story ING1: data ingestion as a separate part (design)

**Lane 1, two judges (R and S).** **Design only: no code, config, workflow or routine changes in this story.**
**Builder:** session_01DVGq1ZcLEd4ZfXCqkm23en (Sonnet). **Orchestrator:** session_01Mt6dcBU5kp2htdPN2KmiZH.
**Status:** story text for the judges. It links the stories it touches and does not restate them: O14
(`O14-retry-policy.md`), GW1 (`GW1-groww-rate-guard.md`, `GW1a-groww-guard-core.md`), DR1
(`DR1-design-staging.md`), O9 (`O9-data-to-drive.md`), O10 (`O10-capture-health.md`), O1 (`O1-daily-run.md`),
A16 (`A16-intraday-quote-recorder.md`, `A16-owner-checklist.md`), A22 (`A22-preopen-data.md`), A4 stories
(`A-data-foundation.md`), G10, STAB1 (another builder; its files are untouched here).

## 0. Owner summary (plain words)

**What you asked for (25 Oct):** every data capture (the 15-minute marks, the live feed, the 3 pm quotes, NSE files,
anything) is its own part, apart from the system that forecasts and decides. The system only reads what was
captured. Each capture has its own schedule, retry and failure rules, so one failing never touches another.

**What is true today (checked in the code, section 3):**
1. Some captures are already apart and work as you want: the 15-minute marks (own routine), the 08:36 pre-open (own
   routine) and about 16 NSE, cue and reference-data workflows on GitHub Actions.
2. The biggest mix is the **14:05 daily run**: one program starts the 3 pm quotes, the v4-window quotes, the candle
   catch-up and the close reads, and also runs the forecasts, the desk, the school, the card and the score steps. They
   share one thread, one commit step, one result line, one exit code, one switch (`v4_pack`) and one clock order.
3. The morning and evening forecast routines also hold capture work (closes archive, closes read, bhavcopy, OI,
   FII/DII, the closes certification). **If you switch those routines off as "forecasting", that capture work stops
   with them** (evidence M8). Use STAB1's switch inside the commands, or edit the prompts; do not delete the routines
   yet.
4. Capture code imports forecast code in three places (the v4 expiry rule, the v4 cutoff flag, the alert reporter).
5. Two writers already capture NSE's 3 pm chain (a workflow and the daily run's `nse` part).
6. The E3 desk starts a Groww capture itself at 15:15 (the execution snapshot). That is the only place where the
   system starts a capture.

**The target (10 lines):** section 4.0.

**The plan:** ten small steps, each judged; new beside old only where it is safe (public NSE data); for Groww's live
captures no two writers ever run at once (strong evidence: two takers lost 74-87 of 224 quotes on 16 Oct), so those
are swapped one at a time with a rollback key and the old path stays until five clean real sessions. Every removal of
an old path has two judges. Nothing is removed in this story.

**Your decisions needed:** three (section 9). **What you must create or change in routines:** section 7.

## 1. The owner's words and the rules this design keeps

Owner, 25 Oct 2026 (`conversations/2026-10-25.md`, "data ingestion as a separate part"): the full quote is in the
log; its parts are: captures "separate ... whether it is live data feed or 15 minutes or any other capture"; "the
system uses that ingested data"; "whether we create GitHub work actions workflow, or ... a scheduled routine, or any
other scheduled job"; "different retry mechanisms and different failure policies". Also 25 Oct: "Data capture will
never stop"; "every removal and cleanup needs to be reviewed thoroughly by a judge and independent judge"; "whether it
takes another 2 weeks". The owner already decided the same split on 13 Oct (`DESK_DECISIONS.md` lines 55-56: "fetch and
reason are separate"); ING1 finishes it.

Rules kept (not redesigned here): research and paper only, no orders; no secret in a file or chat; Drive write-once
with SHA-256 receipts (O9); the CLAUDE.md market-hours rule on hand-run Groww commands and its failed-routine
exception; GW1's 10 a second, 300 a minute, 150 sign-ins a day and its quiet windows; O14's exponential backoff, at
most 5 retries, then escalate; the 350-line limit; one owning document per functionality.

## 2. Overlaps with WORK_REGISTER (read on `origin/main` at `dba473c69`) and the boundary with each

| Row (owner session) | What it owns | ING1's boundary |
|---|---|---|
| O1 daily run, O1 R2 (session_016CU8KFuEEtWAM7ZNnFcKxv) | `fno/daily/`, `DAILY_RUN_STEPS`, CLAUDE.md daily routine | ING1 moves the capture steps and parts out in its steps I7-I9, by that owner's agreement; touches nothing before O14's code lands |
| O14 retry policy (same session) | `RetryPolicy`, `ExponentialBackoff`, `CircuitBreaker`, `RetryRunner`, escalation, step 2b | **Reused unchanged.** Its section 3.1 deadline rule (a retry may not push a later desk step past its limit) does not apply to an ingestion job: ING1 asks the owner to give each job its own deadline (section 4.4) |
| DR1 (session_01SPR8hz6AY8S99wE6ypFRik) | staging, certification, `RecordReader`, ledger, catch-up, per-dataset shadow | **ING1 sits beside DR1, not on top.** DR1 owns "is this data good and which copy is the record"; ING1 owns "who starts, retries, fails and alerts the fetch". One migration sequence per dataset (section 6.1) so no writer is changed twice |
| O9 (session_013u1Ac2N9eRQ8XCYPjwpaat) | Drive write-once store, receipts, `DriveCache`, `StoredFilesLibrary` | Reused as the only read path for the system |
| O10 (013YJ5gjXdxtFu6mwXP6v48N), O8 (012eM7Ti8ZaSVowgyMkgoGmM) | `capture_errors.csv`, `capture-watch.yml`, health expectations table | Failure rows and presence checks reused; ING1 only splits the table into ingestion and system rows (I3), with O8's owner reviewing every `fno/health/` diff |
| O13 routine logs (01Mt6dcBU5kp2htdPN2KmiZH) | Drive run logs per routine, hourly watcher | Reused as the run log of each ingestion routine |
| A16/A16h (01VK88LxJvV1Gi7Wbr3D4fzp), GW1 (session_01GsPm29fZzfH3DiErKAdBVk) | marks, claims, feed probe; Groww guards | Unchanged; ING1 adds a budget table that sums them (4.6) |
| A22/A17e (session_012pfddFKS3kqy6dJQCJ3Z5i, session_01E8AvLgNUPDyLRDEn2WT5Wi) | pre-open and cues routine | The model of an ingestion routine; unchanged |
| A4/A4c/A4e/A4f/A4h/A9c (01MKtUHByHsR9cNwaP5KhFYH) | quote recorders, close reads, NSE hosts | Their commands stay; only who starts them and the system imports change |
| G10 (session_011hvvn9CahAD5dCPHS3kowN), G7b (session_017GCFK7JLcsYeFKESyXtCyf), G6 freeze (session_019rZrcu1GSqUC7PScqwQgo2) | v4 capture part, release, pack-derived rows, freeze | The `v4_pack` split and `first_v4_expiry` import (M4, M5) need their agreement and the freeze route |
| E3 (session_01B3RARTgoiGJwBKXRCgGRe8), A14c part 2 (01JkD3wtEQbxiE7qLHzQS7jp), MS-P0b (session_01KJLFK1oqfytQkHapDCHJh9), REH1 (session_01GAACYjcfHWkC3hp33iiMXV) | execution snapshot; margin broker check; capture probes; rehearsal | Their captures become jobs (I8, I10); REH1 must serve every new job (risk R11) |
| STAB1 (another builder, not yet a register row) | forecasting off | Untouched. It will split `v4_pack`; ING1 adopts its key name (I1) |

No row builds ingestion as a separate layer. Nothing here is a second version of any row.

## 3. Inventory of every capture (strong evidence: read in the code and workflow files named)

"Host" is what starts it today. Routine = a Claude scheduled session the owner created (prompt in CLAUDE.md).
Shared columns come after the table (**S** = shares a process, thread or switch with system code: see M#).

| # | Capture | Source | Window / schedule (IST) | Started by (evidence) | Stored |
|---|---|---|---|---|---|
| C1 | A16 15-minute marks: NIFTY spot, near future, weekly and monthly chains, 26 marks | Groww REST | 09:15-15:30; 7 fires at :52 from 08:52 to 14:52, each 2 h 5 m, plus a one-hour cover (`fno/intraday/cover.py:15`) | A16 routine (`A16-owner-checklist.md` section 2), `intraday run` (`fno/intraday/cli.py:33`) | raw Drive; repo `research/data/intraday/` slots, rv, heartbeat, claims |
| C2 | A22 pre-open: GIFT Nifty, NSE F&O pre-open list, 09:09 candle | NSE homepage API, NSE, Groww candles | 08:40-08:44:59, 09:08:30-09:10:59, 09:10:00-09:10:45 | 08:36 routine (CLAUDE.md:181-208) | Drive day row write-once; repo receipts, `capture_errors.csv` |
| C3 | A17e part B: Asian indices' open levels | Yahoo and others | 08:50-09:05 | same 08:36 routine, background (`global_cues/preopen_cli.py:1`) | Drive; repo snapshot logs |
| C4 | 3 pm NIFTY monthly quotes (`quotes record`) | Groww | 14:55-15:10, retry each minute | **daily run**, part `nifty` (`fno/daily/quote_parts.py:80`) | raw Drive; repo sidecar and `.canonical` |
| C5 | 3 pm NSE chain (`quotes record --source nse`) | NSE public | 14:55-15:10 | **two starters:** daily run part `nse` (`quote_parts.py:82`) and `quote-recorder-nse.yml` (cron 14:20, waits to 14:40, lines 11, 44-48) | repo CSV, sidecar, `.canonical` |
| C6 | A4c indices and A4f weeklies (`quotes record-indices`) | Groww | 15:01-15:13, after NIFTY's commit | daily run part `indices` (`quote_parts.py:84`) | raw Drive; repo sidecar, canonical |
| C7 | A4e v4-window quotes (`quotes record --window v4`) | Groww | 14:32-14:40, started 14:29 | daily run part `v4` (`fno/daily/v4_part.py:27`), only if `daily.live_from.v4_pack` (`config.yaml:216`) | raw Drive; repo `quote-snapshots-v4/` |
| C8 | E3 execution snapshot (`QuoteSnapshotRecorder.capture`) | Groww | about 15:15 | **the desk**, step `snapshot` (`fno/desk/execution_capture.py:37`, `fno/desk/daily_wiring.py:66`) | raw Drive; repo `journal/execution/<day>/` |
| C9 | A14c broker margin check (`margins stress-broker-check`) | Groww | long before 14:55 | daily run step `margin_check` (`fno/daily/wiring.py:174`); command not built, `live_from: null` (`config.yaml:210`) | planned |
| C10 | A16b candle catch-up (`intraday backfill`) | Groww | from 15:33 | daily run step `candles` (`wiring.py:238`) | raw Drive; repo `rv-candle/`, manifests |
| C11 | A4h close read and recheck (`closes read`) | NSE allIndices | 15:40, 16:00 | daily run steps `close_read`, `close_recheck` (`wiring.py:247`); also the evening routine, step 1c (CLAUDE.md:150) | raw and record Drive; repo receipts |
| C12 | Index-close archive, closes certification (DR1-1 shadow) | NSE file, Drive | morning and evening | morning routine 1b and evening routine 1c (CLAUDE.md:139, 150-170) | Drive; repo manifests, `receipts/records/` |
| C13 | Bhavcopy, participant OI, FII/DII (evening) | NSE | evening, before `lab close` | evening routine 1c, and the workflows C14-C16 | Drive; manifests |
| C14 | `index-closes.yml` (21:11, 07:41, 11:41); `panel-days.yml` (21:41, 12:11) | NSE | evening and retries | GitHub Actions | Drive; manifests; **derived** `warmup_closes.csv`, panel |
| C15 | `participant-oi-release.yml` (17:11, 22:45), `-watch` (every 15 min 16:37-23:22), `-sweep` (monthly) | NSE | evening | GitHub Actions | Drive; manifests; `pipeline fire` |
| C16 | `flows-download.yml` (21:10), `flow-history.yml` (21:30, 07:15), `fo-masters.yml` (06:00, 07:45, 11:15, 18:45) | NSE, NSDL | daily | GitHub Actions | Drive; manifests |
| C17 | `nse-margins.yml` (03:30 and catch-ups), `stress-factor.yml` (Sunday) | NSE Clearing | night, weekly | GitHub Actions | Drive; **derived** `margins.csv` |
| C18 | `global-cues.yml` (03:41, 04:41, 14:11) | Cboe, Nasdaq, FBIL, Treasury, RBI | three a day | GitHub Actions | Drive; `research/data/global-cues/` |
| C19 | `vix-history.yml`, `circulars.yml` (hourly), `filings-archive.yml` (6 h), `market-publish.yml` (07:10) | NSE, filings | daily | GitHub Actions | Drive; **publish** to Azure DB (market-publish) |
| C20 | MS-P0b capture probes (`capture-probe`) | Groww REST, NSE | 4 slots a session; **on hold** | hand or a proposed 09:50 routine | Drive |
| C21 | A16h Groww feed probe (live feed) | GrowwFeed | by hand from 27 Oct | hand | probe note |

Not captures, named so they are not confused: `forecast-capture.yml` (the v2 forecast, despite the name),
`v4-fire.yml`, `routine-fire-probe.yml`, `postmortem-weekly.yml`, `forecast-scores.yml`, `number-alert.yml`,
`checks.yml`, `data-checks.yml`. Watchers of ingestion: `capture-watch.yml` (O10), `recorder-watch.yml` (A16i),
`health-check.yml` (17:51, O8).

### 3.1 Retry, failure and alerts today, per capture

| Capture | Retry today | On failure | Alerts today |
|---|---|---|---|
| C1 | per-mark Groww retry once; claims keep one taker per mark (`claims.py:1-5`); extra hour cover | gap recorded, never filled | two bad marks in a row; run stopped; commit refused (`A16-owner-checklist.md` section 4); `recorder-watch.yml` after 30 min silence |
| C2, C3 | each part reads at its window's opening then every 30 s (`fno/preopen/run.py`) | part `late`, `incomplete` or `failed`; row in `capture_errors.csv` | one #fno-desk line per problem; A22d open check next morning |
| C4-C7 | each recorder retries an incomplete attempt every 60 s inside its window; `.canonical` is the first complete attempt (`recorder.py:1-5`) | `none` marker; part `failed` in the run log | the command alerts itself; the run adds one if it did not (`quote_parts.py:281`) |
| C8 | none of its own (`capture()` once, `recorder.py:184`) | no record, so the gate stops fills | desk's data-check alert |
| C10, C11 | none; the run does not retry them (`RETRIED_ON_RERUN` holds only exits and marks); O14 plans a retry | step `failed` | `Alerted` wrapper (`fno/daily/steps.py:111`) |
| C12-C19 | A9b NSE retry rules, a later cron as catch-up; GitHub's own reruns | `continue-on-error` steps, then a failing step ends the run | one line per run; `capture-watch.yml` records non-success runs |

### 3.2 Where capture and system are mixed (the findings; strong evidence unless marked)

- **M1, one process runs both.** `DAILY_RUN_STEPS` (`fno/constants_operations.py:69-97`) lists capture steps
  (`quotes`, `margin_check`, `candles`, `close_read`, `close_recheck`) between forecast and desk steps. The wiring
  builds all of them in one root (`fno/daily/wiring.py:131-267`).
- **M2, one commit thread.** Capture commits happen only in the run's single thread, between the desk's steps
  (`quote_parts.py:7-8`). A desk step that holds the thread (a command may run up to 600 s,
  `fno/daily/steps.py:24`) delays a capture's commit; a desk commit failure stops the run (`RunStopped`,
  `runner.py:58`) and the capture parts are only waited for (`runner.py:72-76`).
- **M3, one result and one exit code.** Capture problems and forecast problems end in the same line "day done with
  problems: <steps>" (`runner.py:62-63`), and the same `Alerted` wrapper alerts both.
- **M4, one switch for capture and forecast.** `daily.live_from.v4_pack` (`config.yaml:216`) gates the v4 capture
  part (`v4_part.py:35`), `v4_release` and `v4_deadline` (`v4_wiring.py:60-61`). Switching the forecast off by this
  key stops the capture (the owner's 25 Oct warning). STAB1 splits it; ING1 adopts its key.
- **M5, capture imports forecast code.** The v4 window's expiry choice calls `first_v4_expiry`
  (`fno/quotes/window_wiring.py:55`, `fno/forecast_v4_rules/v4_expiry.py:14-15`, which imports
  `forecast_v4.sessions` and `forecast_v4.terms`). A16's session RV takes protocol v4's cutoff flag
  (`fno/intraday/wiring.py:14-15, 70, 84`). The repo has no rule that stops such an import (`tools/check_imports.py`
  only checks that a module exists).
- **M6, the system starts a capture.** The desk's `snapshot` step calls the recorder (`execution_capture.py:37`).
- **M7, ordering couples capture timing to the desk.** The 15:33-16:00 reads run after `card`, `school`,
  `recommend` and five score steps in the same thread (`constants_operations.py:80-96`). `NotBefore` only sets a
  floor, so a slow earlier step starts them late (reasoning only: each step may take up to 600 s).
- **M8, forecasting routines host capture lines.** The morning prompt runs `data-librarian index-close` and
  `records certify closes` before `lab open`; the evening prompt runs `closes read --commit`, the certification, three
  librarian commands and the FII/DII snapshot before `lab close` (CLAUDE.md:139-170). Switching those routines off
  stops: the A4h fallback read, DR1-1's closes certification shadow (no other host), and duplicates of the
  workflows' downloads (C13 are also workflow jobs, so those are covered).
- **M9, workflows chain archive and derive in one job.** `index-closes.yml:61-72` archives, then appends the forecast
  panel's closes (`pipeline index-closes`) and the run fails if the append fails; `panel-days.yml` appends only
  "under the v3 freeze" (imports `forecast.freeze.NotFrozen`, `fno/pipeline/panel_days.py:24`; checkout depth 0 for the
  freeze); `nse-margins.yml:70-83` computes margins (`fno/nse_margins/` imports `risk`, `held_rise.py:24-27`);
  `participant-oi-release.yml:80-86` fires a system routine from the ingestion job; `market-publish.yml` publishes
  to the dashboard database in the same job as the archive.
- **M10, shared alert plumbing lives in the daily run.** Capture commands import `fno/daily/alerts.py`
  (`fno/quotes/cli.py:55`, `fno/intraday/cli.py:49`, `fno/close_read/wiring.py:10`, `fno/filings/runs_cli.py:68`,
  `fno/record_store/wiring.py`), so ingestion depends on the O1 package.
- **M11, one health table.** `fno/health/expectations.py:68-96` mixes ingestion rows with forecast and desk rows, and
  has no row for C7, C10, C11, C18 or C19 (gap, strong evidence from the list).
- **M12, retry coupling.** O14 section 3.1 limits a retried capture step by the later desk steps' deadlines; step 2b
  (CLAUDE.md:84) is a run-level rerun of the whole run.
- **M13, rehearsal inside the production root.** `fno/daily/wiring.py:113-116, 135, 140, 143-144, 172, 261` wrap the
  capture parts for REH1; any new job needs rehearsal serving.
- **M14, a future seat inside the recorder.** A16's mark-observer port (`fno/intraday/observer.py`, `wiring.py:78-82`,
  empty today) is designed for LM1 and A21 to run inside the capture process. That would put a system consumer in the
  capture's failure domain.
- **M15, a duplicate writer.** C5 has two starters (reasoning from the schedules; I did not verify which commit won
  each day, some evidence).

## 4. The target

### 4.0 In ten lines
1. **Ingestion job** = one source, one window, one owner of one dataset-day. Its own host, schedule, day lock,
   retry (O14), failure policy, alerts, commits and status file.
2. **System** = forecasts, v4 release, desk, school, recommender, card, scores, editions, publish, and every derived
   table. It reads ingested data only through DR1's records, O9's receipts and the verified Drive cache.
3. **One-way rule:** ingestion code imports no system package; the system never starts, waits inside, or retries a
   capture. A test pins the import list (I1).
4. **Ready** = the dataset-day's record or marker exists and verifies: `.canonical` for quote parts, DR1's record for
   migrated datasets, a receipt plus manifest row for archive files, the ledger row for A16 marks.
5. **A system step that finds its input not ready** polls the ready check until its own deadline, then stops with a
   named reason. It never fetches, substitutes or fills.
6. **Hosts:** Groww jobs in Claude routines (the key stays there); public-file jobs on GitHub Actions when the window
   allows (its cron starts 4-5 hours late); tight public windows in a routine.
7. **Derivations** (panel append, margins, RV with v4 flags, dashboard publish, routine fires) are system jobs that
   start when the input is ready, never inside an ingestion job.
8. **Groww budget** is a table in `config.yaml` that sums every Groww job's worst sign-ins and requests and must stay
   under 150 a day with a margin; windows keep GW1's quiet rules.
9. **One owner per dataset-day** by a config key; the other path refuses to write. Migration swaps owners dataset by
   dataset, with a rollback key.
10. **Health:** one status file per job-day, O10 rows for failures, DR1's ledger for presence, O8 rows for ingestion
    kept apart from system rows.

### 4.1 The pieces (interfaces in the repo's style; a new package `fno/ingest/` for the job layer only)

The existing capture code stays where it is. `fno/ingest/` adds only the job layer (no code moves first).

- `IngestJob` (ABC): `name`, `source`, `datasets`, `window` (`IngestWindow`, from `config.yaml ingest.<job>`),
  `policy` (`IngestPolicy`), `run(day) -> IngestOutcome`. Each existing command gets one adapter class
  (`CommandJob`, wrapping `python -m fno ...` as `CommandStep` does today); a job with a loop of its own (the A16
  marks, the 3 pm recorders) keeps it, as O14 section 4 says ("not wrapped").
- `IngestPolicy` (value): `retry` (`standard`, `short`, `own_loop` or `none`, O14's classes), `deadline` (the job's
  own, never a desk step's), `failure` (`alert_gap`, `alert_and_catch_up`), `source_circuit` (O14's per-source
  breaker), `max_signins`, `max_requests_per_minute` (GW1's guards stay the only pacing).
- `IngestRunner`: takes the job's day lock (`DayLock` for one container, a git claim for two, as A16's `MarkClaims`),
  runs it through O14's `RetryRunner`, commits only the job's own paths (`GitCommitter`, as `CommandStep`
  pathspecs do), writes the status file and escalates once (O14 section 8's text).
- `IngestedData` (reader port): `ready(dataset, session, level) -> Ready | NotReady(reason)` and `read(...)`.
  Adapters: `CanonicalReady` (quote parts, from `PartMarkers`), `RecordReady` (DR1's `RecordReader`),
  `ReceiptReady` (O9 receipt plus manifest row), `LedgerReady` (A16 mark ledger). The system builds readers
  with `StoredFilesLibrary` (`fno/storage/raw_library.py:3-5`: stores only, never fetches) and `DriveCache`
  (`drive_cache.py:1-5`: receipts are the index, bytes checked).
- `IngestOwner`: reads `ingest.owner.<dataset>` (`legacy` or `job`) from the checkout; a path that is not the owner
  refuses before its first request ("owned by <job>").
- Composition root: `fno/ingest/wiring.py` builds the job table; the routines call `python -m fno ingest run <job>`
  (or `ingest day <routine>` for a routine hosting several children).
- Alerts: the shared reporter `ReportedAlerts` moves to a neutral `fno/alerts/reported.py` (22 lines) so ingestion no
  longer imports `fno.daily` (M10).

### 4.2 The jobs (target table)

| Job | Captures | Host | Schedule | Retry | Failure policy |
|---|---|---|---|---|---|
| `marks` | C1 | routine (unchanged: 7 fires) | as A16 | O14 short, inside the fire | gap stays a gap; alerts as today; double cover stays |
| `preopen` | C2, C3 | routine 08:36 (unchanged) | as A22 | own 30 s loops, not wrapped | row `late`, `incomplete`, `failed`; alert; day goes on |
| `quotes-3pm` | C4, C5, C6, C7, C8 | one new routine, "3 pm capture", about 14:20 | as A4 windows | own 60 s loops, not wrapped | each part commits and alerts alone; a failed part never stops another |
| `post-close` | C10, C11 | same routine's tail or a second routine at 15:30 | from 15:33, 15:40, 16:00 | O14 standard, own deadline 19:53 | step status; alert once; catch-up next day for candles |
| `margins-broker` | C9 | with `post-close` or `quotes-3pm` | before 14:00 | O14 standard | alert; never holds a factor (A14c rule) |
| `nse-files` | C12, C13, C14 archive part, C15, C16, C17 download part | Actions (existing workflows, archive steps only) | as today | A9b rules plus catch-up crons | named stop per dataset; O10 row |
| `cues` | C18 | Actions (unchanged) | as today | as today | as today |
| `refs` | C19 except publish | Actions | as today | as today | as today |
| `probes` | C20, C21 | routine, off by default | owner-created | none | stop and alert on any 429 (P0b rule) |

Derive jobs (system side, own schedule, start on ready): `warmup-closes` (C14 append), `panel-days` (C14, freeze),
`nse-span` margins and `stress-factor` (C17), `session-rv-v4` (A16's rv with the v4 flag), `oi-dry-run-fire`
(C15), `market-publish` (stays on Actions: Claude containers cannot reach Postgres, `market-publish.yml:1-3`).

### 4.3 Why the hosts are what they are (evidence)

- **No broker key in GitHub.** Owner 13 Oct (`DESK_DECISIONS.md:60`): "never a broker key in GitHub"; 15 Oct
  (`:206`) the Groww comparison runs "in the daily Claude routine (no broker key in GitHub)";
  `O-operations.md:178`. The Groww key and TOTP secret live in the routine environment
  (`A16-owner-checklist.md` section 1). So every Groww job stays in a routine. (Strong evidence.)
- **GitHub's cron is late.** Morning crons started 4 h 40 min to 5 h 01 min late on 14-16 Oct
  (`global-cues.yml:6`, `nse-margins.yml:13`); `recorder-watch.yml:5` calls the schedule "best effort". Fine for
  evening and overnight files, wrong for windows of 10-15 minutes. (Strong evidence for mornings; the afternoon
  lateness is not measured: some evidence.)
- **Routine limits.** A background command is killed at about 10 minutes unless started with a long timeout
  (`A16-owner-checklist.md` section 7, 23 Oct log); each fire needs `routine_setup.sh` (about a minute); `/fire` allows
  30 a hour per routine (`DESK_DECISIONS.md:56`). The owner creates routines; no builder does.
- **Postgres is unreachable from Claude containers** (`market-publish.yml:2`), so the dashboard publish stays on Actions.
- **Other hosts** ("any other scheduled job", e.g. an always-on worker with a real cron) would remove the lateness and
  the kill limits, at the price of the Groww key on a new host. No evidence in the repo supports or refutes it: owner
  decision Q1.

### 4.4 Retry and failure, per job, not per day

- Each job has its own `IngestPolicy`; a failure of one job is a status row and an alert for that job only. It never
  changes another job's status, the system's run line or exit code.
- O14's classes apply as its section 4 already says: the windowed captures keep their own loops (an outer retry would
  start a second capture, and two Groww takers lose data, `claims.py:1-5`); the post-close reads and the margin check use
  the standard policy (30 s base, cap 8 min, at most 5 retries, then one escalation); the short policy is for A16.
- **Change asked of O14's owner:** the deadline of an ingestion step is its own (for `candles` and the closes, the
  next morning's use, not 16:00 or the desk's school slot), and the daily-run table in O14 section 4 loses these rows
  when I9 moves them. Step 2b retires with O14 as written.
- A hand run after an escalation stays allowed in market hours (the CLAUDE.md exception); a job that never started
  is a failed scheduled job under that wording (reasoning only).

### 4.5 What happens when a capture is late or fails (reader side)

- **Not ready at the step's start:** the system step polls `ready()` (as `forecast snapshot-ready` does today,
  `forecast-capture.yml:90-95`) until its own deadline, then stops with "input not ready: <dataset> <session>: <reason
  from the job's status file>". No capture is started, no older copy is used (DR1 rule: stale is refused).
- **Late but complete:** the record carries its taken-at time; a value first seen after a decision's cutoff is "late,
  never wrong" and is not counted as known then (A17e's as-of rule, DR1's as-seen pointer).
- **Failed:** the job's catch-up (DR1 section 4) re-fetches files the source still serves; live quotes and marks are
  never back-filled. `none` stays `none`.
- **The desk's 15:15 execution capture (C8)** becomes a job output; the desk reads the latest in-window attempt through
  the reader and writes its own as-seen record (`journal/execution/`), so a capture failure is a named stop in the desk,
  not a hidden call.

### 4.6 Groww sign-ins and rate limits across separate jobs

- Limits (GW1): 10 a second, 300 a minute, 150 sign-ins per 24 hours, shared by every session on the owner's account
  (`GW1-groww-rate-guard.md:10-13`). GW1a's guard counts per process (3 tries a day, `groww_sign_in.py`), so separate
  containers cannot see each other; protection is arithmetic plus the quiet windows, which are clock-based and hold
  across containers (`groww_quiet_windows.py:23`).
- **Today's worst case is 38 sign-ins a normal day, 114 if every sign-in fails** (`groww_sign_in.py:9-13`): 21 for
  A16's fires, 5 for the daily run's Groww children (NIFTY, A4c, v4, E3, A16b), 1 pre-open, 4 for "the school's slots",
  2 by hand. O14 adds at most 12 (section 5 there): 126. (The school's 4 are conservative: `fno/school/roads/wiring.py:3`
  says it fetches nothing from Groww; some evidence.)
- **ING1 adds no Groww process by splitting.** Moving the same children into the 3 pm routine keeps the count; only
  new jobs (C9, C20, a feed recorder) add. The budget table lives in `config.yaml` (`ingest.groww_budget`: each job's
  `max_signins`, `max_requests_a_minute`, window); a test sums it and fails above 130 (150 minus a margin of 20,
  reasoning only) and flags two jobs whose windows overlap without a GW1 quiet rule.
- A Groww sign-in failure is never retried by O14 (its section 5); unchanged.

### 4.7 Health record

- One status file per job-day at `research/ops/ingest/<job>/<day>.json`, status vocabulary and public reason codes of
  the daily run's log (`STEP_OK` and the rest, `fno/daily/reason_codes.py`), no values, attempts with class names
  only (the O14 and O1-status-only rule). A file per job-day means two jobs never touch one file.
- Failures also go to O10's `capture_errors.csv`; presence to DR1's completeness ledger; O13 holds each routine's
  private run log in Drive. ING1 adds only the status file, because none of those three says "job J, day D, policy P,
  n attempts, final status".
- O8's table is split into `ingestion_expectations()` and `system_expectations()`; new ingestion rows: C7, C10, C11, C18,
  C19, C9 when built.

## 5. Criteria for the builds (each with a proof that fails when its code is broken on purpose)

| # | Criterion | Proof |
|---|---|---|
| K1 | Ingestion packages (list in `fno/ingest/boundary.py`) import no system package; a new import fails | AST test (like `tests/test_code_size.py`); plant: add `from ..forecast_v4 import terms` to a quote module |
| K2 | The system starts no capture: no `QuoteSnapshotRecorder.capture`, `attempt_now`, `record*` or Groww client in a system package | same test, system side |
| K3 | A path that is not a dataset's owner refuses before any request | test with a fake source that counts requests (must be 0) |
| K4 | Two jobs of different failure domains: one fails, the other's status, commit and alert are unchanged | two-job fake-clock test (O2 style) |
| K5 | Each job commits only its own paths | existing `CommandStep` pathspec tests, per job |
| K6 | A system step with an unready input stops with a named reason at its own deadline and fetches nothing | reader contract test with a fake `IngestedData` |
| K7 | The Groww budget table sums under 130 and lists every Groww command | config test; plant: add a job without an entry |
| K8 | Every alert text of an old path has a mapped alert in the new path | a table in this story plus a test that greps both texts |
| K9 | Rehearsal serves every job (REH1) | `rehearse` day test per job |
| K10 | Real session: the job's record is the same as the old path's (shadow) or the day's record exists and verifies (swap) | the step's own rule-8 run, section 6 |

## 6. Migration (small steps, each separately judged; nothing is removed before its switch has run clean)

### 6.1 The canonical rule and how write-once duplicates are avoided

- **One owner per dataset-day** (`ingest.owner.<dataset>`: `legacy` or `job`, default `legacy`), read at the start of
  every capture path. Changing it is a one-line lane-1 commit, made only between 16:40 and 08:00 IST, never in a window.
- **Class P (public, replayable: NSE files, cues, NSE chain): run beside.** The non-owner runs in shadow: it writes
  under a writer-unique staging name (DR1: "the receipt is the publish step; a Drive file without a receipt is never
  data") or into `<dataset>-shadow`, never a `.canonical`, record or receipt in the owner's name. Compare 5 sessions
  (DR1's number; reasoning only), flip the key, then remove the old path.
- **Class G (Groww live captures: not replayable, rate-limited): no two writers, ever.** Two takers lost 74-87 of
  about 224 quotes on 16 Oct (`claims.py:1-5`, strong evidence). So: swap one capture at a time with the key; the old
  path stays in code, not scheduled, as the rollback; proof by tests, an REH1 rehearsal of a recorded day, the `--dry-run`
  folder runs, then the first real session watched by the orchestrator. Rollback = flip the key and restore the old
  routine line. The old path is removed only after 5 clean real sessions.
- **Duplicates are blocked four ways:** the key (K3); existing write-once refusals (`RawFileConflict`,
  `raw_store.py:86`; "already recorded", `recorder.py:149`); DR1's writer-unique names; a git claim when two
  containers could start the same job (A16's `MarkClaims`).
- **Per dataset, one sequence with DR1:** DR1's order is closes, run logs, 3 pm quotes, pre-open and cues, NSE files,
  A16. ING1 swaps a dataset in the same window as its DR1 phase 2-3, so no writer changes twice.

### 6.2 Steps

| Step | What | Lane, judges | Removes |
|---|---|---|---|
| I0 | This text | lane 1; judges R and S | nothing |
| I1 | Pin the boundary: `ingest.owner.*` keys (default `legacy`, no behaviour change); the import test with today's M-list as an allow-list that shrinks; adopt STAB1's capture key for `v4_pack` | lane 2 (tests, config key unread by code) and the orchestrator | nothing |
| I2 | Job kernel `fno/ingest/` (IngestJob, Policy, Runner, owner, status file, ready port and four adapters) built **unused**; alert reporter moved to `fno/alerts/` (M10) | lane 1; two judges (it calls outside services) | `fno/daily/alerts.py` becomes a re-export, removed in I9 |
| I3 | Health split and the missing ingestion rows (C7, C10, C11, C18, C19); per-job status files written by the existing commands' wrappers; O8's owner reviews | lane 1; two judges | nothing |
| I4 | **Class P, first:** C5 single owner. Measure 5 sessions of the workflow versus the daily-run part (which lands in-window, which commit won); then flip the key and disable the loser | lane 1; two judges | the loser (workflow schedule or the `nse` part) |
| I5 | Class P: split C14, C15, C17 into archive (stays) and derive jobs `warmup-closes`, `panel-days`, `nse-span`, `oi-dry-run-fire` on the system side; derive jobs start on `ready()`. Shadow: the new derive job runs `--check` (computes, appends nothing) and must equal the old append for 5 sessions; then the key flips and the append leaves the archive workflow | lane 1 (panel and margins are records, v3 freeze); two judges each | the append steps in 3 workflows |
| I6 | Class P: morning and evening routines lose their ingestion lines (C12, C13) to the `nse-files` workflows and the `post-close` job; DR1-1's certification shadow gets a kept host first | lane 1; two judges | prompt lines (owner edits, section 7) |
| I7 | Class G: the "3 pm capture" routine hosts C4-C7 as isolated children (the existing `QuoteParts`, `PartLocks`, `PartMarkers` moved, not rewritten); the daily run stops starting parts and its desk steps read `.canonical` (they already wait for it, `config.yaml:163-164`). Keys flip one capture per session, NIFTY last (C4 is the pack's input) | lane 1; two judges | `StartQuoteParts`, `FinishQuoteParts`, `QuoteParts` wiring in the daily run (after 5 clean sessions) |
| I8 | Class G: E3's execution capture (C8) becomes a `quotes-3pm` job output; the desk reads it and writes its as-seen record. E3's owner agrees; money and fills: two judges | lane 1; two judges | the `snapshot` step's capture call |
| I9 | Class G: C10 and C11 leave the daily run for `post-close` (O14 standard policy); `daily run` ends with the desk's steps | lane 1; two judges | steps `candles`, `close_read`, `close_recheck`, `margin_check`, `quotes`, `quotes_done` from `DAILY_RUN_STEPS` |
| I10 | New captures only as jobs: C9 margin check, C20 probes, a feed recorder after A16h's probe; each starts as a job, never a daily-run step | per job | nothing |
| I11 (last) | A16's rv and v4 flag move to the system-side `session-rv-v4`; the observer port is retired or restricted to ingestion observers; `first_v4_expiry` is replaced in the capture by a config superset rule with a pin test in the system tests. Needs the v4 freeze route (Q3) | lane 1; two judges | `v4_cutoff_flag` and the import in `intraday/wiring.py`; the import in `window_wiring.py` |

**Every removal** (the right column) is its own change, after the proof of its step, reviewed by two judges, and states
what is deleted and what test still covers the behaviour. Nothing is deleted in I0-I3.

### 6.3 Never losing a session's data

- Each flip happens after the previous session closed and before the next opens. The old path stays scheduled (Class P)
  or restorable by one key (Class G) until its removal.
- The in-day witness: an ingestion routine writes a start row at its first minute; the `recorder-watch.yml` pattern
  (reads the repository only) alerts if the row is missing 2 minutes before the job's window. A missed start is a failed
  scheduled job, so the CLAUDE.md exception allows a hand run in market hours (strong evidence for the wording,
  reasoning only for applying it here).
- Sessions between steps are never touched: the steps change one capture, on a day the previous steps' proof allows.
- Data volume: no new Groww reads are added by any step (K7).

## 7. What the owner must create or change (routines and schedules)

No session creates, changes or deletes a routine (A16 checklist). By step:

1. **Now, with STAB1:** do not delete the 08:38 morning and 19:53 evening routines. If STAB1's switch is inside
   `lab open` and `lab close` (my recommendation: config-gated commands), no edit is needed. If you prefer editing the
   prompts, remove only the `lab open`, `lab close`, `recommend check` lines and keep steps 1b and 1c.
2. **I4:** disable `quote-recorder-nse.yml`'s schedule or the daily run's `nse` part, whichever the measurement shows
   loses (a lane-1 code change, not a routine).
3. **I6:** edit the morning and evening prompts: remove steps 1b and 1c.
4. **I7:** create routine "Omenix F&O 3 pm capture", every day, `CRON_TZ=Asia/Kolkata 20 14 * * *`, same environment
   as the 14:05 routine (Groww, Drive, Slack settings, push access); first line `git fetch -q origin main && git
   checkout -q --detach origin/main` (stop and post on failure), then `sh tools/routine_setup.sh --groww`, then
   `python -m fno ingest day quotes-3pm` run to its last line; post any "alert NOT sent" or "NOT committed" line to
   #fno-desk. Exact text is written in I7's story.
5. **I9:** edit the 14:05 prompt (a desk and forecast routine from then): remove step 3, 3b, 3c and the quote-part
   section; add the post-close tail to the 3 pm routine or create a 15:30 "post-close" routine (Q2).
6. **I10:** create the P0b probe routine (weekdays 09:50) only if you want it.
7. `config.yaml` keys (`ingest.*`) are lane-1 code changes, not owner work.

## 8. Risks and how each is proven

| # | Risk | Proof | Evidence |
|---|---|---|---|
| R1 | A swap day where neither path starts: the 15-minute window is lost | witness alert; fake-clock end-to-end; REH1 rehearsal; first real session watched; rollback key | reasoning only (no data on a missed start) |
| R2 | Both paths capture: 429 and lost quotes | K3 refusal test; key read at start; flip only 16:40-08:00 | strong (16 Oct loss) |
| R3 | Groww sign-ins above 150 | K7 budget test | strong arithmetic (GW1a) |
| R4 | Overlapping Groww windows across routines | GW1 quiet windows are clock-based; add a test that lists job windows | some evidence |
| R5 | Many jobs push to `main`: refusals | per-job paths, one receipt file per write (O9), pull then push; two-job local-remote test | some evidence |
| R6 | A reader sees a partial copy | receipt is the publish step (DR1); reader contract tests | strong (DR1) |
| R7 | A system step waits forever | K6 deadline test | strong |
| R8 | An alert is lost in the move | K8 mapping test | reasoning only |
| R9 | Frozen v4 files touched | I11 last, freeze route, judges check `FREEZE_v4` list | strong (G6) |
| R10 | Clash with O14 code (`steps.py`, `daily_run.py`) | no ING1 code before O14 merges or its owner agrees in writing | strong (register) |
| R11 | Rehearsal cannot replay a new job | K9; REH1 owner in each step | some evidence |
| R12 | A job's routine is killed early (session limit) | A16's double cover pattern; resume rules (F1 gap) kept | strong (23 Oct) |
| R13 | Owner effort: three more things to create | Q2 | reasoning only |

## 9. Owner's questions (only your call)

1. **Where should Groww captures run?** (a) Claude routines only, as now (recommended: no key in GitHub, no new host,
   works today). (b) Later, one always-on worker with a real cron and the Groww key (no lateness or kill limit, but a new
   host to run and secure). (c) GitHub Actions with the key (reverses your 13 and 15 Oct decisions; not recommended).
2. **How many new routines?** (a) One "3 pm capture" routine that also holds the post-close tail until 16:10, so you
   create one routine (recommended for the first cut: it is today's host minus the desk). (b) Two routines (3 pm
   capture; post-close at 15:30), cleaner failure domains, one more thing to create and watch. Either way each job
   stays an isolated child.
3. **Is protocol v4's freeze still counting while forecasting is off?** I11 (moving A16's v4 flag and the v4 expiry rule
   out of the capture) edits frozen files and needs the freeze amendment route. (a) Yes, it counts: do I11 last, only
   with the route (recommended). (b) No, it is paused: judges may allow the change without a route.

## 10. Gap list: the owner's requirements and where each is covered

| Requirement | Covered by |
|---|---|
| All captures separate, any kind | 3 (inventory), 4.2 |
| Data feed apart from the system | 4.0 items 2-3, 4.5, K1-K2 |
| Workflow, routine or any job | 4.3, Q1 |
| System uses ingested data | 4.1 `IngestedData`, 4.5 |
| Different retry and failure policies | 4.4, 4.2 |
| Data capture never stops | 6.1 class G, 6.3, summary item 3 |
| Removals judged by two judges | 6.2 |
| Stability before speed | 6.2 order, 8 R1-R13 |
| Inventory with mixing | 3, 3.1, 3.2 |
| Groww budget across jobs | 4.6, K7 |
| Late or failed capture | 4.5 |
| Routine changes by the owner | 7 |

Out of scope with reasons: any code, config, workflow or routine change (design only); STAB1's switch (another
builder); redesigning O14, DR1 or GW1; the certification rules of any dataset (DR1); the live-feed recorder's design
(waits for A16h's probe, 27 Oct).

## Claims

Evidence: **strong** = read in the file named; **some** = inferred from files or a dated log; **reasoning only** = my
design judgement.

| # | Claim | Evidence | Where |
|---|---|---|---|
| 1 | C1 and C2/C3 already run in their own routines and are apart from the desk | strong | `A16-owner-checklist.md` sections 2-3; CLAUDE.md:181-208 |
| 2 | The daily run starts C4-C7, C10, C11 and (when built) C9 in one process with forecast and desk steps | strong | `constants_operations.py:69-97`; `daily/wiring.py:131-267` |
| 3 | Captures and desk commit in one thread; a desk failure stops the run | strong | `quote_parts.py:7-8`; `runner.py:58-62` |
| 4 | `v4_pack` gates the v4 capture, release and deadline | strong | `v4_part.py:35`; `v4_wiring.py:60-61`; `config.yaml:216` |
| 5 | Capture code imports the v4 expiry rule and the v4 cutoff flag | strong | `window_wiring.py:55`; `intraday/wiring.py:14-15, 70` |
| 6 | The desk starts the 15:15 execution capture | strong | `execution_capture.py:37`; `desk/daily_wiring.py:66` |
| 7 | Morning and evening routines hold capture lines; switching them off stops them | strong | CLAUDE.md:139-170 |
| 8 | C5 has two schedules; which wrote each day is not checked | strong for two starters, some for the effect | `quote-recorder-nse.yml:11`; `quote_parts.py:82` |
| 9 | Workflows chain archive and derive (and fire, publish) | strong | `index-closes.yml:61-72`; `panel-days.yml`; `nse-margins.yml:70-83`; `participant-oi-release.yml:80-86` |
| 10 | No broker key in GitHub was decided by the owner | strong | `DESK_DECISIONS.md:60, 206`; `O-operations.md:178` |
| 11 | GitHub morning crons start 4-5 hours late | strong (14-16 Oct); the afternoon is unmeasured | `global-cues.yml:6`; `nse-margins.yml:13` |
| 12 | Two simultaneous Groww takers lose data | strong | `claims.py:1-5` |
| 13 | Groww budget: 38 normal, 114 worst, 126 with O14, limit 150, shared by the account | strong arithmetic from GW1a and O14 | `groww_sign_in.py:9-13`; `O14` section 5; `GW1:10-13` |
| 14 | The school fetches nothing from Groww, so GW1a's count of its slots is conservative | some | `school/roads/wiring.py:3` |
| 15 | DR1 already defines ready (records, receipts, `RecordReader`) and "one writer per dataset" | strong | `DR1-design-staging.md` sections 2, 5; `raw_library.py:3-5` |
| 16 | `tools/check_imports.py` has no layer rule, so K1 needs a new test | strong | `tools/check_imports.py:1-40` |
| 17 | The health table mixes ingestion and system rows and misses C7, C10, C11, C18, C19 | strong | `health/expectations.py:68-96` |
| 18 | The target split is stable under O14's classes (windowed captures not wrapped) | strong | `O14` section 4 |
| 19 | A job-layer package with no code moved is the smallest safe change | reasoning only | 4.1 |
| 20 | Five sessions of shadow or clean running before a flip or a removal | reasoning only (DR1 uses the same number) | 6.1 |
| 21 | A margin of 20 sign-ins under 150 | reasoning only | 4.6 |
| 22 | A per-job-day status file is needed beside O10, DR1 and O13 | reasoning only | 4.7 |
| 23 | A missed job start counts as a failed scheduled job for the hand-run exception | reasoning only | 4.4, 6.3 |

**Builder self-review:** none yet (design text; independent reviewers are the judges).
**Real output sample:** not applicable (no code).
