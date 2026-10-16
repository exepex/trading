# R1b re-screen: the three hand-registered cards by code (16 Oct 2026)

Story R1b (`docs/stories/R-factory.md`): the cards screened by hand before R1's code are re-screened by `python -m fno
factory screen`, and each code result is compared with its hand screen. A difference is reported here and never
replaces the hand record silently. Gate log: `research/factory/gates.csv`.

| Card | Trial | Hand screen | Code (R1b) | Same? |
|---|---|---|---|---|
| R2 stock options around results | 53 | `screened_out`: "NO, stopped at stage 3 (cost wall)"; no structure has mean and median EN > 0 at the 5% assumed hurdle (`research/2026-10-15-r2-stock-options-results/results.md`) | G1 `screened_out`, "no stated edge"; label `assumed hurdle` (row `reason=no_stated_edge;assumed_hurdle=yes`) | Same outcome. The reason differs, and the code's is the rule's: an assumed hurdle is never a conservative bound, so the idea stops before any cost is computed (FACTORY_RULES section 2, judge 97). The study's EN figures at the hurdle stay its own feasibility result, not a G1 screen |
| FT1 fill timing | 54 | "Not applicable (measurement, no trade)" | Refused: "a measurement is never screened"; last gate stays G0 `idea` | Same |
| B0 monthly short condor | 55 | "Not applied: a measurement is labelled `measurement`, never screened as a candidate" | Refused: "a measurement is never screened"; last gate stays G0 `idea` | Same |

**The worked example (criterion 4), by the same code** (`tests/factory/test_cost_wall.py`; response 92 l.39-40):

| Period | n | Mean gross | SD | Cost | t (90%, n - 1) | Bound | Net on the bound | Net on the mean | Gross / cost | Code |
|---|---|---|---|---|---|---|---|---|---|---|
| 2024-26 | 33 | +978 | 2,667 | 824 | 1.3086 | +370.5 | -453.5 | +154 | 1.19 | `screened_out`, thin margin |
| 2019-23 | 57 | +408 | 3,403 | 814 | 1.2969 | -176.5 | -990.5 | -406 | 0.50 | `screened_out`, thin margin |

Strong evidence for the arithmetic (code and test), some evidence for the inputs (experiment 1's recorded results).
