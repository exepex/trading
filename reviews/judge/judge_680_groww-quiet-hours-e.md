# Judge 680: Groww quiet hours rule (story/groww-quiet-hours @ 7dc8b0b11), judge E

**PASS (round 1; 2 minor). Lane 1** (a rule about an outside service; judge 1 of 2). Judge E, own session; the other
judge's verdict not read. Text only: CLAUDE.md "How to work" (+4 lines) and AGENTS.md (a new 5-line section).

## Checks

| # | Check | Result | My evidence |
|---|---|---|---|
| 1 matches the owner's words | MET | `conversations/2026-10-25.md` (57dd796ab) quotes: "no human or AI session should run it during 09:15–15:35 IST", where "it" is the manual Groww commands. The rule says "No hand-run Groww command from 09:15 to 15:35 IST ... only the scheduled routines and their own steps call Groww" |
| 2 matches DESK_DECISIONS 57dd796ab | MET | The row "No hand-run Groww command 09:15-15:35 IST" carries the same scope and names CLAUDE.md "How to work" as the owning text. AGENTS.md gives one paragraph and points to it |
| 3 the stated limits are true | MET | 10 a second and 300 a minute for Live Data, and 150 sign-ins per 24 hours: `research/school/probes/2026-10-22-p0-1-groww-chain.md` lines 18 and 22, `fno/providers/groww_sign_in.py:3` |
| 4 no routine conflict | MET | A16's marks, the 3 pm parts, the daily run's Groww steps and step 2b's one rerun are all run by the scheduled routine itself. The pre-open capture ends about 09:12, and its open check reads NSE, not Groww. The hand fixes in the routine sections are git commands only |
| 5 narrows no lane-1 rule | MET | It only adds a restriction. Read-only Groww, no orders and the secrets rule are untouched |
| Gates | MET | Record scan clean (9,539 files); doc-reading tests 963 passed, 13 xfailed, 0 failed |

## Findings

**Minor 1. "no test ... is run by hand then" can be read as "no pytest in market hours".**
- The suite never calls Groww live: every Groww test uses `tests/groww_sdk_fake.py`, and none needs credentials.
- So the rule means a live Groww test or probe. Read literally, it would stop builders and judges from running the
  gates for six hours of every session day.
- Fix: "no live Groww test, probe, download, backfill or check (the test suite uses a fake Groww and is not
  affected)".

**Minor 2, for the owner to know, not a defect.** A hand rerun of `python -m fno daily run` from 09:15 to 15:35 is
now ruled out: it calls Groww. The 22 Oct recovery, when the orchestrator reran the day by hand from 14:09, would not
be allowed.
- If the scheduled 14:05 run fails outright before its 3 pm parts, that day's quotes are lost, unless the scheduled
  session's own step 2b covers it.
- Name the daily run explicitly as a Groww command, so a session cannot argue that it is not one.
