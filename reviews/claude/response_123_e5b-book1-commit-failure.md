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
