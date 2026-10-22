# Story O1-publish-branch: every run commits to main, whatever branch its checkout is on

Owner: the O1/O2 builder (session_014zYLf18PgCzR7YoHs1X5Dp). Lane 1, judge D: git and the scheduled routine.
Ordered by the orchestrator on 22 Oct 2026, urgent: it must be merged before Friday's 08:36 IST pre-open routine.

## What happened (strong evidence: the run's own stop line, reproduced by a test on the old code)

Thursday 22 Oct's 14:05 routine stopped at `quotes`: "the commit failed: git fetch -q failed: fatal: couldn't find
remote ref claude/bold-thompson-2lkkg6". The owner's scheduled session checks out its own session branch, which origin
has never seen. `fno/desk/git_sync.py`'s `Git` took "the current branch" (`rev-parse --abbrev-ref HEAD`) for its fetch,
unshallow, pull, compare and push, so every commit of the run failed. Three readers asked the same of git:
- `fno/desk/daily_wiring.py`'s pull;
- `GitDecidedRuns` (Book 1's earlier runs);
- `PlaybookGit.observed`. Its pull is unchecked, so on a session branch it would have silently read a stale tree.

## The rule

One named constant, `PUBLISH_BRANCH = "main"` (`fno/constants_operations.py`). `Git` takes it as its `target` and
uses it for every fetch (`fetch origin main`), every compare (`origin/main..HEAD`) and every push (`HEAD:main`).
`GitCommitter` pulls `origin main`, and the three readers use the same target. Nothing reads the checkout's branch any
more.

## Other committers checked (strong evidence: read from the code)

- Already on main, through `GitManifestRecorder` (`fno/storage/manifest_commit.py`, `TARGET_BRANCH = "main"`):
  - A22's `preopen record` and A17e's `global-cues preopen` (`build_preopen_committers`, `OwnedPathsCommitter`);
  - A4h's `closes read --commit`;
  - the data librarian and O9's receipts;
  - circulars, flows, intraday and the market read models.
- Number claims (`fno/numbering/git_main.py`, `BRANCH = "main"`) and the AI transport (`fno/ai/transport.py`,
  `BRANCH = "main"`) are already on main too.
- A16's heartbeat reads `origin/main` by default.
- Those four local "main" constants could later point at `PUBLISH_BRANCH`. That is a clean-up in their owners' files,
  and it is not needed for this fix.

## Acceptance

1. A checkout on an unpublished session branch commits and pushes to origin's main. Nothing is published under the
   session's name, and nothing is left unpushed.
2. On that branch, the committer pulls main before it commits (another writer's commit arrives).
3. `GitDecidedRuns` and `PlaybookGit.observed` read main from a session branch.
4. On the old code, test 1 fails with today's exact message ("couldn't find remote ref claude/bold-thompson-2lkkg6").
5. The full suite passes unchanged.
