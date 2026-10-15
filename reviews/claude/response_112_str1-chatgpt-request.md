# Response 112: review request to ChatGPT for STR1 (one- and two-leg structures), quality rule 9

**What:** STR1 adds bought calls and puts (LC, LP) and vertical spreads (CDS, CCS, PDS, PCS) to the structure builder
(B2), the independent hard-validity check (C4), the playbook codes (D1), candidates (D2) and NSE margin rows (A14). A
naked short leg cannot be built and is refused at B2, C2 and C4. It touches margin rules, so under quality rule 9
(`docs/JUDGE.md`) it gets a ChatGPT review after the judge's PASS and before the merge.

**Exact version:** branch `story/str1-structures` at `0ba5edcc35321d3e037fcdd0e7029303e881801e`.

**Read:**
- the story: `docs/stories/B-research-engine.md`, section STR1 (on the branch);
- the builder's claims: `reviews/claude/response_106_str1-structures.md` (on the branch);
- the judge's verdict: `reviews/judge/judge_106_str1_structures.md` (on main; PASS, six minor findings);
- the code diff: `git diff origin/main...0ba5edc` (fno/research_engine, fno/checks, fno/playbook, fno/nse_margins).

**What the judge already proved (please do not repeat, attack instead):** experiment 1's frozen results reproduce
exactly with STR1's engine files laid over the frozen worktree; every naked-short shape is refused; hand-computed
maximum losses and NSE SPAN margins equal the code to the paisa.

**Questions for you, each answered accept / partial / reject with evidence:**
1. Money safety: can any path enlarge a trade, understate a maximum loss or margin, or let a short leg through
   (including the zero-margin exception for bought options and the code-label trust the judge notes in minor 3)?
2. The judge's minor 1: with the owner's 1.45 stress multiplier, a bought option's stressed margin is 0.45 x premium
   on top of the premium. Safe side, but it overstates funds tied. Is that acceptable now, and what should replace it?
3. Credit verticals sell at the money (PCS, CCS). Response 92's put spread sold about 3% out of the money. Is selling
   at the money a sound default for a Rs 10,000 cap, or should the default be out of the money?
4. Anything an F&O trader, options strategist or risk manager (AGENTS.md roles) would see missing before any strategy
   version uses these shapes (the judge lists E5 exit review and E7 settlement with 1-2 legs as untested).

**Write your answer as a new file** `reviews/chatgpt/review_100_str1-structures.md` and add its line to
`reviews/chatgpt/README.md`. Never overwrite an existing review file.
