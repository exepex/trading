# Handover: O1 / O2 builder (session_014zYLf18PgCzR7YoHs1X5Dp)

Written 21 Oct 2026, after the restart. Everything listed is pushed; nothing is held only in a container.

## (a) Identity

- Session `session_014zYLf18PgCzR7YoHs1X5Dp`. Builder of story **O1** (the daily run, `fno daily run`) and story **O2**
  (failure handling, end to end). The orchestrator is `session_01VG1RqxLFUVdvvPuMRYZtDH`; my judge is judge D,
  `session_01Pb8z2koLuxty7mbujFpgZa`.
- Branches:
  - `story/o1-part-start` at `f85e362f`: the rerun-crash fix 6776f7d1 plus a merge of main;
  - `story/o2-failure-handling` at `af9e9dd3`: O2 code rounds 1-3, the e2e harness, and WIP rows.

## (b) Done and merged to main

- O1, judge 178 addenda 14-18 PASS, merged at 1d01fd08 and later. That includes the CLAUDE.md "Daily desk routine"
  section and E2d's `trade_marks` resolution (judge 178 add. 17).
- O1 fix, "the 3 pm parts start no earlier than A4's earliest start (14:38)": judge 293 PASS, on main as 7b08108c.
- O2 story text revisions 1-6: judge 204 addenda 1, 3 and 5 PASS. Revision 6 is at 716e0bf6.
- The orchestrator reports the daily run gave "day done" on 19 and 21 Oct. O1's criterion 9 evidence still has to
  be written into response_165 for judge D.

## (c) Done but not merged

1. **`story/o1-part-start` f85e362f (fix commit 6776f7d1)**, sent to judge D on 21 Oct, no verdict yet.
   - The bug: a rerun whose log already holds `quotes` never opens the day, so `start_due` raised `TypeError` on
     the rerun's first wait. On main today, every mid-day rerun crashes.
   - Merge it on the PASS.
2. **`story/o2-failure-handling`**, not yet sent for a code verdict:
   - **round 1** (9fe595d4): the hard limit on every git call (`fno/desk/git_limit.py`). The process group is
     killed, only the call's own new locks are removed, and nothing is removed while any git process is alive. A
     stopped push is "not confirmed". The same lock rule covers `CommandStep`'s 600 s stop.
   - **round 2** (47b6212d onward): the e2e harness `tests/e2e/`, plus two root fixes. The run now passes its
     `root` to Book 1's orders and to the execution capture's quote folder.
   - **round 3** (aab33abd): the outage families. Also the G1 fix: a 3 pm part that failed without its own alert now
     gets one O1 line (`fno/daily/quote_parts.py` `_alert`).
   - **WIP** (2f6df417): the never-starts row (passes) and the reflog kill switch (`Day.committed`).
   - Gates at af9e9dd3: everything passes except 2 tests that are red on main itself
     (`test_g7_series::test_v1_reads_only_the_a16_rows_it_is_given` and
     `test_forecast_history_page::test_every_point_is_the_reports_own_scored_count_and_mean_brier`).

## (d) In progress (O2, rows still to build; text revision 6 is the contract)

- **Kill-and-rerun.** Kill with `day.clock.kill_when = lambda: day.committed(f"Desk run {day} step {k}")`, which
  raises `Killed`, a `BaseException`, so no step handler catches it. Then a fresh `day.run()`.
  - Compare the end state with the twin day.
  - Also cover: the restart after 15:00 ("pack built: False, already holds a different pack"; the orchestrator,
    from O11).
  - The "between record and commit" kill needs a real process kill. Idea: the day runs in a subprocess, and a
    `commit-msg` hook in the fixture checkout kills it.
