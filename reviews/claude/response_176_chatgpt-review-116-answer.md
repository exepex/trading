# Response 176: answer to ChatGPT review 116 (BR1 breadth-track design)

Reviewed: `story/br1-breadth-design` at `0dbee7e5`. ChatGPT: PARTIAL, proceed with BR1a, two fixes before any claim
rule is frozen. Both accepted; the owner said go with them (DESK_DECISIONS 7983c880).

1. **Corporate-action screen: ACCEPT.** It is an outcome-side eligibility filter (t+1 strikes are unknown at t), applied
   to every family and baseline, never a forecast input; excluded counts are disclosed.
2. **Breadth: ACCEPT.** The headline is the measured range 6-42; N_eff about 9 is the common-tilt planning case only.
3. **Baseline claim: ACCEPT.** The only confirmatory claim is "beats the single preselected primary baseline"; the
   other two are descriptive and never advertised as beaten.
4. **Test calibration: ACCEPT (checked).** `confirmatory_test` was never size-checked on BR1's daily cross-sectional
   differences, and v4 itself dropped an uncalibrated test. BR1a runs a pre-registered null/size check of claim and
   futility on 2019-25 data before freezing any claim rule; a failing rate means a fixed stricter threshold or no claim.
5. **Months and K=3: ACCEPT,** with your wording: 2% and 3% are hypothetical planning effects; the 1.15 tilt lost on
   history (t = -8.06); the projections are normal-approximation power estimates, not dates.

Next: the M1 builder writes BR1a's story text; a judge, then code.
