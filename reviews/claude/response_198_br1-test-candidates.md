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
