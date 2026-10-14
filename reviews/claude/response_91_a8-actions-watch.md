# Response 91: story A8 on GitHub Actions, the participant-OI watch without an AI session (builder's claims)

Branch `story/a8-actions-watch`. Owner's ask: "Create a github action which can run every few hours or minutes and
check the file. No need to waste AI tokens."

## What is built

1. **`python -m fno participant-oi check-once`**: one check, then exit (`fno/research_data/release_check_once.py`,
   `ReleaseCheckOnce`). It reuses the A8 recorder (`ReleaseTimeRecorder.check`, `recheck_recent`, `first_present`) and
   writes the same append-only log, `research/data/participant_oi/release_checks.csv`.
   - NSE's session calendar decides the day; a closed day checks nothing.
   - Once the day's file is recorded present, later runs check nothing and write no row.
   - The re-read of the last 5 seen files (REWRITTEN detection) runs at most once a day. The log itself shows whether
     a run already did it today (a check made today for an earlier day), so no extra state file is needed.
   - Alerts go to #fno-desk through `build_alert_sender` (`FNO_SLACK_BOT_TOKEN`), only for:
     - REWRITTEN;
     - unreachable;
     - the file still absent at the first check from 23:15 IST (once a day).
     The command exits 1 after alerting, so the run shows red.
   - **The day checked is the day whose file is due** (`due_day`): today from 12:00 IST, else yesterday. See the
     lateness evidence below for why.
2. **`.github/workflows/participant-oi-watch.yml`**:
   - cron `7,22,37,52 11-17 * * *` = every 15 minutes, 16:37-23:22 IST, plus `workflow_dispatch`;
   - concurrency group `participant-oi-watch`, never cancelling, so two runs never write at once;
   - the public-record scan hook, then `git pull --no-rebase` and push; never `--no-verify`;
   - only the `FNO_SLACK_BOT_TOKEN` secret.
   - One final step posts one #fno-desk line when the check crashed without a result or the rows were not committed.
     Alerts the command already posted are not repeated. This follows the index-closes (O6) pattern: `continue-on-error`
     on the work step, then an explicit failure step.
3. **`.gitattributes`: `merge=union`** for the two release logs. On the overlap evening both the Claude routine and
   this job append to the same file. Two appends at the end of a file are a git merge conflict, so `git pull --no-rebase`
   would stop the push. A union merge keeps both sides' new rows. The test is a real git merge in a temporary repository.
4. `ReleaseTimeRecorder._first_present` is renamed `first_present` (now used by a second class); no behaviour change.

## GitHub cron lateness on this repository (strong evidence: the Actions API, 14 Oct 2026)

| workflow | scheduled (UTC) | started (UTC) | late |
|---|---|---|---|
| index-closes | 13 Oct 15:41 | never | dropped |
| index-closes | 14 Oct 02:11 | 07:30 | 5 h 19 m |
| index-closes | 14 Oct 06:11 | 11:49 | 5 h 38 m |
| participant-oi-release | 13 Oct 11:41 | never | dropped |
| participant-oi-release | 13 Oct 17:15 | 21:52 (03:22 IST next day) | 4 h 37 m, then cancelled |
| participant-oi-release | 14 Oct 11:41 | not started at about 13:40 | 2 h + |

`workflow_dispatch` runs started within seconds (participant-oi-release runs 1-3, index-closes run 1).

### What this means

- **checked_at stays truthful.** It is the clock time of the check, not of the schedule.
- **Precision.** When GitHub is on time, the first-seen time is at most 15 minutes after NSE's release (5 minutes with
  the routine). With today's lateness it can be hours later, or never inside the evening.
- **A8's availability rule (some evidence: the rule's code plus the release times measured so far):**
  - The rule counts sessions until a file is usable at the 15:00 IST decision. NSE's files appeared between about 18:48
    and 19:19 IST (Last-Modified on 12 and 13 Oct).
  - A first-seen time that is late but before the next day's noon still gives the same lag: next session. After noon
    the run checks the new day, so it never records the old file later than that.
  - A late first-seen time is the safe side: it never makes a file usable earlier than it really was.
- **The real cost is measurement, not safety.**
  - A day counts as measured only when an "absent" check comes before the first "present" one (`first_seen_times`).
  - A run that starts 5 hours late usually finds the file already present, so that day is not measured. The O6 copy's
    only 13 Oct row is exactly that: present at 21:50, no absent row before it.
  - The rule needs 20 measured days before it can leave the next-session default. With runs this late, that target
    could take far longer, or never be reached.
- **Without the "due day" fix, late runs would have been worse than useless.** A run starting at 01:30 IST would have
  checked the next day's file (absent, pointless) and never recorded the evening's file. It is fixed, tested, and
  covered by mutations.

## Honest recommendation (reasoning only)

1. **Do not disable the Claude routine `trig_01Gb78yeScy55Gwo6G8MFEgc` after one evening on this evidence alone.**
   - First look at the job's real start times on that evening (its rows' `checked_at`).
   - If GitHub stays hours late, this job cannot measure release times. It still records the day's file, alerts on
     rewrites, and costs no AI tokens.
2. **The reliable no-AI trigger is `workflow_dispatch` from an outside scheduler**, for example a cron service calling
   GitHub's dispatch API every 15 minutes. This needs a fine-grained GitHub token stored in that service, not in the
   repository. It is the owner's decision; I did not set it up.
3. **Another option for the owner and the judge:** each present row already stores NSE's own `Last-Modified` time.
   - It is when NSE wrote the file, whatever time we checked.
   - Using it as the release-time evidence would make cron lateness irrelevant to measurement.
   - It changes A8's rule (judge 15 used Last-Modified only for rewrites), so it is not built here.
4. **O6's `participant-oi-release.yml` still runs.** It holds a 6-hour watch to `actions/release_checks.csv`, then does
   the Drive upload (A9) and the pipeline fire.
   - This new job does neither, so it does not replace O6's downstream steps.
   - Once this job is trusted, the watch step in O6 can go, with its upload and fire steps triggered differently. That
     is a separate change.
   - `participant-oi compare` assumes a 5-minute interval, so it does not fit this job's log. Both write the main log
     anyway.

## Secret

I cannot read Actions secrets. `FNO_SLACK_BOT_TOKEN` is referenced the same way by the existing O6 workflows, but no run
log I can see has sent an alert yet, so its presence is **unverified**. If it is missing, every alert line in the job log
reads "alert NOT sent" (`NoAlertSender`), and the run is still red. The job does not work around a missing secret.

## Tests and checks

- `tests/research_data/test_release_check_once.py` (10 tests):
  - one check per run, then nothing once present;
  - a closed day;
  - unreachable alerts;
  - still absent: once, from 23:15, and in a run after midnight;
  - the due day;
  - the once-a-day re-read and the REWRITTEN alert;
  - the command posts each alert, fails only then, and checks the due day by default.
- `tests/research_data/test_participant_oi_watch_workflow.py` (3 tests):
  - the schedule is every 15 minutes, from 17:00 IST or earlier, with the last run between 23:15 and 23:30;
  - concurrency, no `--no-verify`, `git pull --no-rebase`, the hook, only the Slack secret;
  - a real git union merge of two appenders.
- Mutations: 15 of 15 caught (each check, the due day, the late-alert rule, the CLI exit and send, union, cron,
  concurrency).
- Full suite with `FNO_SLACK_BOT_TOKEN` unset, `ruff check`, `ruff format --check`, `python tools/check_imports.py`: the
  numbers are in the message to the orchestrator.
