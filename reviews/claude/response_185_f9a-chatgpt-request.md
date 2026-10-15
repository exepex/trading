# Response 185: review request to ChatGPT for F9a, role-value scoring code (quality rule 9)

**Why you:** F9a is scoring code. S1 v1 hashes it before the first counted decision (owner's option A), and it decides
whether each AI role "earns its cost", "drop proposed" or "inconclusive". Quality rule 9 asks for a ChatGPT review
after the judge's PASS (judge 194, PASS at f04076dd; addendum 1) and before the merge. F9a merges after S3.

**Exact version:** branch `story/f9-role-value` at the head named by the orchestrator. Its two follow-up fixes for judge
194's minors are tests and one filter, described below.
**Read:**
- the F9 section of `docs/stories/F-ai-layer.md`;
- claims in `reviews/claude/response_166_f9-role-value.md`: the story text, the answers to judge 172, the owner's
  answers, and "Code round" with its 8 deviations;
- judges 172 (text: FAIL, then addendum 1 PASS) and 194 (code PASS);
- S1's `role_value_schedule` and `role_value_minimum_sample` in `research/evaluation/PROTOCOL.md`;
- S3's `standard_unit.py` and `uncertainty.py`, which F9a imports.

**What F9a does:**
- **The comparison.** Each day a book decides, one AI role (or one declared bundle) is left out of a shadow decision.
  F9b, in slice E, will produce that shadow decision. F9a values both decisions with scoreboard A's one-lot standard
  unit. A no-trade on either side is worth 0 and counts as a change. A pair with an open action waits.
- **The checks.** The two decisions must use the same packs and the run log's snapshot. The day's role must be the one
  the rotation schedules, counted from the common start. A role inside a bundle is never judged alone.
- **The cost.** It is a declared split. The book's daily F8 allocation is divided equally among the roles consulted
  that day, so it is an upper bound. If the cost is unknown, the role gets no verdict.
- **The test.** It uses S3's moving-block bootstrap on net value per opportunity (block 20, 10,000 resamples, seed
  20261014). Two one-sided claims per role, "earns" and "drop", all go into Holm at 5% (owner, 15 Oct). A verdict is
  given only on S1's review dates and only with at least 30 changed opportunities. Worst month and the maximum-loss
  difference are printed beside the verdict and never decide it (owner: "money only, risk shown").
- **Control roles.** They are counted from C4's failure log: violations caught and invalid actions prevented, never
  profit.

**Questions** (for each: accept, partial or reject, with evidence; real cases only, per the owner's rule of 15 Oct to
keep the design simple):
1. **Does the declared cost split bias the verdict in a way that matters?** It is an upper bound, so it leans toward
   "drop". Would an equal split that also gives the decider a share be fairer, or does it only hide cost?
2. **Is Holm over two one-sided claims per role the right family**, given that it is stricter than S1's one-sided 95%
   for a single role? Is 30 changed opportunities a meaningful minimum when roles are ablated once every n days?
3. **The bootstrap runs over a role's applicable opportunities in date order, about 20n trading days per block.** Does
   the time between them break the block idea, for example through regime changes inside a block?
4. **Can a real case produce a wrong "earns" or "drop" without an alert?** For example: a shadow that is not truly
   card-withheld (F9b's end-to-end test), the snapshot reuse, or pairs that never close.
5. **Anything that must change before S1 freezes these files?**

**Answer file:** `reviews/chatgpt/review_122_f9a-role-value.md` plus its line in `reviews/chatgpt/README.md`. Never
overwrite an existing file. If your write is blocked, paste the text in chat and the owner will relay it.
