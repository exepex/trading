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

The comparison is paired against N0, RC1 and REF on h's common road-days, with one point per session.
- **The bound:** a one-sided 95% Student-t lower bound on non-overlapping batch means (S6's t table), counted back
  from the last session. This replaces the moving-block bootstrap, which failed its own null gate: 27% false
  "Watching" at 30 sessions (orchestrator, 22 Oct 2026).
- **The batch length:** 1.5 times the longer of the two cards' frozen holds, in sessions, rounded up and never under
  10. Batch = hold failed the gate below at holds 10-25 (upper ends 10.4-11.0%). Fewer than 2 whole batches give no
  bound: "Not established, too few independent batches".
- **The gate it passed:** the null calibration, 2,000 seeds a configuration. The upper end of the 95% interval of the
  false-"Watching" share is 10% or less at every real hold (3, 10, 15, 18, 25 and 33 sessions; worst 9.0%), with
  shared shocks 0.3, 0.6 and 0.9 and return spreads 0.5 and 1.0. Some evidence: a simulation, not data.
- **A card's hold:** the shortest bound its card states. That is sessions held, calendar days held, sessions before
  expiry, or days to expiry at entry less its last exit day. With no such bound, the hold is the expiry cycle (35 days
  monthly, 7 weekly). Days become sessions at 5 a week, rounded up. N0 holds nothing.
- **The statuses:** Exploratory below 30 sessions, Watching when the bound is above 0 (not a claim, no licence), Not
  established otherwise. No others.

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
min_batches: 2
batch_hold_multiple: 1.5
min_batch: 10
sessions_per_week: 5
monthly_cycle_days: 35
weekly_cycle_days: 7
```
