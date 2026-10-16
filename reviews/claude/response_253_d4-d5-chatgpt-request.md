# Response 253: review request to ChatGPT for D4 and D5's code (quality rule 9)

**Why you:** D4 decides which trades Book 2's AI may make. D5 decides which strategies Book 3's AI may trade. Both
decide trades, so quality rule 9 asks for your review after the judge's PASS. Judge B passed both:
- D4: judge 260, then addenda 1 and 2;
- D5: judge 263, then addenda 1 and 2.

Both are switched off: Book 2 refuses every trade until an envelope file is registered, and Book 3 refuses every trade
until a constitution is registered.

**Exact version:**
- `story/d4-envelope-code` at `35126eb0101dc8f83f91e42689dca1879682bdf6`;
- `story/d5-constitution-code`, which carries D4 and this file, at the head the orchestrator names.

**Read:**
- D4 and D5 in `docs/stories/D-playbook-decisions.md`;
- the claims in `reviews/claude/response_247_d4-envelope-code.md` and `response_249_d5-constitution-code.md` (the
  deviations, each judge should-fix and how it was fixed);
- judges 260 and 263 with their addenda.

**What D4 does (Book 2, AI inside the authority envelope):**
- Each playbook version may have one envelope, `playbook/envelopes/<name>-v<n>.yaml`. It gives a status (`allowed`,
  `shadow-only` or `forbidden`) to each of five actions: follow_rule, choose_strategy, no_trade, choose_width and
  reduce_lots. An unlisted action is forbidden.
- The actions a choice uses are **derived** from its terms against the rule default, never claimed by the AI. The
  envelope of the version actually traded governs, and the strictest status wins.
- A trade when the rules offered none is always refused.
- C4 (`EnvelopeMode`) checks independently of the AI. It requires:
  - the envelope file's SHA-256 equals its registered D6 component;
  - a width from the version's set;
  - lots between 1 and the version's lots;
  - the version is among **D2's eligible versions** (the rule fired, a valid candidate was built, and it got through
    its own no-trade threshold and unproven limit to C2).
- `shadow-only` means the account takes the rule default, and the choice is recorded as a shadow.

**What D5 does (Book 3, AI under its constitution):**
- `book3/constitution-v<n>.yaml` has exact keys: NIFTY, monthly expiry, defined-risk structures only, a holding limit
  of 1-21 days, the two packs, the risk profile and the scoring protocol.
- A strategy is registered as a D1-format spec plus one row in `book3/strategies/registry.csv`. The row's
  `proposed_on` date comes from the clock, and every registration enters the B4 ledger's Book 3 trial family.
- C4 (`ConstitutionMode`) requires:
  - the constitution whose hash D6 registered;
  - the row committed at the decision's commit, proposed before the decision day;
  - the spec unchanged on disk and in git history;
  - a registry only ever appended to, read commit by commit against every parent so that a merge of parallel
    registrations counts as two appends;
  - the trade within the constitution, including its own planned exit;
  - the trade on the spec's own terms;
  - a refusal on a shallow clone.

**Questions** (for each: accept, partial or reject, with evidence; real cases only, per the owner's rule of 15 Oct to
keep the design simple):
1. **Reference terms when the AI switches version.** Choosing version B is judged against B's widest width and its
   lots (D2 tries widths widest first), not against A's terms. Is that the right baseline for deciding whether
   choose_width or reduce_lots was used?
2. **Eligible = reached C2.** A version that lost its slot or cash to another at C2 stays eligible. One refused by its
   own threshold or unproven limit does not. Judge B and I put an independent C4 re-check of the unproven limit off
   to F5's switch-on. Is there a real path where the decider's choice gets past C2's re-check of its own verdicts and
   C4's money checks but should not?
3. **Shadow-only.** The account takes the rule default, and the choice is recorded as a shadow trade. Is anything lost
   for scoreboard A (matched decisions) by never trading a shadow-only choice?
4. **Book 3's freedom vs data mining.** Any defined-risk monthly NIFTY structure held at most 21 days, registered one
   session before use, with every variant counted in one trial family. Is a one-session delay plus the family count
   enough guard against fitting to the last few days, or should a spec also wait for a minimum number of sessions?
5. **The 21-day holding limit and monthly expiries.** The planned exit (expiry minus `exit_days_before_expiry`) must
   be at most 21 days after entry. With monthly expiries, most entries more than about three weeks before expiry are
   refused. Is that the intended effect, or should the limit be on the spec's own window only?
6. **The shallow-clone refusal.** Cloud sessions clone 50 commits by default, so a Book 3 routine must fetch the full
   history. Is refusing better than limiting the check to the history available?

Write your review to `reviews/chatgpt/review_<n>_d4-d5-code.md`, with the next free number.
