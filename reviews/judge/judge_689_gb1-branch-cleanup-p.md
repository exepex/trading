# Judge 689: GB1 branch clean-up, `story/gb1-branch-cleanup` at 52b58038f (code tip e2afda0b8), judge P

**FAIL**, lane 1 (a workflow that deletes refs). 1 blocking, 2 should fix, 2 minor. Second judge: Q (judge 688).

## Criteria

| # | Criterion | Verdict | Evidence |
|---|---|---|---|
| 1 | Nothing in use is deleted | PARTLY | main, keep list, open PR and unmerged register branch are protected (plants 1-4 and 17 caught). Findings 1 and 3 break the rule |
| 2 | Merged goes after the grace, not before | NOT MET | Finding 2: `landed_at` is None for 224 of 453 merged branches |
| 3 | Rehearsal runs by run-id age | MET as code | Both windows tested; the rule itself goes against an owner answer (finding 1) |
| 4 | Idle unmerged go only in the one-off, never with unfinished work | PARTLY | Code paths are protected; captured data is not (finding 3) |
| 5 | Head must match the plan; gone is skipped; failure counted; dry run deletes nothing | MET | `test_delete_goes_through...refused_after_a_push` passes; plants on `head != expected`, `head is None`, `not apply`, exit code and `--force-with-lease` all caught. My dry run (fresh fetch, 7 open PRs from GitHub, 11:2x UTC): inventory 386 WOULD DELETE, 0 SKIP; merged 367 |
| 6 | Workflow shape | MET | dry-run default, schedule gate, `ref: main` plants caught; `APPLY` expression read: a dispatch without the box ticked gives `false`, the schedule `true`; checkout `fetch-depth: 0` fetches every branch |
| 7 | Inventory well formed, never deletes main or a kept branch | MET | test passes; duplicate-row plant caught |

## Findings

1. **Blocking: rehearsal branches go against an owner answer.** `docs/stories/REH1-rehearsal-mode.md:193` (owner, 24 Oct): "Keep the `dryrun/` folders and the `rehearsal/` branches, so the owner can inspect them." The 25 Oct words are about merged and feature branches; a rehearsal run's branch is neither, and REH1n is still with its judges. The story asks the owner (Facts, `rehearsal/*`) but still deletes 4 runs now and all of them after 7 days. Fix: make `rehearsal/*` `keep` in both rules until the owner's quoted answer is in `docs/DESK_DECISIONS.md`. Judge Q reports the same issue (judge 688).
2. **Should fix: the 24-hour grace is measured from the wrong time for half the branches.** `branch_git.py::_landed_at` uses `rev-list --first-parent --ancestry-path sha..main`. On git 2.43 this prints nothing when the tip is not the merge's own second parent (for example, merged into another branch and then into main). Then `landed_at` is None and the grace counts from the tip's commit time. On the real origin: 224 of 453 merged non-fast-forward branches. Real case: `story/o1-r1r2-step-safety-b` reached main at 24 Oct 11:59 UTC (first-parent commit holding its tip), and `--mode merged` already listed it for deletion inside 24 hours. The test only covers a direct second parent. Fix: take the oldest first-parent commit among `rev-list --ancestry-path sha..main` (without `--first-parent`), and add a test with a two-level merge.
3. **Should fix: captured data on idle unmerged branches is deleted.** `claude/lucid-ptolemy-hoov99` and `claude/lucid-ptolemy-ml36q5` (both `delete`) hold 16 Oct 15-minute status rows (`research/data/intraday/slots/2026/10/16/*`, 11:00-12:30). They differ from main's own rows (other capture times and quote counts), so they are not on main. `CODE_PATHS` covers only `fno`, `tools`, `.github`, `config.yaml`. Captured data is write-once and outside "lose a feature branch". Fix: also treat `research/data/`, `receipts/` and `journal/` as work only on this branch (`keep-unsure`), then rebuild the inventory.
4. Minor: plant survivor. `unique_code_files` with `if line` in place of `startswith("+ ")` also counts `-` lines (patch already on main), and no test catches it. It only over-protects. Add a patch-equal commit to the test.
5. Minor: the register row says `tests/tools/` and "CLAUDE.md 'Branch' (two lines)". The real ones are `tests/gb1_branches/` and five lines.

## Plants

20 planted (rules 8, cleanup 7, git 2, workflow 3). 19 caught; 1 survivor (finding 4). Gates on the branch: `pytest -n auto` 18114 passed, 1 skipped, 13 xfailed; ruff, format and `check_imports` clean.

## Notes

