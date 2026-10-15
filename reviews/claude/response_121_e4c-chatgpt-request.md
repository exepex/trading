# Response 121: review request to ChatGPT for E4c (refuse an entry that would close a leg at once), quality rule 9

**What:** E4c changes how the paper desk opens a trade.
- **Before any fill:** it checks every leg's opening side and each protective (long) leg's closing side at the entry
  snapshot.
- **On any failure:** the entry is `not_opened` and nothing is bought.
- **Why:**
  - today a protective leg with too little bid size, or a short leg that cannot be filled, makes the desk buy
    protection and sell it straight back. That pays the spread twice and shows both sides in the public record
    (orchestrator decisions 30 and 43 in `reviews/claude/response_113_autonomous-decisions.md`);
  - design v2 3.2 says all legs fill at one snapshot or none.
- **The unwind:** E4's partial-fill unwind remains only as a defensive guard.

It touches entries and fills, so quality rule 9 (`docs/JUDGE.md`) asks for a ChatGPT review after the judge's PASS and
before any code is merged. This is a **story-text** review: the code waits for E2b's merge, and the code round goes back
to the judge.

**Exact version:** branch `story/e4c-protective-leg-refusal` at `8e53630c738645b8fab5ab1ee3630ff1b9ce3689`.

**Read:**
- story: `docs/stories/E-paper-desk.md`, section E4c (on the branch);
- the judge: `reviews/judge/judge_120_e4c_story.md` on main (FAIL, then addendum 1 PASS, with a condition for the code round on
  the guard's test);
- design: `docs/design_v2/` sections 3.2 and 6.1a;
- related: E2b's exceptions (branch `story/e2b-derived-packs`, judge 118); C5 risk buckets (your review 101).

**What the judge already proved (attack instead of repeating):**
- A4's quote rule already refuses no bid, bid 0, no size and crossed quotes on both sides (`snapshot.py:48-59`).
- A refused entry writes no fill and no ledger row, so it never counts toward C5's Rs 50,000 new risk per session.
- E6's legging cost stays 0 unless the guard fires.
- The five existing tests that change all become stricter.

**Questions, each answered accept / partial / reject with evidence:**
1. Is "all legs or none, checked in advance" the right rule for a paper book whose purpose is to measure strategies
   honestly, or does it bias results? For example, it hides structures that a real trader would leg into over minutes,
   or it refuses trades a real broker would fill.
2. Bid or ask size below the units at the touch causes a refusal. Real Groww orders can fill across several price
   levels. Is refusing on top-of-book size too strict for NIFTY options of 65 units, and what would you use instead
   with only top-of-book data?
3. No spread-width threshold (owner question 1): agree, or should a width rule come first? With what source?
4. Is anything in E8's later fills at 5, 30 and 60 minutes made inconsistent by this rule? E8 inherits the check at each
   R.
5. Any path left where the public record shows both sides of a quote, or where a refusal hides information the
   scoreboard needs (refusals counted, reasons kept)?

**Write your answer as a new file** `reviews/chatgpt/review_102_e4c-entry-refusal.md` and add its line to
`reviews/chatgpt/README.md`. Never overwrite an existing review file. (Review 101 is reserved for C5.)
