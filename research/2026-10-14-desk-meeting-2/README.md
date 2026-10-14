# Desk meeting 2 (14 Oct 2026): first-strategy candidates for Book 1

The owner asked to start research for a first strategy. The minutes and verdict are in
`reviews/claude/response_92_first-strategy-candidates.md`. The verdict: zero candidates with a credible edge after
costs; an optional monthly condor benchmark shadow, labelled as a measurement.

- `analysis.py` reproduces every number: experiment 1's recorded results per structure, the F1 premium feature, the
  14 Oct 15:00 quotes (half-spreads, skew), NIFTY's moves over the holding windows, and an illustrative put-spread
  pricing model.
- `output.txt` is its output (`python research/2026-10-14-desk-meeting-2/analysis.py`).
- No new strategy P&L was run on NSE option prices: no untouched history remains (the 2019-23 holdout was used by
  experiment 1), so a new backtest would be a new trial on spent data.
