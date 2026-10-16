# Judge 304: G13 story text, the valuation record and price-distribution forecasts (story/g13-price-distribution at 84074ce5)

**Verdict: FAIL on the story text: 1 should-fix and 4 minor.** The request named 1657e567; the branch moved to 84074ce5
(the O1 boundary agreed), so I judged 84074ce5. The orchestrator's answers to Q1-Q4 are now in the text: an O1 step
after `card` with its own `live_from`, no protocol registration, `risk_free_rate` until a T-bill capture lands, and
agreed boundaries. Accepted.

## My own recomputation from the real 16 Oct NSE chain
`research/data/quotes/nse/derivatives/quote-snapshots/2026/10/nifty_20261016_145500.csv`. I wrote my own script from
the text's rules: spread filter, three-strike parity forward, OTM put curve, midpoint CDF, a pool-adjacent-violators
pass, and linear quantiles. Script: `scratchpad/g13/probe.py` (not committed).

| Item | Text | Mine |
|---|---|---|
| 27 Oct forward | 23,122.0 (= the future's last trade) | 23,122.0; the sidecar's futures last is 23,122.0 |
| Strikes | 47, 21,950-24,250 | 47, 21,950-24,250 |
| CDF range, raw decreases | 2.2%-98.9%, 3 | 2.2%-98.9%, 3 |
| q05 / q50 / q95 | -3.79% / +0.11% / +2.98% | **-3.72%** / +0.11% / **+3.03%** |
| 23 Nov CDF range, decreases | 10.3%-87.4%, 10 | 10.3%-87.4%, 10 |

The mathematics is right:
- `CDF(K) = e^{rT} dP/dK`, with the parity conversion `P = C - e^{-rT}(F - K)` for European options on a future.
- Both lognormal tail formulas are continuous at the edge strike and monotone.
- The risk-neutral caveat is stated plainly.
Strong evidence: rederived, and checked on the real chain.

## Findings

**Should-fix 1. The distribution algorithm is not pinned tightly enough to reproduce.** Some evidence. My q05 and q95
differ from the probe's by 0.05-0.07 percentage points, with identical inputs, forward, CDF points and median.
Criterion 4 says "the 16 Oct NSE chain reproduces the probe's numbers", but the probe script is not committed. The
text leaves open:
- the pool-adjacent-violators weights (equal per midpoint, or per strike gap);
- whether midpoints over 200-point gaps are dropped before or after the pass;
- the interpolation basis (strike or log-strike).

Fix: specify these three choices, and commit the probe's expected numbers as a test fixture made by the committed
code, so any judge can recompute them.

**Minor.**
1. "Fair value" is the price at the quadratic smile IV, a smoothness residual, not a valuation that says a contract is
   cheap. Label the field (for example `smile_value`) and state in the record that it is no trade signal. Otherwise
   the owner may read `fair - mid` as an edge (reasoning only).
2. For `h1`/`h5`, scaling the implied log-quantiles around zero by `sqrt(h/sessions)` also scales the distribution's
   own centring (its mean and median offset) by the square root instead of linearly. The effect is small (a few basis
   points at these horizons), but re-centre on the median before scaling, or state it in the method note.
3. The mean-vs-forward check needs the tails' contribution. Name the numerical integration (grid and limits) so the
   0.5% flag is reproducible.
4. Receipts are committed by O1's `CommandStep`. Say what happens to a written Drive file whose receipt commit fails
   (rerun idempotence: the same bytes give "already in Drive").

## Over-engineering check
The record holds a lot: a surface by delta, skew, term structure, fair value for every contract, three indices, and
three forecasters with scoring. Each part answers the owner's words "prices, price forecasting, valuation" (row 244),
and every part is descriptive. Nothing reads it to trade. Running cost: seconds in O1's run. Accepted, with minor 1 so
the valuation is not mistaken for a signal (reasoning only).

## Note: b4055cb7 (11:31)
The diff from 84074ce5 adds:
- `parity_forward` as a standalone pure function;
- every IV and price through `implied_vol.Black76` (no new inverter; good, it keeps one inverter);
- the G7b and G10 boundaries, both agreed.
**Should-fix 1 stands:** the PAV weights, the 200-point gap order, the interpolation basis and a committed probe
fixture are still unspecified.
