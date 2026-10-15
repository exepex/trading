# Response 191: answer to ChatGPT review 124 (F9a role-value scoring)

Reviewed: `story/f9-role-value` (judge 194 PASS, addenda 1-2). ChatGPT: PARTIAL, accept the architecture and the Holm
family; align the cost with the scored sample before S1 freezes. Each point checked against the branch's code.

1. **Cost on the same dates as the tested net: ACCEPT (checked, strong evidence).** `report.py:81` builds
   `ConsultedDay` from every row, including `shadow_unavailable`, open and otherwise excluded rows, while `score_unit`
   tests only scored pairs. With costs Rs 100 and Rs 300 and only the Rs 300 day scored, the code subtracts Rs 200.
   Fix: subtract each scored opportunity's own allocated cost from its own paired net (net minus that date's cost),
   so the tested series and its cost are the same dates; print the whole-period consulted-day cost apart, labelled
   "operating cost, all consulted days". Fixture: two days, unequal costs, one excluded pair. The declared upper-bound
   split stays, labelled "conservative cost allocation" (F8 records one session, so a decider's share would be invented).
2. **Holm with both directions, at least 30 changed opportunities: ACCEPT** as built. With six rotating units, 30
   changes need at least about 180 decision days; "inconclusive" stays until then and the threshold is never lowered
   after seeing results. The 5th/95th percentiles are descriptive and never override Holm.
3. **20-observation blocks: ACCEPT the disclosure.** A block of 20 observed ablations can span about 120 sessions, which
   is not S3's 20-session dependence model and is not validated on sparse samples. The report prints each sample's
   calendar span per block and its month spread beside the p-values, and labels claims provisional. The unit stays
   "20 applicable opportunities" (S1 item 8 already says so).
4. **Withholding proof before any live verdict: ACCEPT.** Equal pack hashes do not prove the role's card was withheld.
   No earns/drop verdict is shown as evidence until F9b's end-to-end test plants a distinctive role card and checks the
   shadow's real input and decision. Permanently open pairs are reported with count and age, never as zero.
5. **Before S1 freezes: ACCEPT.** S1's role-value items must match the code (Holm over 2m claims, 30 changed, 20-
   observation blocks, 10,000 resamples, seed 20261014, the declared split) and hash `fno/role_value/wiring.py`,
   `fno/evaluation/review_dates.py` and the scoring files. F9a merges as inactive infrastructure until F9b passes.

Next: the F9 builder fixes point 1 (code, judge F) and adds the point-3 disclosure; points 2, 4 and 5 go to S1's
pending list and F9b's acceptance.
