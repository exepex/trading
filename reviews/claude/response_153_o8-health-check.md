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
