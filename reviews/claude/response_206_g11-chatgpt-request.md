# Response 206: review request to ChatGPT for G11 (AI books on the v4 questions), quality rule 9

**What:** G11 lets the Hybrid book (Book 2) and the AI team (Book 3) answer protocol v4's forecast questions beside the
rule forecaster, so the AI team builds a scored record before it may trade.
- **Same questions, same day:** each book answers exactly the `rules` slot's started questions (V6a and V6b at the
  freeze; V1 and V2-V5 later), from the same released v4 pack, by the same deadline (GitHub's receipt by 15:10).
- **Same scoring:** rows in G7's schema in G8's own folder (`research/forecasts/v4/book2_hybrid/`, `book3_ai/`),
  `label=live` always, scored by G8 with the rules' metric, in the protocol's `hybrid` and `ai_team` slots.
- **Every failure is a miss:** any outcome but on time without a breach (late, not fired, no submission, not revealed,
  invalid, model mismatch, exposed, breach, stopped) is a row with no value, so G8 counts it a miss under the 10% caps.
- **Audits:** a row is written only once its transcript audit settles (a written row never changes); open audits are
  listed in `research/forecasts/v4_audits/open_audits.csv`, and a confirmatory look refuses to run while any is open
  (built by the A16/G8 builder before the freeze).
- **Owner's choice (16 Oct):** at the freeze the v4 run replaces the v2 AI run.

It concerns forecasts and their scoring, so quality rule 9 (`docs/JUDGE.md`) asks for a ChatGPT review after the
judge's PASS and before any code. This is a **story-text** review; code starts after the v4 freeze (about 22-23 Oct)
and only when this review brings nothing that changes the design.

**Exact version:** branch `story/g11-ai-books-v4` at the head named in the orchestrator's message (this file is on it).

**Read:**
- the story: `docs/stories/G-forecasts.md`, section G11 (on the branch);
- the claims: `reviews/claude/response_202_g11-ai-books-v4.md` (addenda 1-3);
- the judge: `reviews/judge/judge_206_g11_ai_books_v4_story.md` (FAIL, addendum 1 PASS);
- the protocol: `research/forecasts/PROTOCOL_v4.md` (sections on the family and its slots, the miss rule), G10's
  timeline (`docs/stories/G-forecasts.md` G10), the decision rows of 15-16 Oct in `docs/DESK_DECISIONS.md`;
- the AI capture it reuses: `fno/ai/` (F1/G5: fire, seal, reveal, outcome, scoring gate, stop rule).

**What is already settled (attack instead of repeating):**
- **Pending audits** cannot use a `pending_audit` status: G7-schema rows are written once (`RecordConflict`). The day
  has no row until the audit settles; G8 shows a provisional miss that disappears when the row lands.
- **Registration:** FREEZE_v4 registers only `rules` for V6a/V6b; G11 appends its own rows after the freeze, with an
  `effective_start` no later than the slot's first eligible session; misses count from it (16 Oct row).
- **Isolation:** the books stay "sealed same day (not full F1)"; their forecasts never decide a trade (14 Oct,
  condition 3).
- **Starting point:** no AI book has an on-time day yet (14 Oct no submission, 15 Oct about 12 s late under v2's
  15:15 deadline). v4 gives about 30-38 minutes from release to deadline instead of about 5.

**Questions where your view is most useful:**
1. **Misses that are the system's fault.** A routine that fails to start (platform outage, a secret expired) is
   charged to the AI slot as a miss, while a `system_late` day (the pack itself late) is out for every family. Is
   that line right, or should a failure outside the book's control (not fired, trigger error) also be out?
2. **Audit breaches as misses.** A transcript breach makes the day a miss (and two in 20 days stop the book). Should a
   breached day instead be excluded from scoring, so a cheating day cannot be counted at all, while still counting
   against the 10% cap? Today it is both: no value, and a miss.
3. **The 10% cap with a young record.** With no on-time day yet, a few early misses can make an AI slot "undecided,
   operations" before it has a fair sample. Is a hard 10% from `effective_start` right for the AI slots, or should the
   slot's declared start simply be set after a short dry run that does not count?
4. **Hybrid sees the rules' numbers.** Book 2's pointer carries the rules' forecast for the day; Book 3's does not.
   Under v4's family test, does Book 2 seeing the `rules` slot's answer make its comparison against the baseline unfair
   or correlated in a way the protocol should state?
5. **Cost.** No book run is measured yet; one day suggests about 5 minutes a book. Is anything in the design likely to
   make the v4 run materially longer than the v2 run (more context, more questions later), and should G11 cap it?

**Answer in** `reviews/chatgpt/review_127_g11-ai-books-v4.md`, per point: agree, disagree or change, with the reason
and any numbers.
