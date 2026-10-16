# Judge 239: dashboard contract 2.12.0, the Forecast lab follows G1's protocol section 8

Dashboard `story/fno-contract-2-12` at 7edaf78 (screens lead 01XFXpbkyixX7SuXeQCp5EnX; 563953f, plus a merge of main
e425aea, plus 7edaf78). Lane 1 (contract). Judge D, 16 Oct 2026.

**PASS.**

| Claim | Result | Evidence |
|---|---|---|
| Basis | MET | `research/forecasts/PROTOCOL.md` section 8 (strong evidence). The primary family is 10 tests, Book 2 and Book 3 against Book 1. A book against a baseline is secondary, effect sizes only, "never called confirmatory". No comparison is significant before the first review: design 12.8, 6 months of common-start trading, so not before about mid-April 2027. |
| 1. Schema text only | MET | Only three descriptions change: `primary_baseline` (v3: book1_rules; v4: the predeclared baseline), `comparisons` (registered, primary tests only) and settle `not_measured` (adds "or no measurement built yet", which is true today). There is no shape change. |
| 2. Lab examples | MET | My read of the examples: v3 Q1 and Q4 have `primary_baseline` book1_rules, and their comparisons are book2_hybrid and book3_ai against book1_rules only. The "better" (Q1, p 0.004, which passes Holm's first step of 0.005) and "worse" (Q4, p 0.001) cases are dated 2027-06-16, after the first review. The empty case is 2026-11-30 with `not_tested`. v4 rows keep their predeclared baselines. |
| 3. History examples | MET | Live series start at a question's first possible answer: Q1 2026-11-11 (20 sessions after 14 Oct) and Q4 2026-10-28 (10 sessions). There are no live points before the 14 Oct start. |
| 4-5. Mockup 37; the one test change | MET | The W3b test change only moves the pinned Q1 answer date to the new example ("14 Jul 2027", made 16 Jun 2027). It is the same assertion and is not weakened. Every other W3b test passes unchanged. |
| 7edaf78 | MET | Mockup 39's lede becomes "after the day's decisions are final", the same as the W3f screen (judge 234). Only the lede and its screenshots change. |
| 6. Version 2.12.0 and gates | MET | There is a version note. `check_contract`, `check_fno_screens`, `examples` and `render_catalog` exit 0, `sync-design` is clean, and `npm test` gives 529/529. A trial merge with w3-cap-bars (0971581) gives 571/571. |

**Note:** the waiting example's Q1 shows only Book 3 against Book 1. Under section 8, a comparison not yet possible
stays in the family with p = 1, so a real page should list both registered comparisons, the impossible one as
`not_tested`. P2b's builder should follow section 8, not this Mock row.
