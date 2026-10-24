# Response 284: A20b, NSE and SEBI circulars kept point in time (builder's claims)

**Story:** `docs/stories/A20-rules-and-dates.md` at e50ca714 (part b; text answer to judge 353 in response 266) ·
**Branch:** `story/a20b-circulars` (independent of A20a's code) · **Builder:** session_013u1Ac2N9eRQ8XCYPjwpaat ·
**Lane:** 1 (NSE, SEBI, Drive, Slack, a workflow)

## What it does

`python -m fno circulars` (workflow `circulars.yml`, hourly 08:00-22:00 IST, every day):
1. reads every row listed so far: Drive `data/circulars/list/` parts through O9's verified Drive cache. If that
   fails, nothing is captured, since a capture now would list everything again;
2. NSE: `www.nseindia.com/api/circulars` for the last 14 days; SEBI: its latest circulars page (25). NSE's items are
   merged per link, keeping every department;
3. every circular whose link is new is **listed in the run that first sees it**, with `first_seen_at` (UTC) and
   `file` = `saved`, `failed` or `not_kept`. F&O-relevant files go to `data/circulars/files/<source>/<YYYY>/<MM>/`.
   A failed file is retried by later runs for 3 days; a retry writes a new row carrying the first `first_seen_at`,
   with `saved`, or `abandoned` after 3 days. A file already receipted counts as saved;
4. the run's new rows form one O9 `PartTable` part (`data/circulars/list/<YYYY>/<MM>/<date>.<run_id>.csv`);
5. problems: a feed refused or unreadable (including a SEBI page with any row in another layout, or NSE's `data` not
   a list), stale by its rule (NSE: no circular dated the previous session, A7 calendar; SEBI: newest over 45 days),
   NSE's calendar not covering the day, a SEBI page with nothing seen before, a file failing or abandoned, the list
   part or earlier parts not read or saved, receipts or state not committed;
6. alerts **once per episode**: `research/ops/alerts/circulars_open.txt` (keys only, committed) holds the problems
   already alerted. New problems and recoveries go in one post. A key counts as alerted only once Slack accepted the
   post, so a refused line is tried again next run. A run with only known problems posts nothing and marks the step
   as having spoken, so the workflow's crash line stays quiet. An abandoned file is never reported as recovered. Any
   open problem exits 1, so O10's watcher records every failed run (`circulars` to be listed in `capture-watch.yml`;
   agreed with O10's builder).

## Claims per criterion (code, test, broken-code proof)

Every mutation below was planted, the named test file run, and the file restored (`mutate.py`, this session's
scratchpad, not committed).

| Crit. | Claim | Code | Tests | Mutations (all CAUGHT unless noted) |
|---|---|---|---|---|
| 5 | Real NSE answer parses whole (63 circulars from 70 items) and real SEBI page (25); 403, 503 with a JSON body, HTML, item without fields, `data` a dict, no `data`, unreachable, SEBI without rows, a SEBI row in another layout, a 404 file are all `FeedFailed` | `fno/circulars/feeds.py` | `tests/circulars/test_feeds.py` | empty SEBI page accepted; non-200 accepted; `data` dict accepted; partial SEBI rows accepted |
| 6 | Exactly the 4 F&O circulars of 15-16 Oct flagged (no NSE commodity or currency "derivatives"); NSE/CMTR/76963 keeps both departments | `relevance.py`, `_merged` | `test_relevance_...`, `test_nse_lists_...` | merge keeps last only; F&O department ignored |
| 7 | NSE stale judged on the previous session from a session day, a holiday and a weekend; empty list stale; beyond the calendar its own problem (`nse:calendar`), not a crash; SEBI 45 days fine, 46 stale, empty stale; a stale feed's circulars still listed; a latest page with nothing seen before is a gap (not on the first ever run) | `freshness.py`, `capture.py` | `test_freshness.py`, `test_capture.py` | NSE rule off; SEBI `<=` → `<`; stale ignored; gap check off; CalendarError not caught |
| 8 | Listed at first sight with time and status; empty list and repeat list write no part; window 14 days; a link failing twice then working ends `saved` with its first time; exactly 3 days still retried, 3 days 1 minute `abandoned`, never again; a failed list part keeps the run's other problems; a receipted file counts as saved | `capture.py` | `test_capture.py` | window 1 day; failed file held back; retry takes a new time; never abandoned; list-part replaces problems; receipt not trusted |
| 9 | One alert per episode; known problem quiet but step marked spoken; one "recovered" line; one-off always alerted; keys only in the state; a refused alert is sent again and the step never claims it spoke; a refused recovery is posted again; a known problem with a refused recovery lets the workflow speak; an abandoned file is not "recovered"; unread parts stop the capture; receipts not committed alerts every run | `job.py`, `episodes.py`, `fno/alerts/step_output.py` `record_posted` | `test_job.py` | known alerts again; no recovered line; step not marked spoken; state saved though not sent; spoken though not sent; abandoned reported recovered; not-committed ignored. **Not caught:** "one-off kept open", an equivalent mutant (one-off keys never enter the state by another path) |
| 13 | Cron `30 2-16 * * *`, `contents: write`; the alert step (name starts "Alert") runs on every `failure()`, so O10's watcher sees it ran, and exits 0 without posting when the job already spoke (`posted == 'true'`: its alert, or an episode already alerted) (judge 359 SF1); env holds only secret references | `.github/workflows/circulars.yml` | `test_workflow.py` (the `if:`, the env, and the script run in bash with `POSTED=true`) | cron changed |
| 14 | Commits only `receipts/` and `research/ops/alerts/` | `wiring.py` | `test_the_job_commits_only_...` | — |
| 15 | Wired only in `fno/circulars/wiring.py`; tests never touch the network | wiring | all offline | — |

## Real output sample (criterion 16)

The committed classes against the real NSE and SEBI, a local folder in place of Drive, dry-run receipts and alerts,
16 Oct 2026, about 18:30 IST, two runs:

```
--- run 20261016T130000Z-aaaaaa
nse: 270 listed, 270 new, 17 file(s) saved
sebi: 25 listed, 25 new, 3 file(s) saved
receipts: (dry run, local folder)
exit 0
--- run 20261016T130100Z-bbbbbb
nse: 270 listed, 0 new, 0 file(s) saved
sebi: 25 listed, 0 new, 0 file(s) saved
receipts: (dry run, local folder)
exit 0
295 rows; Counter({'not_kept': 275, 'saved': 20})
```

After the review fixes: NSE 271 circulars in 14 days, 17 relevant, fresh; SEBI 25, 3 relevant, fresh. The first
scheduled run's log and receipts will be added after merging.

## Builder self-review (quality rule 3)

Two independent review passes:
- **Pass 1, before judge 353's text changes**, ran live against real data. It found that NSE lists a circular once
  per department, and keeping one department lost the F&O flag on 2 of 4 F&O circulars. Fixed by merging.
- **Pass 2, a review agent on the diff:**
  1. **Blocking, accepted:** the state was saved before the alert was sent and its outcome was never checked. A post
     Slack refused then stayed "already alerted" for ever, and the backup line was suppressed. Now a key is saved
     only after a delivered post, new problems and recoveries share one post, and `spoken()` runs only after a
     delivered post. Tests and mutations above.
  2. **Should fix, accepted:** at the calendar's end, `previous_session` raised inside the capture, losing the run
     under the wrong reason. It is now its own problem.
  3. **Should fix, accepted:** an abandoned file also produced "recovered". It no longer does.
  4. **Should fix, accepted:** a failed list part replaced the run's other problems, and a re-served file with new
     bytes could be wrongly abandoned. Problems are now kept, and a receipted file counts as saved.
  5. **Minors, accepted:** NSE `data` not a list; partial SEBI row parse. Not changed: a `first_seen_at` without a
     time zone (this code never writes one).

## After judge 359 (FAIL, 1 should-fix)

- SF1 accepted: with `posted == 'true'` the old condition skipped the alert step, and O10's watcher, which stays
  quiet only when an "Alert"/"One line to" step ran, would have posted on every hourly run of an episode. The step
  now runs on every failure and exits 0 quietly when the job already spoke.
- Minor accepted: the header says 14 days. "NSE and SEBI also publish on holidays" is corrected: NSE issued
  circulars on 13 non-session days of 2026, but your sample (2 Oct, weekends) had none.

## Gates

On the unshallow clone (head after judge 359): 7425 passed; ruff check and format clean; `check_imports.py` and `check_records.py` clean.

## Honest limits

- SEBI relevance is wide on purpose (16 Oct: 3 of 25, two of them commodity-derivatives circulars). An NSE F&O
  rule filed under another department with none of the F&O words is listed but its file is not pre-saved.
- First-seen time is the run's time, so at best hourly. The list starts at the first run: 14 days back for NSE, the
  latest 25 for SEBI. The first run lists about 300 circulars and saves about 20 files.
- `fno/circulars/` is the first live user of O9's `PartTable` (O9 step 2b comes later); store, receipts and cache are
  O9's tested code.
- When receipts or the state file fail to commit, that run sends a second post. If Slack refuses it too, only the
  Actions log and O10's row show it.
- `fno/alerts/run_location.py` is shared with A20a (the same file); `record_posted` is a small extraction in
  `fno/alerts/step_output.py`, and `StepOutputAlerts` now uses it.
