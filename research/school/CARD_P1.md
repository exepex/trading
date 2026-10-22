# Idea card: CARD_P1 market school pilot, frozen comparison (measurement: never promoted)

Template: `research/ideas/TEMPLATE.md`. The pilot (story MS-P1, `docs/stories/MS-market-school.md`; response 327
revision 2; owner "approved", 22 Oct 2026) is a **measurement**: it measures, per road and per driver, whether any rule
beats doing nothing and a random driver after every cost. It shows no edge by itself, gives no licence and no green
banner, and places no order. Counting starts on the first counted session below; P2 reads 30 valid counted sessions.
Labels: **strong evidence**, **some evidence**, **reasoning only**.

## G0: the idea

| Field | Value |
|---|---|
| Id and version | CARD_P1 v1 (a changed driver, road, cost model, denominator or slot is a new card version, never an edit) |
| Ledger trial | 99 (the next free number at writing; the ledger row is written by `factory register` and may move) |
| Registered research question | Does any pilot rule driver beat N0 (do nothing), RC1 (random) and REF (the road's reference rule) after every cost, per road, over 30 valid counted sessions? Descriptive, with uncertainty, no licence (response 327 P2) |
| Proposed by (role or AI) and date | portfolio manager and statistician, market school pilot (Claude MS-P1h builder), 22 Oct 2026 |
| Who pays and why | none claimed. EDGE1: 24 variants (trials 71-98) found no edge after costs; this does not prove no edge exists (**strong evidence** for those 24 variants); most pilot drivers are expected to lose a little after costs (**reasoning only**) |
| Forecast it rests on | none |
| Instrument and structure | NIFTY, BANKNIFTY, FINNIFTY, MIDCPNIFTY monthly options and NIFTY weekly options; defined-risk structures only (credit and debit spreads, iron condors, iron flies), never a naked short leg |
| Entry rule | each driver's own card at the road's 15:00 slot (its canonical capture of the session), fills at that snapshot's touch after the seal; no latency (**reasoning only**) |
| Exit rule | each driver's own card; held to expiry where the card says so (settled at intrinsic against NSE's final settlement price) |
| Size | 1 lot; widest width whose maximum loss with every charge and the Rs 1 pad is at most Rs 10,000; at most 5 new trades per driver per slot |
| Worst loss in Rs | at most Rs 10,000 a trade (C2 refuses above); each driver account Rs 20 lakh with the daily Rs 25,000 stop and the Rs 1.2 lakh brake |
| Expected gross per trade, with source | none stated: a measurement has no expected edge |
| Needs a reaction faster than 60 minutes? | No: one decision a session |
| Frequency | up to one decision per road, driver and session; 30 valid counted sessions |

## What this card freezes (before any counted session)

**How counting is judged.** Each decision is judged against the card version and the first counted session in force at
its own commit: the card's last commit, and `config.yaml` as committed, strictly before the decision's commit. A later
card version applies only to later decisions and never re-counts or un-counts an earlier one. A changed cost model,
road, slot, band, denominator or driver is a new card version, forward only.

### 1. Rule versions and their matched controls

A decision counts only for a driver version registered in D6's `journal/versions.csv` (book `school:<driver id>`,
component `card_sha256` = the SHA-256 of the driver's card file in `research/school/cards/`), in a commit strictly
before the decision's own commit; a changed driver card SHA-256 refuses counting (`CountingRule`,
`fno/school/registration/counting.py`).

| Driver id | Family | Roads | Matched controls on each road it trades |
|---|---|---|---|
| CS1@1 | capped seller | the 4 monthlies | N0@1, RC1@1, REF@1 |
| DB1@1 | debit buyer | the 4 monthlies | N0@1, RC1@1, REF@1 |
| DR1@1 | directional debit spread | the 4 monthlies | N0@1, RC1@1, REF@1 |
| WS1@1 | weekly expiry seller | NIFTY-W | N0@1, RC1@1, REF@1 |
| PS2@1, PS3@1, PS4@1 | width ladder, one family of three versions | the 4 monthlies | N0@1, RC1@1, REF@1 |

