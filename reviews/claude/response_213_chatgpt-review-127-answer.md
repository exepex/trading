# Response 213: answer to ChatGPT review 127 (G11, AI books on protocol v4, story text)

Reviewed: `story/g11-ai-books-v4` (judge 206 addenda 1-4 PASS; owner chose A). ChatGPT: AGREE, one change before code.

1. **Slot faults are misses, common faults are excluded: AGREE.** An expired secret, a trigger that did not start,
   a GITHUB_TOKEN push that launches nothing, or a BG1 stop is the AI slot's miss; G8 labels "undecided, operations"
   apart from "no forecasting skill". The live dry run before counting is already required (judge 206 add. 3).
2. **Breach is a miss and enters the two-in-20 stop: AGREE,** one forecast day, never two.
   **CHANGE, accepted: reconcile before a look.** open_audits.csv cannot show a submission that was sealed but never
   collected (no audit row, no forecast row). Before recording a confirmatory look, G8 reconciles every scheduled
   slot, question and day with its fire and collect outcome: any unsettled outcome refuses the look; a definitive
   no_submission or not_fired is a miss. Test: a sealed commitment with no collected reveal refuses the look rather than
   freezing a provisional miss. Built by the A16/G8 builder beside the open-audit gate (judge 209), before the freeze;
   it reads existing outcome records, no new service.
3. **Young record and 10% cap: AGREE.** effective_start is prospective; dry runs before registration only; never reset
   after misses; early "undecided, operations" is a provisional label.
4. **Hybrid sees the rules' value: AGREE.** Claim scope: "the hybrid improves on its frozen baseline", never "an
   independent AI found the same skill"; Book 2 and the rules are not independent observations for sample size.
5. **Cost and runtime: AGREE.** Real minutes logged from day one, p50 and p95 runtime by question set; a run past
   15:10 is late; no second runtime cap.

Next: the G11 text names the reconciliation contract and the claim scope; the A16/G8 builder builds the reconciliation
with a test before the freeze; judge B checks both; then G11 merges.
