# Response 270: F5 story text, Book 2's AI decider rewritten to design v2 (for judge E)

**Branch:** `story/f5-book2-decider`. The text is in `docs/stories/F5-book2.md`. `F-ai-layer.md`'s old F5 now points to
it.

**Why rewritten:** the old F5 predates design v2. It fed the red team (F3) and owner overrides into Book 2. REPLAN
turns F3 into the devil's advocate, whose objections can never block, and DESK_DECISIONS row 229 drops overrides
on paper.

**What the text decides, and who agreed it:**

| Point | Decision | Agreed with |
|---|---|---|
| Where the AI sees the rule default | A `BookSheet` E2 hook in the `pack` step, written into Book 2's private pack as `"evaluation"`. No journal file, because a committed file would be public (E2c's privacy rule; the O9 rule) | E2c's owner 0134MoC6 proposed it, and who edits the pack code is still open; F6's builder 01KTAQCD wants one hook for Books 2 and 3; O1's builder 014zYLf1 confirmed D2 needs data that exists only from the `pack` step |
| Hand-over | F1t's `AiBookDecider.decide(AcceptedDecision) -> DecidedRun`. F1t fills no record field | F1t 01PLbKH15 (story/f1t-ai-trading-runner 1da500c4) |
| Answer check | `check_answer`, standard library only, called by F1t's `seal` | F1t |
| Selection | F6's generic `SelectionAllocator` with `Pick(opportunity_id, reason, width, lots)` and a `rebuild`, so one implementation serves both books | F6's builder |
| C4 independence | C4 reads `rule_default` and `eligible` from the hash-covered sheet, never from the AI. D3's replay recomputes them | F1t; for judge E to accept or reject |
| Unproven limit | Re-checked at C4 from E5's counts | judge 260 addendum 2 (D4 option 2, for F5's switch-on) |
| Estimand | "AI veto and width selection within the same registered playbook" | D4's known limits; ChatGPT review 130 |

**Open questions in the text:**
1. Does Book 2 switch on without F4's AI judge? I recommend waiting for F4 (reasoning only).
2. One slot per rule-default trade, or a whole set?

**For the judge:**
- The 30 s budget is an estimate (reasoning only): D2 is not re-run at 15:11, only C2, C4 and the store write.
- The E2 hook changes E2c's files. Who makes that edit is not settled yet.
