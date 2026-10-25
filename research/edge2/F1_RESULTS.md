# EDGE2 F1 results: a volatility-premium gate on weekly index option premium

Protocol `research/edge2/F1_PROTOCOL.md`, frozen in `F1_FREEZE.md` (commit `47c01637`, code SHA-256 `9cbe34ce`). One
discovery run at `270959dd` (`f1/discovery.json`, tables in `f1/discovery_tables.md`). Trials 109-114, one Holm family
at 0.05. **Every figure is exploratory** (NIFTY weeklies spent, BANKNIFTY option closes exposed). Rupees are for 1
lot of the time, after C1's charges at today's STT and a Rs 1 entry pad a leg, held to settlement.

## Answer

**No variant has an edge after costs, and nothing is nominated, so the held-out set (FINNIFTY, MIDCPNIFTY) stays
unread and fresh.** [strong evidence for these 6 variants on 702 weekly cycles; it does not rule out every weekly
structure]

- 702 cycles (NIFTY 398, Feb 2019 - Oct 2026; BANKNIFTY 304, Jan 2019 - Nov 2024), 4 skipped (re-dated expiries); 160
  settlements cross-checked against the expiring future, 0 disagree.
- No variant is Holm-significant; the best one-sided p is 0.55. All six are `screened_out` at G1 (the cost wall,
  `research/factory/gates.csv`).
- **The premium is there, but it is smaller than the costs.** The always-on iron fly (WF-G0) earned **+Rs 231 gross a
  trade**, and its charges (Rs 163) plus pads (about Rs 173) cost Rs 336: net **-Rs 105** (Rs 2 pad: -Rs 275). The
  condor (WC-G0) earned only Rs 66 gross against Rs 287 of costs: net -Rs 221.
- **The gate adds nothing.** Against random gates of the same size (RC1), WF-G12's mean sits at p_gate 0.48, WC-G12's
  and WC-G15's at 0.89 (worse than random). The only positive variant, WF-G15 (+Rs 795 on 28 trades, Rs 2 pad +Rs
  598), rests on 18 expiry weeks (below the 30 the protocol needs for a p), a standard error of Rs 1,720 and p_gate
  0.21; two trades in 2023 and one in 2025 (+Rs 13,637) carry it.

| Variant (trial) | Taken | Mean gross | Costs (charges + pads) | Mean net | SE (week-clustered) | p | Rs 2 pad | Win share | Worst trade | Max drawdown |
|---|---|---|---|---|---|---|---|---|---|---|
| WF-G0 (109) | 702 | 231 | 336 | -105 | 266 | 0.65 | -275 | 48% | -9,802 | -192,628 |
| WF-G12 (110) | 153 | 270 | 350 | -80 | 593 | 0.55 | -220 | 48% | -9,802 | -88,099 |
| WF-G15 (111) | 28 | 1,205 | 410 | 795 | 1,720 | 1 (18 weeks) | 598 | 50% | -8,260 | -44,849 |
| WC-G0 (112) | 699 | 66 | 287 | -221 | 153 | 0.93 | -385 | 75% | -9,870 | -171,887 |
| WC-G12 (113) | 150 | -205 | 292 | -497 | 379 | 0.91 | -569 | 75% | -9,870 | -98,553 |
| WC-G15 (114) | 25 | -647 | 331 | -977 | 1,190 | 1 (17 weeks) | -783 | 72% | -9,840 | -52,502 |

By index (always-on): WF earned +Rs 254 a trade on BANKNIFTY and -Rs 380 on NIFTY; WC -Rs 38 and -Rs 361. NIFTY's
weekly since 20 Nov 2024 (the only weekly still listed): WF-G0 -Rs 690 on 99 trades, WC-G0 -Rs 437.

## What each role takes from it

- **Statistician:** six correlated tests, none near significance; the one positive mean (WF-G15) is the kind of
  small-sample winner Holm exists to stop. Not nominated, and it must not be re-tested on this data as if new.
- **Volatility trader:** the weekly ATM premium is real but thin: about Rs 230 a lot-week gross on the fly, i.e. a
  few rupees a unit. "IV rich against an EWMA forecast" did not pick the better weeks.
- **Tax and cost accountant:** costs are the whole story. Four legs pay charges and slippage four times; exercise STT
  on in-the-money legs at settlement adds to it. A 4-leg weekly cannot clear Rs 300-400 of costs on a Rs 230 edge.
- **Options strategist:** the condor's shorts one implied move out keep 75% of trades but earn too little (Rs 66
  gross) to carry the wings and the tail. Fewer legs or larger credit per leg is the only way past the cost wall.
- **Risk manager:** the cap held (worst trade -Rs 9,870), but always-on drawdowns reach -Rs 1.7 to 1.9 lakh a lot over
  the sample: negative drift plus capped tails.
- **F&O trader / microstructure:** fills are at NSE's closes plus Rs 1 a leg; the real weekly spread near expiry is
  often wider for wings, so the true result is likely worse, not better.
- **Red team:** a stale far-strike close could flatter or hurt a result; EDGE1's impossible-price and untraded-leg rules applied
  at every entry (3 condor entries refused for an untraded leg); a stale close inside its bounds cannot be detected.
- **Portfolio manager:** nothing goes to the school's forward test from F1. The useful finding is the size of the
  gross premium against costs, which sets the bar for the next families.

## Limits

- Daily closes: entries at NSE's closing prices (last half-hour weighted), not quotes; settlement at the expiry day's
  index close (checked against the expiring future where one existed).
- BANKNIFTY's weeklies ended 13 Nov 2024; results there transfer to NIFTY's weekly by assumption only.
- Lots before 2024: EDGE1's circular schedule (NIFTY, BANKNIFTY); the held-out lots were never used.
- The EWMA gate is one simple forecast; a better forecaster (v4's) was not tried, by design (one variant set).

## Post-hoc (after the run, not decided on) [reasoning only]

The cost wall suggests where an edge, if any, could survive: structures with fewer legs per rupee of premium, or a
cheaper exit than settlement (exercise STT on in-the-money legs). These are candidates for later pre-registered
families, never re-tests of F1's variants on the same data.

## Deviations

- The G1 inputs were first appended to the six idea cards after the freeze (commit b9b23f9d), which made B4's
  `require_registered` refuse them (judge J's S1). The cards are restored to their frozen text; the inputs stay in
  history at b9b23f9d and the gate rows are unchanged. No number changed.
