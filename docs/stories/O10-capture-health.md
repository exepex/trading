# Story O10: every external capture is fresh or loudly failed

**Repository:** trading · **Lane:** 1 (GitHub workflows, Slack output) · **Size:** M

**Description:** As the owner, I want every job that captures outside data to either deliver today's data on time or
tell #fno-desk that it did not, and to leave one committed error row I can fix from, so that no capture fails
silently (owner, 16 Oct 2026, `docs/DESK_DECISIONS.md`: "we must notify that something failed. Error case needs to be
captured properly so that we could fix them").

**Context and why (evidence read 16 Oct 2026, 10:30-11:10 UTC; strong unless marked):**
- Every capture workflow already posts one line on `failure()`. **None posts on `cancelled()`**: a job killed by its
  `timeout-minutes` is "cancelled", so it says nothing (grep of `.github/workflows/*.yml`).
- A job GitHub never starts posts nothing. Only O8's evening check can see it, and O8's table lacks NSE margins, the
  A4c indices and the market archive (`fno/health/expectations.py`).
- No error is recorded anywhere in the repository; the only trace is the Slack line and the Actions log (kept 90 days).
- Audit Part F's four health problems, checked against GitHub's run list:

| Problem (audit) | What the runs show | Cause |
|---|---|---|
| `health-check.yml` never ran | 0 runs. The workflow was created 15 Oct 18:31 UTC; its cron is 12:21 UTC; its first slot is 16 Oct 12:21 UTC, after the audit | **Not a fault yet**: no slot had come. Proven only when 16 Oct's run appears (claims file will cite it) |
| `nse-margins.yml` 03:30 IST cron never started | 2 runs ever: 15 Oct (manual), 16 Oct 07:12 UTC (scheduled). The 03:30 IST cron (22:00 UTC) merged 16 Oct 06:08 UTC (3c333417), so its first slot is 16 Oct 22:00 UTC | The 03:30 claim is wrong (no slot yet). Real: of the two old morning slots (02:15, 03:00 UTC) on 16 Oct, one started 4-5 h late and **one never started** |
| `participant-oi-release` second slot cancelled nightly | Runs 4, 6, 8 (13, 14, 15 Oct): created 20:21-21:52 UTC (01:51-03:22 IST, 3-4.5 h late), each cancelled after exactly 5 h 50 min in the watch step (run 38801338770, job 116650851676) | A run starting after midnight IST takes `day = now_ist().date()` (the **next** day) and `until` 23:30 of that day (`participant_oi_cli.py`), so it watches a file NSE will not publish for 20 h until the 350-minute timeout kills it; the cancel posts nothing |
| `quote-recorder-nse.yml` fails daily | 2 runs: 14 Oct started 14:04 UTC (19:34 IST), 15 Oct 13:42 UTC (19:12 IST); both wrote `none` and alerted (log of run 38745053176: "alert sent to #fno-desk") | GitHub starts it about 5 h late, after the 15:10 window. Owner decision 15 Oct: "Keep as fallback". Since 16 Oct the 14:33 routine records NSE first, so a late run now prints "already recorded" and exits 0 (`fno/quotes/cli.py` `GOOD_STATUSES`) [some: confirmed by 16 Oct's run when it appears] |

**Inventory of external captures** (expected freshness by NSE's session calendar; evidence location):

| Capture | Runs on | Due by (IST) | Evidence in the repo | O8 row today | O10 adds |
|---|---|---|---|---|---|
| 3 pm NIFTY, Groww | 14:33 routine | session 15:13 | `quotes/groww/.../nifty_*.canonical` | yes | - |
| 3 pm NIFTY, NSE | same routine (+ fallback workflow) | session 15:13 | `quotes/nse/.../nifty_*.canonical` | yes | - |
| 3 pm BANKNIFTY, FINNIFTY, MIDCPNIFTY (A4c) | same routine, step 3b | session 15:13 | `quotes/groww/.../<index>_*.canonical` | no | 3 rows, live from 19 Oct |
| A16 15-minute marks | A16 routine | per mark | `research/data/intraday/` | not live (`None`) | - (A16/O9 own the live date) |
| Forecast capture v2, AI books | forecast-capture.yml + routines | 15:15 | `research/forecasts/` | yes | - |
| NSE SPAN margins (A14) | nse-margins.yml | session 09:15 | `research/data/margins/margins.csv` (`as_of`) | no | 1 row |
| Participant OI (A8) | participant-oi-release / -watch | 23:30 | `manifests/participant-oi.csv` | yes | - |
| Index closes, VIX close | index-closes.yml | next day 12:00 | `nifty-panel/warmup_closes.csv` | yes | - |
| F&O bhavcopy, NIFTY panel | panel-days.yml (frozen v3) | next day 13:00 | `nifty-panel/manifest.json` | yes | - |
| FII/DII flows | flows-download.yml | next day 12:00 | `manifests/fii-dii-cash-by-session.csv` | yes | - |
| Market archive: corporate actions, EQUITY_L (lost if missed: NSE overwrites) | market-publish.yml 07:10 | next day 12:00 | `manifests/corporate-actions.csv`, `equity-list.csv` | no | 2 rows |
| Company filings (A12) | filings-archive.yml, every 6 h | not per session | `manifests/filings/` | no (stated) | failures only (watcher below) |
| Stress factor (A14c) | stress-factor.yml, weekly | derived, not lost | `risk` files | no (stated) | failures only |
| Global cues (A17), A16b candles, VIX OHLC | **no schedule** | - | - | no | out: scheduling them is audit item 12 (A17 owner) |

**Scope.** In:
1. **One watcher for every capture workflow: `capture-watch.yml`.** It runs on GitHub's `workflow_run` event
   (`types: [completed]`) for every capture workflow above, so no capture workflow is edited (panel-days.yml stays
   frozen). For a run whose conclusion is not `success` or `skipped`, it runs `python -m fno health capture-failed`,
   which:
   - reads the run and its jobs from GitHub's API (the run's own `GITHUB_TOKEN`, `actions: read`): the first job step
     that did not succeed is the `step`, the run's conclusion (`failure`, `cancelled`, `timed_out`) is the `kind`;
   - appends one row to `research/ops/capture_errors.csv`: `date` (IST date of the run's start), `job` (workflow name),
     `step`, `kind`, `message` (the step's name and conclusion; one line, at most 200 characters, never a log excerpt,
     so no secret can enter), `run_url`; a row for the same `run_url` is never written twice (re-runs);
   - posts one line to #fno-desk through `fno.composition.build_alert_sender()` **only when the run cannot have posted
     its own line**: conclusion `cancelled` or `timed_out`. A `failure` already posted through the workflow's own
     step, so a second line would be noise;
   - commits only `research/ops/capture_errors.csv` (`git pull --no-rebase` first). If the watcher itself fails, its
     own `failure()` step posts one line.
2. **O8 reads the error file and gains the missing freshness rows** (split agreed with O8's owner through the
   orchestrator before coding):
   - new rows: A4c's three indices (`CanonicalCheck` gets the underlying's name; live from 19 Oct), NSE margins (a row
     of `margins.csv` whose `as_of` is the session, by 09:15; `SessionRowCheck` gets the date column), corporate
     actions and EQUITY_L manifests (by 12:00 the next day);
   - the daily message gets one line "capture errors: <n> in the window (<jobs>)" from `capture_errors.csv`, so the
     evening summary names them even if a Slack line was missed;
   - each new `missed` or `unknown` result is appended to `capture_errors.csv` once (`job` = the check's name, `step`
     = `freshness`, `kind` = the status, `run_url` = the health run's URL, keyed on (date, job, kind)), so a job that
     never started, and a routine's miss, also leave the committed error row.
3. **The four health problems:**
   - participant-oi-release: `watch` takes its default day from `release_check_once.due_day` (before 12:00 IST, the
     evening before), as `check-once` already does. A run starting after midnight then checks the due day's file once
     and stops (its `until` has passed) instead of watching the wrong day for 6 h. Test with a planted 01:52 IST start.
   - nse-margins: the job is already idempotent ("nothing new" on a rerun), so add two catch-up slots (05:00 and 06:30
     IST) so a dropped or late slot is covered by the next; O8's 09:15 row alerts the evening if all fail. Workflow
     owned by A14 (01Vm1WnH): edited only with its owner's agreement through the orchestrator.
   - quote-recorder-nse: kept (owner, 15 Oct). Proven healthy only if 16 Oct's late run prints "already recorded";
     otherwise the cause and a proposal go to the owner. Its one real risk is written down: a run started on time
     races the routine for the same `.canonical` (reasoning only).
   - health-check: no change unless 16 Oct's 12:21 UTC slot fails to appear by 23:59 IST; then find why with the run
     list and fix.

Out: the routines' own alerts (they already post: the 3 pm recorder, A4c, A16); scheduling A17, A16b and VIX OHLC
(audit item 12); news, circulars and master files (A19, A20); O2's desk-run failure suite; moving these files to Drive
(O9 decides that later; `research/ops/` holds O8's run record today).

**Acceptance criteria:**
1. For a failed, cancelled and timed-out run (planted API JSON), `capture-failed` writes exactly one row with the right
   job, first failing step, kind and run URL; a second call for the same run writes nothing; a `success` run writes
   nothing.
2. It posts one line for `cancelled` and `timed_out`, none for `failure`; with no Slack token it prints that no alert
   was sent and still writes the row (fake sender).
3. No row or line holds a log excerpt; a message is one line of at most 200 characters (test with a planted long step
   name and a newline).
4. `capture-watch.yml` lists every capture workflow (a test compares its list with the workflow files that commit
   `research/data` or post capture alerts), has `actions: read` and `contents: write`, commits only
   `research/ops/capture_errors.csv`, and holds no secret value.
5. O8: the new rows give `ok`, `late`, `missed` and `not due` from planted evidence; A4c is silent before 19 Oct; the
   message carries the capture-errors line; a new miss is appended once and never twice across two runs.
6. participant-oi `watch` started at 01:52 IST checks the previous day once and returns; at 17:11 IST it watches today.
7. Run logs cited in the claims file: the first `capture-watch` run on a real non-success run, 16 Oct's health-check
   and quote-recorder-nse runs, and the first nse-margins catch-up run.
8. Gates pass; no file or class over 350 lines; composition only in `fno/health/wiring.py`.

**Known limits:** `workflow_run` fires only for workflows on `main`, and a workflow GitHub never starts gives no
event (O8's freshness rows cover that, the same evening). A run that GitHub starts but cancels before any step leaves
no step name ("before any step"). The watcher is itself an Actions job; if it never starts, O8's error-count line is
the backstop.

**Depends:** O8, O8b, O8c (merged); A14 owner for nse-margins.yml · **Status:** text for the orchestrator.
