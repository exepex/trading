# EDGE2 F9 results: the implied-volatility crush around scheduled Indian events

Protocol `research/edge2/F9_PROTOCOL.md`, frozen in `F9_FREEZE.md` (commit `80fdcd34`, code SHA-256 `a255a04c`). One
discovery run at `effae511` (`f9/discovery.json`). Trials 124-127, one Holm family at 0.05. **Every figure is
exploratory** (NIFTY and BANKNIFTY monthly closes spent). Rupees per trade for 1 lot of the time, C1's charges at
today's 0.15% STT on 4 legs in and 4 out, a Rs 1 pad a leg a side.

## Answer

**No variant makes money after costs, and nothing is nominated, so the FINNIFTY and MIDCPNIFTY held-out set stays
unread.** There **is** an event effect: the same trade loses Rs 140-190 less on event days than on ordinary days. It
is far too small to pay for eight orders. [strong evidence that these 4 rules lose on 55 events, 2019-2026; some
evidence for the event effect: p_event 0.002-0.039 against ordinary days, not a Holm-covered test]

| Variant (trial) | Decided trades (events) | Mean gross | Charges | Pads | Mean net | SE (event-clustered) | p | Rs 2 pad | Ordinary days, mean net | p_event, as run (pooled) | p_event, year-matched (deviation) | Win share |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| FLY-E0 (124) | 109 (55) | 175 | 307 | 334 | -467 | 87 | 1.00 | -801 | -608 | 0.008 | 0.011 | 12% |
| FLY-E1 (125) | 108 (55) | 182 | 305 | 336 | -459 | 73 | 1.00 | -795 | -617 | 0.034 | 0.044 | 20% |
| CONDOR-E0 (126) | 109 (55) | 212 | 274 | 334 | -396 | 139 | 1.00 | -735 | -588 | 0.002 | 0.0035 | 17% |
| CONDOR-E1 (127) | 108 (54) | 216 | 272 | 331 | -388 | 98 | 1.00 | -706 | -574 | 0.039 | 0.048 | 29% |

- **The bar was Rs 820 gross; the best variant earned Rs 216.** The event crush on a 1-2 session hold of a monthly
  fly or condor is worth about Rs 175-215 a lot gross; costs are about Rs 600-640.
- **By type** (FLY-E0): RBI days -Rs 558 on 90 trades; Budget days -Rs 377 on 16; the election-result trades
  +Rs 1,798 on the 3 decided ones, **+Rs 765 on all 4** with the incomplete one below (CONDOR-E0: +Rs 3,226 decided,
  +Rs 2,041 on all 4; FLY-E1: +Rs 522 on 2, -Rs 410 on 3). Three or four trades are no evidence.
- **The one incomplete exit** (kept out of the decided mean, as the protocol says) is **the 2024 election-result day's
  BANKNIFTY trade** (BANKNIFTY -8.2%): a leg did not trade at the exit close. Its net is -Rs 2,334 (FLY-E0), -Rs 2,275
  (FLY-E1) and -Rs 1,514 (CONDOR-E0); CONDOR-E1 has none. With it, FLY-E0's worst trade is that one (-Rs 2,334)
  instead of -Rs 2,147; the other variants' worst trades are unchanged.
- **Gamma.** The largest event-day moves (entry close to E's close, the near-month future): the 2024 election result
  day BANKNIFTY -8.2% (overnight gap -0.9%) and NIFTY -6.4% (gap -1.7%); the 8 Apr 2026 RBI day BANKNIFTY +5.8% (gap
  +4.6%) and NIFTY +3.9% (gap +3.0%); the 2020 Budget (a Saturday session) BANKNIFTY -3.4%. The cap held: the worst
  single trades lost Rs 2,147 (FLY-E0), Rs 3,971 (FLY-E1), Rs 4,569 (CONDOR-E0) and Rs 4,764 (CONDOR-E1), within Rs
  10,000. Every event's gap and move per variant is in `f9/discovery.json` ("gamma").
- Skips: the 2 trades of the 4 Dec 2026 RBI meeting (still ahead); 1 entry with no traded ATM straddle; 1 untraded
  leg at entry; the incomplete exit named above.

## What each role takes from it

- **Volatility trader:** the event premium is real but small at this horizon: event days beat ordinary days by about
  Rs 150 a lot on a fly. Most of a monthly option's vega is not released in one session.
- **Tax and cost accountant:** eight orders at today's charges plus pads cost about Rs 600-640. A one-day option trade
  in Indian index options cannot pay that from a Rs 200 edge.
- **Statistician:** p_event is a control comparison, not the registered test; the Holm family (mean net > 0) fails
  everywhere (p 1.0). The election-day gains rest on 2-3 trades.
- **Risk manager:** the Rs 10,000 cap is far from binding at these widths; the worst event day (2024 election) cost
  Rs 885-2,334 a fly.
- **Portfolio manager:** nothing goes forward. With F1, F6 and F8, four families now say the same thing: at one lot,
  today's charges and slippage are larger than the premia these simple rules can harvest.

## Limits

- Daily closes: entries and exits at NSE's closing prices; a pad of Rs 1 a leg a side (Rs 2 reported).
- The 2021 and 2022 Budgets are not in the sample: A6's official announcement dates (30 and 31 Jan) are not before
  their entry sessions, and the pre-registered point-in-time rule was kept, though 1 February was widely expected.
- The control days are ordinary sessions at least 2 sessions from any event, the same rules and the same costs.
- No G1 row is logged: the factory reads G1 inputs only from the idea card, and adding them after the freeze is what
  judge 642 found against (S1). The protocol's own decision (Holm, p_event, the bar) is final for F9's versions.

## Deviations

- **The ordinary-day control pooled all years** (judge 668 S1). Protocol section 7 registers control draws from the
  "same years" as the events; `summary.event_control_p` drew from every control day of 2019-2026 together. The run's
  figures are kept as run; the year-matched values (the same seed, each draw taking as many control days from each
  year as there were events traded that year) are reported beside them: 0.011, 0.044, 0.0035 and 0.048 for FLY-E0,
  FLY-E1, CONDOR-E0 and CONDOR-E1 (pooled: 0.008, 0.034, 0.002, 0.039). Recomputed by the builder from the frozen run's
  rows; judge 668's own computation gives the same four values. Neither changes the answer: nothing passes Holm.
