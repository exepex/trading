# Judge 688: GB1, Git branch clean-up (story/gb1-branch-cleanup @ 52b58038f; code tip e2afda0b8)

**FAIL on 2 should-fix, round 1 of 2, Judge Q (Judge P the other; not read). Lane 1.** Own session
(session_01R97adLHpBi5iPjJiQQvhWE). Labels: strong, some, reasoning only. Nothing was deleted by me or by the story.

## Criteria

| # | Criterion | Result | My evidence |
|---|---|---|---|
| 1 | Nothing in use is deleted | PARTLY | main, keep list, open-PR heads and unmerged register branches are all `keep` (all 7 open PRs from GitHub checked); but 4 rehearsal branches are `delete` against REH1 Q3 (finding 1) |
| 2 | Merged goes after the 24 h grace; late push counts | MET | `branch_rules.py:96-102`; plants on `max(landed, tip)` and `--reverse` caught |
| 3 | Rehearsal runs by run-id age | MET as built | `rehearsal_branch`; plant on the window caught. Owner's permission open (finding 1) |
| 4 | Idle unmerged goes only in the one-off, never with code or recent activity | MET | plants on `recent_mentions`, `code_files`, `RECENT` caught; standing rule returns KEEP for unmerged (plant caught) |
| 5 | Head must match; gone skipped; failure counted; dry run deletes nothing | MET | `branch_cleanup.py:56-84`; `--force-with-lease=<ref>:<sha>` (`branch_git.py:82-88`); 6 plants caught |
| 6 | Workflow shape | MET | YAML parses; dispatch default `apply=false`, `mode=inventory`; schedule gated by `vars.BRANCH_CLEANUP_SCHEDULE == 'on'`; `contents: write`, `pull-requests: read`; no secret; checkout `ref: main`, `fetch-depth: 0`; APPLY expression gives "false" for an unticked dispatch, "true" only for the gated schedule |
| 7 | Committed inventory well formed, never deletes main or a kept branch | MET | rebuilt it myself (`branch_inventory.py --now 2026-10-25T10:43Z`, 7 open PRs): 598 rows, every decision identical; all 386 delete SHAs equal origin's heads now; merged flag equals `merge-base --is-ancestor` for every delete row |

Gates on the branch: `tests/gb1_branches` + capture-watch + code-size 3033 passed; full suite 18,114 passed, 1 skipped, 13 xfailed (my run on 52b58038f); ruff and
`check_imports` clean. Largest new file 145 lines.

## Findings

1. **Should fix: rehearsal branches are deleted against a standing owner decision (strong evidence).**
   REH1 Q3 (owner, 24 Oct, `docs/stories/REH1-rehearsal-mode.md:193`): "Keep ... the `rehearsal/` branches, so the
   owner can inspect them." The inventory deletes 4 (`rehearsal/2026-10-23-20261024T0449..0533*`), which
   `docs/dryruns/DRY2_2026-10-23.md:26-29` cites as DRY2's evidence, and the standing rule deletes every rehearsal
   branch after 7 days. The story itself asks the owner; the orchestrator confirms (25 Oct 11:08 UTC) no answer yet.
   Fix: until the owner says yes, the 4 rows are `keep-unsure` and the standing rule keeps rehearsal branches (a
   switch that is off, or the rule removed); when the owner answers, record it and turn it on.
2. **Should fix: the standing rule never deletes a fast-forwarded merged branch (strong evidence).**
   `merged_branch` returns `keep-unsure` whenever the tip is on main's first-parent line, with no time limit, and the
   standing rule never revisits it: the 16 such branches (some last touched 15 Oct) stay forever and every new one
   adds to them. Deleting them loses nothing (the tip is a commit on `main`; a later push recreates the branch). That
   misses the owner's "Anything that merges into Git main branch, we delete", and the new CLAUDE.md line ("A branch
   merged into `main` is deleted ... 24 hours after it landed") is untrue for them. Fix: apply the grace to them too
   (e.g. 24 h, or a longer window if a fresh-cut session branch needs it, measured from `landed_at`), or make CLAUDE.md
   and the story say exactly which merged branches are never deleted and who clears them.
3. **Minor: a test name over-claims.** `test_unfinished_code_is_counted_only_for_commits_not_on_main` has no
   patch-equal commit; my plant counting every `git cherry` line survived (errs safe). Add a cherry-picked case.
4. **Minor:** `CODE_PATHS` leaves out `tests/`: a test-only branch counts as nothing of value (here
   `fix/g8-v1-series-test` and `story/c5b-restart-decision`, both superseded on main, so no loss today). The register
   row names `tests/tools/`; the tests are in `tests/gb1_branches/`.

## Plants

25 planted (rules, re-check, dry-run switch, exit code, lease, main-line reading, workflow default, gate and ref);
24 caught. Survivor: finding 3.

## Notes

- The 13 unmerged non-rehearsal deletes: duplicate or superseded slot rows, tests and review notes, or merge-only
  commits, except `claude/pensive-fermat-erk186`, the Omenix logo set. `conversations/2026-10-13.md` says its final SVGs
  went into omenix-dashboard `design/brand` (ed21a5a); I could not check that repository. Only its generator scripts
  would be lost. The owner accepted such losses.
- Content safety of the merged deletes: every merged tip is reachable from `main`, so a merged delete loses no commit;
  a builder who still pushes recreates the branch; `git pull origin <deleted branch>` fails loudly.
- That GitHub accepts the deletion with `GITHUB_TOKEN` stays unproven until the first applied run (story says so).
