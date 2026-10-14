# Judge 67: story D1, the playbook format

Date: 14 Oct 2026. Code: trading a6029f3, 9637b4f, fb22302. Claims: `reviews/claude/response_70_d1-playbook-format.md`.

## Verdict: FAIL, one must-fix (the B7 gate accepts a report with days removed); everything else MET

## Per criterion

| # | Criterion | My check | Result |
|---|---|---|---|
| 1 | A missing field, unknown feature or structure code is refused, field named | `tests/playbook` 158 pass (every one of 42 fields deleted in turn, unknown keys, features, structures) | MET |
| 2 | Duplicate name and version refused; a changed parameter refused; append-only registry checked against git | **Judge verifies, done in a scratch clone:** registered the example as `research`; `threshold: 0` to `0.5` gives "refused: … rule: differs from the registered version". A **text** field (`size_rule`: Rs 10,000 to 20,000) is refused too: the fingerprint is the whole parsed rule minus `status` and `evidence` (an exclusion list, so a new field is covered by default). Editing a past registry row and committing makes `test_the_repository_registry_was_only_ever_appended_to` fail | MET |
| 3 | Only the allowed status changes, each a new row | Table-driven tests; the transition table matches the story (`paused -> paper` owner only) | MET |
| 4 | No `paper` without all evidence and the owner's date | `EvidenceFilled` and `EvidenceCommitted`: evidence files must exist in the approval's `evidence_commit`, the test results' commit must be in its history, and the file's evidence must equal the evidence committed there. A file set to `paper` without a registry row is refused ("status: is paper but the registry says research") | MET |
| 5 | The worked example loads, marked research, claims no pass | `playbook check`: "research … approved for paper: none (Book 1 trades nothing)", which is the empty state, tested | MET |
| 6 | No `paper` unless every live feature passed B7 (loader gate) | **NOT MET: see below** | NOT MET |

## The must-fix: removed days pass the gate

`RecomputedLiveReports` accepts a committed report when **each row it contains** equals the fresh recomputation
("later days may exist"). B7's gate (`report_passes`) then counts days and agreement **from the committed rows
only**. So deleting days from the report is never noticed: the dropped days are a disagreement (cherry-picking) or
the most recent stretch (truncation).

**My test** (tests/playbook builders):
- the recomputation has 25 days, 5 of which disagree: 80% agreement, so the gate fails;
- I removed the 5 bad rows from the committed report;
- result: "cherry-picked report accepted: True | passes the gate: True".

This is the judge 44 follow-up's very risk ("hand-edited per-day values pass") in another form: removing values
instead of editing them.

**Fix (reasoning only):** the gate should decide on the **recomputation**, not the committed rows, for all recorded days
up to the approval. Alternatively, require the committed days to equal the recomputed days over the span (no gaps), with
the last committed day being the last recorded day before the approval. Add a test that removes a middle day and the
last days.

## Other points

- **The append-only check runs only as a test (CI), not in `playbook check`.** The criterion asks for a test, so this
  is MET. Running `rewritten_history` inside `playbook check` too would catch an edit before CI does (reasoning only,
  minor).
- **`freeze_record` as a required evidence field** (builder's question 2): sound provenance, and it costs nothing when
  a frozen protocol exists. My view: keep it (reasoning only; the owner decides).
- **Forward testing (builder's question 1):** option (a), recorded but untraded decisions for a frozen `research`
  version, fits D1 as built and keeps "Book 1 trades only what passed". Reasoning only; the owner decides.
- **Shallow clone:** `checks.yml` checks out with `fetch-depth: 0` (line 20, with a comment saying the freeze check
  needs it), so CI has full history. The builder's failure came from the container's shallow clone, not a CI gap.

## Project rules

New package with its own composition root (`fno/playbook/wiring.py`, listed in CLAUDE.md); B7's frozen files imported,
not changed; no order capability; files small. Clean.
