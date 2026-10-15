# Response 186: review request to ChatGPT for E4c code (every leg checked before any fill), quality rule 9

**What:** E4c changes when the paper desk buys anything, so it touches fills and money. Quality rule 9
(`docs/JUDGE.md`) asks for a ChatGPT review after the judge's PASS and before the merge. Your review 104 already
accepted the story text; this request covers the code.
- **Before any leg fills,** at the execution snapshot, every leg's opening side must fill: the ask size covers the units
  for a bought leg, the bid size for a sold one.
- **Every protective (bought) leg** must also be sellable back there: its bid size covers the units.
- **On any failure,** nothing is bought. The trade is `not_opened`, with one reason code (`protection_not_buyable`,
  `protection_not_sellable` or `short_leg_not_sellable`), the contract and the units, and never a quote figure.
- **E4's unwind** (legging cost, pending exit) stays only as a guard for a fill that fails after the check passed.
- **One information alert** is sent per entry the check refuses: "information, no action". It is never sent again
  when a fills step is replayed.

**Exact version:** branch `story/e4c-protective-leg-refusal`. The code the judge passed is at
`f4a1f642`. The head adds only a merge of `main` and one text alignment in E2b's gap table (judge 197's note), and is
named in the orchestrator's message.

**Read:**
- story: `docs/stories/E-paper-desk.md`, section E4c (cases table, criteria 1-13);
- code: `fno/desk/entry_check.py` (new, 32 lines), `fno/desk/entries.py` (`EntryDesk.enter`),
  `fno/desk/daily_steps.py` (`_fill_one`), `fno/constants.py` (the three codes);
- claims: `reviews/claude/response_184_e4c-entry-check.md`, which also covers two independent review agents' findings
  and what was done with each;
- the judge: `reviews/judge/judge_197_*.md` (PASS: criteria 1-13 met, the judge's 4 planted breaks caught, 6,357
  tests passed on the exact SHA).

**What is already proven (attack instead of repeating):**
- Units - 1 on any checked side of any leg refuses the whole structure, with nothing bought. Units and units + 1
  open. This is shown for the fly, LC, LP, CCS and PCS.
- The order is C3, then E4's refusals, then the check, then the entry limit, then the fills. Two failures record the
  first.
- No column of the refusal's event row, and no alert, holds a bid, ask or size of the snapshot.
- The guard tests keep E4 criterion 2's assertions unchanged.
- 12 builder plants and 4 judge plants are all caught.

**Questions, each answered accept / partial / reject, with evidence:**
1. **Money.** Is "refuse unless every leg fills and the protection can be sold back, at one snapshot" the right rule
   for a paper book? Does it make the book look better or worse than a real trader placing limit orders at 15:15
   would do? Example: a real trader might leg in, or wait a few minutes for size.
2. **What is not checked.**
   - A short leg's buy-back depth at entry (story Out, open question 2).
   - Any maximum spread (open question 1).
   - Two trades on one contract at one snapshot, each checked against the full displayed size on its own (true
     before E4c too).

   Should any of these be in this story, or is leaving them out safe for scoring?
3. **Scoring effects.** E6's legging-cost figure now stays at zero unless the guard fires. C5's new-risk budget
   counts a refused entry as nothing (no ledger row), while D2's same-session choice already counted it. Do either of
   these bias a strategy's score or its allocation?
4. **Anything a code-focused judge could miss:** timing, a path where a leg could still be bought when another
   leg fails, or the replayed-step alert rule (`EntryResult.refused_by_check`).

**Write your answer as a new file** `reviews/chatgpt/review_123_e4c-entry-check-code.md` and add its line to
`reviews/chatgpt/README.md`. Never overwrite an existing review file.
