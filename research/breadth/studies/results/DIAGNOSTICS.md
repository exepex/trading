# BR1a study results, and diagnostics of study 3's failure (not part of the frozen procedure)

The three studies ran once, in the story's fixed order, on 2,058 files verified against the archive manifests (1,366
legacy and 692 UDiFF). The results are `study1.json`, `study2.json` and `study3.json`. This file adds diagnostics
run afterwards. They change no result and no rule; they only explain one.

## The pre-registered outcome

1. **Study 1: the spot proxy failed its gate.**
   - Y from the near-month future agreed with Y from `UndrlygPric` on **96.0%** of 23,296 pairs compared, against
     the limit of 97%.
   - So, by the fixed fallback, every study uses **2024-01-01 to 2025-12-31 only**, and 2019-2023 is descriptive.
   - The primary baseline is **`trail60`**: mean Brier 0.1924, against 0.1931 for `cal60` and 0.1941 for `market`.
   - That gives δ = 0.02 x 0.1924 = 0.0038.
   - Excluded by the outcome screen: 45 name-days in 2024, 46 in 2025.
2. **Study 2:** the worst inflated variance is 2024's `market`/`trail60` pair. SD 0.0199, lag-1 0.254.
3. **Study 3: no rate passes, so claims are postponed** (the rule written before the run).

   With the sign as recorded (+d), every rate is within the limits. With the sign flipped (-d), the whole window
   fails at every rate:

   | Rate | Looks | Whole, -d: false claim at look 1 / look 2 / either | Worst year, -d |
   |---|---|---|---|
   | 0.02 | 248 / 495 | 0.092 / 0.082 / 0.136 | 0.042 / 0.032 / 0.061 |
   | 0.015 | 263 / 526 | 0.071 / 0.064 / 0.105 | 0.035 / 0.020 / 0.046 |
   | 0.01 | 285 / 569 | 0.064 / 0.052 / 0.094 | 0.026 / 0.019 / 0.039 |
   | 0.005 | 321 / 642 | 0.052 / 0.033 / 0.071 | 0.022 / 0.011 / 0.028 |

   The limits are 0.025 per look and 0.045 at either look. Futility was not run, because the story runs it only at
   a selected rate.

## Diagnostics: why it fails (some evidence; one 2024-25 window)

- **It is not caused by blocks repeating within a path.** The whole window is 437 days, shorter than the 495-day
  paths. But with 300-day paths, where nothing has to repeat, -d still gives 0.110 at look 1 and 0.085 at look 2 at
  the 0.02 rate.
- **The daily differences are strongly skewed:** skew +1.83 for `market`/`trail60`, +1.58 for `market`/`cal60`, and
  -1.63 for `trail60`/`cal60`. Their extremes are a few crash and event days, when Y = 1 across most names.
- **The over-rejection comes from the two `market` pairs.** Per member, at one-sided rate/3 = 0.0067, with 1,000
  paths of 495 days:

  | Pair | +d | -d |
  |---|---|---|
  | `market`/`trail60` | 0.011 | **0.064** |
  | `market`/`cal60` | 0.027 | **0.088** |
  | `trail60`/`cal60` | 0.002 | 0.000 |

- **What it means (reasoning only):** a few days with huge cross-sectional loss differences decide the mean. The
  5-session batch-means and studentized-bootstrap test does not absorb them. A forecaster that did well on a few
  crash days could be "proven" by luck, which is exactly the false claim this study was built to catch.
- **An earlier, separate check:** on a synthetic Gaussian AR(1) null with lag 0.3, the same test gave 0.030 at
  look 2 (nominal 0.020, SE about 0.004) and false futility 0.035 (nominal 0.025). It is mildly anti-conservative
  even without skew.

## What this does not decide

The written rule postpones claims, and nothing here changes that. A test that stays valid on crash-dominated daily
differences needs a new protocol version, with the owner's decision and a new judge and ChatGPT round. Examples
are a crash-day gate as in v4, a test on per-day ranks, or a test calibrated on this null. ChatGPT review 121 said a
crash-day gate should come only if this study showed a failure. It has.
