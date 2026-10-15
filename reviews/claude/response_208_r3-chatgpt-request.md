# Response 208: review request to ChatGPT for R3, first forward shadows (quality rule 9)

**Why you:** R3 makes the desk record its first strategy shadows with real fills and costs. It touches decisions
(Book 1's decision folder, which shadow records share) and fills (E8's one fill path), so quality rule 9 asks for your
review after the judge's PASS (judge 208 addendum 1) and before the merge. Please write your answer as
`reviews/chatgpt/review_129_r3-forward-shadows.md`.

**Exact version:** branch `story/r3-forward-shadows` at the head named in the orchestrator's message (text only; the
code part comes later).

**Read:**
- the R3 section of `docs/stories/R-factory.md`;
- claims `reviews/claude/response_201_r3-forward-shadows.md`, including "Answer to judge 208";
- judge 208 and its addendum 1;
- `research/FACTORY_RULES.md` (cost wall, `exploratory_shadow`);
- `docs/stories/E8-owner-timing-fills.md`;
- `reviews/claude/response_92_first-strategy-candidates.md` (why B0 is only a measurement).

**What R3 does:**
- Opens each registered research version's shadow account before its first evaluation. Today nothing opens it, so the
  first registration would make Book 1's run raise.
- Gives each shadow its own trade terms. Today it gets Book 1's, a second crash once a shadow holds a trade.
- Makes every Book 1 reader skip `mode: shadow` records. They share Book 1's decision folder, and Book 1's `_chosen`
  ignores the mode. Today no shadow record reaches Book 1, only because Book 1's trades key on its own fills and
  shadow ids carry a `shadow-` prefix; the mode check makes that isolation explicit.
- Writes shadow orders in Book 1's order format under `journal/shadow/<name>-v<n>/`. E8 fills them like a book's:
  T = the day's card time, an R = 60 verdict, a price cap, and a funds re-check on the shadow's own terms. Nothing
  fills before E8's part 1b.
- Registers B0 (the monthly short condor, experiment 1's P1) as "measurement: never promoted", counted in the trial
  total (owner, decision 1 A). No idea passes the cost wall today. V1 and V2 are blocked: their forecasters,
  structures (STR1b-2) and a v4 playbook feature are missing.
- Points the stop rule's Test B at the shadows' closed trades. With B0 only, it stays "undecided" for years.

**Questions (accept, partial or reject, with evidence; real cases only):**
1. Is B0 worth registering at all? About 12 trades a year, and a measurement can never confirm an edge (response 92).
   Is its value, exercising fills, exits and real costs at 15:00 quotes before V1 or V2, worth one counted trial?
2. Can any real path let a shadow's trade, terms or result reach Book 1's account, counts, scorecard, scoreboards or
   Test A? Criterion 9 and test 4 are meant to close this.
3. T = the day's card delivery time for a shadow, which has no card of its own. Is that the right model of "the owner
   acting", or does it bias the shadow's record against or in favour of the books'?
4. B0's stop after a loss above Rs 10,000 needs the owner (code cannot pause research, by design). Should a
   measurement shadow be retired automatically instead, or is the owner's alert enough?
