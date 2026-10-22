# Story MS-P1: the market school pilot

**Repository:** trading · **Lane:** 1 for every part that decides, fills, exits, records or reports (each part's lane
below) · **Size:** L, split into 9 parts plus one blocked part · **Builder:** session_01CmKJ6taCLzfEGg7wt6RC4N ·
**Orchestrator:** session_01VG1RqxLFUVdvvPuMRYZtDH · **Sources:** response 327 revision 2 (agreed design, stage P1),
response 325 (target design: sections 3, 4.1, 4.2, 5.1, 9.1, 9.3, 9.5, 9.9, 9.14, 9.19-9.21), DESK_DECISIONS "Market
school approved" and "NSE terms and Groww terms (P0 probe 2)", `research/school/probes/` (P0), `research/edge1/RESULTS.md`.

**Description:** As the portfolio manager, the statistician and the risk manager, I want a small fleet of rule
drivers and control drivers to make one sealed paper decision on each of five index option roads at the 15:00 slot
every session, each driver in its own Rs 20 lakh paper account under the same safety laws, so that after 30 valid
counted sessions (P2) the owner sees honestly, per road and per driver, whether any rule beats doing nothing and a
random driver after every cost. Research and paper trading only: nothing here places, modifies or cancels an order.

**What to expect [strong evidence for the past, reasoning only for the future]:** 98 counted trials found no simple
option rule that beat costs inside the Rs 10,000 cap (EDGE1: every NIFTY variant lost Rs 632-2,085 a trade; the one
run-1 passer, BANKNIFTY iron fly TP50, lost Rs 337 a trade in run 2). Most pilot drivers will lose a little after
costs. The pilot's job is to measure, not to make money; the banner is red or amber every day by design.

## 1. Facts the design rests on (checked on `main`, 22 Oct 2026)

