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
