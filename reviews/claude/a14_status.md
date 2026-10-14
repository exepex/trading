# A14 status (builder session 01FVYzWZtDAZrZLDZ6DtmSYL)

Updated: 14 Oct 2026, about 07:45 IST. Branch `story/A14-nse-margins`, draft PR #90, issue #89. Commit: see the
branch head (this file is committed with it).

Done:
- Story A14 written; code, 47 tests, manifest (1-14 Oct), workflow (manual only; morning schedule 07:45 and 08:30
  IST written in its header for after validation). Full suite 2,148 passed at da54cda and 2,147 after the morning-schedule change (one due-time case removed); ruff and import check clean.
- Mutation checks: late file accepted -> 3 tests fail; invalid file written -> 2-3 tests fail.
- Claims: `reviews/claude/response_77_a14-nse-margins.md` (renumbered from 71 and 74), incl. Groww (a)-(e), stressed-margin
  proposal (1.45 from 2020, 2024 and 2026 windows), the SPAN-netting question.

Open:
- Independent check: Zerodha's public SPAN calculator returns empty before market hours; waiting for the 09:25 IST
  trigger. NSE's own calculator is HTTP 403 from here.
- Judge: SPAN-netting definition (A = scan alone, written now; B = scan minus net option value; exact C2 input =
  max(0, scan - NOV) + min(0, NOV)). C2 unchanged.

Question for the orchestrator: none blocking.
