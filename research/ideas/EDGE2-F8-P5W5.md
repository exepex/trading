# Idea card: EDGE2-F8-P5W5

Written by `research/edge2/f8_cards.py` from `research/edge2/F8_PROTOCOL.md`. Exploratory; the filter is tested only
on the held-out years 2025-26, after a judge (protocol sections 1 and 8).

## G0: the idea

| Field | Value |
|---|---|
| Id and version | EDGE2-F8-P5W5 v1 |
| Ledger trial | 122 |
| Registered research question | edge2-f8-fii-side-weekly-spread: EDGE2 F8: does the sign of the FII net index-futures change, choosing a put or a call credit spread on NIFTY's weekly (entered at the next open, held to expiry), make money after real costs and more than random sides? One Holm family of 3 structures (P0W5, P5W5, P0W10); the filter tested only on held-out 2025-26 after a judge (post-hoc idea from F6); protocol research/edge2/F8_PROTOCOL.md |
| Proposed by (role or AI) and date | options strategist and flow analyst (Claude, EDGE2 builder), 25 Oct 2026 |
| Who pays and why | option buyers paying premium, with the side tilted by FII positioning [some evidence of F6's post-hoc lean; reasoning only that a spread can carry it] |
| Forecast it rests on | none (the sign of the FII net index-futures change) |
| Instrument and structure | NIFTY weekly 2-leg credit spread: short leg 0.5% out of the money, long leg 0.5% beyond it; never a naked short leg |
| Entry rule | the open of the first session after the previous expiry, at each leg's opening trade; put spread after a rise in FII net index futures on the previous session, call spread after a fall |
| Exit rule | held to expiry, cash-settled at the expiry day's index close |
| Size | 1 lot of the contract's market lot on the entry session |
| Worst loss in Rs | at most Rs 10,000 modelled at entry (the cap), plus charges and pads |
| Expected gross per trade, with source | the held-out read; the gross bar is Rs 260 a lot (protocol section 6) |
| Needs a reaction faster than 60 minutes? | no: an opening entry held to settlement |
| Frequency | about 50 cycles a year |

```factory
id: EDGE2-F8-P5W5
version: 1
trial: 122
experiment: edge2-f8-fii-side-weekly-spread-2026-10-25
description: "EDGE2 F8 P5W5: FII-side NIFTY weekly credit spread, short leg 0.5% out of the money, long leg 0.5% beyond it (exploratory)"
question: edge2-f8-fii-side-weekly-spread
hypothesis: yes
measurement: no
data_sets: ["NIFTY weekly options | NSE daily closes | Feb 2019 - 9 Oct 2026", "Participant open interest (A8) | NSE daily files | 2025 - 2026"]
measures: "mean net per trade after C1's charges and the Rs 1 pad, one lot, held to settlement (protocol sections 6-8)"
```
