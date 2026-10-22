# Judge 468: EDGE1 protocol draft (story/edge1-build at ea268f3a), round 1 of 2

Judge B, 22 Oct 2026. Short-report rule (DESK_DECISIONS row 294).

## Verdict: FAIL (1 should-fix)

## Checked and right

- **§2, status.** Every result is exploratory, both reasons are given (the data is spent, and GR1 foresaw the
  direction), and the known-before variants are named (experiment 1's P1 and P2).
- **§3, the seal.** Run 1 reads at most January 2023's closes, for its December 2022 exits, and says so. Run 2 is
  opened once, on the same cycles for all 12 variants.
- **§3, weeklies left out.** The narrowing is justified: the engine's cycles are monthly, every NIFTY weekly is
  spent, and BANKNIFTY's weeklies ended.
- **§5, the widths.** BANKNIFTY's are NIFTY's list times 3, fixed now.
- **§6, the arithmetic.** SL2's mark of at least 3 x the credit is a 2x loss, and TP50's mark of at most 0.5 x the
  credit is half earned. Both are checked on fully traded days only.
- **§7.** The untraded-leg rules from judges 467 and 467.2, word for word.
- **§8, lots.** The circular wins any disagreement.
- **§9, costs and margin.** Today's STT is the decided figure. The historical rates are marked reasoning only and
  checked in the build. The margin build gate is in.
- **§10, G1.** R1's CostWall on run 1, with at least 20 trades.
- **§11, the test.** The re-centred one-sided p, Holm, and the four-part nomination rule, including all trades
  positive at both pads.

## Should-fix 1: the bootstrap block of 20 is 20 months here

§11 uses G4's `resampled_means` with **block 20** over trades in date order. G4's 20 is 20 sessions of daily data.
EDGE1's unit is one monthly trade, and the trades do not overlap: each decision falls 30-45 days before an expiry and
the T21 exit 21 days before it, so one trade's exit comes before the next decision.

The story's own pass rule (judge 467) says "block bootstrap **by month**".

**The normal path:** run 2 has about 45 cycles, and fewer after the not-taken trades. With L = 20:
- there are 26 possible block starts;
- each resample joins 3 blocks;
- so the "bootstrap" is close to resampling 3 overlapping 20-month windows. The null distribution is lumpy, its
  variance is badly estimated, and the p-value is unreliable in either direction.

**Fix.** Set the block to the unit:
- block length 1 trade (a month), or 2-3 if you want some allowance for serial dependence, stated with the reason;
- through G4's same function, with its `block` argument (or the same moving-block code with L passed in), and the
  seed rule unchanged.

## Notes (one line each)

1. **Expected count.** At about 45 run-2 cycles with every-leg-traded entries, several BANKNIFTY variants may fall
   below the 40-trade minimum (p = 1). Print the expected count per variant from run 1's fill rates before run 2.
2. **Holm spans both indices.** "Every variant run 2 tests" covers both indices; say so explicitly in §11.

## Plants

None: this round is text only. The code and freeze come next.
