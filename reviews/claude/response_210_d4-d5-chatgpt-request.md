# Response 210: review request to ChatGPT for D4 and D5, Book 2's authority envelope and Book 3's constitution (quality rule 9)

**Why you:** D4 and D5 decide which trade decisions Books 2 and 3 may take on paper, and what the hard-validity check
(C4) refuses. They govern trade decisions, so quality rule 9 asks for a ChatGPT review after the judge's PASS (judge
207, FAIL, then addendum 1 PASS) and before the merge. They are story text only (owner, 16 Oct: "D4/D5 text only,
no AI cost"). The code waits for slice E's trigger.

**Exact version:** branch `story/d4-d5-envelopes`, at the head the orchestrator names.

**Read:**
- the D4 and D5 sections of `docs/stories/D-playbook-decisions.md`;
- the claims in `reviews/claude/response_204_d4-d5-envelopes.md` (7 claims with evidence, the owner's five answers,
  and the judge 207 table);
- judge 207 and its addendum;
- `docs/DESK_DESIGN.md` 12.2-12.4;
- design v2 `03_layers_factory_desk.md` rule 5 ("the owner never overrides on paper"; only S1's safety stop);
- `docs/DESK_DECISIONS.md`, the 16 Oct rows.

**What D4 and D5 do:**
- **D4, Book 2.** Each playbook version gets a trade envelope that marks each action of a closed list `allowed`,
  `shadow-only` or `forbidden`:
  - follow the rule;
  - choose among the day's eligible paper versions;
  - no trade;
  - a width from the version's own set;
  - reduce lots, never increase.

  Everything else is forbidden: strike, expiry, exit, threshold, structure. The version actually traded governs.
  The same `permits` check is called by Book 2's decider and, independently, by C4. Each envelope's hash is a D6
  version component (`trade_envelope:<name>-v<n>`); a changed file unscores the decision and C4 refuses it.
  Shadow-only actions are recorded but not scored until scoreboard A (S3) reads them.
- **D5, Book 3.** A frozen constitution sets:
  - NIFTY options, monthly expiries only;
  - all nine of C4's defined-risk structures;
  - a planned exit at most 21 calendar days after entry;
  - the packs as its only sources;
  - C2's risk limits and S1's scoring protocol as references, never numbers.

  Every strategy Book 3 invents is a playbook-format spec, registered with its hash in an append-only registry. Its
  registration commit must be a strict ancestor of the decision commit and come on an earlier session (no same-day
  invent-and-trade). An edited spec is refused. C4's Book 3 mode checks all of it.
- **The owner's five answers (16 Oct):** 21 calendar days; all nine codes; monthly only; D3 refuses any owner override
  for every book; and envelope v1 stays narrow.

**Questions** (for each: accept, partial or reject, with evidence; real cases only, per the owner's rule of 15 Oct to
keep the design simple):
1. **Is envelope v1 too narrow to test "does AI judgement add value inside the same tested strategy"?** With one
   approved strategy at one lot, Book 2 can only veto or change the width. Is that enough for a meaningful
   scoreboard A comparison against Book 1, or does it mostly measure vetoes?
2. **Can Book 3 game its constitution with a real case?** For example: registering many near-identical strategies,
   or one with a wide expiry window, then trading whichever looks best on the day. Does "registered on an earlier
   session" plus the trial count stop that, or is a registration cap or a minimum time before the first trade needed?
3. **Does the traded version's envelope governing `choose_strategy` leave a gap?** For example, a version whose
   envelope allows more than the rule default's version does.
4. **Monthly expiries only and the time exit only:** does that make Book 3's horizon (21 days) and its strategy space
   too small to answer the whole-system question?
5. **Anything that must change before slice E's code starts?**

**Answer file:** `reviews/chatgpt/review_130_d4-d5-envelopes.md` plus its line in `reviews/chatgpt/README.md`. Never
overwrite an existing file. If your write is blocked, paste the text in chat and the owner will relay it.
