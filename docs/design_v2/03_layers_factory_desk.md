# 3. Layers 4-5: strategy factory and paper desk

## 3.1 Layer 4: strategy factory

**Purpose.** Test many ideas, each exactly once, under rules written before the data is read, and kill most of them
cheaply. The factory is honest bookkeeping for search: every attempt, pass or fail, is a row in `research/ledger.csv`
(52 rows on 15 Oct 2026), so the owner always knows how many tries stand behind any "winner".

**The pipeline (each gate is a recorded step; an idea stops at the first gate it fails).** Every idea gets a ledger row
at G0, with status `idea`, so ideas stopped by the screen still count in the trial total (ChatGPT review 95, accepted).
The G1 screen is a cheap feasibility observation, not an outcome test; the outcome test is G5, registered at G4.

| Gate | What is checked | Who | Output |
|---|---|---|---|
| G0 Idea card | Who pays and why; the forecast it rests on (if any); structure; entry, exit, size; worst loss in Rs; expected gross per trade with its source | any role or AI | `research/ideas/<id>.md` |
| G1 Feasibility screen (cost wall) | A documented gross-payoff distribution per trade, or a conservative bound, with its source; full round-trip cost (C1 charges plus pads from measured half-spreads, A4 and A16 data); **expected net after costs and tail losses above zero on the conservative bound**; for volatility ideas, the implied-volatility-point edge per vega per lot needed to clear costs. The ratio "gross at least 2 x cost" is shown as a labelled warning ("thin margin"), never a pass mark | code (CostWall) | pass, or ledger status `screened_out` with the numbers; a pre-registered counterexample study may still test it |
| G2 Data spend | The data the test would use has not been spent by an earlier trial (data-spend register, below); if spent, the test is labelled exploratory and cannot pass | code | fresh or exploratory |
| G3 Sample plan | n needed = (z x SD / expected net)^2 from the idea's own SD estimate; the time that takes at the idea's frequency | statistician | registered n and date; above 3 years only if the idea rests on a forecast that already beat its baseline (rung 1) |
| G4 Registration | Protocol text, code hash, ledger row committed before any result | B4 ledger guard | ledger row |
| G5 Test | Historical (fresh data only) or forward shadow (experiment 2 model: decisions recorded, never in a book) | code | result, once; no retuning |
| G6 Verdict | Pass mark from the registration; a fail is final for that version; a variant is a new idea and a new row | judge | verdict in the ledger |

**The cost wall in numbers (strong evidence, our data).** Four-leg monthly NIFTY trade: Rs 810-940 a round trip;
weekly held to expiry: Rs 100-384; two-leg spread: about Rs 410 (response 92). The condor's best measured gross was
+978 (seen data) and +408 (holdout), so its expected net after costs was +153 and -406. On the conservative bound (the
holdout) the screen stops the monthly condor; the 2x warning would also have flagged both periods (about Rs 1,640
needed). This is hindsight, since the costs were not measured this precisely before experiment 1, but it shows what
the screen is for. Expected net includes the tail: an idea whose average gross is twice its cost can still lose on
average once rare maximum losses are counted, which is why the ratio alone is not a pass mark.

**Data-spend register (new, `research/DATA_SPEND.md`).** One row per data set (instrument, period, price type) with
the trials that used it. Spent today: NIFTY monthly options daily closes 2019-26 (experiment 1 and desk meetings);
NIFTY weekly options daily closes Feb 2019 - Oct 2026 (response 94); NIFTY and VIX daily history (predictors, many
trials). Fresh today: stock option chains around results (never used); 15:00 bid/ask quotes from 13 Oct 2026 (forward);
15-minute quotes (not yet recorded); participant OI history (A8, untested).

**Multiple testing.** Within a registered batch, Holm's correction across the batch's primary tests. Across the
factory, every report shows "trial k of K" and the number of false passes expected by chance at the pass level (for
example 52 trials at 1% one-sided gives about 0.5 expected false passes). A single pass among many fails is treated as
"needs a second, independent test" before paper.

**First ideas queue (labelled; none is a candidate yet).**

| Idea | Rests on | Data | Status and label |
|---|---|---|---|
| V1 Sell protected premium only when the volatility forecast is well below implied | v4 forecast skill (rung 1) | 15:00 quotes, forward | waits for rung 1; reasoning only |
| V2 Buy protected movement (debit spreads, straddles within the cap) when forecast is well above implied | v4 forecast skill | same | waits for rung 1; reasoning only |
| R2 Stock options around results: implied move vs realised move | stock chains + results dates | fresh history (2019-26) | feasibility first (costs, liquidity, lot values vs the Rs 10,000 cap); some evidence that event premia exist abroad, none here |
| E3 Event premium (RBI policy, Budget): implied before vs after | NSE chains, events calendar | NIFTY history is spent: forward only | cost wall first; reasoning only |
| P1 Put spread on the skew (response 92 option A) | skew, drift | forward only | model negative (-243 a trade); not now |
| O1 Positioning extremes (participant OI) | A8 | history untested | after 20 measured release days |

