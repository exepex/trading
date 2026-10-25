# Judge 677: DOC1 plan, one clean current document set (story/doc1-clean-docs @ a482f2d7e), judge E

**FAIL (round 1 of 2; 2 should-fix, 3 minor). Lane 1** (it rewrites rule documents; judge 1 of 2). Judge E, own
session; judge F's verdict not read. Text only: the plan (103 lines) and one WORK_REGISTER row.

## Counts re-counted (section 1, at 8edc21139, my own `git ls-tree` and line counts)

| Claim | Mine | Result |
|---|---|---|
| 1,296 Markdown files | 1,296 | MET |
| `docs/`: 108 files, 44,865 lines, 33 over 350, largest 5,057 (HANDOVER) | 108 `.md`, 44,865 lines, 33 over 350, HANDOVER 5,057 (`docs/` has 112 files counting non-Markdown) | MET |
| `docs/stories/`: 75 files, 31 over 350 | 75, 31 | MET |
| `conversations/`: 36 files, 9,511 lines | 36, 9,511 | MET |
| `reviews/` about 950 files | 956 | MET |
| DESK_DECISIONS line 29 quote | holds, word for word | MET |
| DESK_DECISIONS "345 rows" | 339 data rows (340 table lines, less the header) | minor 1 |
| 95 doc-reading test files | 95 | MET |
| code reads DESK_DECISIONS "18 references" | 43 lines in 27 `fno` files; 50 files in code, tools, tests and workflows | minor 1 |

## Findings

**Should-fix 1. `docs/DESK_DECISIONS.md` is a record that money code reads, not a document to rewrite.** Strong
evidence: code read. The plan replaces it with `docs/decisions/` ("superseded rows removed").
- **C5b, risk:** a brake restart is valid only when it cites the title of exactly one owner-quoted row of this file
  (`risk/decision_rows.py`, `risk/overrides.py:51`). C4's validity check reads it too (`checks/validity_account.py:159`).
- **BG1, budget:** `config.yaml` `budget.plan_cost.decision` is "DESK_DECISIONS 15 Oct 2026: Claude plan cost: INR
  20,000 a month". `budget/plan_cost.py` refuses the decided cost when that is not a row of the file.
- **A frozen record cites it:** `research/forecasts/FREEZE_v4.md` (lines 18 and 27) cites its rows by title, and can
  never be edited. CLAUDE.md's routine section, which the plan keeps word for word, cites "DESK_DECISIONS lines 284
  and 287". Workflows and judge reports cite it too.
- **The lane gate names it:** `tools/ci_scope.sh` lists it (and `WORK_REGISTER.md`) as lane-3 paths.
- Removing, renumbering or moving its rows would therefore:
  - make a valid restart or the budget's cost fail;
  - leave frozen citations dangling;
  - change the lane gate.
- Fix: list `docs/DESK_DECISIONS.md` under "Not in scope (records)": kept at its path, append-only, no row removed or
  renumbered. The new `docs/decisions/` pages say what is current and cite its rows.
- The same applies to every document a frozen file or a record cites: `docs/stories/G6-v4-freeze.md` (FREEZE_v4 line
  41) and `docs/JUDGE.md` rule 9 (line 28). They keep their path and their cited sections, or they stay as records.

**Should-fix 2. The register claim and the switch can lose other builders' changes.**
- The row claims `docs/**`, but every story builder edits `docs/stories/` and the register daily. As written, "one
  builder per function" would block them all, or be ignored.
- Between an area's P1 scan and its P6 switch (days), other sessions change that area's documents on `main`. P4 writes
  from the scan's snapshot, and P6 removes the replaced files, so a rule added meanwhile is lost silently.
- Fix:
  - claim only DOC1's own new folders, and each area's files only during its write;
  - pin each scan to a commit;
  - at P6, require `git diff <scan commit>..main` over the area's files to be reconciled. A plant: a rule added after
    the scan must be caught.

**Minor 1.** Correct the two counts above (339 rows; 27 code files and 43 lines, not 18).

**Minor 2. A cross-area pass is missing.**
- The market-school miss was one decision (response 325) that changed several areas at once: Books 1, 2 and 3, the
  plan and the build map. Per-area scanners must also list each cross-area decision and the areas it touches.
- P1 should name `reviews/claude/` responses and `conversations/` explicitly as sources, since that is where 325 and
  the owner's words live.
- With that, P2's "superseded (by what)" and P3's quoted intent would have caught both misses.
- The Book 2 miss is caught by P3: the intent page quotes the 13 Oct words, and P5 checks the design against it.

**Minor 3.** P6 must also update `tools/ci_scope.sh` (a CI file, lane 2) for every moved lane-3 path, and code
comments that cite `DESK_DECISIONS` by line number.

## Checked and sound

- The routine-prompt rule (section 4.1) and P6's 08:30-20:30 IST window.
- No frozen or byte-checked file is in scope: v4's `byte_checked` (149 files) and `RECORDED` name no `docs/` file, and
  no record holds a SHA-256 of any `docs/` file.
- PROC1's item taken over by agreement.
- Delete only with the replacement in the same commit.
- Gates on a482f2d7e in a clean worktree: record scan clean (9,537 files); doc-reading tests 963 passed, 13 xfailed,
  0 failed (no `test_groww_install_command` failure).
