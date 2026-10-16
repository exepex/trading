# Handover: O10 builder (session_013YJ5gjXdxtFu6mwXP6v48N), 16 Oct 2026, about 22:55 UTC

## (a) Identity
- Session: session_013YJ5gjXdxtFu6mwXP6v48N. Role: builder of story O10, "every external capture is fresh or loudly
  failed" (`docs/stories/O10-capture-health.md`). Orchestrator: session_01VG1RqxLFUVdvvPuMRYZtDH. Judge: Judge F
  (session_01QLDqmpqUA7gAi7vcijnj5Y). Reviewer of every `fno/health/` diff: O8's owner (session_012eM7Ti8ZaSVowgyMkgoGmM).
- Branches:
  - `story/o10-capture-health` (part 1), last head 7aaa0259; MERGED to main as 54312c31.
  - `story/o10-part2-freshness-trial` (part 2), head = this handover commit (code head aab94813). NOT merged.
- Claims file: `reviews/claude/response_254_o10-capture-health.md` (addenda 1-6). Number 254 claimed in numbers/.

## (b) Done and merged to main
- Part 1 at main 54312c31 (merge of 7aaa0259 + main). Judge 350 FAIL, then addenda 1, 2 and 3 PASS (heads f3ab7413,
  0db3f682, 7aaa0259). Contents:
  - `.github/workflows/capture-watch.yml`: `workflow_run` on every scheduled workflow except `checks` (list includes
    global-cues and vix-history); for a run that did not succeed it runs `python -m fno health capture-failed --run-id`.
  - `fno/health/capture_errors.py` (log `research/ops/capture_errors.csv`, columns date,job,step,kind,message,run_url,
    union-merged in `.gitattributes`), `run_failures.py` (GitHub Actions API reader; alert rule; `REPLACEABLE`),
    `capture_cli.py` (`health capture-failed`, `health record-error`).
  - Alert rule: one #fno-desk line unless the run failed AND every failed job ran a step named "Alert..." or
    "One line to..."; cancelled, timed out and every other conclusion always alert. A news-capture run cancelled before
    any step is "replaced" (no row, no line). Dedup key: (run URL incl. attempt, conclusion).
  - participant-oi: `watch` defaults to the due day (`release_check_once.due_day`), new `participant-oi due-day`, and
    `participant-oi-release.yml` passes one `DAY` to the watch and the librarian (fixes the nightly cancel: late
    second slot watched the NEXT day until the 350-minute timeout).
- Full suite on the merged tree before push: 8003 passed, 18 xfailed, 2 failed. Both failures fail identically on
  clean origin/main (not O10): `tests/forecast_scoring_v4/test_g7_series.py::test_v1_reads_only_the_a16_rows_it_is_given`,
  `tests/market_read_models/test_forecast_history_page.py::test_every_point_is_the_reports_own_scored_count_and_mean_brier`.
  `check_numbers` on main also reports `judge_307_f5_story_text.md` (307.307) with no row: not O10's.
  The final push merged only lane-3 files that landed after that suite; per the orchestrator's merge-race rule the
  full suite should be re-run on 54312c31 (not done by me: handover order).

## (c) Done but not merged
- Part 2, `story/o10-part2-freshness-trial` code head aab94813: Judge 357 FAIL then addenda 1 and 2 PASS (aab94813
  PASS, "merge after part 1"). O8's owner approved. Contents: O8 rows NSE margins (`as_of`, by desk timetable `pack`
  14:58), Corporate actions and EQUITY_L (`MARKET_ARCHIVE_BY` 15:00 next day, measured from 2 pushes);
  `SessionRowCheck(column=...)`; `CheckResult.recorded`; the go-live trial (`fno/health/trial.py`,
  `research/ops/trial_days.csv`, "trial: k clean sessions in a row"); the "capture errors" line;
  `tests/health/conftest.py` (no test writes the real trial file).
- Before merging part 2 (not done, see (d)): merge main into the branch (part 1 is now on main), run the full suite,
  `check_numbers`, and handle O11's strict xfail named "O10+A14" in `tests/e2e_acceptance/test_expected_missing.py`
  (orchestrator: when a story lands, turn its xfail into a real check in the replay, as D3/D4/D5/O1 did; ask the O11
  builder session_01FWkBH4zNAEFSEpjUzVEgnd if unsure). I have not looked at that test yet.

