# Response 189: story RM2, the real-money test record (story text for the judge's story check)

Builder session: session_01CHxE3ywfyCMxFLx6HGLwRo · Orchestrator: session_01VG1RqxLFUVdvvPuMRYZtDH · Branch:
`story/rm2-real-money-record` · Issue #108 · Lane 1 (JUDGE.md rule 9: judge, then ChatGPT, then the owner).

Files: `docs/stories/RM-real-money.md` (RM2 section; RM1's status line set to done), `docs/WORK_REGISTER.md` (row).
No code. Nothing here places, prepares or enables an order; RM2 makes no Groww call at all.

## Claims

| # | Claim | Evidence |
|---|---|---|
| 1 | Every number RM2 uses is the frozen gate's: 1 lot; max(30, registered) trades and 6 months; −Rs 500 paired bound; prediction floor; Rs 1.50 per unit (pad Rs 1 + Rs 0.50); 10% unknown legs; 90% of cards; −Rs 20,000 cumulative; Rs 20,000 peak to trough; Rs 2 over 5 trades; 5-minute quote age | strong evidence (read side by side with `research/evaluation/REAL_MONEY_GATE.md` on main) |
| 2 | Times match their owners: the card posts after `quotes_done`, so at 15:15 or later (O1, `story/o1-daily-run`); E8's R = 60 paper fill is the next session's 10:15 mark | strong evidence (O1 lines 82-88; E8 rule 2) |
| 3 | RM1's open note is answered: "next A16 snapshot after the fill" is the first mark strictly after the fill time, because an E8 fill always sits on its due mark | strong evidence (E8 rule 2: the fill mark is a mark) |
| 4 | The order-time quote takes the latest A16 mark at or before the order (age 0 allowed), as the gate's fallback says; Drive's upload time cannot date a screenshot, so the owner types the image's time | reasoning only |
| 5 | Records stay in Drive; the repository gets only SHA-256s and a status line without prices, strikes or rupees (decision 8.5, option b) | reasoning only |

## Owner questions

Q1-Q3 in the story (how fills are reported, when an unreported card is skipped, actual or modelled charges). None
changes a gate number; Q2 fills a gap the gate leaves (when a card counts as skipped).

## Coordination

Work register read on main at 3627d0bd: no row covers RM2. E8 (fills), T1 (cards) and A16 (marks) are read only.
