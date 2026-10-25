# Idea card: EDGE2-F1-WC-G0

Written by `research/edge2/cards.py` from `research/edge2/F1_PROTOCOL.md`. Exploratory: discovery on spent data,
held-out read once (protocol section 2).

## G0: the idea

| Field | Value |
|---|---|
| Id and version | EDGE2-F1-WC-G0 v1 |
| Ledger trial | 112 |
| Registered research question | edge2-f1-weekly-vrp-gate: EDGE2 F1: has a defined-risk weekly index option position held to expiry, always or only when ATM implied volatility is rich against an EWMA forecast of realised, made money after real costs? One Holm family of 6 (WF, WC x G0, G12, G15); discovery NIFTY+BANKNIFTY (spent, exploratory), held-out FINNIFTY+MIDCPNIFTY read once; protocol research/edge2/F1_PROTOCOL.md |
| Proposed by (role or AI) and date | volatility trader and options strategist (Claude, EDGE2 builder), 25 Oct 2026 |
| Who pays and why | hedgers and retail buyers of short-dated index options paying a variance risk premium [strong evidence the premium exists in index options; reasoning only that it survives costs on Indian weeklies] |
| Forecast it rests on | none (the gate is an EWMA lambda 0.94 of index close returns, protocol section 5) |
| Instrument and structure | each index's nearest weekly expiry; weekly short iron condor: sell the call and put one implied move out, buy wings one width further; never a naked short leg |
| Entry rule | the close of the first session after the previous expiry, every leg traded, always (no gate); the widest width whose worst loss fits the cap for the cycle's lot |
| Exit rule | held to expiry, cash-settled at the expiry day's index close |
| Size | 1 lot of the contract's market lot on the entry day |
| Worst loss in Rs | at most Rs 10,000 modelled at entry (the cap), plus charges and pads |
| Expected gross per trade, with source | discovery run, added before G1 |
| Needs a reaction faster than 60 minutes? | no: entry at a daily close, exit at settlement |
| Frequency | about 50 cycles a year an index while weeklies existed; fewer when gated or skipped |

```factory
id: EDGE2-F1-WC-G0
version: 1
trial: 112
experiment: edge2-f1-weekly-vrp-gate-2026-10-25
description: "EDGE2 F1 WC G0: weekly short iron condor, always (no gate) (exploratory)"
question: edge2-f1-weekly-vrp-gate
hypothesis: yes
measurement: no
data_sets: ["NIFTY weekly options | NSE daily closes | Feb 2019 - 9 Oct 2026", "BANKNIFTY weekly options | NSE daily closes | 2019 - 13 Nov 2024", "FINNIFTY weekly options | NSE daily closes | first weekly - Nov 2024", "MIDCPNIFTY weekly options | NSE daily closes | first weekly - Nov 2024"]
measures: "mean net per trade after C1's charges and the Rs 1 pad, one lot, held to settlement (protocol sections 7-9)"
```
