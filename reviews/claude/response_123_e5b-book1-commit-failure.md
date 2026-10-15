# Response 123: story E5b, Book 1's decision command on a failed commit (story text for the judge's story check)

Builder: Claude. Branch `story/e5b-book1-commit-failure`, started from `story/e2b-derived-packs` at 9aefbc0 because
the fix uses E2b's `CommitFailed` and `PendingCommitter`. Until E2b merges, this branch's diff against `main`
includes E2b. The story commit alone is the one at this branch's head. Story text only: no code until the judge's
story check passes.

## What the story asks (docs/stories/E-paper-desk.md, "E5b")

- `fno desk book1` handles `CommitFailed` as E3's daily run does: one alert, one line, exit code 1, no traceback.
- Its rerun commits the recorded decision as it was made, and never decides again.

## Facts checked for the story (with evidence)

| Fact | Evidence |
|---|---|
| `Book1.decide` commits through `GitCommitter`, and nothing catches `CommitFailed` | `fno/books/book1.py:74`, `fno/books/book1_cli.py` `cmd_book1`, `fno/books/book1_wiring.py` |
| A rerun with byte-identical inputs returns "already decided" and commits nothing; with any changed input it decides again as a second run | `fno/playbook/decision_store.py:72-75` (it compares `inputs.json` bytes) |
| A Book 1 commit left unpushed stops E3's daily run in the same checkout | decision 51's stray refusal (`GitCommitter._refuse_stray`), as in judge 118 addendum 7 |

## Decision 57 taken into the story

