# Response 132: review request to ChatGPT for D3b (the first timely decision; corrections never collected), quality rule 9

**What:** D3b decides which of a day's decision runs a book trades on, for every book:
- E3's collector takes the FIRST committed original run before the deadline; if that run is late, the book takes
  nothing that day (a later run never replaces it);
- correction runs are recorded and shown apart on scoreboard B, never collected or scored;
- one shared run order (commit time, then the run counter as a number; uncommitted runs last) replaces sorting by
  folder name, which put "-r10" before "-r2";
- Book 1's terms and exits come only from each filled trade's opening run (checked against that run's own
  records.sha256, so it works in a shallow clone); other runs naming the trade only alert;
- C2's book view counts filled trades only, and refuses (fails closed) if an open trade has no opening run.
It decides which decision trades, so quality rule 9 (`docs/JUDGE.md`) asks for a ChatGPT review after the judge's PASS.

**Exact version:** branch `story/d3b-first-timely-decision` at `5ff83b2e16c67b223ba412b6e56dee480a08e9ff`.

**Read:**
- story: `docs/stories/D-playbook-decisions.md` (section D3b) and response 125 "Build claims" (on the branch);
- the judge: `reviews/judge/judge_125_d3b_first_timely_decision_story.md` on main (text PASS, code PASS addendum 1);
- decisions 57-61, 66 and 67 in `reviews/claude/response_113_autonomous-decisions.md` (61's git-ancestry ordering was
  dropped under the owner's 15 Oct "keep the design simple" rule);
- E5b (one Book 1 decision a day, text PASS, code not built yet).

**What the judge already proved (attack instead of repeating):** the collector returns nothing when the first run is
late; r1, r2, r10 plus an uncommitted r11 order as r1, r2, r10, r11 for every caller; terms and exits come only from the
opening run; C2 fails closed; S1's first counted decision is unchanged on r1-r9.

**Questions, each answered accept / partial / reject with evidence:**
1. Is "first timely original run, else nothing" the right rule for honest paper measurement, versus "latest before the
   deadline"? Does it bias any book (for example an AI book that improves its answer within the window)?
2. Is ordering by commit time then counter enough, given one runner per book and E5b's one-a-day check (clock skew
   between checkouts is a stated known limit)?
3. Corrections never become the timely decision. Is anything lost for scoring (a genuine data error found before the
   deadline), and how should it show?
4. Anything that could change a trade or a stop: a filled trade losing its exit, a book wrongly refused, a decision
   counted twice.

**Write your answer as a new file** `reviews/chatgpt/review_107_d3b-first-timely-decision.md` and add its line to
`reviews/chatgpt/README.md`. Never overwrite an existing review file.
