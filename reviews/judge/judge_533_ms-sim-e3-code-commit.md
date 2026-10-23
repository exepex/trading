# Judge 533: MS-SIM-e3 run-id fix, the code commit

**Scope:** story/ms-sim-e3-code-commit at 3892d307 (off main 8c5effca; SIM builder). The diff from main is
`fno/school/simulator/archive/inputs.py`, `tests/school/simulator/archive/test_session.py` and the Claims. I first
looked at a8d668b1; the orchestrator then moved the request to this tip, which adds `requirements.txt`. Lane 1 (run
ids of archived records). Round 1 of 2. Judge H (session_01KNkZVoWvXMkoihKrrXk5Xa).

**Verdict: FAIL**, with 1 should-fix and 2 minors. The cause is right: HEAD moves with every receipt and data commit.
But `git log -1 -- <paths>` is still a history position, and a shallow clone gets it wrong.

## Checked
| Item | Result | Evidence |
|---|---|---|
| A receipt or data commit no longer changes the run id | MET in a full clone | New real-git test. Plants caught: HEAD put back, the path limit dropped from `git log` |
| An uncommitted code or `requirements.txt` change is refused | MET | Tests |
| Targeted gates | MET | `tests/school/simulator` 281 passed. ruff and check_imports are clean. I didn't rerun the full suite: the verdict rests on the defect below, and the builder reports 14,548 |

## Finding
1. **Should-fix: in a shallow clone, `code_commit` names the clone's boundary commit, and archiving then changes it.**
   - In a shallow clone, the boundary commit looks as if it added every file. So when the last code commit is deeper
     than the clone, `git log -1 -- fno ...` returns the boundary commit.
   - My real-git run: a code commit, then 3 data commits, cloned at depth 2:
     - full clone: `62aba5b7cb8e`;
     - shallow clone: `61a5155cd2d5`, a data commit;
     - after `git fetch --unshallow`: `62aba5b7cb8e`.
   - This is the same defect the fix is for, by another route:
     - the cloud containers clone at depth 50 (`receipt_publisher._deepen`'s docstring);
     - main took 666 to 1,330 commits a day on 21-23 Oct, mostly data, and the last code commit is 28 commits deep
       right now, so within hours it is past 50;
     - the run's own receipt publishing unshallows the clone (`_deepen`), so the first run gets one id and its rerun
       another. That gives a second orphan like 20240304_20240306_4490ad2e299b.
   - Expected, either of:
     - **(i) recommended, the root cause:** name the code by content. Hash the tree ids from
       `git rev-parse HEAD:fno HEAD:tools HEAD:config.yaml HEAD:requirements.txt`. These need no history, are the same
       in any clone and on any branch with the same code, and don't move with data commits. The dirty check stays.
     - **(ii)** deepen first, or refuse a shallow clone by name, as `_deepen` does (`Git.is_shallow`).
   - Either one needs a real-git test with a `--depth` clone.

**Minor:**
- (a) **The no-code-commit guard is never reached by its test.** My plant (`if not last` replaced by `if False`)
  survived.
  - `test_a_repository_whose_code_was_never_committed...` uses a repository with no commits, where `git log` itself
    fails first.
  - The guard matters when commits exist but none touch the code paths. Today that case would give `IndexError`
    without the guard.
  - Test that case: one commit holding only `receipts/`. With (i) the case changes: `HEAD:fno` fails by name.
- (b) **`requirements.txt` holds ranges (`numpy>=2.0`; only xlrd is pinned).** Hashing the file catches an edited
  range, not the installed versions.
  - Counting it is right and cheap, so I accept the addition.
  - The run id does not name the library versions. Say so in the Claims. If the orchestrator wants versions in the id,
    put a sorted `importlib.metadata` version list for the imported packages into `inputs_digest`.
  - That is reasoning only: I haven't measured whether a numpy minor-version change moves any practice number.

## Plants
- At a8d668b1: 3 planted, 2 caught, 1 survived (minor a).
- The finding is shown by a real shallow clone, not a plant.
