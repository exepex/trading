# Response 198: three candidate tests for a BR1 protocol v2, measured on study 3's null (exploratory)

Builder: session 013xqaNTCbSBytKgqpfaYFqZ, branch `story/br1a-protocol`. Asked by the orchestrator after the owner
chose "compare all 3 first". **Exploratory, one window (2024-2025), no freeze.** Nothing here changes protocol v1, whose
claims stay postponed. The results inform the owner's choice of a v2, which needs its own story text, judge and ChatGPT
round.

## Part 1: pre-declaration (committed before any run)

### Inputs

- **Daily series:** study 3's three registered-baseline pairs (`market`/`trail60`, `market`/`cal60`,
  `trail60`/`cal60`), their daily mean Brier differences on 2024-01-01 to 2025-12-31 (437 sessions), v4's sign.
- **Paths:** study 3's circular block bootstrap. Its seed words are (20261016, population), it uses 63-session blocks,
  and every member and the primary's loss get the same block starts. There are 2,000 null paths per population. The
  power runs use the first 1,000 of the same paths.
- **Populations:** the whole window, and the worst year (2024). For candidate C, also 2025 alone, as the hold-out.
- **NIFTY 2% days:** a session is a 2% day when |ln(NIFTY(t+1) / NIFTY(t))| is at least 0.02, from the panel's NIFTY
  spot, the same outcome day as d_t. The indicator travels with its day through the bootstrap index.
- **δ:** 0.0038481856, study 1's 0.02 x the primary's mean Brier, the one δ everywhere.

### The candidates

- **A, the v4 crash gate, as frozen in `fno/forecast_v4/confirmatory.py`.** At each look, a member's window is
  judgeable only when it holds at least 5 NIFTY 2% days (`judgeable`) and not more than 10% of its sessions are 2%
  days (`crash_dominated`). A window that is not judgeable gives no claim. Otherwise the test is the frozen
  `confirmatory_test(d, 5, k)` with Holm at the rate. A runs study 3's single loop over the rates (0.02, 0.015, 0.01,
  0.005), each with that rate's look counts. The share of paths judgeable at each look is reported as A's cost.
- **B, rank-based: the daily sign test.** The series tested is s_t = sign(d_t), with the frozen
  `confirmatory_test(s, 5, k)` and Holm, in the same single loop as A.
  - **Null:** each member centred on its **median** within the population, so the share of days won is one half.
  - **The meaning check, stated before the run:** B tests "wins on more days than it loses", not "a lower mean
    Brier", which is what `claim_meaning` claims. So B must **also** pass the limits on study 3's mean-centred null.
    Otherwise a forecaster with no mean skill could be claimed because the daily differences are skewed.
- **C, a threshold calibrated on the null.** This is Holm at α*: the largest α on a grid of 0.0005 steps up to 0.02
  that keeps every limit below.
  - **Calibration:** on paths drawn from **2024's days only** (both signs).
  - **Hold-out check:** on paths drawn from **2025's days only**.
  - **Also reported:** the whole window, which is **tuned on the data it is judged on**, because 2024 is part of it.
  - **Looks:** the 0.02 rate's (248 / 495). α* replaces only the rate in Holm's steps.

### Pass rule, power and winner (orchestrator, 16 Oct; owner's choice)

- **Pass:** the false-claim share is at most 0.025 at look 1, at most 0.025 at look 2, and at most 0.045 at either
  look, for both signs (d and -d), on the whole window and in the worst year. For A and B, at the first rate in the
  loop that passes; B also on the mean-centred null; C also on the 2025 hold-out.
- **Power on +d:** one member at a time is shifted by an improvement of exactly δ (v4's sign: d - δ), with the other
  two kept null. Power is the share of paths on which Holm claims **that** member, at look 1, at look 2 and at
  either, averaged over the three members. It is measured on the whole window at the candidate's selected rate (A,
  B) or α* (C). A candidate that passes at no rate is also measured at 0.02, for information only, and cannot win.
- **Winner:** the candidate that passes with the highest power at either look. A difference within 2 standard
  errors is a tie, and a tie goes to the simplest, in the order A, B, C.
- **Standard errors:** binomial, sqrt(p(1 - p) / paths), shown beside every rate.

### Known limits, stated before the run

- One two-year window. The worst year is also C's calibration year, and 2025 alone has 248 sessions, shorter than
  look 2 (495), so its paths wrap.
- B changes what a claim means, even if it passes. A's gate was built for NIFTY-only members, not for a cross-section
  of names.
- None of this adds crashes that 2024-2025 did not hold.

## Part 2: results

Written after the run, below this line, without editing Part 1.

Run once on 16 Oct 2026, after part 1 (0fd0c2de) and the code (76952bf2) were pushed. The code is
`research/breadth/candidates/` (`prep.py`, `compare.py`, `run.py`, tests in
`tests/research/test_breadth_candidates.py`). The raw output is `research/breadth/candidates/results.json`, with the
log in `run.log`. 437 sessions; 10 NIFTY 2% days in the window.

### Verdict: no candidate passes, so there is no winner (some evidence, one window)

| Candidate | Passes? | Worst false claim at either look (limit 0.045) | Power on +d at either look |
|---|---|---|---|
| A, v4 crash gate | **no**, at every rate | whole, -d: 0.125 at 0.02 ... 0.065 at 0.005 (SE 0.005-0.007) | 0.878 at 0.02, for information only |
| B, daily sign | **no**, at every rate, on both nulls | its own median-centred null: 0.271 at 0.02, 0.168 at 0.005; the mean-centred null: up to 0.929 | 0.982, meaningless at that size |
| C, calibrated | **no**: α* = 0.0055 holds in 2024 only | hold-out 2025, -d: 0.072; whole, -d: 0.098 | 0.871 at α* = 0.0055, for information only |

