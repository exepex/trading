# 26 Oct 2026 (IST): A14c part 2 builder (session 01JkD3wtEQbxiE7qLHzQS7jp)

No owner message reached this session. It ran its own scheduled reminder for Monday's after-close sample.

## What was done
- **Read-only Groww rehearsal at 15:47 IST**, after 15:35 under the owner's 25 Oct rule. It used the A14c part 2
  follow-up's merged head (ff978df29): the real 26 Oct A14 rows, the SPAN file and the dated lot from Drive, and Groww
  through `get_provider` with GW1's guards. The clock was pinned to 10:00; the record stayed in memory and nothing went
  to Slack.
  - 15 of 15 baskets ok.
  - SPAN within Rs 0.50 a lot; exposure equal to the paisa.
  - 17 requests in 69.6 s.
  - Account afterwards: 0 orders, 0 positions, 0 margin used.
  - NIFTY was the same before and after (market closed), so the moving-range rule is not tested yet.
- **A20a's new 06:00 IST lot slot, first day:** the lot file landed at 10:35 IST, about 3.5 h before the 14:05 check.
- Claims added to response 291 on story/a14c-part2-followup (fd02d6a82).

## Decisions so far
- A14c part 2 merges with its follow-up after judge L's PASS and judge M's look at the merge resolution (owner,
  25 Oct). The margin check goes live on Tue 27 Oct (orchestrator, under the owner's 25 Oct rule).

## Open questions
- Tue 27 Oct about 14:06 IST: the first scheduled live check, and the first real test of the two NIFTY readings.
