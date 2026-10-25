# Judge 678: DOC1, one clean current document set, plan (story/doc1-clean-docs @ a482f2d7e)

**FAIL on 3 should-fix, plan round 1 of 2, judge F (judge E the other; not read). Lane 1.** Own session
(session_01A8XfbTUVgeeEpqatHaWbtP). Text only. Labels: strong, some, reasoning only.

## Section 1 counts (re-counted at 8edc21139 with `git ls-tree`, `git show | wc -l`)

| Claim | My count | Result |
|---|---|---|
| 1,296 Markdown files; `docs/` 108 files, 44,865 lines, 33 over 350, largest 5,057 (HANDOVER_2026-10-16) | 1,296; 108 Markdown (112 files in all), 44,865, 33, 5,057 | TRUE (say "108 Markdown files") |
| `docs/stories/` 75 files, 31 over 350 | 75, 31 | TRUE |
| `conversations/` 36 files, 9,511 lines; `reviews/` about 950 | 36, 9,511; 956 | TRUE |
| 95 doc-reading test files | 95 | TRUE |
| DESK_DECISIONS.md "345 rows" | 345 lines, 339 dated rows | minor: lines, not rows |
| DESK_DECISIONS.md "18 references" in code | 9 path mentions in `fno/`, 44 mentions in `fno/` and `tools/`; one runtime read (below); 20 test files | minor: not reproducible; name the readers |

Gates (trial merge with main; only `.md` files change): record scan clean (9,537 files); doc-reading tests 963 passed,
13 xfailed.

## Findings

1. **Should fix: `docs/DESK_DECISIONS.md` is a live input and a record, not only a document (strong evidence).**
   - The money and risk code reads it. `fno/risk/overrides.py:51` checks every brake restart against its rows by title
     (`DESK_DECISIONS_FILE`, story C5b, `decision_rows.py`): the title must belong to exactly one dated row that quotes
     the owner. Removing "superseded" rows or splitting the table into `docs/decisions/` can stop a restart from being
     accepted. A changed title can also make another row match.
   - Records require it. `research/evaluation/REAL_MONEY_GATE.md` (in S1's `frozen_files`, line 420) asks for future
     evidence as "a dated row in `docs/DESK_DECISIONS.md`" (lines 133, 144). PROTOCOL.md and FREEZE_v4.md cite its rows.
     Frozen text cannot follow a move.
   - `tools/ci_scope.sh:12` lists it as a lane-3 path.

   The plan treats it as one of the "documents replaced" (section 2 table) and puts it in the register row's scope.
   Fix: keep DESK_DECISIONS.md where it is, append-only, outside DOC1's scope, like `reviews/`; the new `docs/decisions/`
   pages cite its rows by title. Any change to its form or path is a separate lane-1 code story (C5b's reader, the gate
   text before its freeze).
2. **Should fix: citations into moved files break silently (strong evidence).**
   - Frozen and recorded texts cite `docs/` paths. FREEZE_v4.md cites `docs/JUDGE.md` and
     `docs/stories/G6-v4-freeze.md`; judge reports cite story sections and line numbers (e.g. "line 980").
   - There are 138 "DESK_DECISIONS line/row N" citations in Markdown and code (e.g. CLAUDE.md "lines 284 and 287",
     `fno/playbook/decision_record.py:42` "row 229").
   - P6 moves JUDGE.md to `docs/process/`, splits the multi-story files, and safety rule 4 removes the old files. Nothing
     keeps these citations valid, and no test reads them.

   Fix: add a safety rule. A file cited by a frozen file or a record keeps its path, or keeps a short pointer file at that
   path; `docs/README.md` keeps an old-path to new-path map; decisions are cited by title, not by line. Then add the
   cited paths to section 4's check list.
3. **Should fix: the gate that would have caught the Book 2 and market-school misses is not a deliverable (reasoning
   only).**
   - Both misses were a story or design never checked against the owner's intent, and superseded text left in place.
   - P1-P5 would find today's cases. But only principles 3 and 4 say how the next one is prevented. P7 delivers the
     CLAUDE.md/AGENTS.md slimming, the update-in-place rule and a size test. It does not deliver the JUDGE.md change:
     every story cites its intent line, a judge checks the story against it (a FAIL when missing), and a merge that
     changes a rule updates its area page in the same merge.

   Fix: put those JUDGE.md rules, and how they are checked, into P7 and its gate.

## Notes

- Section 4's other risks hold. The routine prompts name CLAUDE.md sections, and those sections stay word for word. PROC1
  item 3 (the docs archive) is taken over with its builder's agreement before P1. The frozen files listed in section 2
  are out of scope.
- P6's window (outside 08:30-20:30 IST) clears every routine. Name the rehearsals and judge sessions too, or keep the
  switch to one merge, so that one read sees one set.
