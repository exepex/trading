# GB1: Git branch clean-up

Lane 1 (a workflow that deletes refs with write access, and the rule for what counts as "in use"): two judges, at most two
rounds each. Builder: this session, branch `story/gb1-branch-cleanup`. Orchestrator: session_01Mt6dcBU5kp2htdPN2KmiZH.
Register row: `docs/WORK_REGISTER.md`, "GB1 branch clean-up".

## The owner's words (25 Oct 2026)

"I want all old and all the feature branches make them go away. Moving forward, we want to keep our Git branch branches
and features clean. Anything that merges into Git main branch, we delete. That branch, that's it. I'm losing track of what
feature exists in which branch. If a branch is in usage, we keep that branch. And clean the rest of the branches. If we
lose something in a feature branch, let it be." And: "Please don't do anything fast and without validating ... every
removal and cleanup needs to be reviewed thoroughly by a judge and independent judge."

## Facts (origin at 25 Oct 2026, 10:43 UTC: 597 branches)

- 470 were merged into `main`, 126 were not. Nothing is deleted by this story's commits: the deletion is a later workflow run.
- **Why a workflow.** A session's git proxy refuses ref deletion (`git push origin --delete` ends in "send-pack:
  unexpected disconnect") and the GitHub tools have no delete-branch call. A workflow with `permissions: contents:
  write` deletes a ref with its own token; `capture-watch.yml` and the data workflows already push with the same
  permission on this repository. Only a real run proves it works here: the first dry run then the first real run
  (below) are that proof, and a refusal by GitHub makes the run fail loudly (`FAILED <branch>`, exit 1).
- **Nothing reads another branch.** Searched `fno/`, `tools/`, `tests/`, `.github/`, `.claude/`, `.githooks/` and
  `config.yaml` for `origin/`, `ls-remote`, `for-each-ref`, `story/`, `claude/`, `rehearsal/`: every workflow runs on
  `main`; every committer pulls and pushes `main` (`PUBLISH_BRANCH`); the only branch writers are `fno/rehearsal/checkout.py`
  (pushes `refs/heads/rehearsal/<day>-<run_id>`, refuses any other ref) and the session branches the harness creates.
  `ls-remote` is used on one branch only (`fno/ai/remote_observer.py`, the configured target).
- **The `rehearsal/*` branches (49).** Each is one `daily run --rehearse` (REH1): the bare `main` of a replayed day with
  the rehearsal's receipts, pushed once at the end. Nothing ever fetches them back. REH1's Q3 answer (24 Oct) was "keep
  them so the owner can inspect them"; the owner's 25 Oct words are newer and wider, so they go after a window
  (below). Judge files quote run ids as evidence; the evidence is in the judge files, the Drive `dryrun/` folders keep the
  run's data. **Question for the owner, through the orchestrator:** does the 25 Oct rule replace Q3 for rehearsals?
- **A merged branch is not always finished.** O14 and CP1 merged their story text and code is still to come on the same
  branch (register rows). So "merged" alone would delete a branch in use. A branch freshly cut from `main` is also an
  ancestor of `main`, so git cannot tell it from a merged one. Both are covered by the keep list and the 24-hour grace.

## The rules (tools/branch_rules.py, pure, one function per rule)

A branch is **kept** (never deleted) when any of these holds, checked in this order:

1. it is `main`;
2. it is on `.github/branch-keep.txt` (exact names with a reason: the in-flight branches the orchestrator named, and any
   story whose text is merged and code to come);
3. it is the head of an open pull request (`gh pr list --state open`);
4. it is **not merged** and named in the Branch column of `docs/WORK_REGISTER.md` (a merged branch's row may be stale:
   50 merged branches sit in rows with prose states and no "done"; the register is not trusted to release a merged branch).

Then, for a branch nothing protects:

- **Merged** into `main`: deleted once 24 hours have passed since the later of "its merge reached `main`'s own line" and
  its last commit (`GRACE`). Evidence: JUDGE.md's merge procedure merges after the PASS and then marks the register row; a
  builder may still push a lane-3 note. 24 hours covers that, and a deleted branch is recreated by the next push.
- **A rehearsal run's branch:** the standing rule deletes it 7 days after the run started (`REHEARSAL_KEEP`; the run id
  holds the UTC start time); the one-off clean-up keeps runs under 24 hours (a judge of an in-flight rehearsal story may
  open them), marked `keep-unsure`.
- **Not merged** (the one-off only; the standing rule never deletes an unmerged branch): `keep-unsure` when its last
  commit is under 48 hours old, when a file written in the last 48 hours names it, or when it holds **unfinished code**
  (a commit not on `main`, patch for patch, that changes a file under `fno/`, `tools/`, `.github/` or `config.yaml`).
  Otherwise deleted: no open PR, no register row, idle over 48 hours; the owner accepts losing it.

`keep-unsure` is never deleted by the workflow; it is for the orchestrator or the owner to decide. Merged branches in the
grace window leave `keep-unsure` by themselves: the standing rule deletes them the next night.

## The inventory (docs/branch_inventory.csv)

One row per branch: `branch, sha, last_commit_utc, merged, commits_not_on_main, decision, reason`. Made by
`python tools/branch_inventory.py --open-prs <file>` (the open pull requests' heads, one per line; here from the GitHub
tool). Counts at its making:

| Decision | Count | What |
|---|---|---|
| delete | 402 | 381 merged; 17 unmerged, idle over 48 h with no unfinished code; 4 old rehearsal runs |
| keep | 31 | `main`; the keep list (9 of its 11 names exist on origin today; 3 of the 9 are merged); 5 open pull requests' heads (one is a stale, merged one: PR 131); 16 unmerged and in the register |
| keep-unsure | 164 | 84 merged under 24 h ago (go tomorrow); 45 rehearsal runs under 24 h; 26 unmerged and recent or named in a recent file; 9 unmerged holding unfinished code (A14c families, A19 news, A21 rates and announcements, F1t-F4 handover, O10 part 2, P2c paper books, and two of one or two files) |

Restore a deleted branch (GitHub keeps the objects for a while): `git push origin <sha>:refs/heads/<name>` with the `sha`
column.

## The workflow (.github/workflows/branch-cleanup.yml, tools/branch_cleanup.py)

- `workflow_dispatch`, inputs `mode` (`inventory` default, or `merged`) and `apply` (**false by default: a dry run** that
  prints `WOULD DELETE <branch> <sha>: <reason>`). A `schedule` (02:40 IST) runs `merged` with apply, **only while the
  repository variable `BRANCH_CLEANUP_SCHEDULE` is `on`** (off until the orchestrator sets it after the first real run).
- Checks out `main` with full history; reads the inventory, keep list and register from `main`, never from the branch
  the run was started on. `permissions`: `contents: write`, `pull-requests: read`. No secret, no Drive, no Slack.
- **Before each deletion**, from one `git ls-remote` of GitHub taken at the start: the branch exists; its head equals the
  SHA the plan was made from (inventory mode: the CSV's `sha`), else `SKIP ... head moved`; and the keep list, an open PR
  and the register (unmerged only) are re-checked against *current* files, else `SKIP`. `main` is refused by rule 1
  whatever the file says. A second row for one branch stops the run before anything is deleted.
- A failed deletion prints `FAILED`, the rest still run, exit 1. The step summary carries the full list.
- `concurrency: branch-cleanup` (one run at a time, none cancelled).
- **Exact dispatch** (after both judges PASS and the merge to `main`): first `mode=inventory apply=false`, check the
  summary shows 402 `WOULD DELETE` and no `SKIP` of a branch that should go; then `mode=inventory apply=true`; then
  `mode=merged apply=false` to see the standing rule alone; then set `BRANCH_CLEANUP_SCHEDULE=on`.
- Not added to `capture-watch.yml` (it captures nothing); `NOT_WATCHED` in its workflow test names it.

## Acceptance criteria and tests (tests/gb1_branches/)

1. **Nothing in use is deleted.** `main`, keep list, open PR head, unmerged register branch: `test_rules.py::TestEveryRule`,
   `test_run.py` (keep list, open PR, main listed by mistake, stale register row on merged vs unmerged).
2. **Merged goes after the grace, not before; a late push counts.** `test_merged_goes_after_the_grace_not_before`;
   real git: `test_git.py` (merged, unmerged, fresh-cut branch, `landed_at` is the merge's time not main's last move).
3. **Rehearsal runs by run-id age; both windows.** `test_rehearsal_branch_goes_by_its_run_id_start`,
   `test_standing_rule_deletes_a_week_old_rehearsal...`, `test_one_off_rehearsal_window_is_a_day`.
4. **Idle unmerged goes only in the one-off, never with unfinished code or recent activity.**
   `test_one_off_deletes_an_idle_unmerged_branch...`; `test_unfinished_code_is_counted_only_for_commits_not_on_main`.
5. **Head must match the plan; gone is skipped; a failure is counted and the rest run; dry run deletes nothing.** `test_run.py`.
6. **Workflow shape.** Dry run default, schedule gated by the variable, two permissions, no secrets, no `${{ }}` inside a
   script, checkout of `main` with history: `test_workflow_and_inventory.py`; capture-watch's `test_every_job_is_watched` updated.
7. **The committed inventory is well formed and never deletes `main` or a kept branch.** `test_workflow_and_inventory.py`.

**Gap list.** Out of scope, with reason: deleting tags (none exist to clean); closing stale pull requests (the owner's call:
PR 131 stays open and loses nothing, PRs 2, 90 and 99 are old and unmerged); protecting `main` with a branch rule (a
GitHub setting, not code); restoring the session-harness branches (the harness recreates what it needs); unmerged branches
that collect *after* this run (the standing rule never deletes unmerged work; the orchestrator re-runs
`branch_inventory.py` when it wants them listed); a delete that must be atomic with the head check (GitHub's ref-delete API
takes no expected SHA; the window is the seconds between the `ls-remote` and the call, and a branch pushed in it is lost
only if it was already planned for deletion).

## Claims

- **Gates (on this branch, from `origin/main` fefcf893 plus this change):** see the last line of this section, filled
  after the run.
- **Real output sample (dry run, 25 Oct 10:43 UTC, the committed code against the real origin):**
  `python tools/branch_cleanup.py --mode inventory --open-prs <file>` printed 402 `WOULD DELETE` lines (first:
  `WOULD DELETE claude/bold-thompson-hpqkq3 1653fc3926: merged into main`) and `dry run: 402 planned, 0 failed`, no `SKIP`.
  `--mode merged` printed `dry run: 381 planned, 0 failed` (the 402 minus the 17 idle unmerged and the 4 old rehearsals).
  Nothing was deleted from this session.
- **Plants:** 21 one-line breakages of the rules, the re-check, the dry-run switch, the exit code, the git reading and the
  workflow; 20 are caught by the tests. The survivor (`with_code and ahead` to `with_code`) is an equivalent mutant: a
  branch with no commits of its own has no unique files either way. One real bug was found by a test while writing them
  (a sentence's full stop was read as part of a branch name) and fixed (`names_in`).
- **Decision for the judges, built as the safer side:** a merged branch's register row does not protect it (50 stale rows
  would keep 50 merged branches, the very clutter the owner wants gone). The cost: a text-first story's branch must go on
  the keep list, or it is deleted 24 h after the text merges and recreated by the code push. CLAUDE.md says so.
- **Not claimed:** that GitHub accepts the deletion from `GITHUB_TOKEN` in this repository. The workflow cannot show
  that before it runs; the dry run proves everything but the final API call, and the first applied run proves it.
