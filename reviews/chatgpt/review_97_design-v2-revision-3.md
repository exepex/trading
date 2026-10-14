# Review 97 — design v2 revision 3 (commit 6367d73)

**Date:** 15 October 2026 IST. **Reviewer:** ChatGPT, independent second reviewer (statistics, volatility, execution, risk, portfolio, accounting, engineering, red team and judge). **Scope:** Claude response 97 and revision-3 `docs/design_v2/` files on `story/x-design-v2`. Earlier reviews 95 and 96 remain unchanged. Evidence labels follow AGENTS.md.

## Overall verdict: CHANGES REQUIRED

Revision 3 resolves the original four contradictions **in principle**. I accept B1 (three timestamps), B3 (QLIKE ranking loss at zero), and B4 (registered forward exploratory shadows). B2's statistical correction is correct, but is still written as **awaiting owner approval**, while the contradictory decided rule remains present. Two additional precision defects remain in the confirmatory test contract. This is a specification review, not an independent backtest or a judge PASS.

## Original blockers

1. **B1 — ACCEPT (strong evidence).** `04` and `07` now distinguish the 15:00 market-data cutoff, decision finalization and 15:08 card delivery. Advocate timeout is recorded without inventing an objection. The G6/S1 tests must enforce no post-cutoff inputs and the ordering.
2. **B2 — CHANGE (strong evidence).** The proposed `08` §8.2 correction is mathematically right: zero eligible shadows cannot imply futility. But the document retains a decided Test B definition that says “no idea reached rung 2” => NO, followed by a contradictory proposed replacement awaiting the owner. **Exact remaining change:** obtain the owner's explicit approval of the corrected decision 7, then publish exactly one operative Test B rule: zero eligible/resolved trials = UNDECIDED/no_economic_test; NO requires every eligible registered comparison to meet its predeclared sample and have an upper confidence bound below its useful effect. Until approval, mark Test B's stop decision **not executable**; do not implement the incorrect older rule.
3. **B3 — ACCEPT with exact protocol clarification (strong mathematical evidence).** `log(f)+RV/f` for f>0 is defined at RV=0 and paired differences agree with textbook QLIKE when RV>0. Historical RV need not be altered. However, the registered **3% relative minimum effect** uses baseline mean textbook QLIKE on **RV>0** days while the primary paired loss difference includes **all** scored days. That mixes populations. **Exact remaining change:** compute both the paired effect and its 3% benchmark on the **same RV>0 paired dates** for the minimum-effect gate, while retaining all dates (including zeros) for the primary significance test; report the excluded-zero count. Alternatively define an absolute effect threshold in invariant loss-difference units with the owner's approval. Freeze the choice in G6 before results. Do not present the relative 3% as scale-invariant across scoring forms.
4. **B4 — ACCEPT with one multiple-testing fix (strong statistical reasoning).** Registered, cost-screened exploratory shadows can collect forward evidence without becoming paper-eligible. Keeping stopped/retired trials in the family is correct. But `03` §3.1 says a shadow's family is every shadow registered on the question/batch **since its last judgement**. Resetting the family at each judgement lets sequential submissions create repeated chances to pass at nominal 5%. **Exact remaining change:** use a **cumulative family per registered research question**, including all shadows ever registered on that question, whether active, stopped, retired, already judged or newly added. Recompute the Holm family with cumulative membership for every new confirmatory decision; prior published verdicts remain historically recorded, and a later result cannot be called an independent fresh 5% family. If the owner prefers batch-only, pre-register a closed batch and judge all its members together exactly once; no overlapping batches on the same question without a separately registered alpha-spending rule. **My recommendation is cumulative**, because shadows arrive on different dates. A cumulative Holm recalculation alone does not control optional repeated looks; freeze a single decision horizon per hypothesis or a formal alpha-spending/anytime-valid rule. No unplanned re-judging on every attractive interim result.

## Three PARTIAL replies

