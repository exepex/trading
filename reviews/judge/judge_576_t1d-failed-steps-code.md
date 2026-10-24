# Judge 576: T1d code, the card names failed or refused steps (story/t1d-failed-steps at 5cbd3c4c7), round 1

**PASS, lane 1.** Judge I, routed by the orchestrator, 24 Oct 2026. Judged: `git diff 2c80be430 5cbd3c4c7`
(T1d's own changes; R2's round 2 at `2c80be430` is judged by judges B and E). It touches only `fno/cards/`
(4 files), `tests/cards/test_problem_steps.py` and `docs/stories/T-cards.md`; `git diff 2c80be430 5cbd3c4c7 -- fno/desk
fno/daily` is empty. Merges to main together with R2's -b head.

## Criteria

| # | Verdict | Evidence |
|---|---|---|
| 1 | MET | `problem_steps.py:23` calls O1's `run_log.problem_steps`; tests at lines 38, 52, 161; plants J1, J2, J8 caught |
| 2 | MET | no line on ok, not_live, empty log (tests 46, 52, 171); J14 (reason in line) caught |
| 3 | MET | `steps or {}`; `status_lines({})` gives no line (test 46) |
| 4 | MET | `runner.py:59` calls the same `problem_steps`; no `PROBLEMS` left in `fno/daily`; test 69 builds the real `DayRunner` line and the card line from one log |
| 5 | MET | reads only `RunLogReader.steps`; reader refuses odd shapes once (`rule_checks.py:71`, J6 caught); wiring pinned (J7 caught) |
| 6 | MET | `rule_checks.py:108,113`: failed/refused decisions give "decisions step failed: raised:...", `data_check_failed` (J5, J9, J11 caught); other statuses no code of their own |
| Judge 570.1 condition 2 | MET | failed decisions never list "status"/"reason": J3 and J4b (no status check, raw result as books) caught |
| Checklist (pending_judge_I) | MET | rule is O1's, not a copy; DecisionOutcome uses `problem_steps` itself, not the set; the three named plants caught (J1, J2, J3) |

Builder's points checked: odd shapes give "not readable (steps are not name -> {result: {...}})" and
`data_check_failed` (test 133, J6, J13 caught). Every committed run log on `main` (388 versions of 7 files in
history, my own script) has the accepted shape, so no real day turns unreadable. C4 refusals are read on every path
(J10 caught). `{"status": None}` is a step-level result (test 110). P5 (`book_results` dropped) is equivalent: it
empties only results whose status is failed or refused, which always carry `status` and are taken first by
`_decided`; my J4 (same mutation) survived for that reason, agreed.

## Plants

17 planted on the merged tree (tests/cards, tests/daily, tests/desk), each restored with `git checkout --` and
`__pycache__` cleared; tree clean after. 15 caught. Survivors: J4 (equivalent, above) and J15 (the problem line
emitted twice: no test says the line appears exactly once; criterion 1 says "one line"). J15 is minor: the code
appends it once (`ruled_status.py`), a regression would be visible on the card.

## Gates (5cbd3c4c7 merged with origin/main 385fe5b44, merge clean)

- `ruff check` clean; `ruff format --check` 2445 files formatted; `check_imports` clean (2574 files);
  `check_records` clean (9004 files).
- `env -u FNO_SLACK_BOT_TOKEN python -m pytest -q -p no:cacheprovider -n auto`: **15169 passed, 15 xfailed, 0
  failed** in 722 s, load average 10.9 at start, 5.2 at end. The builder's timing failure
  (`test_a_live_holder_keeps_its_lock_after_its_lease_expires`) did not recur in this full run; one run, no rerun
  needed. (A first attempt was stopped by my own tool's time limit before it printed a result; not counted.)
- Sizes: largest changed file 181 lines (`rule_checks.py`); no class near 350.

## Notes (not findings)

- Minor: a test asserting the problem line appears exactly once would catch J15.
- Minor: `RuledStatus(problems=None)` is optional only so T2's older tests construct it unchanged; production
  always passes it, and the wiring test pins that.
- Pre-existing (T2, not T1d): a per-book decisions entry that is not a dict (`None`) would raise `TypeError` past
  `_read`; none exists in history. A malformed previous-day log makes today's execution line unreadable (fails closed).
- Known limit, for the owner, not for me: when only a non-ruled step fails (for example `exits`) the card still says
  "Rule checks: no breach" with the problem line last. The passed text keeps the status unchanged; already put to
  the owner.
