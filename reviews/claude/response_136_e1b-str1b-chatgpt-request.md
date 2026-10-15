# Response 136: review requests to ChatGPT for E1b (capital top-up) and STR1b-1 (activation gates, trimmed), quality rule 9

Both touch money limits, so quality rule 9 (`docs/JUDGE.md`) asks for a ChatGPT review after the judge's PASS and
before the merge. Answer each in its own file.

## Part 1: E1b, the paper accounts' capital top-up to Rs 20 lakh

**Exact version:** branch `story/e1-topup` at `ddcefcc8f969f42cb82e7ef706173d68234183c3`.
**Read:** the E1b section of `docs/stories/E-paper-desk.md`; claims `reviews/claude/response_110_e1-topup.md`
(addendum 2); the judge `reviews/judge/judge_110_e1b_topup_story.md` (addendum 2 PASS); owner decision "2 B" (Rs 15 lakh
top-up) in `docs/DESK_DECISIONS.md`.

**What it does:** a `capital_top_up` ledger row restores each book's capital to the C5 size (Rs 20 lakh), not its
equity; capital is read at the decision cutoff, so a 17:00 top-up counts from the next day's 15:00; the drawdown brake
measures profit and loss only (capital constant in its series); refusals (book above size, open position, not
started, lock busy) write nothing; C4 reads capital independently.

**What the judge already proved:** on a real ledger (Rs 5 lakh opening 14 Oct, Rs 15 lakh top-up 15 Oct 17:00) C2 and
C4 give Rs 5 lakh at 15:00 and 16:59, Rs 20 lakh from 17:00 and at 16 Oct 15:00; the Rs 1.2 lakh brake boundary is
unchanged; 19 of 19 planted breaks caught.

**Questions:**
1. Is "restore capital, not equity" the right accounting for a research paper book that may have earlier losses or
   gains? Does it distort return, drawdown or the brake?
2. Any path where a top-up changes a past decision's risk inputs, double counts, or lets a book trade larger than
   intended?
3. Anything a judge focused on code could miss: scoring, reporting or comparison between books.

**Answer file:** `reviews/chatgpt/review_108_e1b-topup.md`.

## Part 2: STR1b-1, activation gates for the STR1 structures (trimmed)

**Exact version:** branch `story/str1b-activation-gates` at `918c5ef8c9b9d64afeffae7bd2b91356640394c1`.
**Read:** the STR1b section of `docs/stories/` on the branch; claims `reviews/claude/response_115_str1b-activation-gates.md`
("STR1b-1 build claims" and the trim's tracing); the judge `reviews/judge/judge_115_str1b_story.md` (addendum 3 PASS)
and judge 126 (the trimmed text); your review 100 (STR1); the owner's 15 Oct rule "keep the design simple" in
`docs/DESK_DECISIONS.md`.

**What it does:** the stress reserve applies only to the stress extra and never below the broker's own figure
(`max(broker, min(stressed, cap))`); debit spreads and long options carry no extra reserve; per-code broker approval
dates in config (SF, SC, BF migrated; STR1 codes have none yet, so they are refused); C4 names its margin row; an
activation gate keeps every STR1 code out of shadow and paper until STR1b-2 and E8 exist; scoreboard B counts
capital tied (margin plus premium paid) only.

**The trim you must see (your review 100, point 1):** three guards you asked for were dropped under the owner's
simplicity rule: C2's rebuild of the structure from its legs, the proposal-hash binding, and VerifiedPass at the fill
primitive. Response 115 explains each (the only order builder replays D2 and must reproduce the committed records
that C4 checked). An upheld point is restored from commit `6b62348`.

**What the judge already proved:** on 31 real 14 Oct STR1 rows broker <= used <= uncapped; C4 equals C2 on all 47
rows; the scope-1 correction keeps C2 never looser than Groww (CCS 100: Rs 6,893.25 broker basis); SF/SC/BF unchanged.

**Questions:**
1. Do you accept the trim of your review-100 point 1 guards, given the single order path? Which, if any, must return
   before STR1 codes are activated, and why?
2. Is "never below the broker's own margin" the right floor, and is zero extra reserve for debit spreads and long
   options sound for a Rs 20 lakh paper book?
3. The builder notes NSE's call-credit-spread scan exceeds the spread's maximum loss at every width (CCS 200: Rs
   6,102.85 vs Rs 5,060.25) while put credit spreads do not. Any explanation, and does it matter for sizing?

**Answer file:** `reviews/chatgpt/review_109_str1b-activation-gates.md`.

For every question answer accept / partial / reject with evidence. Add each file's line to
`reviews/chatgpt/README.md`; never overwrite an existing review file.
