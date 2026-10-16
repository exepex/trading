# Judge 228: A16f (first mark, push to main) and O9 story text: `story/a16f-first-mark-and-main` 4c6fb11 (lane 1)

**What I did:**
- read the whole diff against current `main` (six files);
- read `OwnedPathsCommitter`, which A16 uses, to see how the new refusal interacts with it;
- read the O9 story in full;
- searched `main` for frozen records and tools that read `research/data`;
- ran the gates on a trial merge.

## Gates

On a trial merge with current `origin/main` (clean): **6909 passed** (`-n auto`). `main` now needs `pytest-xdist`
because `pytest.ini` carries `--dist`, and it is in `requirements.txt`. Ruff, format (1223 files) and
`check_imports` are clean.

## A16f: criteria

| Criterion | Status | Evidence |
|---|---|---|
| (a) A run started at 08:53:17 with `--until 10:05` takes 09:15-10:00, all good | MET | `run()` no longer ends on `NO_MARK`; `_wait_for_next_mark` sleeps until the next mark is within `MAX_WAIT`, then `snapshot()` takes it. The test reproduces 16 Oct's start time and asserts four good marks |
| (b) `--until` before the first mark ends without waiting | MET | The loop still breaks when `_later_mark(until)` is false; tested |
| (c) A session branch absent from origin publishes to `main`; no branch is created on origin | MET | The pull now fetches and merges `origin main`, and the push is `HEAD:main`. The test checks out `claude/lucid-ptolemy-test` and asserts the row on `origin main` and no such branch on origin |
| (d) A branch carrying another change is refused, the path named, `main` untouched | MET | `pull()` lists `git diff --name-only origin/main...HEAD` and refuses any path the writer does not own. It uses `self.owns`, which `OwnedPathsCommitter` (A16) overrides, so A16's owned files pass and nothing else does. Tested with `code.py` on `story/x-unjudged` |
| (e) Existing recorder and committer tests pass | MET | Full suite above |

**Root cause (strong evidence):** both defects match the 16 Oct record in the story. The early-exit fix is the right
place: `snapshot()` keeps its 15-minute cap and `run()` owns the waiting. Pushing data to `main` from any branch is
safe only because of the refusal, which keeps unjudged code from riding along.

**A16f risks (follow-ups, not blocking):**
1. **A refused push is silent.** If the routine's agent commits anything else on the session branch before the recorder
   pushes, for example a conversation log, every mark prints `NOT committed: pull failed: ... carries changes ...`
   and the rows stay in the container. That is the 16 Oct failure in a new form. The output names the paths, but
   nothing alerts #fno-desk. The routine prompt must commit nothing else until the recorder ends. Better: an
   unpublished-row alert, the "nothing left unpushed" last step the story already names.
2. The same push-to-main now applies to every user of the committer (manifests, read-model inputs). That is intended
   and covered by (d).

**Verdict for A16f:** the code passes. It is urgent for Monday 19 Oct's 08:52 fire.

## O9 story text: one must-fix

The owner's decision is quoted with the question asked ("Hash receipt only"), and the design is sound:
- `RawFileStore` stays the seam;
- every record is written once;
- receipts carry only paths and hashes;
- readers sync to a SHA-checked cache;
- risks are stated: single point of failure, 0.41 MB/s, the token expiry around 20 Oct.

**Must-fix: the plan removes data from HEAD that frozen records and tools read.** On `main` these name
`research/data` files:
- `research/2026-10-12-experiment-1/FREEZE.md`;
- `research/forecasts/FREEZE.md`, `FREEZE_v2.md` and `FREEZE_v3.md`;
- the G6 v4 calibration tools that compute the **operative thresholds**: `tools/v4_size_study.py`,
  `v4_brier_regimes.py`, `v4_futility_study.py`, `v4_regime_stress.py` and `v4_vix_null.py`, which read
  `warmup_closes.csv`;
- 22 test files.

"Remove the files from HEAD in one commit per folder" would break those freeze checks and tests, and with them G8's
`operative_thresholds`. The story must list frozen and test inputs as their own class, and say how each stays valid.
Either they stay in the repository as frozen inputs, like the calendar, or the freeze record pins their SHA-256 and
the reader fetches exactly that file from Drive. It must also add a criterion: every freeze check and the full suite
pass after the removal.

**Should-fix (story level):** receipts appended to **one** file by two overlapping runs collide on merge, as two lines
at the end of the same file. The story's own race case (criterion 3) needs per-write receipt files or a union-merge
rule, stated now.

**Verdict for O9: FAIL** (story text, one must-fix).

## Verdict on the SHA

**FAIL for 4c6fb1179029a096701aa243eec6d149c24749ed as a whole, only because O9's text rides in the same commit.**

The **A16f part passes**. To merge it before Monday: push a commit that removes `docs/stories/O9-data-to-drive.md`
from this branch, or moves it to its own branch, with the A16f files byte-identical. I will PASS that SHA after
checking only that diff.

## Addendum 1 (16 Oct 2026): f4bedbeb (4c6fb11..f4bedbeb)

- `git diff --stat 4c6fb11 f4bedbeb`: only `docs/stories/O9-data-to-drive.md` is deleted (106 lines). Every A16f file
  is byte-identical to what I judged at 4c6fb11. Against the merge base the branch now carries only A16f's five files.
- The gates of judge 228 stand: the code is unchanged, and the only change is a deleted file that nothing reads. The
  trial merge with `main` was clean, with 6909 passed.
- The builder accepted O9's must-fix and should-fix, and checked the same freeze files, tools and tests. O9 returns on
  its own branch.
- Follow-up 1 is partly covered: the routine prompt now starts with `git checkout -B main origin/main`. The
  "commit nothing else" line and an unpublished-row alert go to the next A16 story.

**Verdict: PASS for f4bedbeb (A16f).** Merge before Monday 19 Oct's 08:52 fire. After the merge I check the merge and
CI, and Monday's run log for 09:15 taken as good and the rows on `main`.

## Addendum 2 (16 Oct 2026): merge check, A16f merged to main as 4a83ce6

- **Merge is exact.** 4a83ce6's parents are c77868af (main) and f4bedbeb (the passed tip). Recomputing the merge with
  `git merge-tree --write-tree` gives a tree identical to 4a83ce6's (empty diff).
- **A16f files are identical on main.** `git diff f4bedbeb 4a83ce6` on all five A16f files is empty, and nothing
  under `fno/intraday`, `fno/storage` or their tests changed between 4a83ce6 and the current head 78e7daa.
- **CI.** The parent is green. The run on 78e7daa, which contains the merge, was in progress; I confirm it in my
  report.
- **Monday 19 Oct:** I check the 08:52 run's log for 09:15 taken as good and the rows on `main`.

**Verdict: merge check PASS** (CI on the merge to be confirmed).
