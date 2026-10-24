# Idea card: EDGE1-BANKNIFTY-NS-T21 BANKNIFTY NS T21

Written by `research/edge1/cards.py` from `research/edge1/PROTOCOL.md` (frozen in `research/edge1/FREEZE.md`). Every
result is exploratory (spent data, protocol section 2).

## G0: the idea

| Field | Value |
|---|---|
| Id and version | EDGE1-BANKNIFTY-NS-T21 v1 |
| Ledger trial | 97 |
| Registered research question | edge1-rule-based-index-option-trades: has a simple rule-based NIFTY or BANKNIFTY monthly option trade made money after real costs? One Holm family across both indices (protocol section 11) |
| Proposed by (role or AI) and date | options strategist (Claude, EDGE1 builder), 22 Oct 2026 |
| Who pays and why | option buyers paying a variance risk premium for protection [reasoning only: the premium may be gone after costs; that is the question] |
| Forecast it rests on | none |
| Instrument and structure | BANKNIFTY monthly options, the engine's monthly cycle; naked short strangle: SC2's two shorts and no wings; a measurement only, never screened or nominated (not tradeable under the house rules) |
| Entry rule | the engine's entry day (30-45 days before expiry), at that day's NSE closes, only if every leg traded; the widest width whose worst loss fits the cap for the cycle's own lot |
| Exit rule | the planned close, 21 calendar days before expiry (the engine's exit day) |
| Size | 1 lot of the cycle's own market lot (protocol section 8) |
| Worst loss in Rs | unbounded; the report shows the worst trade per lot and the margin it needed (owner's Q1 answer) |
| Expected gross per trade, with source | run 1 (2019-2022), added before G1 |
| Needs a reaction faster than 60 minutes? | no: every rule reads daily closes |
| Frequency | 12 cycles a year at most; fewer when an entry is skipped |

```factory
id: EDGE1-BANKNIFTY-NS-T21
version: 1
trial: 97
experiment: edge1-rule-based-option-trades-2026-10-22
description: "EDGE1 BANKNIFTY NS T21: naked short strangle (exploratory: spent data)"
question: edge1-rule-based-index-option-trades
hypothesis: no
measurement: yes
data_sets: ["BANKNIFTY monthly options | NSE daily closes | 2019 - 20 Oct 2026"]
measures: "mean net per complete trade after C1's charges and the Rs 1 pad, one lot (protocol sections 7-11)"
```