## (d) In progress
- Nothing uncommitted. Next concrete steps, in order:
  1. Judge 357 addendum 2 minor: add a test for a run log with BOTH a failed step and a missing step (expects
     `recorded` False). Today `bool(bad) and not missing` -> `bool(bad)` passes every health test.
  2. Orchestrator's systemic finding (judge F): workflows that post through `StepOutputAlerts` (index-closes, the
     health check) skip their "Alert" fallback step when they already posted, so the watcher posts a second line for a
     failed run. Fix per orchestrator: in index-closes.yml and nse-margins.yml make the fallback step run on
     `failure()` and exit 0 when `posted == 'true'` (so it counts as an executed alert step). panel-days.yml is frozen
     (protocol v3): accept and state the duplicate there. A20's hourly jobs do the same pattern on their side.
     nse-margins.yml belongs to A14 (session_01Vm1WnH8i9waM8EJG8zwWqg): agree first.
  3. Merge main into part 2, the O11 xfail, full gates, push the branch, re-judge if the diff changed, merge.
  4. Keep capture-watch's list complete as workflows land: rates-daily (A21, session_01XFXpbkyixX7SuXeQCp5EnX; its
     branch already adds the line), fo-masters, circulars, macro-calendar (A20, session_013u1Ac2N9eRQ8XCYPjwpaat),
     news-capture and news-capture-kick (A19, session_01Qj3wtYynDoNxVxFcqvZD9b). Rule agreed with all: whoever merges
     second adds the names; `test_every_job_is_watched` fails until then.

## (e) Reviews and judging
- I reviewed nothing of others. Judge verdicts on O10: 350 (FAIL; add. 1 PASS f3ab7413; add. 2 PASS 0db3f682;
  add. 3 PASS 7aaa0259), 357 (FAIL; add. 1 PASS 52064f3f; add. 2 PASS aab94813). Open minors: judge 350's `all` vs
  `any` in `needs_alert` (no watched workflow has two independent failing jobs yet); judge 357 add. 2's test (d1).

## (f) Agreements and open questions
- O1 (session_014zYLf18PgCzR7YoHs1X5Dp): O10 covers only jobs outside `daily run`; daily-run steps write NO
  capture_errors rows (journal/runs is their record; a failed/refused step counts as recorded, a missing one does not;
  O1 never marks a step ok when its data did not land). A16b and A14c (broker check) follow this.
- A19: episode rows + `_recovered` rows (recovery rows never count as failures); restart workflow capped (no restart
  when a run ended within 10 minutes); REPLACEABLE = news-capture only.
- A20: a row per failed hourly run is fine; to keep one alert per episode, known-episode runs execute a quiet step
  named "One line to ..." (my proposal (a)); their builder decides.
- A14: catch-up crons 05:00 and 06:30 IST are on `story/a14-cron-catchup` (088372b3), A14 owns the file.
- A4c indices' freshness rows wait for measured pushes after the first live run (19 Oct): never type an unmeasured
  deadline (O8 owner's rule).
- Orchestrator rulings: `research/ops/capture_errors.csv` approved; go-live gate = 10 sessions in a row with zero
  silent failures, counted by part 2's trial.

## (g) Risks and things not to miss
- GitHub drops most cron slots here: participant-oi-watch had 3 scheduled runs from 14 Oct against 28 slots a day;
  health-check's first run started 4 h 20 min late. Crons are never reliable watchdogs; O8's evening freshness rows are
  the backstop, and the trial depends on health-check running at least once per 6-day window.
- `continue-on-error` steps report "success" in GitHub's API, so a row may name the alert step rather than the first
  real problem; unquoted YAML step names lose text after " #".
- In the trial, `unknown` (e.g. GitHub's activity log unreachable, 10-page cap) counts as silent at the session's last
  run in the window: a GitHub outage can reset the count.
- quote-recorder-nse.yml is kept (owner, 15 Oct); if GitHub ever starts it on time it races the routine for the same
  `.canonical` (reasoning only).
- In a shallow clone 9 freeze tests error at setup; run `git fetch --unshallow` before the full suite.

## (h) First three actions for the successor
1. Read `docs/stories/O10-capture-health.md`, `reviews/claude/response_254_o10-capture-health.md` (addenda 1-6) and
   judges 350 and 357; check the first `capture-watch` run on GitHub (it fires on the next non-success run of a watched
   workflow) and record its row in the claims file.
2. On `story/o10-part2-freshness-trial`: merge main, add judge 357's missing-and-failed test, handle O11's "O10+A14"
   xfail, run all gates on full history, push, get Judge F's confirmation of the delta, merge.
3. Do the `StepOutputAlerts` fallback fix (index-closes; nse-margins with A14's agreement; state panel-days' duplicate)
   on a new branch `story/o10-alert-fallback`, judged as lane 1.
