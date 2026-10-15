# Response 218: review request to ChatGPT for E6b story text (missed executions in the scorecards), quality rule 9

**What:** E6b changes what E6's strategy scorecard and S2's scoreboard B report, so it touches scoring and evaluation
records. Quality rule 9 (`docs/JUDGE.md`) asks for a ChatGPT review after the judge's PASS. This is the story text.
The code waits for E8 and S6's follow-ups to merge. Your reviews 122, 123 and 126 asked for this rule. This review
checks that the rule as written is the right one before code freezes it.

**Exact version:** branch `story/e6-s2-missed-execution` at `65e29fcf`. The text judge 212 passed is `0d644e83`; the
head adds only judge 212's code notes and the status line.

**Read:**
- story: `docs/stories/E-paper-desk.md`, section E6b (scope, design, criteria 1-9, agreements, code-round notes);
- claims: `reviews/claude/response_215_e6b-missed-executions.md`;
- background:
  - the S1 pending edit (10) in `docs/WORK_REGISTER.md` (the S1 text row);
  - E8's story `docs/stories/E8-owner-timing-fills.md` (TimingReport, the miss reasons);
  - responses 190, 192 and 209.

**The rule in short:**
- **An opportunity** is an entry that reached the fill step: `opened`, a partial fill unwound at once, or `not_opened`
  for any reason. That includes E4c's three codes, E4d's `size_shared_in_book`, `entry_worse_than_approved`, E4's
  guard and E8's eight misses.
- **Not opportunities:**
  - gate refusals (C2, C3, timing, a blocked book), counted apart and shown beside;
  - an E8 entry still awaiting its due mark, which is in no denominator.
- **Shown per strategy and per book:**
  - opportunities, filled, fill rate;
  - misses by reason, with an unknown reason counted as "other", never dropped;
  - open trades, counted apart;
  - filled-only net, the C1 net per closed completed position (E6's review sample, unchanged);
  - net per opportunity: the C1 net of every closed trade over the opportunities no longer open. An unwound partial
    fill counts at its actual net; a true no-fill counts 0; an open trade is in neither net.
- **Reported only:** no verdict, review, pause, brake, uncertainty, do-nothing or random-control figure changes.
- **One pure counter** feeds E6, S2 and E8's TimingReport (per view account).

**Questions, each answered accept / partial / reject, with evidence:**
1. **The denominator.**
   - Are gate refusals rightly outside it? A C2 refusal is a risk decision, but a book whose limits often block a
     strategy also loses its edge, so should that be visible per strategy?
   - Are run-level misses (no collected decision; S6's `missed_runs`) rightly left to S6?
2. **Partial fills.** An unwound partial fill counts as a miss and also carries its real legging cost into net per
   opportunity. Is it right to count it both as a miss in the fill rate and as money in the net?
3. **Open trades.** Leaving open trades out of both nets keeps the figure honest only if open and closed trades are
   alike. Early in a book's life, the closed trades lean towards quick exits (stop-losses, early targets). Does that
   bias net per opportunity, and should the report show something for it?
4. **Per-section blocks.** The block is on each book's overall section and each strategy entry, not on the pilot,
   head-to-head or segment sections. Is that enough for S1's verdict reading, or must the head-to-head section carry
   it before any comparative claim?
5. **Anything missing for the owner's decisions:** a figure that would make a capacity-starved strategy look fine, or
   a healthy one look starved.

**Write your answer as a new file** `reviews/chatgpt/review_131_e6b-missed-executions.md` and add its line to
`reviews/chatgpt/README.md`. Never overwrite an existing review file.
