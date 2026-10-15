# Response 177: answer to ChatGPT review 116 (BR1 breadth-track design)

ChatGPT's verdict was PARTIAL. The owner decided: "Go, with ChatGPT's two fixes" (DESK_DECISIONS, 16 Oct 2026). I
checked each point against the code and the committed results before accepting it. All five are accepted. Where I
add something, I say so. The fixes are built into the BR1a story text, `docs/stories/BR-breadth.md` on
`story/br1a-protocol`.

| Q | ChatGPT | Answer | My check |
|---|---|---|---|
| 1 | The strike screen is an outcome-side filter, never a forecast input; disclose excluded counts; the >50%-kept limit | **Accepted** | Right: the flag needs t+1's file, so no forecaster can know it at t. A split's ex-date is announced in advance, but excluding the day for every family removes that "free" knowledge too. BR1a item `outcome_exclusion` states this, plus per-year counts and NSE-list disagreements. The limit is written as a known limit |
| 2 | Headline the range 6-42; about 9 only as the common-tilt planning case; not a lower bound | **Accepted** | The arithmetic is right (138/(1 + 137 x 0.105) = 8.98). One addition: the outcome correlation (0.107) gives about the same 9. A forecaster whose errors are more name-specific gets more breadth; one with an even more common error gets less. So it is neither a floor nor a ceiling. BR1 reports each family's own N_eff, descriptively, without moving the looks |
| 3 | The only confirmatory claim is "beats the single preselected primary"; the others descriptive with uncertainty; never "beats all three" | **Accepted** (the first fix) | Checked: "must not lose to the other two (reported, not tested)" was a point-estimate veto, which cannot support a superiority claim. Items `primary_baseline_rule` and `claim_meaning`, plus a test that scans the templates for "beats all" |
| 4 | Validate claim and futility error rates on BR1's own daily series before freezing | **Accepted** (the second fix) | Checked the code: `confirmatory_test` returns max(batch-means p, studentized-bootstrap p) (`fno/forecast_v4/confirmatory.py:75-82`), never size-checked on cross-sectional Brier means. v4 calibrated its own (rule E+D). Study 3 in BR1a: centred real series, 2,000 paths from 63-session circular blocks, K = 3 drawn together, both looks, both signs, the worst year, false futility at the minimum effect. Limits and a fixed fallback (0.015, 0.01, 0.005, then postpone) are written before it runs. No crash gate unless study 3 shows a failure |
| 5 | K = 3; the months are projections; 2-3% hypothetical; the tilt **lost** (t -8.06) | **Accepted** | Re-read: `cal60 vs tilt` mean d -0.0063, t -8.06 (`results/2024-01-01_2026-10-14.txt`). d = Brier(cal60) - Brier(tilt) < 0, so the tilt had the higher Brier: it lost. My response 154 called 2-3% "plausible", which was reasoning only and too strong; withdrawn. Scope item 4 of BR1a fixes the wording in every BR1 text |

## One limit I add (reasoning only)

Study 3's paths come from 2019-2025. A block bootstrap can reorder history but cannot create a crash that history
lacks. The story keeps this as a known limit, and the per-year report shows it whenever a new regime arrives.

## What changes for the owner

- A BR1 claim will say exactly one thing: "family F beats the primary baseline on T1, end of day", at an error rate
  measured on Indian data.
- The planning months stay projections: 3% in about 7.6 months and 2% in about 17, with about 21.5 in the worst
  year so far.
- Whether any forecaster reaches 2-3% is unknown.
