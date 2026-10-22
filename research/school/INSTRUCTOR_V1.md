# Instructor v1: frozen rules (story MS-INS)

The market school's instructor explains each closed paper trade and ticket and compares each driver with the
controls. It is descriptive only: no licence, no claim, no recommendation. Every instructor record carries this file's
SHA-256. A change is instructor v2: committed before the first session it reads, never applied to sessions already
written. Every number below is a first guess [reasoning only].

## Attribution (part b)

- Stepwise Black-76 on G13's parity forward, with time measured to 15:30 IST on expiry day. Each step's Greeks are
  taken at the step's start.
- Costs are C1's charges plus the spread paid against the path's own mids. The residual balances.
- **Poor fit:** an absolute residual above both Rs 200 and 25% of the Greek components' absolute sum.

## Causes (part c; response 325 section 6.1)

**Terms:**
- `z` is ln(exit level / entry level) / (entry ATM straddle volatility x square root of the time held);
- a stance is read from the entry Greeks;
- directional: a 1% forward move changes the value by 20% of the maximum loss.

**Primary order:** 13, 10, 6, 7, 8, 1, 11, then 2-5 by the largest component, then 9, then 12.

**Precise readings in v1:**
- **Cause 11:** "holding to plan" means held to expiry and settled through d's settlement.
- **Cause 12:** compares the position's mid-to-mid P&L (the Greek components plus the residual, before costs) with
  its model band. The band is lognormal at the entry ATM volatility over the time held, each leg kept at its entry
  volatility, with 201 quantiles. Costs are left out on both sides.
- **Cause 8:** each index's move runs between the path's first and last recorded snapshots, on the ATM volatility of
  its nearest expiry still alive after the window, over the clock time between the two captures. A settled path's
  own move runs to the settlement price.
- **Flat results:** a result of exactly zero fires no component cause (2-5).
- **Cause 13 is not testable in v1** until MS-P1j's fleet can replay a sealed session. Every record counts it as not
  testable; it is never guessed.

## Comparison (part d)

The comparison is paired against N0, RC1 and REF on h's common road-days, with one point per session. Its 90% interval
comes from a moving-block bootstrap over sessions. The statuses are Exploratory, Watching and Not established only.

```thresholds
range_z: 1.645
shock_z: 2.0
market_wide_count: 3
component_share: 0.40
directional_share: 0.20
gap_stop_multiple: 1.25
whipsaw_multiple: 1.0
noise_sds: 1.0
noise_quantiles: 201
poor_fit_rs: 200.0
poor_fit_share: 0.25
min_sessions: 30
block_sessions: 5
sensitivity_blocks: [2, 10]
resamples: 10000
seed: 20261023
interval_tail: 5
```
