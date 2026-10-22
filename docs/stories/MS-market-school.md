# Story MS-P1: the market school pilot

**Repository:** trading · **Lane:** 1 for every part that decides, fills, exits, records or reports (each part's lane
below) · **Size:** L, split into 10 stories (a contracts first, b-i in parallel, j last) · **Builder:** session_01CmKJ6taCLzfEGg7wt6RC4N ·
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
   the fleet runner (MS-P1j) joins the daily run only after that.
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

### 3.2 Drivers and controls (cards frozen in MS-P1h before day 1; numbers are first guesses, reasoning only)

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

### 3.5 Denominator and the capture gate (defined here, frozen in MS-P1h before counting)

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

### 3.6 Fill rule and known limits (orchestrator's answers, 22 Oct 2026)

- **Fill rule:** every road fills at its own decision snapshot's touch (ask to buy, bid to sell), after the seal.
  Every report labels it "no latency [reasoning only]".
- **Drift diagnostic (not a fill):** on NIFTY only, for each filled leg, the touch-to-15:15 drift against E3's 15:15
  capture, so the optimism of "no latency" is measured.
- **NSE terms:** expiry settlement reads the already-archived F&O bhavcopy behind `IndexSettlementSource`.
  - Owner decision 9a5f4d74 keeps the existing NSE reads while the owner writes to NSE.
  - Every report carries one line saying NSE's "virtual trading or simulation" terms question is open.
  - No new NSE read.
- **Daily stop, a known limit:** checked at the slot only, from the previous slot's marks. Losses between slots are
  not seen; option losses are bounded by the Rs 10,000 cap.

## 4. Stories (owner's change of plan, orchestrator 22 Oct: built in parallel by several builders and judges)

Contracts (**MS-P1a**) merge first. Parts **b-i** then run in parallel, each depending on a only. **j** (the join-up)
comes last. Model tier per story follows DESK_DECISIONS "Market school pilot: parallel build and models" (788fdf75):
**H** is the higher model (contracts, safety, accounts and fills with tickets, join-up; every judge), **S** the other.
Rules for every story:
- It touches only its own files below, its own tests (`tests/school/<sub>/`) and, where named, one reserved line.
- It never edits `fno/constants.py`, `fno/config.py`, `config.yaml`, `fno/cli.py`, another story's sub-package or
  any frozen file.
- A type a story needs that a lacks is asked of a's builder (one small lane-1 follow-up of a), never defined twice.
- Each criterion has good, bad, boundary and empty cases, and a named test that fails when its code is broken on
  purpose (quality rule 4).
- No file or class over 350 lines.
- Gates before each push: `pytest -n auto`, `ruff`, `check_imports`, `check_records`.
- Self-review by independent review agents, recorded in Claims.
- Branch `story/ms-p1-<sub>`; never merged by its builder.

### MS-P1a Contracts · lane 1 (money limits and the switch are config keys) · model tier: H · `story/ms-p1-contracts` · depends on nothing

**Files owned:**
- `fno/school/__init__.py`;
- `fno/school/constants.py`: road codes, outcome codes, every reason code of 3.3-3.5 as frozen enums, record schema
  version;
- `fno/school/settings.py`: reads and checks the `school` block;
- `fno/school/contracts/` (`roads.py`, `snapshot.py`, `decisions.py`, `records.py`, `safety.py`, `accounts.py`,
  `dashcam.py`, `tickets.py`, `reports.py`, `clock.py`);
- `fno/school/fakes.py`: in-memory fakes of every port, for every story's tests;
- `tests/school/contracts/`;
- one empty package per later story, each with a `wiring.py` whose docstring names its story and nothing else;
- `fno/school/fake_fleet.py`: the fake fleet for MS-P1i's harness;
- shared files, one line each:
  - `fno/config.py`: add `school` to `ALLOWED_APP_KEYS`;
  - `config.yaml`: the `school` block (below);
  - `tools/check_imports.py`: a rule if needed (school imports no order, Slack or Groww client).