- **§03 benchmark headline — ACCEPT (reasoning only).** Per rupee-day of capital tied may headline strategy capital efficiency if the denominator, benchmark dates and idle-cash accounting are frozen before S2. The whole Rs20 lakh account including idle cash must remain equally visible and cannot be omitted from owner-facing decisions. The document explicitly requires a single rupee-day convention before S2; that is acceptable as a downstream contract, not permission to change it after results.
- **§04 rung-3 TRADE card — ACCEPT (strong evidence on meaning).** A negative early lower bound does not invalidate a strategy already approved for a *paper experiment*. A `TRADE` card must clearly say **paper only**, not real-money eligible, and must never instruct the owner to execute real orders. Anything below rung 3 remains WATCH. The revised text's real-money-ineligible label closes the original objection.
- **§08 real-money gate tightening — CHANGE / OWNER DECISION REQUIRED (strong evidence).** The proposed second untouched forward evaluation or multiplicity adjustment, paired real-vs-paper comparison and cap feasibility are appropriate. But they explicitly alter accepted owner decision 8 and remain unapproved. Keep the old gate authoritative until owner approval; **do not claim revision 3 approved the new gate**. Before any RM1 freeze or real-money recommendation, present the owner with a single exact amended gate and secure a recorded decision. The current proposal is not a blocker to research-only Slice A, but is a blocker to declaring the entire future real-money gate finalized.

## Remaining file-level review

**01/02 — ACCEPT (some evidence/reasoning only).** “Two studies on related data,” 26 snapshots/25 returns, missing interval handling and point-in-time source availability are more accurate. Quotes should remain labelled proxy observations, not executable trade evidence.

**03 — CHANGE only the family rule above (strong statistical reasoning).** Cost wall remains a feasibility screen; screened-out ideas stay in the ledger; R=60 next-session fills and correlated reaction-time variants are honestly represented. Whole-account and per-capital views are both needed.

**04 — ACCEPT (reasoning only).** Timing, `NO TRADE`, paper-only eligibility and the distinction between compatible-with-odds and proved luck are corrected. Hard data/risk checks still block.

**05 — CHANGE only the minimum-effect population mismatch above (strong evidence).** The zero-safe ranking loss is correct. The predeclared premium-adjusted implied baseline is a defensible choice, not guaranteed superior. V4's dimensional golden and V5's settlement reference must be judge-tested in G6.

**06/07 — ACCEPT (reasoning only).** Four loss notions, margin freshness, silent-monitor policy, independent advocate provenance and a forward-only house-forecast evaluation are appropriately described. These are still proposed behavior, not demonstrated safety.

**08 — CHANGE pending owner decisions 7 and 8 (strong evidence).** The statistical stop rule must not call an empty shadow set a failure. Real-money promotion cannot be silently tightened or implemented under two conflicting texts.

**09 / OWNER_SUMMARY / README — ACCEPT (some evidence).** Limitations and uncertainty are better scoped. Exact regulatory/tax figures remain subject to source and deployment verification.

**REPLAN / REPLAN_new_stories — ACCEPT with G6/S1 dependencies (reasoning only).** Slice A is focused; R2 remains feasibility-only; G6 must freeze before scored v4 forecasts; E8 is separately an owner decision; early shadows must not be promoted on exploratory evidence.

## Decision and next actions

**CHANGES REQUIRED — four narrow closure items:**
1. Owner approval and single operative wording for decision 7 / Test B zero-shadow case.
2. G6 minimum-effect test must use a consistent paired-date population (or owner-approved invariant alternative).
3. Replace the resettable `since last judgement` shadow family with cumulative-per-question membership and a fixed judgement horizon (or closed, one-time pre-registered batches).
4. Owner approval of decision 8's tightened real-money gate before RM1 freeze or any claim that it is binding.

No redesign of the eight layers is needed. I would approve the research architecture after (1)–(3) are resolved, while (4) may remain an explicit owner-gated future milestone provided the design does not present the proposed gate as decided. Nothing here authorizes real orders.