**Interfaces.** `IdeaCard` (data class), `CostWall` (rule; strategy), `DataSpendRegister`, `SamplePlan`, existing
`Policy`, `Condition`, `Feature`, `ExitRule` and B4's ledger guard; B2's `Structure` must accept any number of legs
(story STR1). Wiring: a new `fno/factory/wiring.py`.

**Evaluation metric.** For the factory itself: share of ideas stopped at each gate, time from idea to verdict, and the
expected-false-pass count. For an idea: its registered pass mark only.

**Failure modes.** Forking paths (ten variants of one idea counted as one: each variant is a row); an optimistic cost
model (pads come from measured half-spreads and are refreshed monthly); survivorship in stock studies (point-in-time
F&O lists from NSE files, A12's past-member rule); spent data reused (G2); a "pass" built on impossible exits (the
width-bound check, owner decision of 13 Oct 2026, "Simulator: a long structure whose debit is at least its width cannot
win").

## 3.2 Layer 5: paper desk

**Purpose.** Trade approved strategies on paper as if the owner did, with real costs, and record shadows for
candidates, so the scoreboards show what the owner would really have earned.

**Already built (keep):** accounts and lock (E1), fills and exits (E4), expiry settlement (E7), costs and tax ledgers
(C1), risk manager and margins (C2, A14), data and hard-validity checks (C3, C4), playbook and decision records (D1-D3,
D6), packs (E2), timetable (E3), Book 1 (E5), scorecard and pause rules (E6).

**Changes in v2.**
1. **Account Rs 20 lakh, Rs 10,000 maximum loss per trade** (owner, 14 Oct). Config `profiles.paper` changes through a
   lane-1 change to C2's settings. The open-trade limit and drawdown brake are rescaled by risk bucket
   (`06_risk_and_alerts.md`), owner decides the numbers.
2. **Fills at the owner's action time** (story E8). A card sent at time T fills at the first quote snapshot at or after
   T + R, where R is the owner's declared reaction time (proposal: 15 minutes in market hours; reasoning only), at the
   bid for sells and the ask for buys, plus the pad. If T + R is after 15:25 IST, or the owner's availability calendar
   says "away", the fill is at the next session's first snapshot after 09:30 plus R. Exits from the monitor follow
   the same rule. Today's E4 fills at the execution snapshot (15:15); E8 adds the owner-timing rule beside it, and the
   scoreboards show both, so the cost of human delay is measured.
3. **Structures.** Bought options, vertical spreads, and protected four-leg structures (story STR1 opens B2, C4, D1, D2
   and A14 to one- and two-leg shapes). Never a naked short leg: C4 refuses any position whose maximum loss is not
   fixed at entry.
4. **Tax and benchmarks.** Every result is shown before tax, after C1 costs, and after 31.2% tax on the year's net F&O
   profit. Beside it, two benchmarks on the same capital (story S2 change):
   - **Do nothing:** a NIFTY 50 index fund (NIFTY 50 total return index, minus a 0.05% a year expense ratio; long-term
     capital gains tax at 12.5% above Rs 1.25 lakh a year on sale);
   - **Cash:** a liquid-fund rate (proposal: the RBI repo rate as a proxy, taxed at slab).
   An F&O result is reported per rupee of capital tied up (funds at entry, C2), so the comparison with an index fund on
   the same capital is fair. Reasoning only for the proxies; owner decides.
5. **The owner never overrides on paper.** A paper trade cannot be skipped, resized or closed by hand. The owner's own
   ideas go to the Manual paper account (MA1), which is never part of any scoreboard. The only owner action on the
   books is a safety stop (S1 `immediate_pauses`), which is recorded and counted against the book.
6. **Fitted to the owner.** The desk reads an owner profile (capital, loss cap, reaction time, availability, and later
   the real-money discipline record: did the owner follow the card?). The profile is versioned like a rule.

**Interfaces.** Existing: `ExecutionSnapshotSource`, `ExitRule`, `ExitRules`, `RiskRule`, `ExposureRule`,
`OrderBuilder`, `AccountSync`. New: `OwnerTiming` (when the owner could act), `Benchmark` (index fund, cash: one class
each), `TaxModel` (31.2% slab today). Wiring: `fno/desk/wiring.py`, `fno/scoreboard/wiring.py`.

**Evaluation metric.** S1's primary measure (net per unit of risk at stake after all costs), the worst loss, the
largest drawdown, the result against both benchmarks, and the fill error (paper fill vs the next real snapshot).

**Failure modes.** Optimistic fills (bid/ask plus pad, never mid); stale marks (quotes, not closes, for live exits:
response 92 found two cap breaks on stale closes in 2019); margin underestimated (A14 plus the 1.45 stress
multiplier); expiry mishandled (E7); correlated losses across strategies (risk buckets, section 6.2).