- Option A (recovery with Book 1's own marker).
- One Book 1 decision a day: a rerun on a decided day never decides again, whatever the inputs. A changed input is
  alerted as a fact and never acted on.

**Existing rules and tests that allow a second run, and why they stay:**
- `tests/decisions/test_records.py::test_the_same_inputs_twice_are_refused_new_inputs_make_a_new_run` is D3's
  shared store rule. It serves every book, and it is how D3 writes corrections (a new run linked by `corrects`,
  `test_a_correction_is_a_new_run_linked_to_the_record_it_corrects`). Changing the store would break corrections for
  every book. The one-a-day rule therefore sits in `Book1.decide`, and no Book 1 test expects two decisions
  (`tests/book1/` checked).
- `tests/timetable/test_parts.py` (the collector takes the latest run committed before the deadline) stays. With one
  Book 1 decision a day it never has two Book 1 runs to choose from.

**Question for the orchestrator (found, not changed):** the collector takes the latest run committed before the
deadline, so a D3 correction run committed before the deadline would be read as the day's decision.

## Response number

122 was taken (A16b), so this is 123, as the orchestrator said.

## Answer to judge 123 (decision 59)

| Item | Accepted? | Change to the story |
|---|---|---|
| Should-fix 1: a second checkout decides again | **accepted**. `DecisionRun.decide` writes the run before `GitCommitter` pulls, so a check in this checkout alone cannot see origin | Prevention (59 a): before deciding, a fetch and a look at `origin/<branch>`'s day folder, `HEAD` and the disk. Before committing, a check of the pulled tree (a new optional `Committer` argument run by `GitCommitter` after its pull) refuses a second Book 1 run. Guarantee (59 b): E3's collector takes the first non-correction run, in D3b. Test: two checkouts of one bare origin end with exactly one run |
| Should-fix 2: a run on disk, not committed, not in the marker | **accepted** | Named as the third state: one alert with the hand fix (inspect, then `fno desk book1 --commit-run <run_id>`, which refuses an edited run and never runs D2, or remove it). Never a quiet "already decided". It is in criterion 0 |
| Minor 1: what the comparison is | **accepted** | Recomputed inputs, serialized as `DecisionRun` writes them, against each recorded input file, byte for byte. The alert names each differing file and its top-level fields |
| Minor 2: the collector and corrections | **answered by decision 59 (b)** | Cited in Out and in the scope: D3b carries it |

**Cost, said plainly:** `--commit-run` is a small new command option, needed for the hand fix to be one documented
step rather than raw git. The `Committer` port gains a second optional argument (the pre-commit check of the pulled
tree). Both are within the story's size S.

## Notes for the code round (after E2b merges)

- Judge 123 addendum 1: `--commit-run` passes the same check as a normal commit, accepts only a run in the
  on-disk-only state, and never sets commit dates (E3 judges timeliness by committer time).
- Decision 67: drop the two-checkout pre-commit re-check; keep only the cheap origin check before deciding.
- ChatGPT review 107 (orchestrator): the collector sends one integrity alert when a book has more than one original
  run on a day (a double-fired session).

## Code round (for the judge; then ChatGPT, rule 9: it touches what decides a trade)

Built from the PASSed text with the three notes above, rebased onto current `main` (E2b and D3b merged).

**What changed**
- `fno/books/decided_runs.py` (new): `GitDecidedRuns.find(day)` fetches origin and lists Book 1's runs of the day on
  `origin/<branch>`, in `HEAD` and on disk. Each run is given its most public place, with its recorded `inputs.json`.
  If origin cannot be read, it raises `CommitFailed`, so the command gets one alert and decides nothing.
  `changed_fields` names the top-level fields that differ.
- `fno/books/book1.py`: `decide` first recovers Book 1's pending commit, then checks the three places. A run found
  anywhere means nothing is decided again:
  - changed inputs get one alert ("inputs changed after decision ... (inputs.json: <fields>); not decided again");
  - a run on disk only gets one alert with the hand fix (`--commit-run`), never a quiet "already decided";
  - otherwise the result is "already decided" (or "committed on this rerun as recorded").
  `commit_run(day, run_id)` commits a run only when it is on disk only and D3's `edited` check passes. It never runs D2
  and never sets a date. The run's files are committed one by one, so the marker records each file's hash.
- `fno/playbook/decision_run.py`: `DecisionRun.inputs(...)` gives the `inputs.json` bytes a decision would record now.
  It writes nothing and decides nothing. `decide` now shares `_evaluate` with it, so its behaviour is unchanged.
- `fno/desk/pending_commit.py`: the marker name is a constructor argument (default unchanged). Book 1 uses
  `journal/runs/.pending_book1.json`, which is git-ignored.
- `fno/books/book1_cli.py`: adds `--commit-run RUN_ID`. `CommitFailed` gives one alert, the same line printed and exit
  code 1. `CommitRunRefused` gives one line and exit code 1.
- `fno/books/book1_wiring.py`: `build_book1_commits` builds the committer and the runs check. The tests use the same
  function, so the wiring itself is tested.
- `fno/desk/daily_steps.py` (review 107): more than one original run of a book on a day gives one alert ("N original
  runs (...): only <first> counts"). A correction does not count as a second original.

**Claims per criterion** (`tests/book1/test_commit_failure.py`, 11 tests; `tests/timetable/test_first_timely_decision.py`,
2 tests)
- 0. Each of the three states is tested with a changed input:
  - committed: one run, one alert naming `inputs.json: book`, files byte-identical;
  - marker: the recorded run is committed, and the same alert is sent;
  - on disk only: the hand-fix alert, then `--commit-run` commits it unchanged; a second `--commit-run` is refused
    ("on origin"), and an edited run is refused.
  An unchanged rerun says "already decided" with no alert. Two checkouts, one after the other: the second says
  "already decided (r1 on origin)", decides 0 times, and origin holds one run.
- 1. With real git, each of three causes gives exactly one alert, the same line printed, exit code 1 and no
  exception: a staged raw quote file, an unreachable origin and a push rejected three times (pre-receive hook).
- 2. After the cause is removed, the rerun commits the files byte-identical, with one decision in total, and origin
  holds the run. A local commit left unpushed is pushed by the rerun.
- 3. An edited decision file stops the rerun, naming `inputs.json`. Nothing is pushed, and there is no second decision.
- 4. Book 1's marker is `.pending_book1.json`. The daily run's recovery finds nothing of it.
- 5. A successful decision prints `Book 1 <day>: decided (<run>), committed <sha>` and exits 0, with no alert.

**Plants (all caught)**
1. a second decision when a run is found (6 tests failed);
2. the origin check skipped (2);
3. a quiet "already decided" for a run on disk only (1);
4. no catch in the CLI (8);
5. a shared marker in the wiring (3);
6. no hash check in `--commit-run` (1);
7. `--commit-run` in any state (1);
8. no changed-input alert (3);
9. no two-originals alert (1);
10. a correction counted as an original (2).

**Where I depart from the text, or interpret it (please rule)**
- **The concurrent two-checkout case.** Criterion 0's "second pulling only after the first decided" is no longer
  prevented. Decision 67 dropped the pre-commit re-check, so two checkouts deciding at the same moment can both reach
  origin. The guarantee is D3b's first-run rule plus review 107's alert, and that test shows only r1 counts with one
  alert. The sequential case is prevented and tested.
- **"D2 run once in total".** To compare inputs on a decided day, D2's evaluation runs read-only (`DecisionRun.inputs`):
  nothing is written, decided or logged. The tests count decisions written, not evaluations. There is no other way to
  know the inputs D2 would read now; reasoning only.
- **Changed inputs when a day has more than one run.** Every run of the day is compared and none is ranked (D3b's run
  order owns "first"). `tests/decisions/test_one_run_order.py` lists `decided_runs.py` as a reader that uses runs only
  to see whether any exist.

**Known limits**
- Book 2 and Book 3 take the one-a-day rule when they are built (F5, F6), as the story says.
- The input comparison is byte for byte. A field whose serialisation changes with no change in value would be alerted.
  It is never acted on.
