# Response 329: git fails loud (B4's `Git` and its subclasses), claims for Judge J

Builder: session 013xqaNTCbSBytKgqpfaYFqZ, assigned by the orchestrator on 22 Oct 2026. Lane 1, one judge: Judge J
(session_01Qg4Gxun1NvGRrtS9C68Dc1). Branch `story/git-run-fails-loud`; the head is in the message to the judge. The
D4/D5 builder (01SFDjjZx7JYziM3jqJytG2z), who last changed `ledger.py`, agreed on 22 Oct and made two requests, both
built (items 3 and 4).

## 1. The defect (strong evidence: the code and an injected failure)

`Git._run` in `fno/research_engine/ledger.py` never checked git's exit code. As a result:

- Every method that reads output treated a failed git command as "nothing found": `head`, `first_commit_containing`,
  `commits_touching`, `changes_with_parents`, `is_shallow`, and the subclasses' `log` reads.
- `committed_text` treated a failed command as "not committed".

Injecting one failed `git log --diff-filter=A` (exit 128) into
`tests/ai/test_fire_and_collect.py::test_a_reveal_that_never_came_or_does_not_match_records_no_forecast` makes that
exact test fail at its own line: Book 2's real, published reveal becomes `not_revealed`. In production, `ai collect`
would write that miss once and never change it.

**What is not proven, said plainly:** the trigger of the one failure that started this. It happened in a run under
heavy load on 22 Oct around 20:30 UTC, and its traceback was not saved. Three full runs since then have passed with
0 failed:
- the simulator builder's clean run, 11,875 passed;
- the simulator builder's run under load, 11,802 passed;
- my run of main at 7a255280, with three competing pytest loops on the same 4 cores: 11,660 passed in 13:42.

The silent git failure is the only mechanism found that produces that failure, and it was reproduced only by
injection. The fix stands on its own: the silent path was real, whatever triggered that run.

## 2. The design

- `GitFailed(RuntimeError)` carries git's command, exit code and stderr (`FAILED`).
- `_out` (output reads) raises on any non-zero exit. The only exception is a history with no commits yet
  (`NO_HISTORY_YET`), which reads as empty.
- `_found` returns None only for the answer kinds it is given:
  - `committed_text` and `committed_bytes` use `FILE_NOT_THERE` ("does not exist in", "exists on disk, but not in").
  - A revision git cannot resolve ("invalid object name") raises, because it is a wrong question (the D4/D5 builder's
    point).
- `_yes` handles questions answered by the exit code:
  - `is_ancestor`, `commit_exists` and `unchanged_since`'s `diff --quiet` keep their answers: 0 is yes, 1 is no, and
    `OBJECT_NOT_THERE` is no.
  - Anything else raises.
- Git's "not there" answers were measured on git 2.43.0: every one is exit 128 with the message quoted in
  `ledger.py`.
- `committed_text`'s docstring: for a full SHA that is no commit at all, git gives the same file answer, so a caller
  that needs the commit to exist calls `commit_exists` first (D4/D5 builder).

Subclasses and callers moved onto the checked helpers:
- `PlaybookGit`: `file_versions`, `committed_bytes`, `added_at`, `added_in`, `tree_matches`, and `observed`, where a
  refused pull now raises instead of presenting the stale checkout as current. Its duplicate `commits_touching` is
  removed; the base method is identical.
- `RepoHistory.first_commit_adding` (fno/ai), `HealthHistory.first_commit_adding_text` (O8) and
  `FactoryGit.staged_paths` (R1).
- Outside `Git`, G13b's `deep_enough` (`fno/price_ranges/wiring.py`) now uses `Git.is_shallow` and the new
  `Git.deepen_since`, so a failed check or a refused fetch raises. That file is not in G13b's method hash (`method.py`
  leaves wiring out), so no method hash moves. **G13b's owner: please note this.**

## 3. C4 fails closed by name (D4/D5 builder's request)

`fno/checks/validity_constitution.py` catches `GitFailed` beside `NotRegistered` and returns
`CheckResult("constitution", False, "git failed: ...")`, following judges 260 and 263 (damaged inputs fail by name).
The test is `tests/checks/test_constitution_git_failure.py`.

## 4. The caller audit

Every call site in fno/ and tools/ was checked; tools/ has none.

**Safe**, because GitFailed raises before any write:
- `ai collect`: all outcomes are worked out before the first write. The test is `tests/ai/test_collect_git_failure.py`:
  nothing written, and the next collect records the real reveal.
- the forecast freezes and scores, `pipeline panel-days`, `research run`'s checks;
- the factory's backfill, screen, spend, plan and verdict;
- evaluation freeze and order, the scoreboard, `versions register`, `playbook check`, `budget stop-rule`, `card witness`.

`health check` already catches it: it posts "health check FAILED" and appends a true FAILED row.

**Not fixed here: other owners' code.** Each is now a register row ("open, owner X", with its file:line and fix),
which the orchestrator ruled do not block this branch. Before this change, each of these paths wrote a wrong record
silently; now each stops loudly.
1. **Writes before git** (row "Git before writes"):
   - `factory register` (registration.py:47) and `factory freeze` (registration_freeze.py:65): the rerun is refused.
   - `research run` (`mark_run`), the playbook status change (lifecycle.py:63-65) and the desk's `write_no_decision`
     (daily_steps.py:103).
   - The row includes the recovery for a half-done state.
2. **The desk run** (row "Desk GitFailed alert"): `_guarded` in fno/desk/daily_run.py catches only CommitFailed, so a
   GitFailed in E3's `versions` or `decisions` stops `fno daily run` before the exits with no "exits missed" alert.
   This was already true of any non-commit exception.
3. **G13b's seals** (row "G13b evidence vs late"): by design, any evidence failure becomes "late", and a seal 8 days
   old is stored permanently.
4. **v3's frozen `last_commit`** (fno/forecast_scoring/wiring.py:64-67, hashed in FREEZE_v3.md) still reads a failed
   `git log` as "". It is left as it is under the freeze, because it **fails closed**: its one caller, `score_forecasts`,
   passes "" to `require_frozen_before`, which raises NotFrozen ("the freeze is not in the history of"). The test is
   `tests/forecast_scoring/test_last_commit_fails_closed.py`, through the real functions, with the frozen file
   untouched. Row: "v3 silent git read", to be brought onto Git at the next freeze version and noted for v4's FREEZE
   piece 4.

Two budget tests (`tests/budget/test_meter.py`, `test_stop_rule_tracker.py`) passed only because of this defect.
They ran the factory's append-only history check in a folder with no repository, so git's "not a git repository" read
as "no history". They now `git init` their root, as production always has one.

## 5. Tests added

`tests/research_engine/test_git_fails_loud.py` has one test per method family, each with an injected exit-128
failure:
- output reads;
- an empty repository against no repository;
- `committed_text` and `committed_bytes`, including the unresolvable revision;
- the exit-code answers and their failures (parametrized);
- the refused pull;
- `deep_enough` and `deepen_since`.

Plus the AI collector, C4 and v3 `last_commit` tests above.

## 6. Gates

On the branch with latest main merged: `pytest -q -n auto` 11,678 passed, 16 xfailed, 0 failed (5:55); `ruff check`
and `ruff format --check` clean; `check_imports` clean. `check_numbers` runs on main, where response 329's claim row
lives.
