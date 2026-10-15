# Response 216: story LR3, drift detection with a CUSUM (story text for the judge)

Builder: Claude, 16 Oct 2026 (IST), branch `story/lr3-drift-cusum`, issue #103. Lane 1 (a new story; it pauses
strategies). The text is in `docs/stories/LR-learning.md`, section LR3. The evidence is in
`research/2026-10-16-lr3-drift-evidence/`: four scripts and their outputs. **No code.**

## What I checked, and what I found

1. **Design 5.8's normal-theory numbers are right** (strong evidence: Markov chain, `arl.py`). With k 0.5, h 4 gives
   334 observations between false alarms and h 5 gives 925.
2. **k 0.5 detects a collapse, not a lost edge** (strong evidence, same chain). A 0.3 SD shift takes 60-103
   observations. At about 12 trades a year that is 5-8 years.
3. **For strategies, skew moves the false-alarm rate a lot** (strong evidence, experiment 1's real nets resampled,
   `strategy_arl.py`). With a fixed h of 4:
   - the short-premium SF (skew -2.6) has an in-control median run of 40 trades;
   - BF (skew +2.4) never alarms in 3,000 trades.

   So a fixed h is wrong in both directions. LR3 calibrates h per version from its own research nets, to a median
   in-control run of ten years of its trades, with a floor of 4 (`calibrate_h.py`). This gives h 4.0-5.5 and flags a
   1 SD collapse in 8-12 trades.
4. **Design 5.8's forecaster rule, as written, fails on real data** (strong evidence, the v4 back-fill,
   `backfill_cusum.py`).
   - It scales each day's Brier difference by the SD of the first 60 outcomes. That gives 287-503 alarms in about
     1,900 sessions for forecasters that beat the base rate. The first 60 sessions had no 2% move, so the SD was
     0.0001, against 0.08 over the whole history.
   - On 20-outcome blocks, scaled by the back-fill's block SD, it gives 0 alarms in 95 blocks, and catches a
     forecaster 1 block-SD worse than its baseline in about 7 blocks.
5. **What an alarm does follows the design** (4.3, 5.8, REPLAN 4). A strategy alarm pauses new entries through E6's
   existing pause path (`fno/scorecard/pauses.py`: `paper -> paused`, D1's status change) until the owner's restart
   after a review. Open positions run to their exits, with no owner action on paper. A forecaster alarm is an alert
   plus an input to the next review; it never changes a score (v4 is frozen).
6. **One field is missing.** Strategy plans register `expected_net_per_opportunity` and an expected range, but no SD
   (`fno/playbook/schema.py:30`). LR3 needs `expected_sd_per_opportunity`, and R1's sample plan needs it too. That is
   a D1 format change, which goes through the orchestrator.

## Placement

The code goes in `fno/learning/` as `drift_cusum.py`, `drift_strategies.py`, `drift_forecasters.py` and its own
`drift_wiring.py`. LR1's builder (session_0145TfSwzmpk6MBrH92f5h4G), who owns `fno/learning/`, agreed on 16 Oct 2026, with two conditions: E6 and G8 are read through their own readers or ports (no second parser), and the wiring is separate. LR1's post-mortem reads `drift_alarms(period)`, and LR1's builder adds that call.

## Questions for the owner (via the orchestrator), each with my recommendation

1. **Strategy threshold:** calibrate h per version (ten years of trades, floor 4), or keep design 5.8's fixed 4?
   **Recommend calibrating.** A fixed 4 falsely pauses a short-premium strategy about every 40 trades (median), and
   never fires for a long-premium one. Strong evidence for the problem; reasoning for the ten-year target.
2. **Forecaster rule:** 20-outcome blocks scaled by the back-fill's block SD, h 4, instead of design 5.8's daily
   z-scores with the first 60 days' SD and h 5? **Recommend the blocks.** The written rule gives hundreds of false
   alarms on the real back-fill. Strong evidence.
3. **What a strategy alarm does:** pause new entries until the owner's restart after a review (the design), or only
   alert and feed the review? **Recommend the pause, as designed.** It catches only a collapse (about 1 SD worse per
   trade), which is when stopping new risk is right, and the catastrophic-loss rules already pause the same way.
   Reasoning only.
4. **The SD field:** require `expected_sd_per_opportunity` for `paper`, so that every approved version is monitored?
   **Recommend yes.** Otherwise a version shows "drift not monitored". Reasoning only.

## Honest limits (also in the story)

The CUSUM never detects a small edge quietly disappearing; that is the review's job. Monthly strategies react in
months even to breakage, so the catastrophic-loss rules stay the first line. The calibration rests on close-proxy
research history.
