# Response 177: BR1a, the breadth protocol and its freeze gates (story text claims)

Story: `docs/stories/BR-breadth.md`, BR1a, on `story/br1a-protocol`. It builds on response 154 (the design, judge 165
addendum 1 PASS), ChatGPT review 116 (PARTIAL), the orchestrator's answer to it (response 176), and the owner's go
(DESK_DECISIONS, 16 Oct 2026: "Go, with ChatGPT's two fixes"). Lane 1. A judge reviews it, then ChatGPT (rule 9).
No code or study runs before the PASS.

## What the story text claims, and where to check it

| # | Claim | Where | Evidence |
|---|---|---|---|
| 1 | The only confirmatory claim is "family F beats the primary baseline on T1, end of day". The other two baselines are paired, with 95% intervals, labelled descriptive, never "beats all" | items `claim_meaning`, `primary_baseline_rule`; criterion 3 | review 116 Q3; response 176 point 3 |
| 2 | The primary is the lowest mean Brier of `market`, `trail60` and `cal60` over 2019-01-01 to 2025-12-31 (1,736 sessions), recorded before the freeze | item `primary_baseline_rule`; study 1 | judge 165 should-fix 3: no clear winner on 2024-26 (t +1.65, -1.64, +3.31) |
| 3 | No claim rule is frozen before study 3 checks its error rates on BR1's own daily series | study 3; criteria 6-7 | `confirmatory_test` is max(batch-means p, studentized-bootstrap p) (`fno/forecast_v4/confirmatory.py:75-82`), never size-checked on cross-sectional Brier means |
| 4 | Study 3 builds a null from centred real series of each baseline pair (2019-25 and the worst year): 2,000 paths from 63-session circular blocks, the 3 members drawn together, both looks, both signs, Holm, 5-session blocks, at least 12 blocks | study 3 | reasoning: the 63-session blocks keep dependence far beyond the test's 5 |
| 5 | Limits fixed before running: false claim at most 0.025 per look and 0.045 over both; false futility at the minimum effect at most 0.035 | study 3 | reasoning: about 0.0035 SE on 2,000 paths |
| 6 | Fallback fixed now: the rate drops to the first passing value of 0.015, 0.01, 0.005, else claims are postponed. The futility threshold drops likewise, or futility is dropped. Never tuned on post-freeze data | study 3 | review 116 Q4 |
| 7 | The corporate-action screen is outcome-side only (t+1's file); excluded counts and NSE-list disagreements are disclosed; the >50%-kept limit is stated | item `outcome_exclusion`; criterion 4 | judge 165 add. 1: 116 excluded, all 64 remaining large moves real |
| 8 | Spot proxy for 2019-23: the near-month future, checked on the 128 sessions where both formats exist; agreement below 97% makes 2019-23 descriptive only | study 1 | manifests: the overlap runs 2024-01-01 to 2024-07-05 |
| 9 | The worst year (SD and lag-1 of the daily mean, with the AR(1) inflation) sets the look counts; March-April 2020 is reported on its own | item `looks`; study 2 | judge 165 should-fix 6; 2024 is the worst year so far: 2% in 21.5 months |
| 10 | K = 3. T2, direction, the residual target and 14:30 are descriptive | item `confirmatory_family` | judge 165 should-fix 8; review 116 Q5 |
| 11 | BR1's own futility: plain batch-means p_e at most 0.025 at look 1 (`futility_p` with threshold 0.025), or study 3's fixed replacement | item `futility` | judge 165 add. 1 note A |
| 12 | The wording in every BR1 text: the range 6-42; about 9 as the common-tilt planning case only; 2-3% hypothetical; the tilt lost (t -8.06); "unknown whether any forecaster beats the primary by 2-3%" | scope 4; criterion 9 | `results/2024-01-01_2026-10-14.txt` |
| 13 | S1's freezer is made path-generic (`--protocol breadth`), with S1's behaviour and records unchanged | scope 3; criteria 2, 8 | **agreed (16 Oct):** S1's owner (byte-for-byte unchanged, definition passed only through wiring, land before S1's freeze); F9 (`parse_protocol` and `PROTOCOL_FILE` keep their names); order RM1 first, then BR1a, with the real-money gate kept on S1's protocol only; S6's `REQUIRED_ITEMS` line rebased by whichever lands second |

## Gap list

The story's own gap list maps each requirement of review 116, response 176, judge 165 and the owner's go to an item
or a criterion.

## Open before code

- Nothing on coordination: RM1, S1's owner and F9 all agreed (scope 3 of the story). RM1 lands first. BR1's definition
  carries no real-money gate, because a BR1 claim decides no money.
