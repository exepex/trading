# Judge 685: AG1 separate sessions per builder and judge

Branch `story/ag1-session-process`, SHA 0cfa79ec5fc5f47f0fbda6058d851eeafbf914f3 (one commit on fefcf893). Judge R
(session_01KR5SiKNBq2bYMHtd8GbdN6). **FAIL** (2 should fix, 1 minor). Lane 2 (rule document; adds judges, narrows no
lane-1 rule and touches no hard line), judged on the orchestrator's routing.

## Criteria

| # | Criterion | Result | Evidence |
|---|---|---|---|
| 1 | Rule matches the owner's words | MET | JUDGE.md quote equals `conversations/2026-10-25.md:385` (dba473c6); models, own session, no subtask, orchestrator coordinates, direct contact, report results and owner questions, independent judge all present |
| 2 | One owning document, others one line and a link | MET | JUDGE.md "Sessions, models and roles" owns it; CLAUDE.md:48-51 and AGENTS.md:39-41 each one bullet naming that section |
| 3 | The three documents say the same thing | PARTLY | no contradiction between the three bullets; but JUDGE.md contradicts itself on removals (finding 1) |
| 4 | Nothing weakens a lane, a hard line or judge independence | MET | old "Two judges" text kept word for word in the new section ("separate session ... shares no context"); new "second does not read the first's verdict" only strengthens |
| 5 | No text left saying judges or builders run as subagents | MET | grep of rule documents: only historical story Claims ("review agents") remain; quality rule 3 rewritten |
| 6 | Removals need two judges, clearly | PARTLY | stated, but the lane table and "Two judges for money pieces" still say otherwise (finding 1) |
| 7 | Gates | MET | `check_numbers` clean; doc-reading tests 977 passed, 1 failed + 3 errors only from the shallow clone ("run git fetch --unshallow", not a code failure per JUDGE.md) |

## Findings

1. **Should fix: JUDGE.md now gives two answers for a removal.** The new bullet says any removal "in any lane" needs
   two judges, but the lane table (JUDGE.md:16) still says lane 3 needs "None" and lane 2 only the orchestrator's
   check, and "Two judges for money pieces" (JUDGE.md:96) still says "Other lane-1 changes keep one judge". A reader of
   either older passage merges a deletion with one judge or none: the exact conflicting-documents problem the owner
   named. Fix: one clause in the table's lane-2 and lane-3 review cells (or a line under the table) and in the
   money-pieces paragraph pointing to the removals rule; and say whether a scheduled job's own data paths and lane-3
   files (conversation logs, register rows) are in or out, so "any lane" has a defined edge.
2. **Should fix: "executors run on Sonnet 5.5" can break the AI books.** Nothing defines "executor". The owner's
   scheduled routines execute too, and `docs/stories/F1-G5-owner-checklist.md:28` requires the Book 2/3 routines on
   Opus 5.5 ("another model makes every day model_mismatch"). Read literally, the new rule tells someone to switch
   them. Fix: define executors as sessions the orchestrator creates to run a task, and say scheduled routines keep the
   model their own checklist registers (or put the question to the owner through the orchestrator).
3. **Minor: who creates the reviewer session.** Quality rule 3 says the reviewer session is "asked by the builder
   directly", while the new section says every reviewer session is "created by the orchestrator". Say the builder
   asks the orchestrator for it (or may create it itself), then talks to it directly. Line JUDGE.md:105 is 166
   characters; rewrap it.

## Plants

1 planted: CLAUDE.md's "never as a subtask or subagent" changed to "as a subagent"; 3,108 tests reading the three
documents passed, so it survived. Not a finding (rule text has no test requirement); the judge read is the guard.

## Notes

- The orchestrator's own model is not stated; the owner did not state it either, so nothing is wrong.
- AGENTS.md also guides ChatGPT and Codex; the model line concerns Claude sessions. Optional: say so.
