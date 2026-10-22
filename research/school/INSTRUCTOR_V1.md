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

**Simplification:** cause 11's "holding to plan" is held to expiry and settled through d's settlement, in v1.

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
```
