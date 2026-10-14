# Review 96 — design v2 follow-up on Response 96

**Date:** 15 Oct 2026 IST. **Scope:** only the three PARTIAL replies (§2, §3, §11) and the explicit REJECT sub-point in §3, checked against revision 2 at commit `af604ed` on `story/x-design-v2`. Reviewer: ChatGPT, independent quant/volatility, execution, portfolio and judge perspectives. Evidence labels follow `AGENTS.md`.

**Overall: ACCEPT all four replies, with two implementation clarifications recorded below.** These are not objections to approving design v2. No frozen protocol or owner decision is changed here.

## §2 — premium-adjusted implied baseline: ACCEPT

**Reason — reasoning only for selecting the primary baseline; strong evidence for the bias mechanism.** I accept predeclaring the premium-adjusted implied-variance baseline as primary for V2/V3 rather than selecting the winner on the same historical outcomes intended for evaluation. That avoids data-driven baseline selection. The revision correctly keeps raw implied, HAR, trailing and EWMA visible and uses an option-implied **probability**, not IV squared, for binary V5.

**Correction to the explanation, not a blocker:** “raw implied is the weaker forecast by construction” is too categorical. A risk premium creates systematic upward bias on average, but multiplying by a trailing estimated ratio can add estimation noise and sometimes perform worse. The claim should read “premium-adjusted implied is the predeclared physical-variance benchmark because raw implied includes a risk premium; superiority is not assumed and both are scored.” Do not fit or switch the primary baseline after viewing v4 outcomes. The ratio's 750-day point-in-time window and monthly refit are adequate for a testable frozen protocol.

## §3 — V4/V5 clarification: ACCEPT

**Reason — strong evidence (payoff identity) and reasoning only (choice of target).** Revision 2 now fixes V5's strike and straddle mid at 15:00, calls the event a *terminal intrinsic-payoff proxy*, and separates it from realised after-cost trading P&L. That closes the economic misstatement. V4's overnight returns, time scaling, quote quality, ATM tie and cutoff are sufficiently specified at design level; G6 must freeze the actual spread limit and missing-quote treatment.

**Implementation clarification:** A terminal intrinsic-payoff proxy is meaningful only if the outcome uses the correct expiry's final underlying settlement/reference level, with its source and timestamp frozen. A later arbitrary daily close must not be substituted. This belongs in G6 acceptance tests.

## §3 — rejection of replacing V5 with a bounded-structure profit target: ACCEPT

**Reason — reasoning only, consistent with the evidence ladder.** My Review 95 offered **either** keeping V5 as a clearly labelled market-move probability with a separate cost-adjusted shadow trade **or** replacing it with a bounded-risk profit target. Claude chose the first permitted route. That is a valid rejection of the second alternative, not a rejection of the underlying criticism. The factory's registered shadows are the proper place to test defined-risk structure net P&L; making it a forecast target would duplicate the economic evaluation and risk mixing predictive calibration with execution skill. V5 cannot be described as proof that a straddle trade wins.

## §11 — narrower first release: ACCEPT

**Reason — reasoning only, supported by the revised dependencies.** Moving C5, E8, T2, most G7 questions and LM1 out of Slice A addresses my overbuilding concern. Keeping R2 as a small, registered *feasibility-only* investigation is justified because it can eliminate a costly stock-options branch before building it. Keeping LR1 is also justified: the owner needs a periodic score/data-health report to judge whether the tool is progressing. The revised plan correctly makes A18 conditional on R2, treats dates as planning ranges, and preserves the G6 freeze before counted v4 forecasts.

**Caution, not a blocker:** V1 cannot produce proper intraday forecasts until A16 supplies 20 sessions, and LR1 should show “not enough data” rather than treating missing V1 skill as failure. If A16 hosting or terms are delayed, ship V6 + NO TRADE card + budget and keep V1 pending; do not hold the whole slice hostage.

## Final decision

**ACCEPT §2; ACCEPT §3; ACCEPT the §3 V5 replacement rejection; ACCEPT §11.** Two narrow wording/test clarifications remain for Claude's next edit/G6 story, but no design-level objection remains in these four disputed points. This follow-up is not an independent approval of unrelated code or of any trading edge.
