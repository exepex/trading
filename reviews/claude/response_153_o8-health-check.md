# Response 153: story O8, the daily health check (story text for the judge)

The story is `docs/stories/O8-health-check.md`, on branch `story/o8-health-check`. The orchestrator gave a go for the
story text only (noise-and-fairness step 6, 15 Oct 2026). No code is written yet.

## Sources read
- Handover, section 11 (`conversations/2026-10-15_handover_noise_fairness.md`).
- Response 144, items 6 and 18.
- The owner's v4 timeline row in `docs/DESK_DECISIONS.md`.
- Every job's committed output on `main`. File and line evidence is in the story's table.

## Choices for the judge to check (reasoning only unless marked)

1. **The window is "last N sessions", not "today".** This answers the cron-lateness trap in the simplest way: every
   run, early or hours late, re-checks the same 5 sessions, and evening jobs that are not due yet are listed as
   `not due`. N = 5 fits GitHub's one-week activity log (some evidence: the log's `time_period=week` in
   `fno/ai/receipts.py`).
2. **Push times reuse F1's `PushReceipts`.** No second GitHub client is written. The commit that added a file comes
   from `git log --diff-filter=A`.
3. **Deadlines are imported from their owners.** One exception: the 15:13 canonical pull lives only in
   `forecast-capture.yml`, so it is a named constant here until step 5's timing-consistency test.
4. **Blank forecast probabilities are reported, not failed.** Whether a blank counts is the forecast protocol's rule
   (G9). The health check reports that the rows exist and are on time.
5. **The watcher of the watcher is the next run, using `research/ops/health_runs.csv`.** A job that never runs at all
   is caught only by the missing 18:00 message (Known limits).
6. **The cron is 17:51 IST, not 18:00.** This is a jittered minute, per the scheduling guidance. A late start is
   harmless (choice 1).

## Facts found while measuring (strong evidence)
- The NSE recorder's canonicals for 14 and 15 Oct both hold `none`. The first real run would report them as
  `missed (none)`.
- `journal/runs/` and `research/data/intraday/slots/` do not exist on `main`: the desk run and A16's marks are not live.
  Their checks start at a `live_from` date set by the orchestrator.
- `forecast-scores.yml` writes reports on some days only. `nse-margins.yml` is not scheduled. Both are left out, with
  the reasons in the story.

## Questions for the orchestrator
1. The response number 153 is my pick, because 150-152 exist on other branches. Please confirm or reassign it.
2. The `live_from` dates for the desk run and A16: should they be the first live day of each, set when that goes live?

## Addendum 1: judge 164 (FAIL on 2f3f777, text only). All ten findings checked and accepted.

| Finding | My check | Change in the story |
|---|---|---|
| SF1: deadline ownership | **True.** `fno/ai/timing.py` holds `LATEST_START = time(15, 13)`, so my "no module owns 15:13" was wrong. A8 23:30, closes 12:00, panel 13:00 and flows 23:59 exist only as cron comments. | 15:13 is imported from `LATEST_START`. The four others are health-owned constants (`A8_RELEASE_BY`, `INDEX_CLOSE_BY`, `PANEL_DAY_BY`, `FLOWS_BY`), each with its cron source, listed for step 5. Criterion 3 greps that they are the only time literals in `fno/health/`. |
| SF2: N = 5 versus the 7-day log | **True by reasoning.** Five sessions span more than 7 days in any holiday week. The judge measured 86 of the 2025 runs; I did not re-run that count. | Accepted the judge's suggestion: the window is the sessions dated from 6 days before the run's IST date up to that date. The oldest push it can need is at most 6 d 8 h 47 min old, so it stays inside the log on every run. Criterion 1 adds the 2025 check: no push older than 7 days. |
| SF3: criterion 1 contradicts the window | **True.** A 03:10 run on a session day moves the window. | The window is defined once. Criterion 1 now requires that session D is checked by every run from D 17:51 to D+6 23:59 and not after. |
| SF4: which time decides "late" | **True.** Forecasts and the desk use in-file times, by their own protocols. | The table has a "time that decides late" column for each row. Criteria 2 and 4 are per row. |
| SF5: one line per (check, session) | **True.** NSE alone would repeat for 5 days. | One line per check, listing its bad sessions. |
| Minor 1: a stopped AI book | **True** (`fire.py:55-65`). | The fire log's reason is shown. |
| Minor 2: NSE label | **True.** The owner moved NSE into the 14:33 routine (conversation of 15 Oct). | The label is "in the 14:33 routine; the Actions job at 14:20 is a fallback". |
| Minor 3: watcher bounds | **True.** | Missing days are reported only inside the window and after the file's first row. Criterion 6 says what a same-day re-run does. |
| Minor 4: "closed day" | **True.** Closed days never enter a window of sessions. | `not expected` is only muhurat, before `live_from`, or the desk's `skipped` step. The closed-day column is dropped. |
| Minor 5: A16 has no deadline | **True.** | It says A16's own per-mark status is final and is reported as counts. |
| Note: F1's 10-page cap | Accepted. | Added to Known limits. |