| Fact | Evidence | Label |
|---|---|---|
| BANKNIFTY, FINNIFTY, MIDCPNIFTY 3 pm captures exist from 19 Oct (3 sessions), NIFTY monthly from 13 Oct, NIFTY weekly from 22 Oct (1 session) | `research/data/quotes/groww/derivatives/quote-snapshots*/2026/10/*.meta.json` | strong |
| Each capture records two monthly expiries (27 Oct and 23 Nov on 22 Oct); the weekly capture the two nearest weeklies (3 and 9 Nov) | the sidecars' `expiries` | strong |
| Capture times: NIFTY 14:55-15:01, the other three 15:01-15:07, NIFTY weekly 15:06-15:08 | the sidecars' `started_at`, `finished_at` | strong |
| Groww gives no quote timestamp; a quote is "valid" only with a trade that day (A4's rule) | sidecar `note`, `fno/quotes/quote_validity.py` | strong |
| No sidecar carries a lot size; lots come from A20a's daily master files (from 21-22 Oct) | sidecars; `fno/fo_masters/` | strong |
| Only NIFTY has a second (15:15, E3) capture; the other roads have one capture a session | sidecars | strong |
| The chain's `spot` is Groww's `underlying_ltp`; India VIX and futures levels in NIFTY's sidecar come from NSE | `fno/quotes/recorder.py:243,258` | strong |
| E7 settles NIFTY legs only, from NSE's F&O bhavcopy `SttlmPric` | `fno/desk/settlement.py:1-30` | strong |
| `PaperAccount(root, book)`, `FillMaker`, `price_leg`, `entry_problems` (E4c/E4d), `ExitRule`s and C2's rules exist and are book-agnostic in their interfaces | `fno/books/account.py:83`, `fno/desk/execution.py`, `pricing.py`, `entry_check.py`, `exit_rules.py`, `fno/risk/` | strong |

## 2. Hard constraints (orchestrator, 22 Oct 2026)

1. No change to `DAILY_RUN_STEPS`, the weather, v4 or any frozen file until the orchestrator says the owner signed v4's
   freeze (expected after Mon 26 Oct). Everything is built behind the school's own switch and run by its own command;
   joining the daily run is part MS-P1j, which waits.
2. The owner approved the two sections (22 Oct 2026, "Yes, add them"; DESK_DECISIONS "Market school pilot: report
   sections and brake"): built behind their own flag, off, and live only with the pilot; the signed-off pages stay
   byte-identical while the flag is off.
3. Existing captures only: no new Groww or NSE read, no new endpoint. No futures, calendars, diagonals, AI drivers,
   stocks or extra slots.
4. Hard lines: no order path anywhere in `fno/school/` (a test lists its imports); no secret in a file; Slack only
   through the existing `AlertSender` and only when a part says so; no scheduled task created or changed.

## 3. Design (new package `fno/school/`, one `wiring.py` per sub-package)

| Sub-package | Interface | Reuses |
|---|---|---|
| `roads/` | `Road` (code, underlying, expiry kind, slot dataset), `RoadDay` (session, expiries in use, dated lot, strike step, snapshot ID or closure), `RoadCatalogue.day(session) -> list[RoadDay]`, `LotSource`, `ExpirySource` | A4/A4c/A4f sidecars and canonical markers, the hash-checked quote store (`build_quote_store`), A20a lots, A7 calendar, `expiry_listing` |
| `quality/` | `RoadQualityGate.check(road_day, snapshot) -> RoadStatus` (open, or closed with one reason code); `CaptureGateReport` | A4's `quote_validity`, C3/C4 checks (`fno/checks`), EDGE1's impossible-price rule |
| `drivers/` | `Driver.decide(road_day, snapshot, history) -> Decision`; `RuleDriver(card)`; `NothingDriver` (N0); `RandomDriver` (RC1, seeded) | D2's `CandidateBuilder` (widest width under the cap), D6 version rows |
| `safety/` | `SafetyLaw.check(proposal, account_view, day) -> LawResult`; `SafetyLaws` runs every law, all reasons kept | C2's `MaxLossPerTrade`, `BucketCap`, `OpenRiskCap`, `NewRiskPerDay`, `MarginRoom`; C4's naked-leg and price checks |
| `accounts/` | `DriverAccounts.for_driver(version) -> PaperAccount` | `fno/books/account.py`, `lock.py`, E2c's `PrivateFiles` |
| `execution/` | `SchoolFills` (entry and exit at the slot's touch), `SchoolSettlement` (expiry) | E4's `price_leg`, E4c/E4d's `entry_problems`, `FillMaker`, `closing_quotes`, `ExitRule`s, E7 generalised by an `IndexSettlementSource` |
| `dashcam/` | `DashcamStore` (write-once), `DecisionRecord`, `OutcomeRecord`, `Seal` | O9's `DataStore` (Drive plus receipts), `RawFileConflict` |
| `tickets/` | `TicketBook` (1-lot virtual trades), `OpportunityCounts` (eligible, fillable, executed) | the same pricing and laws |
| `fleet/` | `FleetRunner.run(session, mode)`: every driver on every road, each isolated, a time limit each | A16's observer-group isolation |
| `reports/` | `SchoolSection` (08:50 "Today", 20:05 "How did today go"), `Banner` (red, amber) | FL1-1d's section interface |

Composition: `fno/school/wiring.py` builds the fleet for `python -m fno school run` (and later for the daily run).
A driver is a frozen card file plus one D6 row; a new driver needs no engine code.

### 3.1 Roads (5) and the 15:00 slot

| Road | Capture | Expiry used |
|---|---|---|
| NIFTY-M | A4 canonical NIFTY monthly (14:55-15:10) | the two recorded monthlies |
| BANKNIFTY-M, FINNIFTY-M, MIDCPNIFTY-M | A4c canonical (15:01-15:13) | the two recorded monthlies |
| NIFTY-W | A4f canonical NIFTY weekly | the two recorded weeklies |

"The 15:00 slot" is each road's canonical capture of the session. A position can be entered, exited or marked only in
an expiry its road records that day; a position whose expiry leaves the capture before it closes is settled (E7) or
marked "unmarked", never priced from anything else.

### 3.2 Drivers and controls (cards frozen in MS-P1g before day 1; numbers are first guesses, reasoning only)

| Code | Family | Roads | Entry | Structure | Exit |
|---|---|---|---|---|---|
| CS1 | capped seller | 4 monthlies | spot above (below) its 20-session mean of 15:00 spots, 20-45 days to expiry | bull put (bear call) credit spread, short strike 1 expected move out, widest width under the cap | 50% of credit, loss 2x credit, or 10 sessions |
| DB1 | debit buyer | 4 monthlies | 20-session realised volatility of 15:00 spots above the implied move from the ATM straddle | bought iron fly (long ATM straddle, short wings), debit at most the cap | +100% of debit, 10 sessions, or 5 days before expiry |
| DR1 | directional debit spread | 4 monthlies | 15:00 spot at a 20-session high (low) | bull call (bear put) debit spread, 1 step out | +80%, 10 sessions, or spot back through the 20-session mean |
| WS1 | weekly expiry seller | NIFTY-W | 1-3 sessions before the nearest weekly expiry | iron condor, shorts 1 expected move out, widest wings under the cap | 50% of credit, loss 1.5x credit, or expiry (settled) |
| PS2-4 | width ladder (one family, three versions) | 4 monthlies | 30-45 days to expiry, no open position of the version on that road | iron condor, shorts 1 expected move out; narrow, mid, widest wings under the cap | 50% of credit, or 21 days held |
| REF | reference rule, one per road | all 5 | every session the road is open | short iron condor at 1 expected move, widest wings under the cap, nearest eligible expiry | held to expiry (settled) |
| PS5 | control, measurement only | BANKNIFTY-M | EDGE1's SF TP50 as frozen | iron fly | 50% TP, 21 days |
| KL1 | control, measurement only | NIFTY-M | EDGE1's NIFTY SC3 EXP as frozen | iron condor | expiry |
| RC1 | random control | all 5 | every session the road is open | a random structure of the families above, random direction and short strike within 10 steps of the money, seeded by SHA-256(session, driver, road), same caps | the twin family's exit |
| N0 | do nothing | all 5 | never | none | none |

- **Expected move** = the mid of the ATM straddle of that expiry at the snapshot (model-free, one rule for every
  index; no VIX, which only NIFTY has and from NSE).
- **History** = the road's own recorded 15:00 spots (the captures); a driver needing 20 sessions says "no trade: not
  enough history" until it has them (BANKNIFTY, FINNIFTY, MIDCPNIFTY reach 20 sessions about 16 Nov). No new read.
- Sizing (325 section 4.1): 1 lot, widest width whose maximum loss with every charge and the Rs 1 pad is at most
  Rs 10,000; at most 5 new trades per driver per slot, ranked by the card's frozen score; every other fired road is a
  ticket. PS5, KL1, RC1 and N0 are never ranked, recommended or shown as candidates.

### 3.3 Safety laws (325 section 9.1, 327 item 8; only these stop a paper trade)

1. Protected structures only: every sold leg covered by a bought leg of the same type and expiry (C4).
2. Maximum loss at most Rs 10,000 including every charge and the pad (C2 `MaxLossPerTrade`).
3. C2 caps per driver account: bucket Rs 30,000, open risk Rs 1.5 lakh, new risk Rs 50,000 a day, margin room
   within the Rs 20 lakh (C2's own rules on the driver's account; never resizing a trade).
4. Daily stop: a driver whose realised plus marked loss since the previous session's slot reaches Rs 25,000 opens
   nothing more that session; planned exits continue; a close that reduces risk is allowed only at valid two-sided
   quotes; a fill is never invented.
5. Quote gate: every leg valid and two-sided by A4's rule, its displayed size covering the units (E4d, per account),
   and every protective leg sellable back (E4c).
6. No record, no trade (325 section 9.14): a decision whose seal is missing or late is refused.
7. Driver brake (owner, 22 Oct 2026, DESK_DECISIONS "Market school pilot: report sections and brake": "Pause till
   monthly review"): a driver version whose paper equity falls Rs 1.2 lakh below its high opens nothing from the next
   decision until the next monthly review lifts it by a recorded review row; no owner restart is needed; planned
   exits continue. The desk's own brake rule (C2, `owner_overrides.csv`) is unchanged and not read by the school.

### 3.4 The dashcam (write-once, Drive only, receipts in GitHub)

- **Decision record** per (session, slot, road, driver version): driver code and version, card SHA-256, road, slot,
  snapshot ID and SHA-256, road status and reason, inputs used (expected move, history window), proposal (legs, lots,
  quotes witnessed: bid, ask, sizes), credit or debit, maximum loss, costs, every safety-law result, the outcome code
  (`trade`, `ticket`, `no_trade`, `refused`, `road_closed`, `unavailable`) and a reason code. One gz JSONL file per
  slot and session for the whole fleet (probe 3: 1 file a slot, not one per record), canonical JSON so equal input
  gives equal bytes.
- **Seal:** the file is saved write-once through O9's `DataStore`, its receipt committed and pushed, and only then do
  fills run; each fill row names the decision file's SHA-256. A fill without a matching pushed seal is refused.
- **Outcome record** when a trade or ticket closes: fills, exit reason and price, gross, costs, net, return on risk
  (net / maximum loss), slippage against mid. A correction is a new record naming the old one, never an edit.
- **Privacy:** the repository gets receipts and public counts (outcome codes per road and driver per session), never a
  contract, strike, price or card internal (E2c's rule).

### 3.5 Denominator and the capture gate (defined here, frozen in MS-P1g before counting)

- **Scheduled road decision:** every (session, road, driver version) where the session is a trading day by A7's
  calendar. Every one has exactly one sealed outcome; `refused`, `road_closed` and `unavailable` stay in the
  denominator of every report.
- **Scheduled observations of a road-session:** 1 snapshot (the canonical capture: present, complete, in window,
  hash matching its sidecar, expiries matching A7's listed expiries, lot found) plus every leg in the road's frozen
  band (strikes within the card's band of the money, on the expiries the road uses). A leg observation counts when it
  is valid (A4), two-sided and not impossible (EDGE1's bounds).
- **Gate per road:** the snapshot passes on 10 of 10 consecutive sessions **and** over 95% of the band's leg
  observations pass over those sessions. A failing road stays closed for counting while others run; P2 counts 30 valid
  counted sessions after the registered first counted date.

## 4. Parts (one branch each, `story/ms-p1-<part>`; built in this order)

Every part: good, bad, boundary and empty cases per criterion; a named test that fails when its code is broken on
purpose (quality rule 4); no file or class over 350 lines; gates `pytest -n auto`, `ruff`, `check_imports`,
`check_records` before each push; self-review by independent review agents recorded in Claims.

### MS-P1a Roads and the quality gate · lane 1 (closes roads, which decides trades) · `story/ms-p1-roads`

1. `RoadCatalogue.day(session)` returns the 5 roads with expiries, dated lot (A20a) and strike step from recorded
   files only; a non-trading day returns no road; a missing capture gives `road_closed: capture_missing`.
2. `RoadQualityGate` closes a road with exactly one reason code for: capture missing, incomplete, out of window, hash
   mismatch, expiry not listed by A7 (`expiry_mismatch`), lot missing or two sources disagreeing (`lot_mismatch`), an
   impossible price in the band (`impossible_price`). Planted-fault tests for each.
3. `python -m fno school capture-gate --from --to` prints per road: sessions, snapshots passed, leg observations
   passed / scheduled, consecutive clean sessions, gate pass or not; read-only, run on the recorded October days in
   Claims.

### MS-P1b The dashcam · lane 1 (records) · `story/ms-p1-dashcam`

1. Decision and outcome records round-trip through canonical JSON; equal inputs give byte-identical files.
2. `DashcamStore` saves through O9's `DataStore`; a second save of other bytes at the same key raises (replay
   conflict) and is reported as "rule broken", never overwritten.
3. `Seal` is valid only when the receipt is committed and pushed; a fill step given an unsealed, late or other-hash
   decision refuses every fill of it (`stale_seal`). Planted-fault tests.
4. Public counts file: outcome codes only; a test runs the record scan over it and asserts no strike, price or symbol.

### MS-P1c Drivers and controls · lane 1 (decides trades) · `story/ms-p1-drivers`

1. `RuleDriver` reads a card (entry, structure, exit, roads, band, score) and builds through D2's `CandidateBuilder`;
   each family of 3.2 fires on a fixture at its threshold and not just below it.
2. N0 always seals `no_trade: n0`; RC1 is reproducible from its seed and obeys the same caps; PS5 and KL1 match
   EDGE1's frozen definitions (a test against `research/edge1/` parameters).
3. `no_trade` reasons are codes from one enum (not enough history, no expiry in window, no structure under the cap,
   rule not fired, position already open).

### MS-P1d Safety laws, accounts and fills · lane 1 (money, fills, exits) · `story/ms-p1-fills`

1. One `PaperAccount` per driver version (Rs 20 lakh), private through `PrivateFiles`; the school's risk profile in
   `config.yaml` (allowed keys added to `fno/config.py`).
2. Every law of 3.3 refuses at limit + Rs 1 and passes at the limit; all reasons kept; no law can resize a trade. The
   brake (law 7) pauses at Rs 1.2 lakh below the high, stays paused across sessions, and lifts only on a review row.
3. Daily stop: after Rs 25,000 of loss, new entries are refused, planned exits fill, a risk-reducing close fills only
   at valid two-sided quotes; a missing quote leaves the position open with `exit_waiting_quote`, never a guessed price.
4. Entries and exits fill at the slot's touch by E4/E4c/E4d; expiry legs settle by E7 generalised to all four indices
   (`IndexSettlementSource` reading the already-archived F&O bhavcopy; no new read).
5. Planted faults: missing quote (entry refused, sealed `refused: missing_quote`), impossible price, size above
   displayed quantity (refused, never partial).

### MS-P1e Tickets and the three counts · lane 1 (evaluation records) · `story/ms-p1-tickets`

1. A fired rule beyond the 5-trade limit, or on a driver stopped for the day, is a 1-lot ticket at the same quotes and
   laws (account limits relaxed only); tickets are never in an account and never summed into rupees shown to the owner.
2. Per road, driver and session: eligible (rule fired and a structure built), fillable (passes every law and the quote
   gate), executed (filled in the account). Eligible >= fillable >= executed always (test).
3. Shared displayed size (327 item 10): per contract and side, units wanted by all accounts against the displayed
   size are counted; a report never sums fills the same displayed size could not serve.

### MS-P1f The fleet runner, the switch and the command · lane 1 (decides trades; a config switch) · `story/ms-p1-fleet`

1. `school.enabled` (default false) gates every paper decision; with it off the command prints "school off" and
   writes nothing. Separate keys `school.reports` (sections, default false) and `school.first_counted` (from the card).
2. `python -m fno school run [--session D] [--dry-run]`: roads, gate, drivers, seal, fills, exits, tickets, counts, in
   that order; one driver's exception is caught, named by class, and sealed as `unavailable` for its roads; others go on.
3. Every scheduled road decision has exactly one sealed outcome (test over a whole fixture day: count = roads x drivers).
4. A rerun of the same session skips sealed decisions; it never seals twice.

### MS-P1g The frozen comparison card · lane 1 (evaluation records) · `story/ms-p1-card`

1. An R1 factory card (`fno/factory/card.py` block) names: each driver version and its matched control (N0, RC1, REF of
   its road), the 5 roads, the 15:00 slot, the cost model version (C1), the denominator of 3.5, the bands, and the
   first counted session; one D6 row per driver version in `journal/versions.csv`.
2. A decision counts only if the card's and its version row's commits are ancestors of the decision's commit (D6's
   rule); a test plants a later card and sees every decision of the day as not counted.
3. Comparisons run on one frozen common group of road-days; five roads on one day are reported as one session, not five
   independent tests.

### MS-P1h The 08:50 and 20:05 sections and the banner · lane 1 (Slack reports) · `story/ms-p1-sections`

1. Sections built behind `school.reports` (off): "Today" (open roads, planned trades with worst loss, banner) and "How
   did today go" (each trade's net, the three counts, fleet total labelled "separate hypothetical accounts, not one
   budget", refusals and closures shown).
2. `Banner` returns red (any capture or quality failure on a shown road, or no candidate) or amber; there is no green
   value in the type (test).
3. With the flag off the signed-off pages render byte-identical to today (golden-file test).

### MS-P1i Acceptance on recorded days · lane 1 · `story/ms-p1-acceptance`

1. One recorded session replayed twice in dry run (local store): every decision, outcome and count file byte-identical.
2. The planted-fault suite in one place: missing quote, expiry mismatch, lot mismatch, stale seal, impossible price,
   replay conflict; and a planted refused entry that survives replay and appears in both report sections and every
   count's denominator.
3. Zero unsealed, over-cap, invented or duplicate fills over the replayed day (asserted).

### MS-P1j Joining the daily run · lane 1 · **blocked** until the orchestrator says the owner signed v4's freeze

New step(s) after v4's in `DAILY_RUN_STEPS`, never inside its frozen files; their own status; the switch still decides.

## 5. Gap list (response 327 P1 and the orchestrator's scope)

| Requirement | Where |
|---|---|
| 5 roads at 15:00 from existing captures | 3.1, P1a-1 |
| About 5 rule families (capped seller, debit buyer, directional debit spread, weekly expiry seller, PS2-4 as one) | 3.2, P1c-1 |
| N0, RC1, one reference rule per road; PS5 and KL1 measurement only | 3.2, P1c-2 |
| Per-driver Rs 20 lakh accounts reusing fno/books and fno/desk fills (touch, E4c, E4d) | P1d-1, P1d-4 |
| Safety laws (protected, Rs 10k, Rs 25k daily stop, C2 caps, quote gate) | 3.3, P1d-2, P1d-3 |
| Dashcam sealed before fills; every decision a sealed outcome with a reason; refusals in the denominator | 3.4, 3.5, P1b, P1f-3 |
| Tickets under the same rules, three counts | P1e |
| Shared order book (327 item 10) | P1e-3 |
| Banner red and amber only | P1h-2 |
| Driver brake: pause at Rs 1.2 lakh below the high until the monthly review | 3.3 law 7, P1d-2 |
| Own switch; sections behind a flag | P1f-1, P1h-1 |
| Frozen comparison card before day 1 | P1g |
| Capture gate per road, denominator first | 3.5, P1a-3 |
| Planted faults and replay twice | P1i |
| Daily run wiring after v4's freeze | P1j (blocked) |

**Out of scope, with reason:** futures, calendars, diagonals (probe 5: no model); stocks and extra slots (P3+; NSE
terms block the survey); AI drivers (327 item 7: after a dry run); instructor, condition map, licences, recommender
top 3, simulator (P2+); E8 owner-timing fills (the pilot has no recommendation to follow); the monthly review itself (P2+;
P1 only reads its recorded row to lift a brake).

## 6. Open questions (for the orchestrator; none blocks MS-P1a or MS-P1b)

1. **Fill snapshot.** Only NIFTY has a second capture. Proposal: every road fills at its decision snapshot's touch,
   after the seal, the same rule for all five roads; reports label it "no latency: fills at the quotes the driver saw"
   [reasoning only: optimistic by about the quote drift in 1-10 minutes, unmeasured]. Using E3's 15:15 capture for
   NIFTY only would make roads incomparable. Needs the orchestrator's (and, if it judges so, the owner's) yes.
2. **NSE terms.** NSE's terms forbid using website data "for any gaming, virtual trading or simulation". The pilot
   prices from Groww only, but E7's settlement price and A4's listed-contract check read NSE's archived bhavcopy, and
   NIFTY's sidecar carries NSE levels. The owner kept the existing reads; whether paper settlement from them is a
   permitted use is the owner's call. Until answered, settlement sits behind `IndexSettlementSource` so a Groww-based
   source can replace it in one class.
3. **Reference rule.** Proposal REF in 3.2 (an always-on iron condor at 1 expected move, held to expiry) as the fixed
   per-road baseline. Alternative: the S6 random twin only. Confirm.
4. **Daily stop with one mark a session.** With one slot a day the stop is checked at the slot, before new entries,
   from the previous slot's marks to this one. Intraday losses between slots are not seen (A16 is NIFTY only). Confirm
   this reading is acceptable for P1.
5. **The monthly review that lifts a brake.** Proposal: a review row (date, driver version, decision) in a school
   reviews file, written on or after the first Saturday of the next month (325 section 6.5); no row, no lift. Who
   writes it in P1 (the orchestrator, from the owner's words) to confirm.
6. **Story numbering.** This file holds the market school's stories; later stages add sections, not new files.

## Claims

Per round, at an exact pushed SHA: which criteria are met, with the test name and the broken-code proof; the
self-review findings and what was done; a real output sample (dry run on a recorded day, counts only). Empty until
MS-P1a is built.