**Interfaces and frozen data types (frozen dataclasses or `Protocol`s; field names final in a's code):**

| Contract (module in `fno/school/contracts/`) | Shape (the code is the authority) |
|---|---|
| `Road`, `ROADS` (`roads.py`) | `code` (one of 5), `underlying`, `expiry_kind`, `dataset` (A4's and A4f's own constants), `stem` |
| `RoadDay`, `RoadStatus`, `DatedLot` | `road`, `session`, `expiries` (nearest first), `lot` (units, source), `strike_step`, `status` (open, or closed by exactly one `ClosureReason`) |
| `RoadCatalogue` | `day(session) -> tuple[RoadDay, ...]`: all five roads on a trading day, none on a closed day |
| `SlotSnapshot`, `SlotQuote`, `ContractKey` (`snapshot.py`) | `road`, `session`, `snapshot_id`, `sha256`, aware `started_at`/`finished_at`, `spot`, `expiries`, `quotes`; a quote's `two_sided` and `mid` |
| `SnapshotSource` | `for_road(road_day) -> SlotSnapshot`, or `SnapshotUnavailable(reason)` |
| `LegSpec`, `Proposal` (`decisions.py`) | legs; `lot`; `net_premium`; `max_loss` (every charge and pad); `costs` (inside `max_loss`); `score` |
| `DriverCard`, `SpotPoint`, `OpenPosition` | card `code`, `version`, `family`, `role`, `roads`, `band_steps`, `parameters`, `card_sha256`; history of recorded 15:00 spots; open position with `structure`, legs, `lot`, `opened`, `entry_net`, `max_loss` |
| `Driver` | `decide(road_day, snapshot, history, positions) -> Decision`; `review_exit(position, snapshot, history) -> ExitReason | None` |
| `Decision` | `driver_id`, `road`, `session`, `outcome`, `reason` (from that outcome's enum), `proposal` (exactly for trade, ticket and refused) |
| `SafetyLaw`, `LawResult`, `AccountView` (`safety.py`) | `check(proposal, account, snapshot, session) -> LawResult` (`passed`, `reason`, `limit`, `value`, `note`); the view holds equity, its high, loss since the previous slot, positions, `brake_engaged_on`, `brake_lifted_on`. Law 6 (no record, no trade) is `FillPort.enter`'s seal check |
| `AccountPort`, `LedgerEntry` (`accounts.py`) | `view(driver_id, marks by road, session)`; `record(driver_id, LedgerEntry)`: an opening or closing (with its `ExitReason`) filled result, idempotent |
| `FillPort`, `FillResult`, `FilledLeg`, `SealedDecision` | `FillResult.cash`: rupees moved, after charges. `enter(sealed, snapshot, seal, at)` (refuses `stale_seal` unless the seal covers the decision file at `at`); `exit(position, snapshot, file_sha256, seal, at)`; `settle(position, expiry)`. A result is exactly one of: filled legs (with time and the file they rest on), a refusal, or a state |
| `IndexSettlementSource`, `SettlementPrice` | `price(underlying, expiry)` with the settlement file's SHA-256, or `SettlementUnavailable` |
| `DecisionRecord`, `ExitRecord`, `OutcomeRecord`, `DriftRow` (`records.py`) | the fields of 3.4; a closed road is exactly a `road_closed` decision with the same reason; `DriftRow` is the NIFTY diagnostic, never a fill |
| `encode_slot_file`, `decode_slot_file` (`slot_file.py`) | one gzip (time zero, no name) of canonical JSON lines per (session, slot, kind): equal records, equal bytes |
| `DashcamStore`, `Seal` (`dashcam.py`, `seal.py`) | `seal(session, slot, kind, records) -> Seal`; `find(session, slot, kind) -> Seal | None`; `read(seal) -> records`; write-once per (session, slot, kind): other records raise `ReplayConflict` |
| `FleetRunner`, `SessionRun`, `RunMode` (`fleet.py`) | `run(session, mode) -> SessionRun`: one sealed decision per scheduled (road, driver version), sealed before any fill; a rerun seals nothing new; off: `SCHOOL_OFF_LINE` and nothing recorded. Fake: `fno/school/fake_fleet.py` |
| The law split (`constants.py`) | `ACCOUNT_LIMITS` (bucket, open risk, new risk a day, margin room: relaxed for tickets), `DRIVER_STOPS` (daily stop, brake: a stopped or braked driver issues no tickets that day), `TRADE_VALIDITY` (every other refusal) |
| `OpportunityCounts` (`tickets.py`) | `eligible >= fillable >= executed >= 0` per (session, road, driver) |
| `ReportSection`, `SectionText`, `Banner` (`reports.py`) | `render(session)`; the banner is red or amber, no other value |
| `Clock`, `FixedClock` (`clock.py`) | `now()`, aware; fixed in replay |

**The `school` block in `config.yaml` (all off):**
- `enabled: false`;
- `reports: false`;
- `first_counted: null`;
- `account_rs: 2000000`;
- `max_loss_rs: 10000`;
- `daily_stop_rs: 25000`;
- `brake_rs: 120000`;
- `max_new_trades_per_slot: 5`;
- `bucket_rs`, `open_risk_rs` and `new_risk_day_rs`, at C2's values.

**Acceptance tests:**
1. Every type is frozen.
2. `OpportunityCounts` refuses `fillable > eligible`.
3. A record round-trips to identical bytes, and a changed field changes the bytes.
4. `Banner` has exactly two members.
5. `settings` refuses an unknown or missing key and a negative limit.
6. The repository's settings load with `enabled` and `reports` false; `SCHOOL_OFF_LINE` ("school off") is the line
   j prints when the switch is off (a has no fleet path to test it on).
7. An import test: nothing under `fno/school/` imports an order call, a Slack client or the Groww SDK.
8. Every fake satisfies its `Protocol`, checked by a conformance test that each later story's real class must also
   pass (`tests/school/contracts/conformance.py`, importable).

### MS-P1b Roads and the quality gate · lane 1 (closes roads, which decides trades) · model tier: S · depends on a

**Files owned:** `fno/school/roads/`, `fno/school/quality/`, `tests/school/roads/`, `tests/school/quality/`.

**Implements:** `RoadCatalogue`, `SnapshotSource` (over the hash-checked quote store, A4/A4c/A4f sidecars, canonical
markers, A20a lots, A7 calendar), `RoadQualityGate`, `CaptureGateReport`.

**Acceptance tests:**
1. 5 roads on a trading day, none on a holiday.
2. Each closure reason of 3.5 from a planted fixture: missing, incomplete, out of window, hash mismatch, expiry
   mismatch, lot mismatch, impossible price.
3. Exactly one reason per closed road.
4. The capture gate on fixtures at 10 of 10 and 9 of 10 sessions, and at 95.0% and 95.1% of leg observations
   (boundary).
5. The conformance test.
6. Claims: a read-only `capture-gate` run on the recorded October days (counts only).

### MS-P1c The dashcam · lane 1 (records) · model tier: S · depends on a

**Files owned:** `fno/school/dashcam/`, `tests/school/dashcam/`.

**Implements:** `DashcamStore` over O9's `DataStore` (one gz JSONL file per slot and session; receipt committed and
pushed before `seal` returns); seal checking; public counts file; replay reader.

**Acceptance tests:**
1. Write-once: the same bytes again is a no-op; other bytes raise `ReplayConflict`, reported as "rule broken".
2. A seal not yet pushed, pushed after the fill time, or naming another file's SHA-256 is refused (`stale_seal`).
3. The public counts file passes the record scan and holds no strike, price or symbol (test).
4. Replay reads back exactly the records sealed.
5. The conformance test.

### MS-P1d Safety laws, accounts and fills · lane 1 (money, limits, fills, exits) · model tier: H · depends on a

**Files owned:** `fno/school/safety/`, `fno/school/accounts/`, `fno/school/execution/`, `tests/school/safety/`,
`tests/school/accounts/`, `tests/school/execution/`.

**Implements:**
- one `SafetyLaw` per law 1-5 and 7 of 3.3 (law 6 is the fill port's seal check); `SafetyLaws` runs all of them and keeps every reason; C2's rule classes are
  reused on the driver's `AccountView` through an adapter, never edited;
- `AccountPort`: one `PaperAccount` per driver version (`fno/books/account.py`), private through E2c's
  `PrivateFiles`;
- `FillPort` (fill rule of 3.6): E4's `price_leg`, E4c/E4d's `entry_problems`, `FillMaker` and `closing_quotes`; exits
  by E4's `ExitRule`s;
- the NIFTY drift diagnostic of 3.6 (a diagnostic row, never a fill);
- expiry settlement through `IndexSettlementSource`: a new class reading the archived F&O bhavcopy for all four
  indices; `fno/desk/settlement.py` is reused, not edited.

**Acceptance tests:**
1. Each law passes at its limit and refuses at limit + Rs 1.
2. No law changes a proposal (test over all laws).
3. Daily stop:
   - entries are refused after Rs 25,000 of loss;
   - an exit is never refused by it;
   - a risk-reducing close needs valid two-sided quotes.
4. Brake:
   - it pauses at Rs 1.2 lakh below the high;
   - it holds across sessions;
   - it lifts only on a row in `research/school/reviews/`;
   - exits continue.
5. Quote gate:
   - a missing or one-sided quote refuses the entry;
   - so does size above the displayed size;
   - so does a protective leg that cannot be sold back.
6. A fill without a valid seal is refused.
7. Entries fill at the decision snapshot's touch (ask to buy, bid to sell) or not at all, never partial; a missing
   quote gives `refused: missing_quote`.
8. An exit with a missing quote waits (`exit_waiting_quote`) and never takes a guessed price.
9. Settlement is at intrinsic against each index's `SttlmPric`; a missing file gives `settlement_needed`.
10. The drift row on NIFTY: a filled leg absent from the 15:15 capture gives `drift_unknown`, never a number.
11. The conformance test for each port.

### MS-P1e Rule drivers and controls · lane 1 (decides trades) · model tier: S · depends on a

**Files owned:**
- `fno/school/drivers/`;
- `research/school/cards/` (one card file per driver version, draft until h freezes them);
- `tests/school/drivers/`.

**Implements:**
- `RuleDriver(card)` for CS1, DB1, DR1, WS1 and PS2-4, built through D2's `CandidateBuilder` (widest width under the
  cap);
- `ReferenceDriver` (REF, per road);
- `NothingDriver` (N0);
- `RandomDriver` (RC1, seeded by SHA-256(session, driver, road));
- PS5 and KL1 as `role: measurement-only`.

**Acceptance tests:**
1. Each family fires at its threshold and not just below it.
2. "Not enough history" with 19 sessions, a trade with 20.
3. N0 always gives `no_trade: n0`.
4. RC1 gives the same draw for the same seed and a different one for another seed, under the same caps.
5. PS5 and KL1 match EDGE1's frozen parameters (a test against `research/edge1/`).
6. Every `no_trade` carries a reason code from a's enum.
7. The conformance test.

### MS-P1f Tickets and the three counts · lane 1 (evaluation records) · model tier: H · depends on a

**Files owned:** `fno/school/tickets/`, `tests/school/tickets/`.

**Implements:**
- `TicketBook`: a 1-lot virtual trade for every fired rule beyond the 5-trade limit, or on a driver stopped for the
  day, priced at the same quotes and checked by the same laws (through a's `SafetyLaw` and `FillPort` contracts),
  with only the account limits relaxed;
- the `OpportunityCounts` builder (eligible, fillable, executed);
- the shared-displayed-size count (327 item 10).

**Acceptance tests:**
1. Tickets:
   - the same quotes and laws as trades;
   - never in an account;
   - never summed into rupees.
2. `eligible >= fillable >= executed` over a fixture day.
3. A displayed size shared by two accounts is counted, and no report sums fills it could not serve.
4. A refused ticket stays in every count's denominator.
5. The conformance test.

### MS-P1g The 08:50 and 20:05 sections · lane 1 (Slack reports, signed-off pages) · model tier: S · depends on a

**Files owned:**
- `fno/school/reports/`;
- `tests/school/reports/`;
- one reserved line in `fno/forecast_lab/page_wiring.py`, adding the school's sections only when `school.reports` is
  true.

**Implements:**
- `ReportSection` for "Today": open and closed roads, the planned paper trades with worst loss, the banner, labelled
  Paper;
- `ReportSection` for "How did today go":
  - each trade's net;
  - the three counts;
  - refusals and closures;
  - the fleet total labelled "separate hypothetical accounts, not one budget";
- `Banner` rule: red on any capture or quality failure of a shown road, or no candidate; else amber.

**Acceptance tests:**
1. With the flag off, both editions render byte-identical to today (golden files).
2. With it on, the sections appear and say Paper.
3. No green is reachable (type and test).
4. A refusal planted in the input appears in the evening section.
5. No contract, strike or card internal appears in either section (privacy test).
6. Both sections carry the NSE-terms line of 3.6 and the "no latency [reasoning only]" label (test).

### MS-P1h The frozen comparison card · lane 1 (evaluation records) · model tier: S · depends on a

**Files owned:** `research/school/CARD_P1.md` (R1 card with its factory block), `fno/school/registration/`,
`tests/school/registration/`.

**Shared file, one row per driver version:** `journal/versions.csv` (D6), appended only, at registration.

**Implements:**
- the card names:
  - each driver version and its matched controls (N0, RC1, REF of its road);
  - the 5 roads;
  - the 15:00 slot;
  - C1's cost version;
  - the denominator and bands of 3.5;
  - the first counted session;
- `CountingRule`: a decision counts only if the card's and its version row's commits are ancestors of the decision's
  commit (D6's rule);
- the common group of road-days, with one session counted as one session, not five tests.

**Acceptance tests:**
1. A card registered after a decision makes that day not counted.
2. A changed card SHA-256 refuses counting.
3. Five roads on one day form one cluster in the comparison.
4. `read_card` accepts the card.

### MS-P1i The acceptance harness · lane 1 · model tier: S · depends on a

**Files owned:** `tests/school/acceptance/` (the harness and its recorded-day fixture builder), `fno/school/acceptance/`
(fault planters only, no production path).

**Implements:**
- planters for the 6 faults:
  - missing quote;
  - expiry mismatch;
  - lot mismatch;
  - stale seal;
  - impossible price;
  - replay conflict;
- a planted refused entry;
- a two-run comparator (byte equality of every record and count file);
- checks for zero unsealed, over-cap, invented or duplicate fills.

Runs on a's fakes here; story j must pass it with the real wiring.

**Acceptance tests:**
1. Each planter makes the fake fleet give its exact reason code.
2. The comparator fails on one changed byte.
3. The planted refusal survives two runs and appears in both sections' inputs and every count's denominator.

### MS-P1j The join-up: fleet runner, switch and composition · lane 1 · model tier: H · depends on a-i · daily-run part blocked until the v4 freeze is signed

**Files owned:**
- `fno/school/fleet/`;
- `fno/school/wiring.py` (the composition root);
- the reserved line in `fno/cli.py` that registers `python -m fno school`;
- later (blocked) the new step rows in `DAILY_RUN_STEPS`, after v4's, never inside its frozen files.

**Implements:** `FleetRunner.run(session, mode)` (a's contract; it passes `check_fleet` and MS-P1i's harness):
- **requirement from MS-P1f:** the `check(decision, accepted)` given to `tickets.rules.classify` builds its
  `AccountView` with the trades already accepted in that slot, so the bucket, open-risk, new-risk and margin laws add
  them up before any fill;
- **requirement (orchestrator, 22 Oct):** before `review_exit`, the fleet checks that each position's driver and road
  match the driver asked and the snapshot's road; a mismatch is that driver's `unavailable: driver_error`, never an
  exit;
- **requirement (orchestrator, 22 Oct):** a REF entry refused only by account limits (C2's bucket among them) becomes
  `ticket: account_limit` through `tickets.rules.classify`, the same rule as every driver, so REF stays measured on
  every open road-slot;
- **requirement (orchestrator, 22 Oct):** the daily and the 30-session reports show, per road, the share of scheduled
  decisions refused for quotes (law 5: `missing_quote`, `one_sided_quote`, `size_above_displayed`,
  `protection_unsellable`). The capture gate's band is about 10 steps of the money while the shorts sit about 20 steps
  out, so thin far legs stay visible here even when the road passes its gate;
- order: roads, gate, drivers, laws, seal, fills, exits, tickets, counts;
- each driver isolated: an exception is named by class and sealed `unavailable`;
- a time limit per driver;
- a rerun skips sealed decisions;
- MS-P1d limit 2 (orchestrator, 22 Oct 2026): a driver account's shared displayed size (E4d) counts its entries
  at the snapshot, not its exits of older positions there (`AccountView` cannot show them). Exits therefore run after
  the slot's entries, as the order above has it: an exit that then finds too little size waits
  (`exit_waiting_quote`), and an entry never counts on size an exit will take.

**Acceptance tests:**
1. `school.enabled: false` prints "school off" and writes nothing.
2. Every scheduled road decision has exactly one sealed outcome (count = trading roads x drivers).
3. A rerun seals nothing twice.
4. i's harness passes on the real wiring, including one recorded session replayed twice with identical records.
5. The end-to-end dry run on a recorded day, recorded in Claims.

## 5. Gap list (response 327 P1 and the orchestrator's scope)

| Requirement | Story |
|---|---|
| 5 roads at 15:00 from existing captures | 3.1; b |
| About 5 rule families (capped seller, debit buyer, directional debit spread, weekly expiry seller, PS2-4 as one) | 3.2; e |
| N0, RC1, one reference rule per road; PS5 and KL1 measurement only | 3.2; e |
| Per-driver Rs 20 lakh accounts reusing fno/books and fno/desk fills (touch, E4c, E4d) | d |
| Safety laws (protected, Rs 10k, Rs 25k daily stop, C2 caps, quote gate) | 3.3; d |
| Driver brake: pause at Rs 1.2 lakh below the high until the monthly review | 3.3 law 7; d |
| Dashcam sealed before fills; every decision a sealed outcome with a reason; refusals in the denominator | 3.4, 3.5; c, d, f, j |
| Tickets under the same rules, three counts | f |
| Shared order book (327 item 10) | f |
| Fill rule, NIFTY drift diagnostic, NSE-terms line | 3.6; d, g |
| Banner red and amber only | a (type), g |
| Own switch; sections behind a flag | a (keys), g, j |
| Frozen comparison card before day 1 | h |
| Capture gate per road, denominator first | 3.5; b |
| Planted faults and replay twice | i (harness), j (real run) |
| Fleet runner and daily-run wiring after v4's freeze | j |

**Out of scope, with reason:**
- futures, calendars and diagonals: probe 5 found no payoff or margin model;
- stocks and extra slots: P3+, and NSE's terms block the survey;
- AI drivers: 327 item 7, after a dry run;
- the instructor, condition map, licences, recommender top 3 and simulator: P2+;
- E8 owner-timing fills: the pilot has no recommendation to follow;
- the monthly review itself: P2+; P1 only reads its recorded row to lift a brake.

## 6. Questions answered (orchestrator, 22 Oct 2026)

1. **Fill snapshot:** accepted as 3.6 proposes, with the NIFTY drift diagnostic added.
2. **NSE terms:** owner decision 9a5f4d74. Existing NSE reads stay while the owner writes to NSE. Settlement stays
   behind `IndexSettlementSource`, every report carries the open-question line, and no new NSE read is added.
3. **Reference rule:** accepted with the cap. Shorts at 1 expected move, the widest wings whose maximum loss including
   costs is at most Rs 10,000, held to expiry. RC1 stays as the random control.
4. **Daily stop:** accepted for P1 as a known limit (3.6).
5. **Monthly review:** a recorded row in `research/school/reviews/`, written by the orchestrator session on or after
   the first Saturday of the next month. No row, no lift. The owner restarts nothing.
6. **Thin roads:** a closed thin road is an honest result.

**MS-P1d's questions (orchestrator, 22 Oct 2026, to builder session_014VUoPfMfRWNXyJSnXxB5NL):**

7. **Margin room (law 3), revised by the orchestrator the same day:** C2's margins file holds NIFTY rows only (SF, SC,
   BF, widths 100-300). Where every position of the check (the proposal and each held one) has a sourced row, C2's
   `MarginRoom` runs and fails closed (a stale row refuses). Where any position has no usable row, law 3 **refuses**
   (`margin_room`, note "margin not checked: no data"), never inventing a margin: design 6.1a, no usable margin, no new
   entry. The first answer (pass labelled) was withdrawn because it weakened an agreed safety law. The fix is data:
   school margin rows for BANKNIFTY, FINNIFTY, MIDCPNIFTY and the missing structures and widths, a separate piece
   opened by the orchestrator. Until it lands, those roads' entries are refused by law 3.
8. **Bucket groups:** {NIFTY}, {BANKNIFTY, FINNIFTY}, {MIDCPNIFTY}: FINNIFTY's largest weights are BANKNIFTY's banks,
   so one shock hits both [some evidence: index composition]. Kept as data in the school's `BucketMap`.
9. **Boundaries:** the daily stop and the brake refuse when the loss reaches their limit (>=); every other law passes
   at its limit and refuses beyond it. Tests pin both.
10. **Account storage:** `PaperAccount(<repo>/journal/school, "shadow:school-<code>-v<version>")`, mirrored through
    E2c's `PrivateFiles` under its repository path (outside the desk's `journal/shadow/`, which the desk's marking and
    scorecards read). The one shared-file line is `.gitignore`'s `journal/school/`.
11. **Brake lift rows:** `research/school/reviews/brake_lifts.csv`, columns `reviewed_on, driver_id, review_ref`,
    written by the orchestrator. A row dated strictly before a session lifts the brake from that session and restarts
    the equity high.
12. **Maximum loss (law 2):** the largest of the proposal's own figure, C2's at the mids and B2's at the touch with
    the Rs 1 pad, refused above Rs 10,000. **Law 1** refuses legs on two expiries (no calendar model).

## Claims

Per round, at an exact pushed SHA: which criteria are met, with the test name and the broken-code proof; the
self-review findings and what was done; a real output sample (dry run on a recorded day, counts only). Empty until
MS-P1a is built; each later story keeps its own Claims subsection here.

### MS-P1a Claims (round 1, branch `story/ms-p1-contracts`; the SHA is in the commit that carries this text)

| # | Criterion | Code | Test (broken-code proof: the plant it catches) |
|---|---|---|---|
| 1 | Every type is frozen | `fno/school/contracts/*.py` | `test_types.py::test_every_contract_type_is_frozen` (all dataclasses of 10 modules) |
| 2 | `OpportunityCounts` refuses `fillable > eligible` | `contracts/tickets.py` | `test_counts_out_of_order_are_refused` (plant: check removed) |
| 3 | Records round-trip to identical bytes; a change changes them | `contracts/codec.py`, `records.py`, `slot_file.py` | `test_records.py` (plants: unsorted keys, int kept in a float field, -0.0, gzip time, union int) |
| 4 | Banner has two members | `contracts/reports.py` | `test_the_banner_has_red_and_amber_only` (plant: GREEN added) |
| 5 | Settings refuse unknown or missing keys and negative limits | `fno/school/settings.py` | `test_settings.py` (plants: subset check, `< -1`) |
| 6 | The repository's settings load off | `config.yaml` `school` | `test_the_repository_settings_are_off_with_todays_limits` (plant: `enabled: true`) |
| 7 | No order, Slack, Groww or HTTP import under `fno/school/`; no production module imports the fakes | all | `test_boundaries.py` |
| 8 | Every fake passes the conformance check its real class must pass | `fno/school/fakes.py`, `tests/school/contracts/conformance.py` | `test_fakes_conform.py` (plants: fake replay conflict removed, bid used to buy, ledger not idempotent) |

- **Gates on this tree:** `pytest -q -n auto` gave 10,244 passed, 16 xfailed. `ruff check fno tests tools`, `check_imports` and `check_records` are clean.
- **Plants:** 24 planted, 24 caught (script in the builder's scratchpad; each one restored after its run).
- **Self-review** (one independent review agent on `8d093468..2fb6deab`): 4 blocking, 8 should-fix and 5 minor findings. All were fixed in this round except where marked:
  - The fill port could not check which file a seal names. Fixed: `SealedDecision` plus `enter(sealed, snapshot, seal, at)`. Conformance tests a late and a wrong-SHA seal.
  - The account could not build positions from a bare fill. Fixed: `LedgerEntry`. Conformance checks that the entry shows open and that recording it again changes nothing.
  - `view` took one road's snapshot. Fixed: marks by road.
  - The dashcam file format was not in the contract, and gzip was not deterministic. Fixed: `encode_slot_file` (gzip time zero) and a `RecordKind` in the key.
  - Int-in-float and -0.0 round-trips. Fixed in `to_plain`.
  - The safety-law check shared one account. Fixed: (proposal, account) pairs.
  - The brake had no latched state. Fixed: `brake_engaged_on`.
  - Record and decision consistency. Fixed:
    - a closed road is exactly a `road_closed` decision with the same reason;
    - an open road names its snapshot;
    - a refusal carries its proposal;
    - a `FillResult` is exactly one of three forms;
    - `Proposal.costs` added.
  - Exits. Fixed: an `ExitReason` enum, `Driver.review_exit`, and an `ExitRecord` sealed with the decisions.
  - Drift. Fixed: a `DriftRow` type, no longer an exit state.
  - Settlement had no seal. Fixed: `FillResult.rests_on` (the settlement file's SHA-256) and an `IndexSettlementSource` port with a conformance check.
  - Minor, fixed:
    - law 6 is the fill port's check (story updated);
    - `Road.dataset` uses A4's and A4f's own constants;
    - the catalogue check needs all five roads;
    - the fill check verifies touch prices and units;
    - a clock check added;
    - `RefusalReason.IMPOSSIBLE_LEG_PRICE` keeps every reason code unique;
    - snapshot expiries are sorted.
  - Not changed (finding 12, partly): `SCHOOL_OFF_LINE`, `NO_LATENCY_LABEL`, `NSE_TERMS_LINE`, `FLEET_TOTAL_LABEL` and `PAPER_LABEL` stay unused in a. They are the frozen wording for g and j, so those parts cannot drift apart. Criterion 6 now claims only what a can test.
- **Deliberate duplication:** the `school` limits copy today's book caps rather than reading `risk.profiles.books`, so a desk change cannot move the pilot mid-count. `test_the_school_limits_equal_the_books_caps_today` makes any divergence a visible decision.
- **Real output sample:** a fixture decision record's canonical bytes (fixture strikes, not live):
  `{"card_sha256":"efef...","decision":{"driver_id":"CS1@1","outcome":"trade","proposal":{"costs":85.0,"legs":[{"key":{"expiry":"2026-11-23","kind":"PE","strike":1000.0},"lots":1,"side":"sell"},...`

### MS-P1a Claims, round 2 (judge 479, FAIL round 1: four should-fixes)

| Judge 479 finding | Fix | Test (and the plants it catches) |
|---|---|---|
| 1. The import test missed relative imports, and the contracts loaded `requests`, `fno.providers` and `fno.intraday` | `test_boundaries.py` resolves relative imports. The contracts, constants, settings and both fakes import only the stdlib and `fno/school`: the order sides and the two dataset names are now school constants, pinned equal to their sources | `test_a_planted_relative_import_is_caught` (the judge's two plants); `test_the_contracts_load_only_the_standard_library_and_the_school` (a fresh interpreter: nothing loaded outside the stdlib but the empty `fno` package); `test_shared_values.py`. Plants: both relative imports in `roads/__init__.py`, a recorder import in `contracts/roads.py`, a changed dataset name |
| 2. No dashcam lookup | `DashcamStore.find(session, slot, kind) -> Seal \| None` (additive) | `check_dashcam`: None before the seal, the seal after, None for another kind. Plant: a fake `find` that always says None |
| 3. No frozen law split | `ACCOUNT_LIMITS`, `DRIVER_STOPS` and `TRADE_VALIDITY` in `constants.py`; `TicketReason.ACCOUNT_LIMIT` replaces `DRIVER_STOPPED` (orchestrator's ruling, checked against reviews 138 and 139: "relax only account-level cash/bucket limits") | `test_law_split.py`: exact sets, a partition of every refusal, never protection, max loss, quotes, prices or the seal. Plants: max loss added to the limits, the brake dropped from the stops |
| 4. No fleet contract | `contracts/fleet.py` (`FleetRunner`, `SessionRun`, `RunMode`) and `fake_fleet.py` | `check_fleet` and `check_fleet_off` on the fake; `test_fake_fleet.py`. Plants: a wrong seal SHA at fill, no rerun skip, the switch ignored, `SessionRun` consistency removed |

- **Also, from MS-P1f's questions (orchestrator, 22 Oct):** a `FillResult.cash` property. The fakes use it; f will
  use it. Test: `test_a_fill_s_cash_is_premium_received_less_paid_and_charges`. Plant: the sign flipped.
- **Changes for the b-e builders**, listed for the orchestrator. Everything else is additive.
  - **(i) Renamed:** `TicketReason.DRIVER_STOPPED` is now `ACCOUNT_LIMIT`.
  - **(ii) Moved:** `Road.dataset` values are unchanged, but the import source changed. `SIDE_BUY`, `SIDE_SELL` and
    `SIDES` now also live in `fno.school.constants`, so school code should import them from there.
  - **(iii) New method:** `DashcamStore.find` must now be implemented by c's store.
  - **(iv) New field (for d, orchestrator, 22 Oct):** `LawResult.note: str = ""` is a plain label recorded with the
    result. It never changes `passed`: a law with unusable input still refuses (fails closed, as C2 does).
  - **(v) New code (for e, orchestrator, 22 Oct):** `NoTradeReason.NO_VALID_QUOTES` ("no valid ATM straddle or no
    two-sided quotes for the structure"), apart from `NO_STRUCTURE_UNDER_CAP`.
- **Judge's notes (no action):**
  - `OpportunityCounts` has no scheduled count. MS-P1f's `CountTotals.scheduled` carries the denominator.
  - A refused ticket and a refused trade look the same in a `Decision`. That is deliberate: both are `refused`, with
    the law results in the record.
- **Gates on this tree:** `pytest -q -n auto` gave 10,270 passed, 16 xfailed. `ruff`, `check_imports` and
  `check_records` are clean.
- **Plants:** 36 planted, 36 caught over a's tests.

### MS-P1d Claims (round 1, branch `story/ms-p1-fills`; the SHA is in the commit that carries this text)

**Merged a's round 2 (32fdbdde):** school `SIDE_BUY`/`SIDE_SELL` from `fno.school.constants`; `LawResult.note` carries
the margin label; `FillResult.cash` replaces the test's own cash sum (the school code had none of its own: E1's
ledger moves cash); no `TicketReason` is used here; every law's refusal reason falls in exactly one of a's
`ACCOUNT_LIMITS` (bucket, open risk, new risk, margin room), `DRIVER_STOPS` (daily stop, brake) and `TRADE_VALIDITY`
(the rest).

Builder session_014VUoPfMfRWNXyJSnXxB5NL. Based on `story/ms-p1-contracts` at 756e6545. Built against a's contracts
and conformance checks only, with no second version of any type. Nothing in fno/desk, fno/books, fno/risk,
fno/checks or fno/costs.py is edited. The one shared line is `.gitignore`'s `journal/school/` (section 6 item 10).

| # | Criterion | Code | Test (broken-code proof: the plant it catches) |
|---|---|---|---|
| 1 | Each law passes at its limit and refuses at limit + Rs 1. The stop and the brake refuse at reaching the limit (section 6 item 9) | `safety/*_laws.py`, `margin_law.py` | `safety/test_limits.py` (plants: stop `<=`, brake `>`, impossible bound not strict, touch loss ignored); caps and margin room tested at their own computed totals |
| 2 | No law changes a proposal | `safety/law_set.py` | `test_laws.py::test_no_law_changes_a_proposal`, over all 13 laws. **Honest note:** this is guaranteed by the frozen types, so the test cannot fail by construction. It pins that guarantee; it does not prove anything beyond it |
| 3 | Daily stop: entries refused after Rs 25,000 of loss; an exit never refused; a risk-reducing close needs valid two-sided quotes | `account_laws.DailyStopLaw`, `accounts/school_accounts.py`, `execution/school_fills.exit` | `test_laws.py::test_the_daily_stop_refuses_entries_after_a_real_loss_but_never_an_exit` (real account, real loss); `test_accounts::test_the_loss_since_the_previous_slot` (plant: loss zero) |
| 4 | Brake: pauses at Rs 1.2 lakh below the high; holds across sessions; lifts only on a `research/school/reviews/` row; exits continue | `accounts/brake.py`, `reviews.py`, `account_laws.BrakeLaw` | `accounts/test_brake_state.py`, `test_laws.py::test_the_brake_*`, `test_exits_continue_under_the_brake` (plants: latch ignored, stale rows engage, pre-fall review lifts, same-day row lifts, high reset from an unmarked row) |
| 5 | Quote gate: missing or one-sided quote, size above the displayed size (E4d, per account), protection not sellable back | `execution/entry_gate.py` (E4c/E4d's `entry_problems` as the authority), `safety/quote_laws.py` | `test_laws.py::test_the_quote_gate_*`, `test_the_size_this_account_already_took_here_counts` (plants: taken ignored, taken from other roads or sessions) |
| 6 | A fill without a valid seal is refused | `school_fills._sealed_in_time` | `test_fills.py::test_no_valid_seal_no_fill`, `test_a_seal_or_fill_after_the_session_s_close_is_stale` (plants: seal check removed, late seal fills) |
| 7 | Entries fill at the decision snapshot's touch or not at all, never partial; a missing quote gives `refused: missing_quote` | `school_fills.enter` (E4's `price_leg`, `FillMaker`, C1's charges) | `test_fills.py` (plants: touch swapped, gate ignored) |
| 8 | An exit with a missing quote waits (`exit_waiting_quote`), never at a guessed price | `school_fills.exit` (`closing_quotes`, all legs or none) | `test_an_exit_with_any_leg_unquotable_waits_and_fills_nothing` (plant: partial closes) |
| 9 | Settlement at intrinsic against each index's `SttlmPric`; a missing file gives `settlement_needed` | `execution/settlement_fills.py`, `settlement_source.py` (E7's `NseFinalSettlement` unedited; `ArchivedOnly`: stores only, never a new NSE read) | `test_settlement.py`, run on a 4-index fixture built from NSE's real 25 Jan 2024 file (plants: settles at zero, `settlement_needed` dropped, no-file not refused) |
| 10 | NIFTY drift: a leg absent from the 15:15 capture gives `drift_unknown` | `execution/drift.py`, `capture_1515.py` | `test_drift.py` (plant: unknown becomes 0.0) |
| 11 | Conformance for each port | all | `check_fill_port`, `check_fill_port_missing_quote`, `check_account_port`, `check_settlement_source`, and `check_safety_law` for every law, including margin room |

**Orchestrator's answers (section 6, items 7-12), built:**
- Margin room refuses where any position has no usable row, with `LawResult.note` = `MARGIN_NOT_CHECKED` (`margin_law.py`, `margin_not_checked(result)`); C2 refuses a stale row, a missing or a malformed file itself.
- NIFTY's rows are never used for another index.
- A stale row, a missing file or a malformed file refuses.
- FINNIFTY shares BANKNIFTY's bucket.
- The stop and the brake act at the limit (>=).
- Accounts are in `journal/school/`, with brake lifts in `research/school/reviews/brake_lifts.csv`.
- Law 2 takes the largest of the three maximum losses.
- Law 1 refuses legs that span two expiries.

**Gates on this tree:**
- Full `pytest -n auto` on the final tree: 10,486 passed, 16 xfailed.
- `ruff check` and `ruff format --check` (fno, tests, tools), `check_imports` (2,095 files) and `check_records` (8,136 files) are clean.
- No file is over 350 lines; the largest is 128.

**Plants:** 37 planted and 37 caught (after the merge with a and the revised margin rule). The script is in the builder's scratchpad; each plant was restored after its run. One plant first survived ("brake high reset from an unmarked row"); its test was made sharper.

**Self-review** (one independent review agent, on the uncommitted tree): 3 blocking, 5 should-fix and 7 minor findings, each checked by me.
- Fixed:
  - B1: NIFTY margin rows were applied to other indices. Fixed by `margin_law.py`.
  - B2: a late seal could fill at an old touch. A seal or fill after the session's 15:30 close is now `stale_seal`.
  - B3: a crash part way through a close was not seen. The ledger and the position records are now compared unit for unit.
  - S4: a view of an earlier session used later data. It is now refused.
  - S5: duplicate contract legs could over-fill. They are refused in `enter`, in the ledger and by C2's proposal; C2 units are now summed.
  - S7: a close of a position never opened, or a reused ID, was accepted. Both are refused before any fill.
  - M11: the brake high was reset from an unmarked row. Fixed.
  - M15: the docstring path was wrong. Fixed.
- Accepted as known limits (reported to the orchestrator):
  - S6: E4d per account counts this account's entries at the snapshot, not its exits of older positions there. The fill port's own `enter` checks size without the account (`FillPort.enter` has no account). The fleet (j) must take a new `view` after each `record` before the next proposal's laws.
  - S8: a held NIFTY position with margin rows but no mark makes margin room refuse.
  - M10: the bucket, open-risk and new-risk caps add C2's maximum loss at the mids, as the desk does, while law 2 also checks the touch.
  - M12: `one_sided_quote` names every A4 problem (crossed, no size, no trade today). A finer code would be a change to a.
  - M14: a gate disagreement between E4c and the school raises rather than refusing (a bug signal), so j's isolation seals it as `unavailable`.
  - E2c's pull overwrites local files (inherited, unchanged).
- Ruled: M9 (the stop and brake boundary) is section 6 item 9.

**Privacy change for the judge (separate commit, orchestrator's request):** `fno/record_scan/forbidden_files.py` adds
`journal/school/` to `PAPER_ACCOUNT_FILES`, so a forced `git add -f` of a school account file is refused by the
public-record scan. The desk's two patterns are unchanged. Tests: `tests/record_scan/test_school_account_files.py`
(plant: the pattern removed, 5 tests fail).

**Known limits (reasoning only):**
- The daily stop compares this slot with the previous session's row, which was taken before its fills. It therefore also counts that slot's entry costs, so it acts sooner.
- An unmarkable position counts at its maximum loss for the stop, but never engages the brake.
- **Until the margin-data piece lands, law 3 refuses every BANKNIFTY, FINNIFTY and MIDCPNIFTY entry, and every NIFTY
  structure or width without a row** (all PCS, CCS, CDS and PDS today). The pilot cannot trade those until then.

**Real output sample:** none from a recorded day. A real snapshot needs b's `SnapshotSource` and j's fleet, and neither exists on this branch. On the fixture snapshot, a 1-lot BANKNIFTY bull put spread passes 12 of the 13 laws and is refused by margin room (no BANKNIFTY margin rows, noted "margin not checked: no data"). It fills at a bid of 10 and an ask of 5 (30 units each) with C1's charges, and its maximum loss at the touch is above the figure at the mids (`test_max_loss_counts_the_touch_the_fill_pays_not_only_the_mid`).
