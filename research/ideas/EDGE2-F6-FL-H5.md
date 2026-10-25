# Idea card: EDGE2-F6-FL-H5

Written by `research/edge2/f6_cards.py` from `research/edge2/F6_PROTOCOL.md`. Exploratory; research only while
futures are on hold (protocol section 2).

## G0: the idea

| Field | Value |
|---|---|
| Id and version | EDGE2-F6-FL-H5 v1 |
| Ledger trial | 118 |
| Registered research question | edge2-f6-participant-oi-futures: EDGE2 F6: does the FII or client net index-futures position in NSE's participant OI file predict the next 1 or 5 NIFTY futures sessions, traded from the next open, after real costs? One Holm family of 6 (FD, FL, CD x H1, H5); discovery to 2024 (exploratory), held-out 2025-26 read once after a judge; research only (futures on hold); protocol research/edge2/F6_PROTOCOL.md |
| Proposed by (role or AI) and date | derivatives flow analyst and quant (Claude, EDGE2 builder), 25 Oct 2026 |
| Who pays and why | the other side of FII positioning flow, or retail clients in the fade [some evidence that FII positioning and retail losses are real; reasoning only that a 1-5 session edge survives costs] |
| Forecast it rests on | none (FII net index futures against its 20-session mean, followed) |
| Instrument and structure | NIFTY future, the nearest expiry on or after the exit session; one lot long or short |
| Entry rule | day t's participant OI file (published after the close) decides; enter at session t+1's open |
| Exit rule | from the next session's open to the close five sessions after the signal, at that session's close |
| Size | 1 lot of the contract's market lot on the entry session |
| Worst loss in Rs | unbounded in principle (a future has no cap): reported per trade; research only, never traded under the hold |
| Expected gross per trade, with source | discovery run, added before G1 |
| Needs a reaction faster than 60 minutes? | no: an open-to-close daily rule |
| Frequency | about 250 signals a year (one a session) |

```factory
id: EDGE2-F6-FL-H5
version: 1
trial: 118
experiment: edge2-f6-participant-oi-futures-2026-10-25
description: "EDGE2 F6 FL H5: FII net index futures against its 20-session mean, followed, from the next session's open to the close five sessions after the signal (exploratory, research only)"
question: edge2-f6-participant-oi-futures
hypothesis: yes
measurement: no
data_sets: ["Participant open interest (A8) | NSE daily files | 2019 - 2024", "Participant open interest (A8) | NSE daily files | 2025 - 2026", "NIFTY near-month future | NSE daily open and close (F&O files) | 2019 - 2024", "NIFTY near-month future | NSE daily open and close (F&O files) | 2025 - 2026"]
measures: "mean net per trade after the futures charges and a 1-point pad, one lot (protocol sections 4-6)"
```