PS5@1 (EDGE1 BANKNIFTY SF TP50, ledger trial 94, road BANKNIFTY-M) and KL1@1 (EDGE1 NIFTY SC3 EXP, ledger trial 76, road
NIFTY-M) are measurement-only controls (EDGE1's rules as frozen, their data spent; this card adds no trial for them), and N0, RC1 and REF are controls: none is a
candidate and none is ever ranked or recommended. Their card SHA-256s and the D6 rows are written when MS-P1e's cards
are frozen; until the rows exist nothing counts (`version_not_registered_before`).

### 2. Roads, slot and fills

| Item | Frozen value |
|---|---|
| Roads | NIFTY-M, BANKNIFTY-M, FINNIFTY-M, MIDCPNIFTY-M, NIFTY-W (the existing canonical captures only; no new read) |
| Slot | 15:00: each road's canonical 3 pm capture of the session |
| Fill rule | the decision snapshot's touch (ask to buy, bid to sell), after the seal; "no latency [reasoning only]" |
| NSE terms | open question: NSE's "virtual trading or simulation" terms; settlement reads the already-archived F&O bhavcopy |

### 3. Cost model

C1's charges (`fno/costs.py`), read from the `charges:` block of `config.yaml` (9 lines, SHA-256
`5177fb366c49ac3b5ba420c34930a0978eefe463a525b24d5bee79982d1e1889` at this card's freeze) plus the Rs 1 pad. A
changed charge schedule is a new card version that applies to later decisions only.

### 4. Denominator and capture gate

- **Scheduled road decision:** every (session, road, driver version) on a trading day by A7's calendar. Each has
  exactly one sealed outcome (`trade`, `ticket`, `no_trade`, `refused`, `road_closed`, `unavailable`) with a reason;
  `refused`, `road_closed` and `unavailable` stay in the denominator of every report.
- **Original opportunities:** a ticket (a fired rule beyond the 5-trade limit or on a stopped driver) is counted in
  the eligible, fillable and executed counts, never summed into rupees and never in an account.
- **Band (one source: part b's `DEFAULT_BAND_STEPS` in `fno/school/quality/band.py`, 10 strike steps):** the strikes
  within 10 steps of the money on each side (the money: the strike nearest the spot on the nearest expiry), on every
  expiry the road records that session. The card freezes b's number and does not define its own: if the constant
  moves, this card is out of date and a new card version is needed (`test_the_cards_band_is_the_quality_gates_constant`
  checks it once b is on the branch). The band is the gate's observation set only: it measures whether two-sided quotes
  were captured (capture completeness), not whether every leg a driver may trade is inside it. Law 5 checks each traded
  leg when the trade is made, and a refusal stays in every denominator; part j's report shows, per road, the share of
  trades refused for quotes, so thin far legs stay visible. Every driver card's `band_steps` must be 10 (RC1's widest
  short strike, as b notes). Whether 10 steps is wide enough for the 1-expected-move shorts is **reasoning only**.
- **Impossible price (one source: part b's `impossible_keys` in `fno/school/quality/prices.py`, EDGE1's rule, protocol
  revision 7, judge 473.1):** a vertical (a sold leg with the bought leg of its type) is impossible when no price
  inside both legs' bid-ask ranges can put it between 0 and its width; each leg also may not break the bounds no market
  can break (a call's bid above the index, a put's bid above its strike). Both legs of a broken vertical are flagged.
- **Gate per road:** the snapshot passes (present, complete, in window, hash matching, expiries matching A7's, lot
  found) on 10 of 10 consecutive sessions **and** over 95% of the band's leg observations are valid (A4), two-sided
  and not impossible over those sessions. A failing road stays closed for counting while others run.
- **Unit of comparison:** the common group of road-days on which a driver and all its matched controls have a counted
  decision, computed from the counted decisions at report time and per card version, so it cannot be chosen after the
  results; the five roads of one session are one cluster, so a session counts as one session, not five tests
  (`fno/school/registration/clusters.py`).

### 5. First counted session

**Not set.** It is set by the orchestrator when P1's 10-session gate passes, as `school.first_counted` in
`config.yaml`. A decision counts only if `config.yaml`, as committed in the decision's own history, holds the value
and the commit that first wrote that value is strictly before the decision's commit (`first_counted_not_frozen_before`
otherwise): moving the date later or earlier afterwards never re-counts or un-counts a past decision. Until it is set
nothing counts (`no_first_counted_session`).

## Machine block (story R1)

Read by `python -m fno factory` (G0 fields only: a measurement is never screened).

```factory
id: CARD_P1
version: 1
trial: 99
experiment: market-school-pilot-2026-10-22
description: "Market school pilot P1: rule drivers vs N0, RC1 and REF on five index option roads at 15:00; measurement, never promoted, no licence"
question: market-school-pilot-vs-controls
hypothesis: no
measurement: yes
```

## G1-G6

| Field | Value |
|---|---|
| Feasibility screen | Not applied: a measurement is never screened |
| Data spend | Forward only: each session's existing 15:00 captures after the first counted session; PS5 and KL1 reuse EDGE1's frozen rules, spent data is not re-read |
| Sample plan | 30 valid counted sessions, then a descriptive review with uncertainty (response 327 P2); no licence from 40 trades; a plan needing years says "not established" |
| Pass mark | none |
| Result and verdict | none (a measurement has no verdict) |