None is even a borderline pass. At every rate, each candidate's largest excess is at least 3 standard errors
above its limit (the closest: A at 0.005, 0.065 against 0.045 at either look, SE 0.005).

### A, the v4 crash gate

| Rate | Looks | Whole +d (look 1 / 2 / either) | Whole -d | Worst year +d | Worst year -d | Share judgeable, whole (look 1 / 2) |
|---|---|---|---|---|---|---|
| 0.02 | 248 / 495 | 0.002 / 0.018 / 0.019 | **0.072 / 0.082 / 0.125** | 0.004 / 0.004 / 0.009 | **0.040 / 0.032 / 0.059** | 0.62 / 0.95 |
| 0.015 | 263 / 526 | 0.001 / 0.011 / 0.011 | **0.057 / 0.064 / 0.097** | 0.002 / 0.001 / 0.002 | **0.033** / 0.019 / 0.044 | 0.67 / 0.97 |
| 0.01 | 285 / 569 | 0.003 / 0.006 / 0.008 | **0.053 / 0.051 / 0.087** | 0.001 / 0.001 / 0.002 | 0.025 / 0.019 / 0.038 | 0.72 / 0.98 |
| 0.005 | 321 / 642 | 0.001 / 0.001 / 0.002 | **0.044 / 0.033 / 0.065** | 0.001 / 0.000 / 0.001 | 0.021 / 0.011 / 0.028 | 0.78 / 0.99 |

- The gate removes only windows with too few 2% days. With 10 such days in 437 sessions (2.3%), the "more than 10%"
  cut never triggers. So the gate cuts calm windows, not crash-dominated ones.
- That cost is 22-38% of look-1 windows not judged at all, and the false claims barely move (0.125 against study 3's
  0.136 at 0.02).
- Power at 0.02, for information only (the rate fails): 0.37 at look 1, 0.88 at look 2.

### B, the daily sign test

- B fails on its own null at every rate: 0.27 at either look at 0.02, still 0.17 at 0.005. On the mean-centred null
  (the meaning check) it is far worse: 0.46-0.93.
- **Why (some evidence):** the daily sign of who wins has long memory. For `market`/`trail60` and `market`/`cal60`,
  the sign's autocorrelation is 0.25-0.34 at lag 1 and still 0.19-0.22 at lag 20. Its variance over 63-session blocks
  is 6-8 times what 5-session batches see. Who wins comes in regimes lasting months.
- B's power (0.98) means nothing at that size.

### C, the calibrated threshold

| Population | +d (look 1 / 2 / either) | -d |
|---|---|---|
| 2024 (calibration, in-sample) | 0.001 / 0.001 / 0.002 | 0.025 / 0.019 / 0.037 |
| **2025 (hold-out)** | 0.003 / 0.018 / 0.020 | **0.044 / 0.051 / 0.072** |
| Whole window (tuned on data it is judged on) | 0.001 / 0.007 / 0.009 | **0.064 / 0.055 / 0.098** |

- **α* = 0.0055 against the nominal 0.02**, almost 4 times smaller. In plain words: on 2024's data the frozen test
  would need a quarter of its stated rate to be honest.
- **Even that does not transfer.** The hold-out year and the whole window still exceed the limits at α*. 2024, the
  worst year by variance (study 2), is **not** the worst year for the test's size. So a threshold calibrated on one
  year can be anti-conservative in the next.
- Power at α*, for information only: 0.53 at look 1, 0.87 at look 2.

### What this means, by role

- **Statistician (some evidence).** The failure has one main cause, and none of the three candidates addresses it:
  **dependence lasting longer than the test's 5-session blocks.**
  - Study 3's mean-difference series for the two `market` pairs: the variance ratio of 63-session to 5-session means
    is 1.43 and 2.08.
  - For `trail60`/`cal60`, which over-rejects about nil, it is 0.62.
  - Skew adds to it, but the gate (A) and the ranks (B) leave the dependence in, and the calibrated threshold (C)
    only fits the dependence of the year it was tuned on.
- **Options strategist (reasoning only).** The `market` pairs are the relevant ones. A real rule or AI forecaster
  will lean on the implied move, so its errors against `trail60` will drift with the volatility risk premium, which
  moves over months. That is the same long-memory pattern.
- **Risk manager (reasoning only).** Any of A-C, adopted as is, would let a forecaster "prove" skill by luck at 2-6
  times the stated rate. Claims should stay postponed.
- **Mathematician (reasoning only), a candidate for a separate pre-declared run (not run here):**
  - **D:** the same frozen test with batches and bootstrap blocks of 21 sessions instead of 5.
  - **Its cost:** with at least 12 batches, the first look needs at least 252 sessions, and the look counts rise by
    about the variance ratio (roughly 1.3-2 times), so look 2 lands somewhere around 650-1,000 sessions, i.e. 2.5-4
    years.
  - **Its known limit:** 437 sessions hold only about 20 batches of 21, so the size check itself would be noisy.
  - **The honest alternative:** report BR1 descriptively and wait for more history.

### What I recommend (reasoning only)

1. Keep claims postponed under v1. None of A, B or C should become v2.
2. If the owner wants a v2 attempt, pre-declare candidate D as above, measured the same way. Expect it to buy
   honesty at the cost of 2.5-4 years of looks, which defeats BR1's purpose of fast evidence.
3. Otherwise run BR1 descriptively (paired differences with intervals, never a claim) while history grows, and
   re-measure the size check on each new year.
