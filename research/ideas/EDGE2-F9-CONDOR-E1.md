# Idea card: EDGE2-F9-CONDOR-E1

Written by `research/edge2/f9_cards.py` from `research/edge2/F9_PROTOCOL.md`. Exploratory (spent closes); events
fixed in `research/edge2/f9_events.csv` before any price was read.

## G0: the idea

| Field | Value |
|---|---|
| Id and version | EDGE2-F9-CONDOR-E1 v1 |
| Ledger trial | 127 |
| Registered research question | edge2-f9-event-iv-crush: EDGE2 F9: has a defined-risk short NIFTY or BANKNIFTY monthly iron fly or condor, opened at the close before a scheduled RBI policy decision, Union Budget or election result and closed after it, made money after real costs and more than on ordinary days? One Holm family of 4 (FLY, CONDOR x E0, E1); exploratory (spent closes); held-out FINNIFTY and MIDCPNIFTY monthlies read once after a judge; protocol research/edge2/F9_PROTOCOL.md |
| Proposed by (role or AI) and date | volatility trader and options strategist (Claude, EDGE2 builder), 25 Oct 2026 |
| Who pays and why | hedgers buying protection before scheduled announcements (the event premium) [some evidence abroad; not measured on Indian index options here] |
| Forecast it rests on | none (the A6 event calendar) |
| Instrument and structure | NIFTY and BANKNIFTY monthly options, the nearest expiry at least 5 sessions after the exit; short iron condor: sell the call and put one event-free session's implied move out, buy wings one width beyond; never a naked short leg |
| Entry rule | the close of the last session before the event day, every leg traded; exposed to the overnight gap |
| Exit rule | the close of the session after the event day |
| Size | 1 lot of the contract's market lot on the entry session |
| Worst loss in Rs | at most Rs 10,000 modelled at entry (the cap), plus charges and pads |
| Expected gross per trade, with source | the discovery run; the gross bar is Rs 820 a lot (protocol section 6) |
| Needs a reaction faster than 60 minutes? | no: close to close |
| Frequency | about 8 scheduled events a year, 2 trades each |

```factory
id: EDGE2-F9-CONDOR-E1
version: 1
trial: 127
experiment: edge2-f9-event-iv-crush-2026-10-25
description: "EDGE2 F9 CONDOR E1: event IV crush, short iron condor, exit the close of the session after the event day (exploratory)"
question: edge2-f9-event-iv-crush
hypothesis: yes
measurement: no
data_sets: ["NIFTY monthly options | NSE daily closes | 2019-2023", "NIFTY monthly options | NSE daily closes | 2024-2026", "BANKNIFTY monthly options | NSE daily closes | 2019 - 20 Oct 2026", "Event calendar (A6) | dates | 2019-2026"]
measures: "mean net per trade after C1's charges and the Rs 1 pad on 4 legs in and out, one lot (protocol sections 4-7)"
```
