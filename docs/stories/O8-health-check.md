# Story O8: the daily health check (noise-and-fairness step 6)

**Repository:** trading · **Lane:** 1 (a new workflow that posts to Slack) · **Size:** M

**Description:** As the owner, I want one free job each evening to check, from what the repository actually holds,
that every daily job did its work on time over the last few sessions, and to post one summary to #fno-desk, so that
a routine that never started, ran late or wrote "nothing" is seen the same day instead of weeks later.

**Context and why:**
- Handover 15 Oct, section 11 (`conversations/2026-10-15_handover_noise_fairness.md`), the agreed rules:
  - time-critical work runs on Claude routines;
  - GitHub cron is a fallback, or runs the evening data jobs, and starts late on its own terms (14 Oct's forecast
    capture ran at 19:27 IST);
  - deadlines live in the data, so lateness loses a day but never corrupts one.
- What is missing: nothing notices a routine that never started. Today that raises no alert.
- What the handover asks for: "one daily health check, a GitHub Actions job at about 18:00 IST (no Claude credits; a
  late start is harmless)", posting "all on time" or which routine was late or missed.
- Response 144, item 18 (judge 138's red team), five traps:
  - a cron hours late checks the wrong day;
  - a `none` canonical looks committed;
  - 20 of 20 is not the normal forecast count;
  - push times must come from GitHub;
  - nothing watches the watcher.
- Orchestrator, 15 Oct: check the last N sessions with push times, and post one summary. Keep it simple: one job and
  one message.
- Owner, 15 Oct (`docs/DESK_DECISIONS.md`): the v4 timeline (14:30 cutoff, 15:10 deadline, 15:15 snapshot) goes live in
  about a week. The deadlines this check uses must therefore change in one place. The timing-consistency test (step 5,
  after G10) will later prove every copy agrees.

**What each job leaves in the repository (measured on `main`, 15 Oct; strong evidence):**

| Job | Per-session evidence | Done means | Time that decides "late" | Deadline (owner) |
|---|---|---|---|---|
| 3 pm Groww recorder (14:33 routine) | `research/data/quotes/groww/derivatives/quote-snapshots/YYYY/MM/nifty_YYYYMMDD.canonical` plus one `.meta.json` per attempt (`fno/quotes/recorder.py:131`) | the canonical names a snapshot (not `none`, `recorder.py:48`) whose sidecar says `complete` and `in_window` | push receipt of the canonical | 15:13, `LATEST_START` (`fno/ai/timing.py`: the capture's last pull) |
| NSE recorder (in the 14:33 routine; the Actions job at 14:20 is a fallback) | the same under `quotes/nse/` | the same | push receipt of the canonical | 15:13, `LATEST_START` |
| Forecast v2 capture | `research/forecasts/live_v2/YYYY/YYYY-MM-DD_pack.json` and `_forecasts.csv` | one row per (non-AI forecaster, question), 4 x 5 = 20 today, counted from `fno/constants.py`; a blank probability is a row, counted apart | in-file `generated_at` of every row (protocol v2's own rule) | 15:15, `GENERATION_DEADLINE` (`fno/forecast/schema_v2.py:18`) |
| AI books' commitments | `research/forecasts/ai_v1/submissions/YYYY/YYYY-MM-DD_<book>.commitment.json`, `.reveal.json`; `ai_v1/YYYY/..._<book>_forecasts.csv`; the day's `_fired.json` | commitment, reveal and forecasts present; a book not fired shows the fire log's `reason` (stop rule or late start, `fno/ai/fire.py:55-65`), not "never ran" | push receipt of the commitment (protocol v2 section 5, as F1) | 15:15, `receipt_deadline` (`fno/ai/timing.py`) |
| Desk daily run (E3) | `journal/runs/YYYY-MM-DD.json` (`fno/desk/run_log.py`) | all six steps present | in-file `finished_at` of the `decisions` step | `desk.timetable.decision_deadline` (`config.yaml`) |
| A16 15-minute marks | `research/data/intraday/slots/YYYY/MM/DD/`, its ledger | 26 marks (`fno/intraday/slots.py:9`) with status `good` | none of its own: A16's per-mark status (`status.py:16`, 120 s per mark) is final and is reported as counted (missed, late) | none (A16's own) |
| A8 participant OI | row for the session in `research/data/manifests/participant-oi.csv` | present | push receipt of the commit adding the row | 23:30, `A8_RELEASE_BY` (health-owned; the 22:45 cron's window, `participant-oi-release.yml:13`) |
| Index closes (A13) | row in `research/data/nifty-panel/warmup_closes.csv` | present | push receipt | 12:00 next day, `INDEX_CLOSE_BY` (health-owned; after the 11:41 retry, `index-closes.yml:18`) |
| Panel days (A13) | `nifty-panel/manifest.json` `end` on or after the session | present | push receipt | 13:00 next day, `PANEL_DAY_BY` (health-owned; after the 12:11 retry, `panel-days.yml:19`) |
| FII/DII flows | row in `research/data/manifests/fii-dii-cash-by-session.csv` | present | push receipt | 23:59, `FLOWS_BY` (health-owned; after the 21:10 cron, `flows-download.yml:10`) |

The four health-owned deadlines (`A8_RELEASE_BY`, `INDEX_CLOSE_BY`, `PANEL_DAY_BY`, `FLOWS_BY`) exist nowhere else in
`fno/` (judge 164 grep). They live in `fno/health/expectations.py`, each with its cron source in a comment, and are
listed for step 5's timing-consistency test.

Not checked, each for a stated reason:
- `forecast-scores.yml` writes a report only on some days (10-13 and 10-15).
- `market-publish.yml` publishes to the dashboard, which has its own checks (P stories).
- `nse-margins.yml` is not scheduled (manual run only).
- `filings-archive.yml` is not per session.
- The A4c indices recording is added as one row of the expectations table by whichever story merges second, O8 or A4c.

**Scope.** In:
- **One expectations table, the only place that lists the checks.**
  - It lives in `fno/health/expectations.py`.
  - Each row is one `Expectation`: its name, the job, a `SessionCheck` strategy (canonical, record count, run log,
    marks, manifest row), the time that decides "late" (push receipt or in-file time, per the table above), its
    deadline, and its `live_from` date (a check is silent before it).
  - Each deadline is imported from the module or config that owns it (`LATEST_START`, `GENERATION_DEADLINE`,
    `receipt_deadline`, `desk.timetable.decision_deadline`), never typed again. The four with no owner are the
    health-owned constants named under the table.
- **The day is the session, not the clock** (trap 1).
  - **The window, defined once:** the NSE calendar's sessions dated from 6 calendar days before the run's IST date up
    to that date (`config.yaml` `health.window_days: 6`). The oldest push it can need is at most 6 days 8 h 47 min
    old (a 15:13 push on the first day, read at 23:59 on the last), so it stays inside GitHub's 7-day activity log
    (`time_period=week`, `fno/ai/receipts.py:19`) on every run, holiday weeks included.
  - So session D is checked by every run from D 17:51 up to 6 days later, far beyond the measured cron lateness (5 h
    on 14-15 Oct, `conversations/2026-10-15.md`).
  - Each check's status at the run time is one of:
    - `ok`;
    - `late`: present, but pushed after its deadline;
    - `missed`: absent, `none` or incomplete;
    - `not due`: its deadline has not passed yet, as for the evening data jobs at 18:00;
    - `not expected`: a muhurat session, a check before its `live_from`, or the desk's `skipped` step (closed days
      never enter the window, so they need no status);
    - `unknown`: a file is unreadable, or the push time cannot be established.
  - A skipped run loses nothing, because the next run re-checks the window.
- **`none` and incomplete are misses** (trap 2):
  - a canonical holding `none` is reported as `missed (none)`;
  - a canonical naming a sidecar with `complete: false` is `missed (incomplete)`;
  - no canonical at all is `missed (never ran)`.
- **Counts come from the constants** (trap 3). The forecast row count is derived from the forecaster and question
  constants, not the literal 20. Blank probabilities are reported as a number beside the count; they are not a health
  failure, because whether a blank counts is the protocol's rule (G9).
- **Push times from GitHub** (trap 4).
  - "On time" uses GitHub's push time of the commit that added the file, through the existing `PushReceipts` interface
    (`fno/ai/receipts.py`, story F1), never a commit date.
  - The commit that added a file comes from `git log --diff-filter=A`; the workflow checks out the full history.
  - A push time that cannot be established is `unknown`, never `ok`.
- **The watcher is watched** (trap 5).
  - Each run appends one row to `research/ops/health_runs.csv`: date, start, finish, result.
  - Each run reports every calendar day inside its window with no row as "health check did not run on <date>"; days
    before the file's first row are not reported (the first run has no history).
- **One job, one message.**
  - `.github/workflows/health-check.yml` runs on a cron at 17:51 IST, plus a manual run. It runs
    `python -m fno health check`, which posts one message to #fno-desk through `fno.composition.build_alert_sender()`
    (`FNO_SLACK_BOT_TOKEN`).
  - Message format:
    - first line: "health <date>: all on time (<checks> checks, sessions <first>-<last>)", or "health <date>: <k>
      problems";
    - then one line per check with a problem, listing its bad sessions with their status and time or reason
      (for example "NSE recorder: missed (none) 14, 15 Oct"), so a check never takes more than one line;
    - then one line listing what is `not due`.
  - If the check itself fails, it posts "health check FAILED: <error type>", and the workflow fails red.
  - The job then commits `research/ops/health_runs.csv` only (lane 3 data, scheduled job output). It needs
    `contents: write` permission and runs with the Actions token.

Out:
- Fixing any job it finds late; re-running anything; changing any routine or deadline.
- Alerts other than the one message.
- Reading Drive. The check reads only the repository and GitHub's activity log, so it needs no Drive or Groww secret.
- Step 5's timing-consistency test.

**Design:**
- `fno/health/` package:
  - `expectations.py`: the table above;
  - `session_checks.py`: one small `SessionCheck` class per evidence kind, behind one interface, each returning a
    `CheckResult(status, detail)` for one session at one run time;
  - `window.py`: the window, defined once (sessions dated from 6 days before the run's IST date to that date, from
    `fno/research_data/calendar.py`);
  - `report.py`: the message text;
  - `run_record.py`: `health_runs.csv`;
  - `wiring.py`: the composition root, which builds the calendar, `PushReceipts`, the alert sender and the table.
- `fno/constants.py` gets the status names and the run-record file name. `config.yaml` gets `health.window_days`, an
  allowed key in `fno/config.py`.
- The CLI is `python -m fno health check [--at <IST time>]`. `--at` is for tests and dry runs, and a dry run posts
  nothing (`--dry-run` prints the message).

**Acceptance criteria:**
1. **The right sessions, whenever it runs.** With a planted calendar and repository:
   - session D is in the window of runs at D 17:51, D 23:40, D+1 03:10 and D+6 23:59, and not at D+7 00:01;
   - closed days never appear; a muhurat session is `not expected`; a check before its `live_from` is silent;
   - over every daily 17:51 run of 2025 with the real calendar, no session in the window needs a push older than
     7 days (so a holiday week gives no `unknown` from the log's age).
2. **Each status from its evidence, by the row's own time.** For every check in the table, a test plants each case:
   `ok`, `late` (the row's deciding time, push receipt or in-file time, one second past the deadline; exactly at it is
   `ok`), `missed` (absent; `none`; incomplete sidecar; one forecast row short; 25 of 26 marks; a run log without
   `decisions`), `not due` (an evening job at 18:00) and `unknown` (no push found; unreadable file). An AI book that
   was not fired shows the fire log's reason. Each case gets the right status and a reason naming the file.
3. **Counts and deadlines come from their owners.**
   - The forecast row count follows the constants: a test with an added question expects 24.
   - Each owned deadline is the owner's object (`LATEST_START`, `GENERATION_DEADLINE`, `receipt_deadline`, the desk
     config); the four health-owned constants are the only time literals in `fno/health/` (a test greps for them).
   - Changing `desk.timetable.decision_deadline` in a test config moves the desk check's deadline.
4. **Push times only from GitHub, where the row uses a push.** For each push-receipt row, a file whose commit date
   is before the deadline but whose push is after it is `late`; a commit date after the deadline with a push before it
   is `ok` (fake `PushReceipts`). No code path reads a commit date for timing.
5. **One message, and it always arrives.**
   - All ok gives exactly one line.
   - Problems give the header plus one line per check, never one per (check, session).
   - An exception inside the check posts "health check FAILED: <type>" and exits non-zero.
   - With no Slack token, it prints the message and says no alert was sent.
   - All of this is tested with a fake sender.
6. **The watcher is watched.** A run appends exactly one row. A later run reports each calendar day inside its window
   that has no row, and none before the file's first row. A second run on the same day appends its own row and reports
   no missing day for that date (tests).
7. **The workflow.**
   - Cron 17:51 IST, `workflow_dispatch`, full history checkout, `contents: write` permission.
   - It commits only `research/ops/health_runs.csv`, using `git pull --no-rebase` before the push.
   - No secret appears in any file or log (record scan, plus a test that greps the workflow and the output).
8. **Real sample.**
   - A dry run on the real repository for the last 5 sessions to 15 Oct, with its output in the claims file.
   - It must show today's real findings. For example, the NSE canonicals for 14 and 15 Oct hold `none`, so they show
     as `missed (none)`.
9. **Engineering rules.** Every check is behind the `SessionCheck` interface and wired only in `fno/health/wiring.py`
   (named in CLAUDE.md's list of composition roots). No file or class is over 350 lines.

**Gap list:**

| Requirement (source) | Criterion or reason out |
|---|---|
| Daily job at about 18:00 IST on GitHub Actions, no Claude credits (handover 11) | 7 |
| Canonical committed by 15:13 (handover 11) | 2, 4 |
| Forecast v2 records complete and on time (handover 11) | 2, 3 |
| AI books' sealed commitments by 15:15 (handover 11) | 2, 4 |
| A8 rows for the day (handover 11) | 2 |
| One line: all on time, or which routine was late or missed (handover 11; orchestrator: one message) | 5 |
| Catches a routine that never started (handover 11) | 2 (`missed (never ran)`) |
| Last N sessions (orchestrator; response 144 item 6) | 1 (the last 6 calendar days, inside GitHub's log: judge 164) |
| Push times from GitHub (orchestrator; response 144 items 6 and 18) | 4 |
| Wrong day if the cron is hours late (response 144 item 18) | 1 |
| "none" canonicals look committed (item 18) | 2 |
| 20 of 20 is not the normal count (item 18) | 3 (count from constants, blanks reported apart) |
| Nothing watches the watcher (item 18) | 6 |
| 3 pm recorder: Groww, NSE, A4c indices once merged (orchestrator) | 2; A4c as one table row (scope) |
| Forecast capture, desk run, A16 marks, scheduled data jobs (orchestrator) | 2 (each named in the table) |
| v4 timeline changes deadlines within a week (owner, 15 Oct) | 3 (one place per deadline; four health-owned, listed for step 5) |
| Timing-consistency test (step 5) | out: later, after G10 |
| Keep it simple (owner's simplicity rule) | one job, one message, no fixing |

**Known limits (one line each):**
- F1's activity reader stops at 10 pages of 100 pushes (`receipts.py:21`); `main` had 693 first-parent commits in the
  week of 15 Oct, so a busier week shows the oldest pushes as `unknown` (shared with F1, judge 164 note).
- A health job that never runs at all is only noticed by the owner seeing no 18:00 message, or by the next run.
- The desk run log and A16's marks are not live yet (`journal/runs/` and `research/data/intraday/slots/` do not exist on
  main), so those checks start at their `live_from` dates, set when each goes live (orchestrator, 15 Oct).
- The check proves that files and push times are present, not that the data inside them is right; that is the data
  checks' job (C3).

**Test plan:**
- `tests/health/` uses planted repository trees, a fake calendar, a fake `PushReceipts` and a fake alert sender; it
  never uses the network.
- One test per criterion, each with good, bad, boundary (exactly at the deadline) and empty cases (no file, no
  sessions).
- Every criterion is broken on purpose once.

**Judge verifies:** runs the dry run on the real repository and checks two findings by hand (one `ok`, one `missed`);
plants a late push, a `none` canonical and a skipped health run; reads the workflow for secrets and permissions.

**Depends:** A4/A4b and A7 (calendar), F1 (`PushReceipts`), G2 (forecast v2), E3 (run log), A16, A8, A13 ·
**Status:** story text revision 2 (judge 164: should-fix 1-5, minors 1-5) for the judge's check before code
(claims: `reviews/claude/response_153_o8-health-check.md`)
