# Protocol: EDGE2 F9, the implied-volatility crush around scheduled Indian events

Story: EDGE2 edge search (owner, 25 Oct 2026: "no proven edge: let's try to find them using dry runs"); the
orchestrator's conditions of 25 Oct 2026 (block `edge2-f9`: trials 124-127, as the factory needs consecutive numbers; 128-132 released).
Builder: session_01VhppcYHXq3yTJBV2UnsWSs. Written and committed **before any option price of this study is read**.
EXPLORATORY: it can nominate for a judged held-out read and then the school's forward test, never prove.

## 1. The question

Does a defined-risk short position in NIFTY's or BANKNIFTY's monthly options, opened at the close before a scheduled
RBI policy decision, a Union Budget or a general-election result and closed after it, make money after every cost,
and more than the same trade on ordinary days?

Why it could work [some evidence: implied volatility rises into scheduled announcements and falls after them, the
event premium, documented abroad (Beber and Brandt 2006 on macroeconomic news in US options; Dubinsky, Johannes,
Kaeck and Seeger 2019 on earnings announcements); not measured on Indian index options here]. Who pays: hedgers who buy protection before the
event. Why it could fail: the realised move on the day (gamma) can exceed the premium lost by the options, as on the
2024 election result day (NIFTY about -5.9%) [strong evidence for that day's move; NSE closes].

**Gross bar, stated now (section 6): Rs 820 a lot a trade.** F1, F6 and F8 showed that costs decide at this
size; a structure that cannot clear this bar in gross cannot pay.

## 2. Status and data spend

- NIFTY and BANKNIFTY monthly option closes are `spent` and `exposed` (EDGE1, G13b, GR1): every discovery figure is
  exploratory.
- The event list (A6, `research/data/events/events.csv`, committed 12 Oct 2026) is `exposed` as a predictor. It is
  fixed here, before any price is read (section 3).
- **Held-out:** FINNIFTY and MIDCPNIFTY **monthly** options on the same events (no trial has read their prices),
  read **once**, only for nominated variants, only after a lane-1 judge passes the frozen rules. Caveat in every
  report: the same event days and correlated indices; it guards against instrument noise, not a regime change.

## 3. Events (fixed now)

- Every row of `events.csv` at its commit on `main` at this registration, with `scheduled = yes`: RBI MPC decision
  days, Union Budget days (interim budgets included), general-election result days. Off-cycle RBI meetings
  (`scheduled = no`) are excluded: their date was not known beforehand.
- The row is used only if its `announced_on` is before the entry session (no look-ahead).
- The registration commit lists every event used, with its date, type, `announced_on` and source URL
  (`research/edge2/f9_events.csv`, generated from `events.csv` before any price is read).

## 4. The trade

- **Entry:** the close of the last session before the event day E (regular or special). **The position is exposed to
  any overnight gap into E** (decided now, orchestrator's question): the gap is part of the event risk the premium
  pays for, and daily closes cannot fill a trade after the open honestly. Each event's gap is reported (section 5). **Exit:** variant E0 at the
  close of E's session (the first session on or after E, special sessions included, as NSE held special sessions on
  Budget Saturdays); variant E1 at the close of the next session after that.
- **Expiry:** the index's monthly expiry (an expiry with a future listed that day) with at least 5 sessions after the
  exit session; the nearest such.
- **Forward:** the same expiry's future close at entry. ATM strike K: the listed strike nearest the forward.
- **Structures (fixed now):**
  - **FLY:** sell the call and put at K, buy wings W either side.
  - **CONDOR:** sell the call nearest F x (1 + m) and the put nearest F x (1 - m), m = the event-free one-session
    implied move sigma_IV x sqrt(1 / 252) from the entry straddle (as F1's gate), buy wings W beyond.
- **Wings and the cap:** W is the widest of EDGE1's widths (NIFTY 300, 250, 200, 150, 100; BANKNIFTY x 3) with
  (W - credit) x lot <= Rs 10,000 at the trade's dated lot; none fits: `no_trade_cap`, counted.
- **Lots:** the contract's market lot on the entry session: UDiFF's board lot from 2024, EDGE1's checked circular
  schedule before (`research/edge1/LOT_CHECK.md`). (A20a's archived lot file starts on 21 Oct 2026, after these
  events.)
- **Fills:** every leg traded on the entry and the exit day, at its close; EDGE1's impossible-price rule at entry and
  exit; an exit with an untraded leg is `incomplete_exit` and kept apart from the decided mean.
- **Variants (4 trials):** {FLY, CONDOR} x {E0, E1}, NIFTY and BANKNIFTY trades pooled.

## 5. Gamma, reported for every event

The index's move from the entry close to E's open (the overnight gap) and to the exit close (per cent), its absolute size against the entry straddle's
implied one-session move, and the worst event per variant and per type (each Budget day and each election result
listed by name).

## 6. Costs and the gross bar

C1's charges at today's rates (0.15% STT) on 4 legs in and 4 out; a pad of Rs 1 a unit a leg on every order (decided),
Rs 2 reported. **Round trip, NIFTY at today's lot of 65** [arithmetic, `fno.costs`]: sell the ATM call and put at Rs 250,
buy the wings at Rs 110, exit at 90% of those prices: entry charges Rs 163, exit charges Rs 132, pads 8 x 65 = Rs 520:
**Rs 816 a trade; the gross bar is Rs 820**.

## 7. Statistics and nomination (discovery)

- Per variant: mean net per trade; standard error clustered by event (NIFTY's and BANKNIFTY's trades of one event are
  one cluster); one-sided p of mean > 0 from its normal approximation (fewer than 30 events: reported only, p = 1).
  Holm across the 4 at 0.05.
- **Control (RC1, ordinary days):** 2,000 draws of the same number of non-event sessions (no A6 event within 2
  sessions), same years, same rules, seed 20261025; p_event = share of random means >= the event mean. It asks
  whether event days are better than any day, i.e. whether there is an event premium beyond ordinary theta.
- **Nomination to the held-out read** (all four; at most 2): Holm-significant; p_event <= 0.10; mean net > 0 at the
  Rs 2 pad; mean gross above the Rs 820 bar.

## 8. Held-out read (once, after a lane-1 judge)

FINNIFTY (from its first monthly expiry) and MIDCPNIFTY (from its first) on the same events, the nominated variants
only, the same code with their own width lists (FINNIFTY as NIFTY's, MIDCPNIFTY half of NIFTY's, as F1) and lots
(F1's held-out schedule, which needs `LOT_CHECK.md` written first). Pass: Holm across the nominated at 0.05 and mean
net > 0 at the Rs 2 pad. A pass is a proposal to the owner for a forward test in the school.

## 9. Registration

Ledger trials 124-127 (block `edge2-f9`; 128-132 released by the orchestrator, 25 Oct 2026), idea cards `research/ideas/EDGE2-F9-*.md` (G0 and G2 fields
only; any result-derived input goes in no frozen card), question `edge2-f9-event-iv-crush`, alpha 0.05, DATA_SPEND
rows and `f9_events.csv`, all in one commit before any price is read.

## 10. Deviations

None yet.
