# Response 327: The market school, agreed design (for the owner's final review)

Orchestrator, 22 Oct 2026. This joins response 325 (the target design) with the corrections in review 138, response
326 and review 139. **Claude and ChatGPT agree on everything below. ChatGPT's two remaining conditions are accepted:
both check out.** Research and paper trading only: no real order is ever placed. Labels: strong evidence, some evidence,
reasoning only.

## 1. What stays from response 325 (the target)

The full school stays the long-term design:
- many drivers on many roads: the 4 indices, F&O stocks, futures and options, several times of day;
- a write-once dashcam of every decision;
- an instructor;
- the simulator, for practice only;
- forward paper trading as the only proof;
- the recommender with its banner;
- the 20 gap items and items 21-32.

What changed is the **order of building** and the **statistics**, listed below.

## 2. Corrections agreed with ChatGPT

1. **Tickets** obey the same quote, lot, cost and loss rules as real paper trades. Only the account limits are relaxed. Every report shows three counts: eligible, fillable and executed.
2. **Hard road or bad driver** is measured with control drivers that drive every open road-slot. N0 does nothing; RC1 is random; one fixed reference rule runs per road. Results are paired per road, day and slot, and abstentions are kept. The control drivers obey the same quote and risk rules.
3. **Condition map v1** has three statuses only: Exploratory, Watching and Not established. "Supported" waits for:
   - a frozen test family;
   - one metric;
   - a measured false-claim rate on null data;
   - an untouched second forward window.

   Three drivers agreeing is not a replication.
4. **No licence from 40 trades.** A licence needs a sample-size plan, a one-sided 95% lower bound above zero after multiple-test adjustment, and a second forward window. Calibration is published only as a descriptive check at 100 or more outcomes over 60 or more sessions, in 5 bins. If the plan needs years, the report says "not established".
5. **Driver catalogue:**
   - PS5 and KL1 are controls only;
   - PS2-4 counts as one family, and FT4 and FT5 as one question;
   - PS8 is not fresh;
   - calendars and diagonals wait for a verified payoff and margin model.
6. **Simulator spreads** are shown as three labelled scenarios: median, 75th and 95th percentile. A bucket with fewer than 30 quoted sessions says "insufficient spread data". It stays practice only.
7. **AI drivers:**
   - transport is chosen after a 5-session dry run;
   - the first sealed answer is the scored one;
   - repeat runs measure instability only;
   - not in the pilot.
8. **Daily Rs 25,000 stop:** no new entries; planned exits continue; a close that reduces risk is allowed at valid two-sided quotes only; a fill is never invented. Fleet totals are labelled "separate hypothetical accounts, not one budget".
9. **Banner v1:** red or amber only. Changing RM1 from Book 1 to "driver version" is a separate decision for the owner and the judge. A future green would mean "eligible for the owner's own review", never "buy".
10. **Many accounts do not share one order book.** Each account's fill is measured on its own, and reports never sum fills that the same displayed size could not serve.

## 3. ChatGPT's two conditions (accepted)

- **Freeze the pilot's comparison before day 1.** Each rule version and its matched control, the roads, the cost model, the denominator, the 15:00 slot and the first counted date are registered (R1 card plus D6 rows) before the first counted session. Strategies are compared on one frozen common group of road-days. Five roads on one day are not five independent tests. [strong: statistics]
- **Separate switches.** The pilot's paper decisions, future futures trading and the capture-only reads each have their own switch. A failure in a new capture never touches v4's frozen daily routine. [strong: data integrity]

## 4. The build order

| Stage | What | Gate to the next stage |
|---|---|---|
| **P0 probes** | Groww chain fields, rate types and quotas; NSE and Groww terms for automated reading; Drive write quota; physical settlement and expiry-day margin rules; futures and calendar payoff and margin models; work-register rows | every probe answered in a dated note |
| **P0b capture probes** (only after P0 terms pass) | one futures quote and LTP probe on a small fixed list; one stock-option chain probe on a small fixed list; 5 sessions measuring completeness, empty bid/ask share, blocks and 429s, latency, Drive writes, and any effect on A16 and v4 receipts. They create no tickets, positions or claims, and use no fresh data window | 5 clean sessions, then capture volume grows within the terms |
| **P1 pilot** | NIFTY, BANKNIFTY, FINNIFTY and MIDCPNIFTY monthly options plus the NIFTY weekly at 15:00 only, from existing captures; about 5 rule drivers plus N0, RC1, the reference rule, and PS5 and KL1 as controls; dashcam; safety laws; tickets with three counts; 08:50 and 20:05 sections (red and amber); the comparison frozen before day 1 | **per road**: over 95% valid, time-bound two-sided captures on 10 consecutive sessions (a failing road stays closed while others run); zero unsealed, over-cap, invented or duplicate fills; planted faults caught (missing quote, expiry or lot mismatch, stale seal, impossible price, replay conflict); one recorded day replayed twice, identical |
| **P2 measure** | 30 forward sessions, then a descriptive review against the matched control, with uncertainty; no licence | the owner decides what to add |
| **P3+ expand** | one at a time, each with its own gate: more slots (Groww conductor); futures (after the owner's 5 futures numbers, section 5); stock options (after the terms check and 20 sessions of survey data); AI drivers (after the dry run); deeper instructor, simulator and map statuses | each stage's gate |

**Effort and dates [reasoning only]:**
- P0: about 3 builder days and 1 judge day.
- P1: about 10-18 builder days and 5-8 judge days. That is ChatGPT's 8-15 and 4-7 for NIFTY alone, plus the extra expiry, lot and quote tests for the other roads.
- Plausible start of the P1 count: late November. The real date comes from the P0 notes.
- First descriptive review: about 30 sessions after that, around mid-January 2027.

## 5. Owner decisions still needed (none blocks P0)

1. **Final review of this design** (yes, or changes).
2. **Futures numbers, needed before any futures driver starts** (not for the pilot):
   - (a) the largest planned stop loss per lot in rupees;
   - (b) the largest gap or stress loss per lot, and per futures account;
   - (c) the largest notional, margin and total open exposure;
   - (d) overnight or same day only;
   - (e) a lot that already breaks a limit is refused.

   The arithmetic, at NIFTY's 21 Oct close of 22,811: one lot is worth Rs 14.8 lakh, a 1% move is Rs 14,827, and a 5.9% gap is about Rs 87,480 [strong]. A stop never guarantees the gap limit.
3. Adding the "Today" and "How did today go" sections to the signed-off 08:50 and 20:05 pages.
4. The drawdown brake: suspend the driver until the monthly review, or wait for your restart.
5. A second Groww API key, if Groww allows one.

## 6. Not approved by anyone

- The immediate 410-road build.
- Any licence or green banner from the pilot.
- Any change to the Rs 10,000 options cap.
- Any real order.
