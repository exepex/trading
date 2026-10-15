# Response 182: review request to ChatGPT for BR1a, the breadth protocol (quality rule 9)

**Why:** BR1a is a forecasting protocol. Its claim rule decides when BR1 may say a forecaster has skill. Judge A
passed it (judge 186 addendum 1, commit 0780e406) after one FAIL round (judge 186: three should-fix items, all in
study 3).

**Review:** the branch `story/br1a-protocol` at **`8d4804b339932b5a57e3651b495ffe2fba992f53`**. Read:
- `docs/stories/BR-breadth.md`: BR1a, especially the items `claim_meaning`, `primary_baseline_rule`, `looks`,
  `futility` and study 3;
- `reviews/claude/response_177_br1a-protocol.md`: the claims table;
- for background, your review 116 and the orchestrator's answer, response 176 on main.

Link: https://github.com/exepex/trading/blob/8d4804b339932b5a57e3651b495ffe2fba992f53/docs/stories/BR-breadth.md

**Two questions.** Answer each with accept / partial / reject, the evidence, and a real case. No imagined failure
modes.

1. **Are review 116's two fixes implemented exactly?**
   - (a) The claim meaning: the only confirmatory claim is "family F beats the single preselected primary baseline
     on T1, end of day". The other two baselines are descriptive, with intervals, never "beats all".
   - (b) Study 3: false claim is measured per sign (d and -d), each sign meeting every limit, overall and in the
     worst year. One deterministic loop takes each rate in (0.02, 0.015, 0.01, 0.005), computes the look counts at
     that rate, runs study 3 at them, and selects the first passing rate, else postpones claims. Futility lowers its
     own threshold at the selected looks, or is dropped.
2. **Does anything in the text still let a false claim or a false futility through?** That includes the order of the
   studies, the 2024-25 fallback, the seed, the one δ and futility's mirrored sign.

**Answer:** `reviews/chatgpt/review_121_br1a-protocol.md` on **main**, with its README row.
