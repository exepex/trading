# Review 127 — G11 AI books on protocol v4

**Reviewed:** G11 story on `story/g11-ai-books-v4`, Response 206, Response 202 addenda, v4 protocol and G10 timing, F1/G5 capture contracts. **Second reviewer:** ChatGPT under quality rule 9. **Verdict: AGREE with the basic story; CHANGE one audit-freeze timing detail before code.** Confidence: strong evidence for documented contracts, some evidence for the two actual late/missing AI days, reasoning only for projected runtime. Judge 206's PASS is reported, not independently reproduced. This is a story-text review, no AI-trading approval.

## 1. System fault versus slot fault — AGREE (strong evidence)

A common pack that is unavailable or `system_late` prevents every forecaster from answering the same question and should be excluded symmetrically. An expired AI secret, trigger failure, workflow token that fails to launch a job or BG1 budget stop affects only that AI slot: counting it as a **miss** correctly measures operational ability to produce a forecast by 15:10. This is not a statistical claim that the model's forecast was inaccurate; G8 must distinguish `undecided, operations` from `no forecasting skill`. The real workflow risk is already named: a push made with an Actions run's own token does not trigger the downstream workflow. Add a live dry-run fixture before counting; do not invent a new “external outage” exemption.

## 2. Transcript breach — AGREE (strong evidence)

A breached forecast has no eligible value and counts as a miss under the 10% overall and big-move-day caps. It must also enter the separate **two breaches in 20 days** stop rule. Excluding it from the miss denominator would make a dishonest or non-isolated run improve its own apparent reliability. One event can legitimately affect both operational coverage and breach-stop status; it is not counted as two separate forecast days. No additional scoring exclusion is needed.

**CHANGE one audit boundary (strong evidence from the immutable-row contract):** G11 says the `open_audits.csv` row enters in the same commit as a collected submission, and the G8 look refuses while rows are open. But if a submission is never collected, there may be **no audit row** and also no forecast row. At a confirmatory look, G8 must distinguish a settled `no_submission`/ `not_fired` miss from a **submitted but uncollected/unsettled audit**. The open-audit file alone cannot prove there are no uncollected submissions. The simplest condition is to reconcile each scheduled slot/question/day with its fire/collect outcome before recording a look; any unsettled outcome refuses the look, while a definitive no-submission becomes a miss. Test a day with a sealed commitment but no collected reveal: look must refuse, not permanently freeze a provisional miss. This can change a confirmatory verdict and uses existing outcome records rather than a new service.

## 3. Young record and 10% cap — AGREE (some evidence for actual early failures; reasoning only for operating policy)

The 14 Oct `no_submission` and 15 Oct roughly **12-second late** v2 results demonstrate that lateness is not hypothetical. v4's 30–38 minute window is materially larger, but there is no evidence it will succeed. A prospective `effective_start` before the first eligible session is the right fairness rule; a dry run **before** registration can be used for readiness, but once the slot starts, misses count immediately. At 1 miss in 5 days the miss share is 20%; at 1 in 10 it is 10%. Early `undecided, operations` is a truthful provisional label, not permanent disqualification: the ratio can improve with subsequent successes. Do not reset the start after seeing misses.

## 4. Hybrid sees rules' numbers — AGREE with explicit claim scope (strong evidence)

Book 2 is intentionally a **hybrid**, so seeing the rules forecast is an input feature, not leakage, provided the rules value is from the same released pack, timestamped before the deadline and not a future outcome. Its errors will be correlated with rules; v4's paired day-level differences already preserve that dependence. The proper claim is “hybrid improves on its frozen baseline,” **not** “independent AI discovered the same skill without rules.” Book 3's no-rules pointer remains a useful independent comparison. Do not treat Book 2 and rules as independent observations when estimating family-level sample size.

## 5. Cost and runtime — AGREE conditionally (some evidence)

The single observed 15 Oct run took about five minutes per book; **two books × 5–10 minutes = 10–20 book-minutes per session** is an estimate, not a measurement. Later V1–V5 prompts may be longer. The v4 deadline and BG1's existing monthly 50% minutes cap, 80% alert and 100% stop are sufficient; a second G11 runtime cap adds complexity and could bias misses. Log actual elapsed/model minutes from day one and report p50/p95 runtime by question set; if runtime exceeds the available 14:40–15:10 window, the run is late and counted as such. Reassess prompt scope only after observed lateness.

## Role challenge and final decision

**Mathematician/statistician/quant modeller:** same-day paired comparisons are appropriate; missingness and post-hoc registration are the main inference risks. **F&O/options/volatility trader:** a forecast Brier/QLIKE advantage is not a tradable after-cost edge. **Risk/portfolio/head of desk:** operational misses and isolation breaches must not be turned into successful forecasts or paper trades. **Market/macro/flows/equity/investment banking:** common news/regime exposure correlates forecasters; hybrid is not an independent model. **Execution/microstructure:** 15:10 GitHub receipt is a forecast deadline, not a market fill. **Regulation:** paper only. **Behavioural:** don't reset a poor early record. **Tax/cost accounting:** BG1 minutes are budget, not evidence of net profit. **Data engineer/red team:** plant a commitment with missing collect/audit record, wrong pack hash and Actions-token non-trigger.

**Final verdict: CHANGE one pre-look reconciliation contract, otherwise AGREE.** No new scheduler, cost cap or alternate protocol is justified. No real-order capability is authorized.
