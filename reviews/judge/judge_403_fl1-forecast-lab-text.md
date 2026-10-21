# Judge 403: FL1 story text, the forecast lab and daily reports (story/fl1-forecast-lab at a6c6db0d)

**Verdict: FAIL on the story text: 3 should-fix findings and 3 minor. Lane 1.** Number claimed with O12's tool.

The text is honest and well grounded:
- it tells the owner first that no live forecaster has beaten its base rate yet, that next-day direction is close to
  a coin flip, and that trust is counted in trading days (about 60 for calibration, 6-12 months for an edge);
- it reuses E8's fill parts, G13's scores, A16's observer and LR1's publish-once;
- it splits the build into five parts gated on their inputs;
- it matches the owner's 21 Oct rows 262-264: two channels, NIFTY and BANKNIFTY, ranges first, top 10, the 08:45 slot
  waiting for A22, BANKNIFTY lab positions waiting for A16's marks.

The three findings are in the lab's decision logic, where a wrong design would mislead the owner about trust.

## Findings

**Should-fix 1. The 09:30 positions can use a forecast sealed after the price they trade on (look-ahead).** Strong
evidence: text read.
- The "open" slot's seal cutoff is "before 09:45" (Design, Forecasts row).
- The lab's positions are priced and filled at "the 09:30 mark", with the ranker scoring candidates "under the sealed
  5-95% quantiles".
- So a forecast sealed at 09:44, after seeing 09:30-09:44 prices, could pick positions priced at 09:30.

Fix: the forecast a position is ranked on must be sealed before the mark it is priced and filled at. For example, the
open slot's cutoff is at or before the 09:30 mark's capture start, or the positions use a later mark than the seal.
Add a criterion: a forecast sealed after the fill mark is never used to rank, the day's positions are "not taken:
forecast sealed late", and that is alerted.

**Should-fix 2. The ranker does not say whose ranges it trades, and on the implied range it has no edge by
construction.** Some evidence (reasoning, plus the text's own baselines).
- The forecasts are G13's (`implied`, `rv20`, `hist750`) and later G13b's, but the `RangeRanker` row says only "the
  sealed 5-95% quantiles".
- If it ranks on the option-implied range, then expected payoff against the same options' prices is about zero before
  costs, so the top 10 are chosen by noise and costs.
- Ranking on `rv20` or `hist750` is a real test of "realised versus implied" (the volatility risk premium).

Fix: name the forecaster or forecasters the lab ranks on, state why, and state that the implied range is a baseline,
never a ranking source. Print in each report which forecaster picked the positions, so a lab result is never read as
"the engine works" when it only measures one baseline against another.

**Should-fix 3. Flat tails at the 5% and 95% levels bias the ranking towards selling premium.** Some evidence
(mathematics).
- With "flat tails at the 5% and 95% levels", the outer 5% of probability on each side sits at q05 and q95.
- A short vertical or condor whose short strike is inside the band, but whose wing is beyond q95, then loses only up
  to the payoff at q95 in that model, instead of losing more towards the wing's maximum loss.
- So expected payoff is overstated for exactly the credit structures whose losses live in the tails, and the top-10
  ranking leans to them. That is the pattern experiment 1 already paid for.

Fix: use a tail that keeps the measured mass beyond q05 and q95 at least as far as each candidate's wing. For defined
risk, the payoff beyond the wing is flat at maximum loss, so put the tail mass at the wing (or at maximum loss) and
not at q95, or use G13's anchored lognormal tail. Test it with a condor whose wing lies beyond q95.

**Minor.**
1. **Size.** State each lab position's size (one lot each, as scoreboard A standardises), so P&L across the 10 is
   comparable and the costs (Rs 800-940 a four-leg trade) are per lot.
2. **Winner's curse.** Picking the top 10 of many candidates by expected net overstates each pick's edge. The match
   report should show expected against realised net by rank, so the bias is visible to the owner.
3. **Horizon against exit time.** The forecasts are about the N+1 (or N+3) close, but positions exit at the 15:15 mark.
   Say so in the report, or exit at the mark nearest the forecast's target.
