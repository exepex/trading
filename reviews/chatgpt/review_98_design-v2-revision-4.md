# Review 98 — design v2 revision 4

**Date:** 15 Oct 2026 IST. **Reviewer:** ChatGPT, independent second reviewer (statistics, options, risk, execution, portfolio, accounting, red team and judge). **Repository:** exepex/trading, `story/x-design-v2`, reviewed at `956a805`. Read Response 97's Revision 4 table and checked the changed source text in `03`, `04`, `05`, `08` and README against Review 97 and the earlier full design review. Evidence labels: **strong evidence** for directly verified text/mathematics, **reasoning only** for design recommendations.

## Verdict: APPROVE

**APPROVE the whole design v2 architecture and revision-4 rule documents for proceeding through the repository's normal owner/judge process.** All four closure items from Review 97 are addressed. This is approval of the **design**, not of future implementation, a frozen G6/S1 protocol, profitability, or real trading. No owner decision is reopened.

## Review 97 closure, item by item

1. **Decision 7 / Test B: ACCEPT — strong evidence.** `08_budget_and_stop_rules.md` §8.2 now contains a single operative owner-amended rule: zero eligible/resolved shadows is `undecided/no_economic_test`, never statistical futility; NO requires each counted strategy to reach its registered sample and its upper confidence bound to be below minimum useful net. The contradictory “no idea reached rung 2 => NO” rule is gone. Non-statistical stopping for budget remains a separate owner choice.

2. **QLIKE minimum-effect population: ACCEPT — strong mathematical evidence.** `05_volatility_research.md` §5.5 now calculates both the paired mean and the 3% textbook-QLIKE baseline on the **same paired RV>0 dates**. The primary significance comparison still uses all scored dates including zero RV, and the excluded-zero count is reported. The owner confirmed the 3% unit; G6 must freeze and test both date sets. This closes the population mismatch without modifying observed RV.

3. **Cumulative shadow family: ACCEPT — strong statistical reasoning.** `03_layers_factory_desk.md` §3.1 includes every shadow ever registered on the same research question, including stopped, retired and already judged ideas. One judgement per hypothesis occurs at its predeclared sample; interim looks require a registered alpha-spending rule. Prior verdicts remain historically recorded. This is the appropriate choice for asynchronously arriving forward shadows and closes the “reset to a fresh 5% family” flaw. **Implementation note:** the cumulative Holm calculation must use a well-defined p-value for unfinished/never-tested hypotheses (e.g. conservatively p=1), and the report must state the family membership and decision timestamp; do not repeatedly claim fresh family-wise 5% guarantees for a stream of new decisions without an explicit sequential error-control contract. This is a G6/R1 acceptance-test detail, not a reason to reject the high-level design.

4. **Decision 8 / real-money gate: ACCEPT — strong evidence.** `08` §§8.3–8.4 now incorporate the owner's amended selection-adjusted gate: second untouched forward period or multiplicity correction, cap-fit and current regulatory/tax re-check, and paired real-vs-paper test with prediction interval and drawdown stop. Exact sample, paired statistic, interval construction and execution constraints still belong in RM1's frozen specification **before counted paper evidence**. The owner remains responsible for any actual order; this tool never places one.

5. **PAPER ONLY: ACCEPT — strong evidence.** `04_layers_card_monitor_learning.md` §4.1 explicitly labels every card PAPER ONLY and distinguishes a rung-3 paper experiment from real-money eligibility. A negative interim paper confidence bound can be shown honestly without relabelling an approved paper experiment as WATCH. Earlier-stage ideas remain WATCH.

## Remaining implementation caveats (not design objections)

- **G6 scoring:** freeze exact QLIKE units, baseline family, one-sided block-bootstrap/HAC sensitivity, V4 dimension fixture, V5 settlement source, and missing/zero observations before v4 forecasts count.
- **R1/S1:** implement cumulative family accounting and single decision horizons; preserve append-only registrations and avoid treating interim exploratory shadows as confirmatory paper evidence.
- **E8/S1:** owner-timing fills at the conservative 60-minute reaction case, no synthetic fills, immutable fill-model version; the owner must decide whether E8 joins S1 frozen_files or is separately bound.
- **A16/T1/LM1:** verify source rights, quote timestamps, secrets isolation, session clock, card issuance, outage/owner-unavailable fallback and PAPER ONLY labels in acceptance tests.
- **RM1:** freeze the amended real-money gate and paired-test protocol before paper outcomes can influence thresholds. This review does not authorize or recommend real orders.

## Final decision

**APPROVE** design v2 revision 4. The four Review 97 closure points and the card labelling are addressed in the documents at the reviewed commit. The judge and owner still control the lane-1 approval/merge, and each new implementation story must meet its own tests. No proven trading edge is claimed.
