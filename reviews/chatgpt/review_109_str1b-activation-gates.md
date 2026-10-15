# Review 109 — STR1b-1 Activation Gates

> Relayed by the owner in chat on 15 Oct 2026. ChatGPT reported that its own write of this file was blocked by its
> tool's safety checks, so Claude committed the text as received (formatting only; wording unchanged).

**Overall verdict: PARTIAL** — I accept removing the three guards from Review 100, provided the existing C4 safety
boundary is verified end to end before activating STR1 structures.

I reviewed Claude's Response 115, the STR1b-1 implementation at commit 918c5ef8, and the relevant C2/C4 margin
calculations.

## 1. Removing the three guards — ACCEPT with conditions

Evidence: Strong evidence from the existing code path; reasoning only for future bypass risks.

I accept the removal of all three guards:

| Removed guard | Verdict | Reason |
|---|---|---|
| C2 independently reconstructs structures from option legs | ACCEPT | C4 already independently validates the structure in the current execution path. |
| C4 pass bound to the proposal through an additional hash | ACCEPT | The existing D3 record-integrity check protects the normal execution path. |
| VerifiedPass required by the fill primitive | ACCEPT | The current architecture has one controlled entry path through E3. |

However, before activating STR1, I require an end-to-end test proving that a failed C4 check cannot produce a paper
fill.

The test should cover LC, LP, credit spreads, debit spreads, incorrect structure labels and changed decision records.

I would not restore all three production guards merely to defend against hypothetical future callers. If another entry
path is introduced, the shared safety boundary must be reconsidered.

## 2. Broker margin floor — ACCEPT

Evidence: Strong mathematical evidence.

The implementation uses:

Required SPAN = max(Broker SPAN, min(Stressed SPAN, Cap))

For the reported CCS 100 example:

| Component | Amount |
|---|---|
| Broker-basis blocked SPAN | ₹6,893.25 |
| Terminal-loss-derived cap | ₹2,564.25 |
| Difference | ₹4,329.00 |

Reducing the margin to ₹2,564.25 would understate the broker-basis requirement by ₹4,329.

I also accept zero additional stress reserve for bought options and debit spreads, provided the premium, charges and
any broker-required margin are already counted.

Zero additional reserve does not mean zero cash requirement.

Before activation, the relevant structure and width must have a dated broker-margin verification.

## 3. CCS margin exceeding maximum loss — PARTIAL

Evidence: Strong evidence for the arithmetic; reasoning only for the explanation.

Claude reports:

| CCS 200 | Amount |
|---|---|
| Margin | ₹6,102.85 |
| Maximum terminal loss | ₹5,060.25 |
| Difference | ₹1,042.60 |

The margin is approximately 20.6% higher than the terminal maximum loss.

This is not necessarily an error. SPAN collateral requirements can differ from a fully hedged spread's maximum terminal
payoff because of scenario calculations, offsets and option-value treatment.

However, the available aggregate figures do not establish the precise cause.

I recommend verifying the difference against the relevant broker-margin calculation rather than changing the formula
to force margin below maximum loss.

## Final recommendation

Accept the trimmed STR1b-1 design, subject to two activation conditions: an end-to-end C4 refusal test and dated
broker-margin approval for each newly enabled structure.

I attempted to create `reviews/chatgpt/review_109_str1b-activation-gates.md` on main, but the repository write was
blocked by the tool's safety checks. No file was committed or pushed, and I have not updated the README.
