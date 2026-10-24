# Idea card: EDGE1-NIFTY-SC3-SL2 NIFTY SC3 SL2

Written by `research/edge1/cards.py` from `research/edge1/PROTOCOL.md` (frozen in `research/edge1/FREEZE.md`). Every
result is exploratory (spent data, protocol section 2).

## G0: the idea

| Field | Value |
|---|---|
| Id and version | EDGE1-NIFTY-SC3-SL2 v1 |
| Ledger trial | 77 |
| Registered research question | edge1-rule-based-index-option-trades: has a simple rule-based NIFTY or BANKNIFTY monthly option trade made money after real costs? One Holm family across both indices (protocol section 11) |
| Proposed by (role or AI) and date | options strategist (Claude, EDGE1 builder), 22 Oct 2026 |
| Who pays and why | option buyers paying a variance risk premium for protection [reasoning only: the premium may be gone after costs; that is the question] |
| Forecast it rests on | none |
| Instrument and structure | NIFTY monthly options, the engine's monthly cycle; short iron condor: sell the call nearest spot x 1.03 and the put nearest spot x 0.97, buy wings one width further out; never a naked short leg |
| Entry rule | the engine's entry day (30-45 days before expiry), at that day's NSE closes, only if every leg traded; the widest width whose worst loss fits the cap for the cycle's own lot |
| Exit rule | the first fully traded close with mark >= 3 x credit (a loss of 2 x credit), else the T21 close |
| Size | 1 lot of the cycle's own market lot (protocol section 8) |
| Worst loss in Rs | at most Rs 10,000 modelled at entry (the cap), plus charges and pads |
| Expected gross per trade, with source | run 1 (2019-2022), added before G1 |
| Needs a reaction faster than 60 minutes? | no: every rule reads daily closes |
| Frequency | 12 cycles a year at most; fewer when an entry is skipped |

```factory
id: EDGE1-NIFTY-SC3-SL2
version: 1
trial: 77
experiment: edge1-rule-based-option-trades-2026-10-22
description: "EDGE1 NIFTY SC3 SL2: short iron condor (exploratory: spent data)"
question: edge1-rule-based-index-option-trades
hypothesis: yes
measurement: no
data_sets: ["NIFTY monthly options | NSE daily closes | 2019-2023", "NIFTY monthly options | NSE daily closes | 2024-2026"]
measures: "mean net per complete trade after C1's charges and the Rs 1 pad, one lot (protocol sections 7-11)"
gross: {kind: measured, mean: 7.321428571428677, sd: 2714.213162581602, n: 28, source: "EDGE1 run 1, research/edge1/selection.json at 81f02afe (story/edge1-build), g1.inputs; exploratory (sd_gross)"}
tail: {probability: 0.0, loss: 0.0, in_gross: yes}
cost: {measured: 760.2674064505358, source: "EDGE1 run 1, research/edge1/selection.json at 81f02afe (story/edge1-build), g1.inputs; exploratory (mean charges plus pads, Rs 1 pad)"}
sd_per_trade: 2714.7934261485066
frequency_per_year: 7.0
pass_level: 0.05
```
