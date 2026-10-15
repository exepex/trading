# Response 122: story E5b, Book 1's decision command on a failed commit (story text for the judge's story check)

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

## Choice for the orchestrator

- **A (recommended):** recover through `PendingCommitter`, with its own marker.
- **B:** alert only, with a hand fix.

The reasoning is in the story. It is a design choice, not an owner number.

## Response number

122 is the next free number on `main` (the highest there is 121). If another open branch already took 122, the
orchestrator renumbers it.
