# The recommender's rung rule, version 1 (story REC1a)

Frozen before the recommender's first live day. Its SHA-256 is pinned in `fno/recommend/rungs.py`
(`RUNG_RULE_SHA256`), and every recommendation record carries it. A changed number is a new version of this file
with a new pinned hash, forward only: it never re-rates an earlier record. Every number comes from the approved
market-school design (`reviews/claude/response_327_market-school-agreed.md`, items 3 and 4 and stage P2; owner
"approved", 22 Oct 2026); none is chosen here. This is not an R1 ledger trial: the rule tests no hypothesis itself,
it reads the measurements already registered (CARD_P1, trial 99) and RM1.

## What counts

A version's evidence on day d, decided at `made_at`, counts each session s of that version only when all hold:
1. the outcome is from forward paper trading (never a backtest, the simulator or a rehearsal);
2. the counting rule in force counted it (MS-P1h's `CountingRule` for school drivers; S1's order rule for the
   desk's books);
3. s is before d (day d itself never counts);
4. GitHub's push receipt of the commit that brought the outcome's receipt to `main` is strictly before `made_at`. A
   receipt GitHub cannot answer does not count that day (fails closed).

A session counts once, however many outcomes it holds.

## The rungs

| Rung | Name | Rule |
|---|---|---|
| 0 | Unproven | 0 counted sessions |
| 1 | Exploratory | 1 to 29 counted sessions, or 30 or more without the descriptive review |
| 2 | Watching | 30 or more counted sessions and stage P2's descriptive review against the matched control recorded |
| 3 | Established | rung 2's conditions and all three: the sample-size plan is met; the one-sided 95% lower bound of the net result is above zero after the frozen multiple-test adjustment; a second untouched forward window agrees |

Only rung 3 is "proven". A paper trade of a version at rung 0, 1 or 2 is never a recommendation.

## Day conditions

Each of these, when true on day d, lowers every version's shown rung for that day by one, cumulatively, never below
0; nothing raises a rung: today's quote or road gate failed; the market weather is red; M1's record names a
scheduled event that day.

## Calibration

A calibrated probability is shown only with at least 100 outcomes over at least 60 sessions, in 5 bins, as a
descriptive check. Before that the line reads "not enough outcomes to calibrate".

## Values (read by the test that pins the code to this file)

| Name | Value |
|---|---|
| watching_sessions | 30 |
| calibration_min_outcomes | 100 |
| calibration_min_sessions | 60 |
| calibration_bins | 5 |
| day_condition_step | 1 |