- More register rows than O14's and CP1's say that code continues on an already-merged branch (`story/e6-s2-missed-execution`, `s6-scorecard-measures`, `s3-scoreboard-a`, `lr3-drift-cusum`, `f2-analyst-cards`, `g10-build`, `rm2-real-money-record`, `oss1-vollib-reference`). Deleting them loses no commit, because all of it is on main, and the next push recreates them. Still, the orchestrator should confirm which of these are in use and add those to the keep list.
- The open PR list has grown from 5 to 7 (`story/f5-code`, `story/ing1-data-ingestion`). Both are protected at the run's own `gh pr list`.
- Fast-forwarded merged branches stay `keep-unsure` forever. That is the safe side and Judge Q's finding; I agree it is a gap against CLAUDE.md's new line.

## Addendum 1

Round 2 at `640445b94` (judge P): **FAIL**, 2 should fix still open. Re-checked on a fresh fetch of every branch,
26 Oct 04:15 UTC.

| Round-1 finding | Verdict | Evidence |
|---|---|---|
| 1 Rehearsal branches (blocking) | Fixed | `ongoing_decision` gives `KEEP` and `inventory_decision` gives `KEEP_UNSURE` (`REHEARSAL_WHY`). The inventory has 49 rehearsal rows, none `delete`. Test `test_rehearsal_runs_are_kept_for_the_owner` |
| 2 Grace measured from the wrong time | **Not fixed** | `branch_git.py::_landed_at` is unchanged (`--first-parent --ancestry-path`). On the tip: 225 of 470 merged branches have `landed_at` None. Three real branches would be deleted now inside their 24 h: `story/gw1-groww-rate-guard` (reached main 25 Oct 09:20 UTC, tip 01:09), `story/reh1q-scheduled-reads` and `story/reh1s-guard-recorders` (reached main 25 Oct 05:17 UTC). No answer or pushback was given. Fix as asked: the oldest first-parent commit among `rev-list --ancestry-path <sha>..main` (no `--first-parent`), plus a test where the tip is not the merge's own second parent |
| 3 Captured data on idle branches | **Not fixed** | `CODE_PATHS` now adds `tests` but not `research/data`, `receipts` or `journal`. `claude/lucid-ptolemy-hoov99` and `-ml36q5` are still `delete` in `docs/branch_inventory.csv`. The orchestrator (25 Oct, to this judge) ruled: keep them `keep-unsure` and report them |
| 4 Survivor on cherry lines (minor) | Fixed | `test_a_cherry_picked_commit_is_not_unfinished_work` |
| 5 Register row text (minor) | Not checked further | Text only |

Also accepted: dropping `on_main_line` (Judge Q's finding). A branch with no commit of its own loses nothing when it is deleted, and the next push recreates it.

This is my second and last round: if the builder disputes 2 or 3, the owner decides (JUDGE.md "Rounds"). A
tip that fixes both with the tests named above will be re-checked narrowly on request.

## Addendum 2

Narrow re-check at `3e6c4f85e` (judge P), on the builder's request after addendum 1: **PASS**, lane 1. Findings 2
and 3 are fixed; no new finding.

| Finding | Verdict | Evidence |
|---|---|---|
| 2 Grace timing | Fixed | `_landed_at` binary-searches main's first-parent line with `merge-base --is-ancestor`. This is correct because once a main-line commit holds the tip, every later one does. New test `test_a_branch_merged_through_another_branch_landed_with_the_last_merge`. Checked on a fresh fetch of every branch: all 447 merged `delete` rows have a landing time, and none is inside 24 h. My 16 differences were fast-forwarded tips that sit on main's line themselves, where the tool's answer (the tip itself) is the right one. `gw1-groww-rate-guard` and `reh1q-scheduled-reads` are now `keep-unsure` |
| 3 Captured data | Fixed | `WORK_PATHS` adds `research/data`, `receipts` and `journal`. `claude/lucid-ptolemy-hoov99` and `-ml36q5` are `keep-unsure`. Test `test_a_branch_that_only_adds_capture_rows_holds_unfinished_work` |

Inventory: 460 delete, 31 keep, 109 keep-unsure; 0 rehearsal rows deleted. Plants: 4 more (`research/data` removed,
landing one commit early, a wrong binary-search bound, the work-files rule off), all 4 caught. Gates on the tip:
`pytest -n 3` 18116 passed, 1 skipped, 13 xfailed; ruff, format and `check_imports` clean.
Minor (no block): `unique_work_files`' docstring and the `work_files` comment still say "code files".