- **Hung git and hung command:** a hanging hook in the fixture checkout, and a `Foreground` child that never ends.
- **Trade rows**, through fixture data only:
  - a `paper` fixture strategy with committed evidence (`tests/playbook/test_loader.py` `approved_repository`);
  - a registered research shadow, with registry rows dated on or before 13 Oct;
  - futures in the snapshot meta, which needs a fake `LevelSource` for the recorder;
  - NSE's F&O file for C4's listing check, served by the NSE archive fake.
  - Then: exits held, the next-session block (already visible without trades: `test_never_starts.py`), E4c, data
    and limits, Drive (b), and the shadow cases (a), (b) and (c). Case (c) is `xfail(strict=True)` naming the D2 gap.
- The test that the source tree's `playbook/`, registry and versions files are byte-unchanged after the suite.

## (e) Reviews done for other stories (plug-ins into `DAILY_RUN_STEPS`)

- **Approved:**
  - A16b `candles`: merged to main b6256a9a. The `locks=locks` line is added in O2's branch.
  - G13 `price_distribution` (story/g13-price-distribution 3600b911): after `card` and before `candles`; it passes
    `waiting`.
- **Agreed:**
  - F1t: the order pack, ai_fire, book1, ai_collect, decisions; its receipt observer is a child that runs
    `git ls-remote` only.
  - F5: its rule-default sheet is built inside the pack step; budget 5 s, still to be measured.
  - A14c: `margin_check`. No `capture_errors.csv` rows from the step and no alert of its own on failure. A mismatch
    is a finding, so its own alert with exit 0.
  - LR3: a `DriftReview` with `open_positions` 0.
  - M1 and G7: `record_folders()`.
  - O10: it covers only jobs outside the daily run. A step is never `ok` when its data did not land.

## (f) Open questions and agreements

- **O1 follow-up** (agreed with G7 and M1, not yet written):
  - weather and forecasts_v4 run before margin_check;
  - both start as children at the run's start;
  - per-step pathspecs from `fno.weather.folders.record_folders()` (main 61e7e690) and G7's `record_folders()`
    (story/g7-record-folders).
  - The 14:05 start and `live_from` go to the owner with the v4 freeze.
- **New from the orchestrator (21 Oct):**
  - plug FL1's three runs (08:45, 09:30, 15:45; the O11 builder `session_01FWkBH4zNAEFSEpjUzVEgnd`) into the run
    design, with no second runner;
  - coordinate on the A4 builder's unsent-alert fix (story/a4-unsent-alert-text, WIP), which is G2. If the A4
    builder does not answer, I own finishing it.
- The alert first-line story (design 6.5), still to write.

## (g) Risks and gaps a successor must not miss

- On main, a mid-day rerun crashes until story/o1-part-start 6776f7d1 is merged.
- **G2:**
  - What happens: a child command prints only "alert NOT sent: <reason>", not the alert's text
    (`fno/quotes/cli.py` `record_today`), so an unsent child alert is lost when Slack is down.
  - Owner: A4.
  - O2 test: a strict xfail in `tests/e2e/test_outages.py`.
- **The D2 isolation gap:** `fno/playbook/evaluate.py` 52-59. One shadow's failure aborts Book 1's whole decision. It
  needs a register row and an owner before the first paper approval (judge 204 add. 5).
- Nothing trades in production: `playbook/registry.csv` holds no `paper` strategy.
- Shadow fills and exits do not exist yet; that is E8 part 1b.
- C5 reads NSE contract IDs as OPTIDXNIFTY, so an NSE-fed 15:15 capture (Groww settings missing, so `quotes.provider:
  auto` falls back to NSE) would refuse every trade. The orchestrator assigned it to C5's owner.

## (h) The successor's first three actions

1. Get judge D's verdict on story/o1-part-start f85e362f, then merge it: pull, full suite on the merged tree, push.
2. Send O2 rounds 1-3 (story/o2-failure-handling af9e9dd3, claims in response_203) to judge D, and merge on the PASS.
3. Build the kill-and-rerun rows, then the trade fixture rows, in `tests/e2e/`.
