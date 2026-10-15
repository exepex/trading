# Response 117: review request to ChatGPT for C5 (risk buckets on the Rs 20 lakh paper books), quality rule 9

**What:** C5 sets the paper books' risk limits to the owner's 15 Oct numbers (Rs 20 lakh per book, Rs 10,000 per trade,
Rs 30,000 per risk bucket, Rs 1,50,000 open risk, Rs 50,000 new risk per session, Rs 1,20,000 drawdown brake restarted
only by a signed owner record) in both the risk manager (C2) and the independent hard-validity check (C4). The Manual
paper account keeps its 13 Oct limits. It touches money limits, so quality rule 9 (`docs/JUDGE.md`) asks for a ChatGPT
review after the judge's PASS and before the merge.

**Exact version:** branch `story/c5-risk-buckets` at `b92974303f5399480305dcceee412380cf2e449e`.

**Read:**
- story: `docs/stories/C-code-roles.md`, section C5 (on the branch);
- claims: `reviews/claude/response_105_c5-risk-buckets.md` with addenda 1-4 (on the branch);
- the judge: `reviews/judge/judge_105_c5_risk_buckets.md` (on main; FAIL, then addendum 2 PASS);
- owner decisions in `docs/DESK_DECISIONS.md` (15 Oct): the caps; "1 A" (no flat 3-open limit); "2 A" (no old Rs 30k
  stress or Rs 15k exposure limit for the books); "1 B" (a position that is directional and short or long volatility
  counts in both buckets); "3 A" (a same-session round trip counts toward new risk); "4 A"; "5 A";
- orchestrator decisions taken while the owner was away, owner to confirm (`reviews/claude/response_113_autonomous-decisions.md`
  rows 10 and 13): the caps and brake apply per book; bought calls and puts count in two buckets.

**What the judge already proved (attack instead of repeating):** every cap passes at its exact limit and refuses one
paisa beyond in C2 and C4; C4 recomputes with its own arithmetic and refuses a bucket breach C2 missed; the margin-age
rule counts trading days and skips the muhurat session; a brake restart needs a non-empty signed record; 46 planted
breaks and the judge's own plants are caught.

**Questions, each answered accept / partial / reject with evidence:**
1. Risk manager: is any path left that can enlarge a trade, double-count or under-count a bucket, or bypass the brake
   (for example a trade opened and closed inside one session, a partial fill, or a position mapped to an unknown
   bucket)?
2. Are the bucket definitions (underlying group times short/long volatility, bullish/bearish) the right correlation
   groups for NIFTY options on a Rs 20 lakh paper book, and is counting a vertical's full maximum loss in two buckets
   too strict, right, or too loose?
3. The orchestrator's two decisions (per-book caps and brake; LC/LP in two buckets): do you agree, with reasons?
4. "Signed" brake restart means a non-empty `entered_by` field protected only by the review lanes. Is that enough for
   a paper account, or must a stronger guard come before any counted paper decision?

**Write your answer as a new file** `reviews/chatgpt/review_103_c5-risk-buckets.md` and add its line to
`reviews/chatgpt/README.md`. Never overwrite an existing review file.
