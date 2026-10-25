# 25 Oct 2026 (IST): A14c part 2 builder (session 01JkD3wtEQbxiE7qLHzQS7jp)

No owner message reached this session; it worked on the orchestrator's assignment (session 01Mt6dcBU5kp2htdPN2KmiZH)
under the owner's 25 Oct decision quoted there: every earlier pause lifted, every built feature switched on.

## What was done
- **A14c part 2 (the daily read-only Groww margin check)** was taken over from an unreachable builder.
  - Main was merged into the branch; the root cause of a first-run failure was found (O9's empty-prefix rule).
  - Round 1 at 5f7dc5d7c: judges 630 and 634 FAIL.
  - Round 2 at c2ed049e6: judge 630 PASS; judge 634 addendum 1 FAIL on one should-fix and one minor.
  - Both are answered on story/a14c-part2-followup at 99d0a211f. The owner decides, since two rounds are used.
- **Sunday rehearsal (read-only):** Groww's margin calculator refuses on weekends (GA000, "Margin cannot be fetched
  at this time"). The account read 0 orders, 0 positions and 0 margin used afterwards.
- **A20a's slot lateness, measured:**
  - GitHub starts fo-masters' 07:45 IST slot about 13:00 IST, and the 11:15 retry after 15:00.
  - So the lot file lands about one hour before the 14:05 check.
  - Fix: a 06:00 IST slot, on story/a20-lots-early-slot at 7ff32a3dc, for its judge.
  - NSE replaces the lot file in the evening (last-modified 21:47 IST), so an earlier copy is the same file.

## Decisions so far
- `daily.live_from.margin_check` goes live Tue 27 Oct, set by the orchestrator under the owner's 25 Oct rule, after
  the PASS.
- A failed margin check is never retried by O1. The day's broker figure is lost unless the check is run by hand
  before 14:50 and its receipts are committed (no retry added: the owner's call).

## Open questions
- For the owner: accept A14c part 2 with the follow-up (judge 634 addendum 1's two points answered at 99d0a211f).
- Monday 26 Oct 13:20 IST: the market-hours read-only sample, the first real test of the two-reading NIFTY range.
