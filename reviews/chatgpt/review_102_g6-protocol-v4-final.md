# Review 102 — G6 protocol v4 final narrow re-review

**Date:** 15 October 2026 IST. **Reviewer:** ChatGPT, independent statistician, quantitative modeller, volatility trader, risk manager and judge perspective. **Reviewed:** `story/g6-protocol-v4` at `a0c191e`, response 99 revisions 6–8, updated `PROTOCOL_v4.md` and supporting regime/VIX studies as reported by Claude. Judge 98 addendum 8 reports PASS. Evidence labels follow AGENTS.md. This is a design/protocol review, not an independent rerun of the large simulations.

## Verdict: APPROVE

**APPROVE the final v4 protocol for the project's normal freeze process.** The sole blocker in Review 101, uncalibrated V7 borrowing V6b's thresholds, is closed by making V7 **descriptive-only** after a VIX-specific null study found no reliable claim/futility rule. Revisions 7–8 then tested regime effects and extended the five-big-days gate to every confirmatory member. I find no new logical error that warrants another revision. This is **not** evidence of profitable options trading or of universal error-rate control in future unseen regimes.

### Revision 6 — V7: ACCEPT (some evidence)

The VIX-specific study compared three candidate rules under both orientations and calm/volatile regimes. Reported false claim/futility rates exceeded their limits; retaining V6b thresholds would be unjustified. The code/protocol now leave V7's three registered slots in the 15-member family at p=1 and **exclude them from Test A**, so they cannot create a YES or force/block a NO. That is the correct fail-closed alternative from Review 101. **Strong evidence:** explicit protocol logic; **some evidence:** reported VIX-null simulation results.

### Revision 7 — regime stress: ACCEPT (some evidence)

Testing both claim and futility against calm and crash windows for V1, V2, V6a and V6b exposed genuine regime-specific problems. The revised study distinguishes the **local true effect** from a false verdict; a high rejection rate is not a type-I error when the local alternative is genuinely true. It also withdraws an incorrect comparison of crash-cut rates across differently selected populations. The requirement to show each scored window's mean VIX, number of 2%-move days and event band is appropriate and independently auditable. These are disclosures, not a claim that calibration works in every possible future regime.

### Revision 8 — five-big-days gate for all questions: ACCEPT (some evidence)

The gate is now applied to **every** confirmatory question, including QLIKE V1/V2. A window with fewer than five NIFTY 2%-move days cannot yield either a claim or futility; it stays **UNDECIDED**. This prevents the identified calm-window false verdicts instead of calling absent evidence failure. The reported full-period results are within measured tolerance, while remaining crash-window exceptions and the limitations of regime selection are disclosed. **Strong evidence:** the logical no-verdict rule; **some evidence:** the simulation sizes and regime results.

### Remaining limitations — accepted, not blockers

- V1, V2 and V6a are effectively unclaimable on a useful timeline under the calibrated thresholds. V6b is conditionally judgeable and V7 descriptive only. That makes a six-month Test A result likely inconclusive; it must not be marketed as a useful three-book ranking.
- A five-big-days threshold is a deliberately selected research eligibility rule. It excludes calm markets; any conclusion applies to **eligible windows**, not all market regimes.
- A single historical crash and calm period cannot establish universal robustness. The disclosed 2020–21 regime exceptions remain relevant, especially for interpreting any future YES/NO.
- The owner/judge must keep the freeze immutable, retain the full 15-member family and the predeclared two looks, and label all unjudgeable members undecided. G7/G8 must use the protocol's exact eligibility and provenance.
- Forecast significance remains separate from registered shadow trading P&L and cannot authorize real orders.

## Final decision

**APPROVE — no further protocol revision requested.** Review 101's V7 blocker is closed and revisions 7–8 address the newly discovered calm-regime error without pretending to eliminate every regime limitation. Proceed to the documented G7/G8/freeze prerequisites and judge verification; do not claim that a forecast has a trading edge merely because its score passes.
