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

### MS-P1a2 Contracts follow-up · lane 1 · model tier: H · `story/ms-p1-contracts-a2` · additive only

Asked by the orchestrator, 22 Oct 2026, for b and e.
- `RoadDay.strike_steps: Mapping[date, float]` holds each recorded expiry's own step (FINNIFTY's November monthly
  lists 100-point strikes against October's 50). It is optional; when given it names every expiry, each above zero,
  and the nearest is `strike_step`. `RoadDay.step_for(expiry)` returns that expiry's step and never borrows another.
  The field is left out of the hash, so `RoadDay` stays hashable.
- `RoadStatus.detail: str = ""` is a plain detail for a closed road only (e.g. why a listing was unreadable). The
  fleet records it in the decision record's `inputs` under `ROAD_DETAIL_INPUT`, so the record layout and its bytes
  do not change.
- Conformance: `check_road_catalogue` now requires every open road's steps for every recorded expiry.
- `Seal.pushed_at`'s comment (judge 485, Judge J): it is the receipt commit's time; the proof of the push is the
  receipt on the remote, since `DashcamStore.seal` returns only after the push succeeded. Comment only.

### MS-P1a3 Contracts follow-up: the ledger reader · lane 1 · model tier: H · `story/ms-p1-contracts-a3` · additive only

Asked for by j (orchestrator, 22 Oct 2026). The shape was agreed with d's builder, who implements it on
`SchoolAccounts`.
- **The reader:** `LedgerReader.entries(driver_id) -> tuple[LedgerEntry, ...]` (`contracts/accounts.py`). It returns
  every entry recorded in the driver's account, in the order recorded: each opening, then its closing once closed.
  - It is read-only: it opens no account and writes no equity row.
  - An account never opened gives ().
- **Why j needs it:**
  - settlement runs before the session's first `view` (judge 486's note);
  - an outcome names its own entry fill.
- **Conformance:** `check_ledger_reader(reader, port, opening, closing, marks, session)`.
- **Fake:** `FakeAccounts.entries`.

**Claims (round 1):**
- `test_ledger_reader` checks the fake against the conformance check.
- `test_the_ledger_reader_check_refuses_a_wrong_reader` feeds the check five bad readers:
  - one ahead of its ledger;
  - one that never answers;
  - one in reversed order;
  - one with a phantom entry for an empty account;
  - one a step late.
- **Plants:** 4 planted, 4 caught: the fake's reader, and each of the check's three entry assertions.
- **Limit:** the "a read writes nothing" assertion has no plant on the fakes, because a fake view keeps no state. d's
  real `SchoolAccounts` is where that assertion bites.

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
1. Each law passes at its limit and refuses at limit + Rs 1; the daily stop and the brake refuse when the loss reaches
   their limit (3.3: "reaches", "falls ... below"; section 6 item 9), so they pass at limit - Rs 1 and refuse at it.
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
- `classify(fired, check, max_new)` (`rules.py`): one driver's fired decisions at one slot, in rank order (frozen
  score, ties by the fixed road order).
  - Each is checked by the same safety laws through `check(decision, accepted)`. `accepted` holds the trades already
    taken this slot, so the bucket, open-risk, new-risk and margin laws see them before any fill; MS-P1j builds that
    running view.
  - The first `max_new` that pass every law trade.
  - A later one that passes is `ticket: trade_limit`.
  - One refused only by `ACCOUNT_LIMITS` is `ticket: account_limit` (orchestrator, 22 Oct 2026).
  - Any other refusal, the daily stop and the brake included, is `refused`. A stopped or braked driver issues no
    tickets that day.
  - The reason a refusal records: a stop first, then a trade-validity law; an account limit only when account limits
    alone refused (judge 490).
  - No law results at all raise, in `classify`, `TicketBook.enter` and `counts_for`: a wiring fault never passes.
  - Only trades enter `accepted`: a ticket never takes a place or adds risk to the running view.
- `TicketBook` (`book.py`):
  - it takes the ticket's sealed `DecisionRecord` and refuses on a binding law (anything but `ACCOUNT_LIMITS`) in that
    record's own `law_results`, never results passed beside it (judge 490);
  - it fills through the same `FillPort` as trades;
  - it records only in a `TicketLedger`, its own type over an account store on its own root, never a driver's
    account.
- `counts_for` and `totals` (`counts.py`): eligible, fillable and executed per decision; `scheduled` (every sealed
  decision) is the denominator; one row per (session, road, driver).
- `allocate` (`shared_size.py`, 327 item 10; orchestrator's rulings on judge 481): whole fills are served against each
  contract's and side's displayed size at one road's snapshot.
  - Account fills are served first; tickets get only what is left.
  - Within each group, owners are ordered by a seed from SHA-256(session, slot, road), so no name biases the
    comparison. The seed and the order are recorded.
  - `fill_status` marks an account entry the size could not serve `unavailable: size_shared`; it stays in every
    denominator (`counts_for(..., size_shared=True)`: fillable, not executed).
  - `UnavailableReason.SIZE_SHARED` is added to a's constants, additively.
- `account_net` (`rupees.py`): the only rupee sum. It leaves out tickets and every account outcome whose entry or exit
  was unservable, keyed by (driver, fill), and names those positions.
- `TicketBook`: a 1-lot virtual trade for every fired rule beyond the 5-trade limit, or refused only by an account limit
  (ACCOUNT_LIMITS; a driver stopped for the day or braked gets no tickets, DRIVER_STOPS), priced at the same quotes and checked by the same laws (through a's `SafetyLaw` and `FillPort` contracts),
  with only the account limits relaxed;
- the `OpportunityCounts` builder (eligible, fillable, executed);
- the shared-displayed-size count (327 item 10).

**Acceptance tests:**
1. Tickets:
   - the same quotes and laws as trades, with only the account limits relaxed (`test_rules.py`, `test_book.py`);
   - never in an account;
   - never summed into rupees.
2. `eligible >= fillable >= executed` over a fixture day (`test_counts.py`).
3. A displayed size shared by two accounts is counted, and no report sums fills it could not serve
   (`test_shared_size.py`).
4. A refused ticket stays in every count's denominator (`test_counts.py`).
5. f implements no port of a, so there is no conformance check of its own. Its tests run on a's fakes, which pass
   `conformance.py`.

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
- **requirement from MS-P1f (judge 481):** after a road's entry fills and before any account records them, the fleet
  runs `tickets.shared_size.allocate` over that snapshot's account and ticket fills. It records only the servable
  account entries, gives each unservable one `fill_status`'s `unavailable: size_shared`, passes `size_shared` to
  `counts_for`, and passes `unservable_fills` to `account_net`;
- **requirement from MS-P1f (judge 481 note):** every outcome record of a position from the ticket ledger has
  `is_ticket=True`, or `account_net` would sum it;
- **requirement (Judge B, judge 479.2):** any after-the-fact "sealed before fill" check (replay, audit, j's harness
  on old seals) uses O8's push evidence for the receipt, never `Seal.pushed_at`: that is the receipt commit's time, a
  lower bound on the push, and is trustworthy only at the moment `DashcamStore.seal` returns after a successful push;
- **requirement (orchestrator, 22 Oct):** the daily and the 30-session reports show, per road, the share of scheduled
  decisions refused for quotes (law 5: `missing_quote`, `one_sided_quote`, `size_above_displayed`,
  `protection_unsellable`). The capture gate's band is about 10 steps of the money while the shorts sit about 20 steps
  out, so thin far legs stay visible here even when the road passes its gate;
- order: roads, gate, drivers, laws, seal, fills, exits, tickets, counts;
- each driver isolated: an exception is named by class and sealed `unavailable`;
- a time limit per driver;
- a rerun skips sealed decisions;
- **runbook step (orchestrator, 22 Oct 2026; judge 495):** any new comparison-card version (an edit of
  `research/school/CARD_P1.md`) needs new D6 rows registered before its decisions count: one `school:<driver id>` row per
  driver version (12 today), a new version id, a `starts_on` strictly later than the book's previous row (D6 refuses an
  equal or earlier date, so it cannot be registered the same day), `comparison_card_sha256` the new card's SHA-256 and
  `card_sha256` unchanged unless the driver card changed too, committed after the card. Until then every decision made
  under the new version is `comparison_card_mismatch` (denominator kept, nothing counted); decisions made earlier keep
  their own verdict. The run's output says so by name when it sees the mismatch (orchestrator, 23 Oct 2026);
- **requirement (orchestrator, 22 Oct 2026, judge 494):** a law result's `note` can name contracts or legs (MS-P1m's
  margin causes do), so it is never posted to Slack; the reports count "margin not checked" refusals by their cause
  (`margin_not_checked`, the cause after the prefix), never by quoting the note;
- MS-P1d limit 2 (orchestrator, 22 Oct 2026): a driver account's shared displayed size (E4d) counts its entries
  at the snapshot, not its exits of older positions there (`AccountView` cannot show them). Exits therefore run after
  the slot's entries, as the order above has it: an exit that then finds too little size waits
  (`exit_waiting_quote`), and an entry never counts on size an exit will take.
- judge 486's note (orchestrator, 22 Oct 2026): expiry settlement runs before the session's first account `view`. An
  expired position has no mark in the next capture, so a view taken before its settlement counts it at minus its
  maximum loss, and that can trip the daily stop.
- settlement's store (orchestrator, 22 Oct 2026): once MS-P1b and MS-P1d are both on `main`, j's composition root
  builds d's settlement source on b's `build_archive_stores` (the service account's Drive, else the owner's, else
  `RawFilesNotConfigured`); d's own `SettlementStoresNotConfigured` stays until then.

**Design (builder, 22 Oct 2026; for the orchestrator's check).** `fno/school/fleet/`:
- `history.py` `RecordedSpotHistory`: each road's earlier recorded 15:00 spots, read from the repository's committed
  sidecars of canonical captures (complete, in window, a spot), strictly before the session. No Drive and no new read.
- `running_view.py`: the slot's running `AccountView`, which is the account's own view plus the trades already
  accepted this slot (their maximum losses, as open positions opened this session). It is rebuilt after each account
  record.
- `slot.py` `SlotPlan`: per road, the catalogue's road days, then the snapshot, then the quality gate. A closed road
  gives every driver `road_closed` with the road's one reason, and its detail goes in `inputs["road_detail"]`.
- `decide.py`:
  - each driver on each open road, isolated: an exception is sealed `unavailable: driver_error`, named by class, and
    a driver over its time limit is sealed `unavailable: deadline`;
  - then `tickets.rules.classify` with the running view;
  - then each open position's `review_exit`, after the pairing check (driver and road), giving `ExitRecord`s.
- `fill.py` (round 2, after the self-review): rebuilt from the sealed records and the ledgers on every run:
  - entry fills (account trades by `SchoolFills`, tickets priced by `TicketBook.price` under their own laws); a fill
    the ledger already holds is read back, never made again;
  - exit fills of the positions still open;
  - per road, one `allocate`: entries first (accounts, then tickets), exits only from what is left (MS-P1d limit 2);
  - only what it serves is recorded: an account entry it cannot serve is `size_shared` (fillable, not executed), a
    ticket it cannot serve is not opened, and an exit it cannot serve waits. So no ledger holds an unservable fill,
    no outcome rests on one, and `account_net`'s exclusion has nothing left to exclude (it stays as a second guard);
  - then the NIFTY drift rows of the served account entries.
- `outcomes.py`: an `OutcomeRecord` per closed position, with `is_ticket` set from the ledger it came from.
- `runner.py` `SchoolFleet.run(session, mode)`:
  1. the switch;
  2. settlement of expired positions (accounts and tickets) before the first view;
  3. if the session's decisions are already sealed, nothing is decided or sealed again;
  4. otherwise: plan, decide, seal `decisions`;
  5. the finish, on every run: fill what the ledgers lack, seal `outcomes` and `drift` each once, write the public
     counts and commit them (the single runner). A session whose outcomes, drift and counts all exist only commits
     what is uncommitted. So a crash anywhere between the seal and the commit is completed by a rerun, never doubled.
- `quote_share.py`: per road, the share of scheduled decisions refused by law 5's four reasons. Margin-not-checked
  refusals are counted by their cause, never by quoting a note. Notes never leave the dashcam.
- `fno/school/wiring.py`: the composition root (b, c, d, e, f, the settlement source on b's `build_archive_stores`,
  and g's day inputs); `python -m fno school run [--session D] [--replay]` is the reserved CLI line. Off by
  `school.enabled`.
- `tests/school/acceptance/real_rig.py`: i's harness on the real fleet, with b's captures written as files and the
  archived listing and lot files as fixtures; the dashcam is c's store on a local Drive folder and a local git remote.
- The daily-run steps are a separate branch, `story/ms-p1j-daily-steps`, not merged until the v4 sign-off.

**Runbook: a new card version (Judge H, judge 495 addendum 1; orchestrator, 22 Oct 2026).** Any new comparison-card
version needs new D6 rows that name it. That covers a charges change (which `config.yaml` makes CI demand) and any
change to the roads, slot, band or drivers. The rows must be registered and pushed BEFORE the next counted session's
15:00 slot. Until then every decision is `comparison_card_mismatch`: it does not count, so the rule fails closed.

1. Edit `research/school/CARD_P1.md`:
   - raise its version (the header table and the factory block's `version:`);
   - say what changed;
   - commit and push it.
   Note that commit as `CARD_COMMIT`.
2. The card's hash: `git show CARD_COMMIT:research/school/CARD_P1.md | sha256sum`.
3. Each driver card's hash, for every driver version in the card's section 1:
   `sha256sum research/school/cards/<CODE>_v<N>.yaml`.
4. For each driver version, one row, using the book's next version id (`python -m fno versions check` lists them):
   `python -m fno versions register school:<CODE>@<N> <next id> --starts-on <next counted session> --components
   '{"card_sha256": "<driver card hash>", "comparison_card_sha256": "<card hash>"}' --reason "Market school pilot P1
   driver version, comparison card CARD_P1 v<version>"`. The command commits `journal/versions.csv` at once; push it.
5. Check:
   - `python -m fno versions check` shows every driver version with the new hash;
   - `python -m pytest -q tests/school/registration` passes. That includes h's
     `test_the_charges_block_in_force_matches_the_cost_hash_frozen_in_the_current_card_version`, which fails CI while
     `config.yaml`'s `charges:` block differs from the hash frozen in the current card version.
6. A row registered after a decision never counts that decision (D6's ancestor rule). Versions apply forward only.

**Runbook: "dashcam stuck: stored file unverifiable" (Judge K, judge 529; MS-P1c follow-up).** `school run` stops with
`stopped: dashcam stuck: stored file unverifiable <session> <slot> <kind> (<why>)` and exits 1 (the alert). Cause:
Drive holds that key's file and `main` has no receipt for it (a run stopped between the two), and the file is not
one this fleet could have written. What waits depends on the kind (Judge K, judge 529.2); the fleet never seals over
the stored file:
- `decisions`: nothing for that session is decided, sealed, filled or counted until a person decides.
- `outcomes` or `drift`: the stop comes after the fills, so the decisions are already sealed and the fills booked in
  the ledgers. An `outcomes` stop leaves the outcomes, the drift rows, the instructor's files and the counts waiting;
  a `drift` stop comes after the outcomes are sealed too, so only the drift rows, the instructor's files and the
  counts wait. A rerun after the person's decision books no fill twice (it reads the ledgers).
1. Read the why. "not this fleet's" usually means a card or driver changed between the two runs (compare the
   cards' commits with the stored records' `card_sha256`); "unreadable", "not canonical", "another kind", "another
   session or slot" mean the file is damaged or misplaced.
2. Fetch the stored file from Drive (`data/school/dashcam/<YYYY>/<MM>/<DD>/1500.<kind>.jsonl.gz`, the slot
   without its colon) and decode it (`fno.school.contracts.slot_file.decode_slot_file`); it is never deleted or
   overwritten (write-once).
3. Raise it to the owner and the orchestrator with the key, the why and what the file holds; the session's record is
   their decision (for example, a card change reverted so the file is this fleet's again, after which a rerun
   adopts it). Never edit the file, never write its receipt by hand.

**Acceptance tests:**
1. `school.enabled: false` prints "school off" and writes nothing.
2. Every scheduled road decision has exactly one sealed outcome (count = trading roads x drivers).
3. A rerun seals nothing twice.
4. i's harness passes on the real wiring, including one recorded session replayed twice with identical records.
5. The end-to-end dry run on a recorded day, recorded in Claims.

### MS-P1m The roads' margins · lane 1 (money limits: C2's margin room; two judges) · model tier: H · depends on nothing in P1

Owner: the A14 builder (session 01Vm1WnH8i9waM8EJG8zwWqg; orchestrator, 22 Oct 2026). Law 3 asks C2's `MarginRoom` on
each driver account. Today C2 has margins for NIFTY's monthly ATM-shaped rows only (`margins.csv`, SF, SC and BF, widths
100-300). The pilot needs a margin for every position its drivers propose: four indices' monthlies and NIFTY's weeklies,
seven structures, any width, and shorts one expected move out.

**Why per proposal, not rows (orchestrator's rule: measure first; strong evidence).** A14-style rows were compared
with the pilot's real legs on 37 archived sessions (every 12th session, 6 Jan 2025 - 6 Oct 2026), widths 1-8 strike
steps (each expiry's own step, read from its listed strikes near the index; judge 492), 14,800 comparisons, every
combination measured. The figure is C2's stressed margin at k 2.1, per unit. The row is A14's own structure (SC
shorts at spot ±2%, spreads at ATM); the real legs are the pilot's (shorts one expected move out, the ATM straddle in
the file; debit spreads one step out). The table gives the share of cases where the row is below the real position,
and the lowest row/real ratio:

| Road | SC | PCS | CCS | CDS | PDS |
|---|---|---|---|---|---|
| NIFTY-M | 75% below, min 0.86 | 98% below, min 0.90 | 97% below, min 0.88 | 1% below, min 0.82 | 13% below, min 0.88 |
| BANKNIFTY-M | 70% below, min 0.81 | 94% below, min 0.85 | 89% below, min 0.87 | 3% below, min 0.85 | 11% below, min 0.87 |
| FINNIFTY-M | 75% below, min 0.82 | 97% below, min 0.85 | 94% below, min 0.88 | 5% below, min 0.87 | 10% below, min 0.87 |
| MIDCPNIFTY-M | 83% below, min 0.76 | 97% below, min 0.85 | 92% below, min 0.88 | 8% below, min 0.84 | 12% below, min 0.84 |
| NIFTY-W | 31% below, min 0.92 | 97% below, min 0.91 | 98% below, min 0.88 | 2% below, min 0.91 | 11% below, min 0.88 |

A spread sold further out collects less premium, and C2's margin subtracts the premium received (`min(0, NOV)`), so
ATM rows understate the school's credit trades by up to 24%. So the school computes each proposal's margin on its own
legs, with the same calculator and the same archived file. No rows are added anywhere.

**Source (no new read; strong evidence, the archived 21 Oct file):** the session's beginning-of-day SPAN file, as
A14 reads it: A9's first-archived copy in Drive, its SHA-256 equal to the manifest's, created before 09:00 IST on its
day. That file holds NIFTY (18 expiries, the weeklies included), BANKNIFTY (6), FINNIFTY (3) and MIDCPNIFTY (3); every
expiry checked is in exactly one scan tier, and the strike steps are 50, 100, 50 and 25. The lot is the day's market lot
from A20a's master files.

**Builds** (`fno/nse_margins/road_trades.py`, `road_margin.py`, the root `road_wiring.py`):
- `RoadTradeTerms`: C2's `TradeTerms` plus the index, the expiry, the legs (one unit each) and the units per lot the
  trade was entered with (the road day's dated lot from MS-P1b, A20a; an open trade keeps its own). It refuses an index
  outside the four, no legs, no lot, and legs that are not its structure's shape. A spread is one bought and one sold
  leg of its type, `width` apart, with the right leg sold; a fly or condor is a body of one call and one put on the
  body's side with wings `width` out, a fly's body on one strike, a condor's sold call above its sold put; one unit per
  leg; only SF, SC, BF, PCS, CCS, CDS and PDS.
- `road_proposal` and `road_open_trade`: C2's `Proposal` and `OpenTrade` built from the same terms (lot size, legs, and
  units = side x lot x lots), so the margin and the trade cannot disagree. **MS-P1d must build every school proposal
  and open trade through them** (its own acceptance test). C2's `MarginRoom` prices from the terms but counts units
  from the trade: a hand-built pair with a lot of 1 inside a 65-unit proposal passed with Rs 840 needed instead of Rs
  54,600 (self-review, 22 Oct 2026).
- `ArchivedSpanMargin`: C2's `StressedMargin` for those terms. C2's `MarginRoom` asks it the margin of every open trade
  and of the proposal, unchanged. Each figure is A14's `SpanMarginCalculator` with `NseIndexOptionExposure` on the
  trade's own legs and lot, read from the session's file in A14's daily mode (`read_span_file(..., symbol=...)`: a
  change of margin method refuses, as it stops A14's job; checked on 16 recent sessions x 4 indices, none refused). It
  applies C2's STR1 cap (`stress_cap_per_lot`) and the factor in force from A14c's file. The file is downloaded once per
  session and parsed once per index.
- `record(day)` and `trade_record(terms, day)`: the method, the factor row, the labels "k measured on NIFTY monthly
  only [reasoning only]" and "no broker check yet for BANKNIFTY, FINNIFTY and MIDCPNIFTY" (orchestrator, 22 Oct 2026),
  the file name and SHA-256, and per trade the index, expiry, legs, lot and per-lot scan, NOV and exposure. The dashcam
  (MS-P1c) seals them with the decision.
- `build_road_margin(cfg, env, factor=None)`: a caller may pass its own factor row per session (the practice run over
  history, whose sessions predate the factor file's first row of 14 Oct 2026: each session's own archived file times
  the latest factor; orchestrator, 23 Oct 2026). The default is C2's file lookup, unchanged, and it still refuses a
  session before that first row. The row used is named in every record either way.
- A14's point-in-time rule (written before 09:00 IST) becomes one `SpanFile.written_in_time`, used by A14's job, A14c's
  run and this margin (it was copied in the first two).

**Fails closed, by name** (law 3 then refuses the trade, as `RiskInputError`; C2's manager turns it into a refusal):
terms without legs; a day with no archived file or no manifest row; a SHA-256 other than the manifest's; written at or
after 09:00; a damaged file, no part for the index, or a change of margin method; an out-of-model expiry (a day after
it, beyond 9 months, or an expiry day before 20 Nov 2024); a leg not in the file; any Drive failure, missing settings
and a refused sign-in included, and an unreadable manifest (by class name only).

**Expiry day is priced, not refused (round 2; judge 491, orchestrator's ruling (a), 22 Oct 2026).** C2's room prices
every open trade first, so refusing an expiring trade froze its whole account that day: REF holds a NIFTY weekly on
every weekly expiry day, so REF and RC1 would lose their entries on all roads about one session in five, which biases
the controls. `ExpiryDayIndexExposure` (`fno/nse_margins/expiry_day_exposure.py`, a new `ExposureRule`; A14's own rule
is unchanged) adds SEBI's extra 2% ELM to each short index option expiring that day: SEBI/HO/MRD/TPD-1/P/CIR/2024/132
of 1 Oct 2024, para 5.6, from 20 Nov 2024; NSE Clearing NCL/CMPT/64639 levies it "on short index options contracts"
(P0 probe 4, checked). So an at-the-money short carries 4%, and one more than 10% out of the money 5%. The archived
beginning-of-day file still holds the expiring series in one scan tier (strong evidence: 29 Sep 2026 monthly, 13 Oct
2026 weekly). `trade_record` names the extra when it applies. Known limit [reasoning only]: C2's factor k also
multiplies the exposure, so k 2.1 on top of SEBI's doubled ELM roughly doubles an expiring fly's stressed margin
(NIFTY weekly SF 100 on 13 Oct 2026: Rs 2,48,443 a lot); whether k should stress an expiry-day ELM is for A14c's
per-underlying follow-up.

**Unchanged:** `margins.csv`, A14's daily job and workflow, and C2's and C4's NIFTY path, byte for byte.

**Known limits:**
- k 2.1 was measured on NIFTY monthly history only [reasoning only for the other indices and the weeklies];
  per-underlying k is an A14c follow-up after the freeze.
- Our calculator matches Groww on NIFTY (A14c part 2 rehearsal, 21 Oct 2026: 15 of 15 baskets within tolerance), but
  the other three indices have no broker check yet [reasoning only].
- The file is the beginning-of-day one: a 15:00 decision uses the morning's scan arrays and prices, as A14's rows do.
- A school proposal must never go through E8's owner-timing record (`fno/desk/owner_timing/order_record.py` writes the
  terms with `asdict` and reads them back as plain `TradeTerms`, which would drop the legs). The pilot has no owner
  timing (out of scope above).

**Acceptance tests:**
1. The figure is A14's calculator on the trade's own legs at C2's factor (stressed, at entry, broker), on a planted
   file; on the real 21 Oct file, NIFTY's ATM SF 100 equals that day's `margins.csv` row, and one structure of each
   other index and one NIFTY weekly is reproduced by hand in the claims.
2. Each refusal above, one test each, with its name.
3. The trade's own lot is used; a different lot changes the figure. A credit spread in rupees worked by hand: the
   credit's `min(0, NOV)` and C2's cap binding (planted arrays and prices).
4. C2's own `MarginRoom` on this margin, with an open trade and a proposal: it passes with the room exactly enough and
   refuses one rupee short; an open trade without legs refuses.
5. `margins.csv`, C2's and C4's NIFTY path are untouched (no file of theirs changes; the existing suite passes).
6. The file is downloaded once per session and parsed once per index (counting fakes).
7. Every shape refusal of `RoadTradeTerms`; `road_proposal` and `road_open_trade` carry the terms' lot, legs and units.
8. Expiry day: 2% + 2% (and 3% + 2% deep out of the money) worked by hand; any other day is A14's rule; an expiry day
   before 20 Nov 2024 and a day after expiry still refuse; an account holding an expiring trade still enters another
   road that day (C2's own room).
9. The gap measure above is reproducible from its script, with the same counts.
10. Mutations on every rule above.

### MS-INS The instructor v1 · lane 1 (evaluation records) · model tier: H · `story/ms-ins-<part>` · depends on a, c, d, f, h (on `main`); reads b and e

**Builder:** session_01LH7m9r5TCAKgZbeHVYkiTD · **Orchestrator:** session_01VG1RqxLFUVdvvPuMRYZtDH · **Sources:**
DESK_DECISIONS "Simulator and Instructor v1 start now" (owner: "Yes, start now (Recommended)"); response 325 sections
6.1, 6.2 and 6.3b; response 327 corrections 2, 3 and 4; reviews 138 (sections 2-4) and 139 (points 2-4).

**Description:** As the statistician, the options strategist and the risk manager, I want every closed paper trade and
every closed ticket explained (where its rupees came from, and a code-built cause), and every driver compared with
the controls that drove the same road on the same session and slot, so that the 30-session review and the 20:05 line
say honestly why a result happened and whether a driver did better than doing nothing, a random driver and the
reference rule. Descriptive only: no licence, no claim, no recommendation.

**What to expect [reasoning only]:** with 30 sessions, holds of up to about 30 sessions and five roads sharing one
market, the paired intervals will be wide. Most rows will read "Exploratory" or "Not established". That is the
honest result, not a defect. The planted-edge test (INS-d) tells the owner, before the count starts, how many
sessions a real edge of a given size needs to show.

#### Boundaries

- **Reads, never writes:** the sealed dashcam files (decision, exit and outcome records) through c's `ReplayReader`,
  each checked against its seal; f's counts (`counts_for`, `totals`); h's `CountingRule`, `common_road_days` and
  `session_clusters`. For the attribution only, these recorded inputs, all read-only:
  - each session's recorded snapshot of the position's road, through b's `SnapshotSource`, checked against the
    `snapshot_sha256` that session's sealed decision record names;
  - d's `IndexSettlementSource`, for settlement exits and the hold-to-plan check (cause 11);
  - A6's events (`fno/research_data/events.py`, `known_on` rule), for cause 7;
  - the frozen card files and e's drivers, for the stop level (cause 6) and the replay (cause 13);
  - `config.yaml`'s `risk_free_rate`, G13's rate.
- It never writes into the dashcam, an account, the ticket ledger, a card or `journal/versions.csv`, and never
  changes, reorders or delays a decision. No new Groww or NSE read; no order path; nothing to Slack (the "why" line is
  text that j's wiring hands to g's 20:05 section); no scheduled task.
- **Its own records:** write-once through O9's `DataStore` (dataset `school-instructor`, one gzip canonical JSON lines
  file per session and kind: `attribution`, `causes`, `paired`). Equal inputs give equal bytes; other bytes for a
  written key are refused. A correction is a new record naming the old one. GitHub gets the receipts and a public
  counts file: cause tags per driver and session, no rupees, contract, strike, price or card internal (E2c's rule).
- **Frozen rules:** every threshold below lives in `research/school/INSTRUCTOR_V1.md` and in
  `fno/school/instructor/thresholds.py`; a test pins the two together. Each record carries the card's SHA-256. A change
  is a new instructor version (v2), committed before the first session it reads, never applied to sessions already
  written.

#### INS-a Contracts and the reader · `story/ms-ins-contracts`

**Files owned:** `fno/school/instructor/{__init__,contracts,ports,reader,records_file,adapters,fakes,wiring}.py`,
`tests/school/instructor/{__init__,builders,conformance,test_reader,test_ports,test_types}.py`.

**Implements:**
- frozen types: `HeldPath` (one closed trade or ticket: its outcome record, its entry decision record, its exit record
  if any, and the snapshots of every session held, entry to exit), `Attribution`, `Cause`, `Classification`,
  `PairedRow`, `MapStatus`;
- `MapStatus` has exactly three members: `exploratory`, `watching`, `not_established` (327 correction 3);
- `PathReader.closed_between(first, last) -> ClosedRead` and `closed_on(session)` (= `closed_between(session,
  session)`, one resolver; orchestrator's ruling on judge 501): the trades and tickets closed on those sessions.
  - An original is read on its own close day as its latest correction, sealed on any session up to today. The original
    stays on file.
  - A correction is never a path on the day its own file was sealed.
  - So the days' `closed_on` add up to `closed_between` over the range.
  - A day's tally recomputed after a correction can change. The 20:05 line keeps what was known at 20:05; later
    reviews use the corrected figure.
  - A decisions file whose bytes differ from its seal is a `sealed_file_damaged` fault on each path that needs it.
  - An outcomes file that cannot be read is listed in `ClosedRead.unreadable`: an alert in every report, never a
    guess. The other days still read;
- ports, each with an in-memory fake that passes `conformance.py`:
  - `SnapshotArchive`: over b's `SnapshotSource`;
  - `EventCalendar`: over A6;
  - `CardReplay`: over e's drivers;
  - `InstructorStore`: over O9's `DataStore`.

**Acceptance tests:**
1. A trade held 3 sessions gives one path with 3 snapshots in session order, and a ticket gives a path marked ticket.
2. A corrected outcome is read once, as its correction.
3. A snapshot whose SHA-256 differs from its decision record's gives a path flagged `data_fault`, never numbers.
4. A session with no closed outcome gives an empty tuple.
5. The read-only test: every dashcam, account, ticket and card fake used raises on any write, and a full instructor
   run on the fake fleet completes.
6. The import test: nothing under `fno/school/instructor/` imports an order call, a Slack client or the Groww SDK.
7. The conformance test for each port.

#### INS-b The P&L attribution · `story/ms-ins-attribution`

**Files owned:** `fno/school/instructor/attribution/` (`greeks.py`, `points.py`, `attribute.py`),
`tests/school/instructor/attribution/`.

**Method (frozen; reuses G13's pricing, `fno/price_distribution/pricing.py` and `forward.py`; nothing re-derived):**
- **Steps:** one step per pair of consecutive recorded snapshots of the position's road while it was held, from the
  entry snapshot to the exit snapshot. A settlement exit's last step ends at expiry, at the settlement price.
- **At each snapshot:**
  - forward `F`: each expiry's G13 `averaged_forward` from two-sided mids, at G13's rate;
  - time `T`: minutes from the snapshot's `finished_at` to 15:30 IST on expiry day, divided by 365 x 1440;
  - each leg's `sigma`: the Black-76 implied volatility of its mid.
- **Per leg and step**, with signed units `q` (buy +, sell -) and Black-76 Greeks at the step's start:
  - delta P&L = `q x delta x dF`;
  - gamma P&L = `q x 1/2 x gamma x dF^2`;
  - vega P&L = `q x vega x d(sigma)`;
  - theta P&L = `q x theta x dt` (calendar time).
- **Market P&L:** the sum over legs of `q x (mid at exit - mid at entry)`. At expiry the mid is the intrinsic value
  against the settlement price.
- **Residual:** market P&L minus the four Greek components. It is the balancing item and is always shown.
- **Costs:** every leg's C1 charges (entry and exit `FilledLeg.charges`) plus the spread paid against the mids.
  The spread is measured here from the fills, against the mids of the path's own first and last snapshots (none at a
  settlement). It is not taken from the outcome record's `slippage_vs_mid`, whose basis is not fixed, so the residual
  never absorbs a cost measured on other mids (INS-b self-review).
- **The identity** holds for every path: delta + gamma + vega + theta + residual - costs = the outcome record's `net`,
  to Rs 0.01.
- **Gaps:**
  - a leg without a two-sided quote at an intermediate snapshot merges that step with the next (`steps_merged` counted);
  - an implied volatility that cannot be solved puts that leg's step wholly in the residual (`iv_unsolved`);
  - the last step of a settlement has vega 0 (no volatility at expiry).
- **Poor fit:** a path is flagged `poor_fit` when the absolute residual is above both Rs 200 and 25% of the sum of the
  absolute Greek components. It is shown beside its causes, never hidden.

**Acceptance tests:**
1. Hand-computed: a 2-leg bull put spread over 2 snapshots, every intermediate value written out in the test's
   docstring, matched to Rs 0.01.
2. A pure forward move (sigma and T unchanged) gives vega = theta = 0.
3. A pure time step (F and sigma unchanged) gives delta = gamma = vega = 0.
4. The identity on every fixture path and on 200 random fake paths.
5. Step merging over a missing quote.
6. An unsolvable IV goes to the residual.
7. A settlement last step.
8. `poor_fit` at Rs 200 and 25%, and just beyond each (boundary).
9. An empty path (entry and exit on one snapshot) gives zero Greek components and costs-only.
10. Broken-code proof: flipping the sign of `q`, or using the step's end Greeks, fails test 1.

#### INS-c Root causes · `story/ms-ins-causes`

**Files owned:** `fno/school/instructor/causes/` (`terms.py`, `market.py`, `evidence.py`, `rules.py`, `classify.py`),
`fno/school/instructor/thresholds.py` (shared by b, c and d, so it sits beside them), `CardStops` and
`NotYetReplayable` in `adapters.py`, `build_classifier` in `wiring.py`, `research/school/INSTRUCTOR_V1.md`,
`tests/school/instructor/causes/`.

**Terms (frozen):**
- **Move `z`:** `ln(S_exit / S_entry) / (sigma_atm x sqrt(T_held))`. `S` is the snapshot's spot, or the settlement
  price. `sigma_atm` is the entry snapshot's ATM straddle implied volatility of the position's nearest expiry.
  `T_held` is the calendar time held. The 90% range is `|z| <= 1.645`. 325 said "the forecast's 90% range"; v1 uses
  the option-implied range, one rule on all five roads, because v4's forecast covers NIFTY only.
- **Stance:** from the entry Greeks, never from the family label, so RC1's random structures are classed the same way:
  - short volatility: net vega < 0; long volatility: net vega > 0;
  - directional: a 1% move in `F` changes the position's value by at least 20% of its maximum loss;
  - long premium: a debit at entry; short premium: a credit.
- **Loser:** net < 0. **Winner:** net >= 0 (a winner takes the "helped" form of a tag).

**The 13 tags (325 section 6.1, thresholds frozen, all reasoning only):**

| # | Tag | Loser rule | Winner form |
|---|---|---|---|
| 1 | Move beyond range | `|z| > 1.645` | the same fact |
| 2 | Wrong direction | directional, delta P&L < 0, `|z| <= 1.645` | right direction: directional, delta P&L > 0 |
| 3 | Volatility rose | short volatility, vega P&L <= -40% of the loss | volatility fell: short volatility, vega P&L >= 40% of the gain |
| 4 | Volatility collapsed | long volatility, vega P&L <= -40% of the loss | volatility rose: long volatility, vega P&L >= 40% of the gain |
| 5 | Time decay | long premium, theta P&L <= -40% of the loss, settlement or exit level inside the entry breakevens | decay earned: short premium, theta P&L >= 40% of the gain |
| 6 | Gap through stop | exit `loss_limit`, loss above 1.25x the card's stop (`exit_loss_multiple` x the entry credit or debit). 325's futures rule (0.3%) has no use in v1: no futures | none |
| 7 | Scheduled event shock | an A6 event known at entry falls after entry and on or before exit, and `|z| > 2` | the same fact |
| 8 | Unscheduled shock | no such event, and at least 3 of the 4 underlyings moved `|z| > 2` over the same sessions (each on its own entry ATM volatility). With fewer than 3 measurable: "not testable", counted | the same fact |
| 9 | Costs ate the edge | gross >= 0 and net < 0 | none |
| 10 | Bad price or data | a snapshot SHA-256 mismatch, an impossible price (b's `impossible_keys`) on a filled or attributed leg, or a fill outside its snapshot's touch | the same fact |
| 11 | Exit whipsaw | exit `loss_limit` or `profit_target`, and holding to the card's last exit (settled through d's `settle`, computed, never recorded) would have netted more than the actual by over 1x the loss | exit cost the gain: a target exit, holding would have netted more by over 1x the gain |
| 12 | Normal noise | the mid-to-mid P&L (Greek components plus residual, before costs) within 1 standard deviation of the position's own model P&L: entry volatilities held (sticky strike), lognormal over `T_held`, 201 frozen quantiles | the same rule |
| 13 | Rule broken | replaying the frozen card (h's SHA-256) on the recorded snapshot and history gives another decision (outcome, reason or proposal) | the same fact |

- **Primary:** the first tag that fires in this frozen order: 13, 10, 6, 7, 8, 1, 11, then 2-5 by the largest
  absolute component, then 9, then 12. Tags 13 and 10 first, because those outcomes teach nothing about the market.
- **Secondary:** the next two that fire, in the same order. When none fires the path is `unclassified`: counted and
  shown, never forced into a tag.
- **Cause 11 waits** for the expiry's settlement. Until then it is "not yet testable". When the settlement arrives, a
  new classification record names the earlier one and may change the primary.
- **Modifiers (327 correction 2, which replaces 325's median of the drivers who chose to trade):** on the entry
  road-slot:
  - **hard road:** REF and RC1 both closed there with net < 0;
  - **bad driver:** the driver lost while REF and RC1 both closed with net >= 0;
  - "not testable" when either control abstained, was refused or is still open.

**Acceptance tests:**
1. One plant per tag (13 fixtures), each giving its tag as primary.
2. At and just beyond each threshold (1.645, 2, 40%, 1.25x, 1x, 1 standard deviation, 20% of maximum loss, 3 of 4).
3. Winners get the winner forms; tags 6 and 9 never fire on a winner.
4. The precedence on a fixture where four tags fire.
5. `unclassified` when nothing fires.
6. Cause 11's later record names the first one.
7. Both modifiers and "not testable".
8. The thresholds file and the card agree (test).
9. Empty: no closed path gives no record.

#### INS-d The paired comparison · `story/ms-ins-paired`

**Files owned:** `fno/school/instructor/paired/` (`values.py`, `series.py`, `holds.py`, `status.py`, `compare.py`,
`nulls.py`), `tests/school/instructor/paired/`. S2's files are untouched: the bootstrap argument once planned there was
reverted when the method changed (orchestrator's ruling b).

**Method (frozen):**
- **Pairs:** each driver version D against each control C in {N0, RC1, REF of the road}, on h's common group of
  road-days where both are counted, at the same session, road and slot.
- **Value of a road-slot:**
  - an entry decided there and closed (trade or ticket): its outcome's `return_on_risk`;
  - `no_trade` or `refused`: 0. Abstentions are kept and counted;
  - `unavailable`: left out of the pair and counted.
- **Measure:** the primary measure is per opportunity, tickets included (idea quality, review 138 section 11). The
  executed-only measure is shown beside it.
- **Clustering:** one value per session, the mean over that session's roads of (D - C). Five roads on one day are one
  point, not five.
- **Cut:** the series stops at the first session with a pair still open (S3's rule). Later closed pairs are shown
  "after the cut, not a claim".
- **Bound (orchestrator's ruling, 22 Oct 2026; it replaces the moving-block bootstrap, which failed its own null gate
  at 27% false "Watching"):**
  - the mean, and a one-sided 95% Student-t lower bound on non-overlapping batch means, counted back from the last
    session (S6's t table);
  - batch length: 1.5 times the longer of the pair's two frozen card holds, rounded up, never under 10 sessions;
  - a card's hold (`holds.py`) is the shortest bound its card states: sessions held, calendar days held, sessions
    before expiry, or days to expiry at entry less its last exit day. Without one, it is the expiry cycle (36 days
    monthly, since REF can enter at 36 days; 7 weekly). RC1 takes its rule twins' longest hold. Days become sessions at 5 a week, rounded up, and N0 holds nothing;
  - the real holds: WS1 3, CS1, DB1 and DR1 10, PS2-4 and RC1 15, PS5 18, REF 26, KL1 33;
  - batch = hold was measured first and failed the gate at holds 10-25 (upper ends 10.4-11.0%), hence the 1.5.
- **Status (`MapStatus`), v1 (orchestrator's ruling D, 22 Oct 2026):**
  - `exploratory` below 30 valid counted sessions, `not_established` from 30;
  - v1 never assigns `watching`. A sparse, negatively skewed seller (the shape of CS1, PS2-4, WS1, REF) makes the
    batch-t bound look positive falsely in up to 43.4% of runs (upper end 45.6%; loss chance 5%, hold 26, 120
    sessions), far above the 10% gate, and no t level or batch length fixes it;
  - the mean and the bound are shown as descriptive numbers, labelled "descriptive, not a test";
  - a seller-shaped driver's row says "this method can falsely look positive up to 46% for this payoff shape (rarer
    full losses can be worse)";
  - a row without a bound says "too few independent batches: no bound before N sessions";
  - Watching returns only with a v2 card (the model-variance floor, option B) whose own null gate passes the skewed
    shapes (loss chances 0.05 to 0.2, at the cards' holds) and the Gaussian ones.
- **Live null:** every review also compares RC1 with N0 on the same days, so the null's own rate of looking good is
  visible.

**Acceptance tests:**
1. Hand-computed: 3 sessions x 2 roads, with abstentions, against each control.
2. A session's five roads make one series point (series length = sessions).
3. An abstention counts as 0 and in the abstention count.
4. The cut at an open pair.
5. The v1 ladder at 29 and 30 sessions; v1 never assigns Watching, even on a clearly positive series (and no module
   but the type names it).
6. `MapStatus` has exactly three members, so no Supported or Confirmed can be built.
7. **Null calibration (327 correction 3; orchestrator's conditions 1-3):**
   - the Gaussian null's false-positive share of the bound, at 2,000 seeds, has the upper end of its 95% interval at
     10% or less at every hold the cards hold, read from the cards at test time;
   - the skewed-seller null is measured too. It fails, which is why v1 assigns no Watching, and its rate is the one
     printed on seller rows.
8. **Planted edge (325 section 6.2; orchestrator's ruling c):** the power table goes in the Claims and in the 30-session
   review. A test shows +1.0 gives a positive bound in half the seeds at 30 sessions and 95% at 60.
9. Empty: no common road-day gives no row.

#### INS-e Outputs: records, the 30-session review and the "why" line · `story/ms-ins-outputs`

**Files owned:** `fno/school/instructor/outputs/` (`store.py`, `run.py`, `controls.py`, `comparison.py`, `review.py`,
`review_text.py`, `labels.py`, `why_line.py`, `public_counts.py`, `command.py`), `fno/school/instructor/__main__.py`,
the part-e builders in `fno/school/instructor/wiring.py`, `PathReader.orphan_corrections` (criterion 8),
`tests/school/instructor/outputs/`. The public counts file goes to `research/school/counts/instructor/`, inside
MS-P1j's counts folder, so j's one counts commit takes both.

**Implements:**
- `InstructorRun.for_session(session)`: reads, attributes, classifies and pairs; writes the three record files
  write-once; idempotent.
- `DescriptiveReview.build(first, last)`, the P2 review's input, labelled "descriptive, not a claim, no licence".
  Per driver version:
  - scheduled, eligible, fillable and executed counts, and abstentions;
  - net after costs, maximum drawdown, worst day and worst trade (325 section 6.3b);
  - the attribution sums;
  - primary and secondary tag counts;
  - `poor_fit` and `unclassified` counts;
  - each paired row with its status.
- `WhyLineSource.lines(session)`: one line per trade or ticket closed that session, for example "CS1@v1 NIFTY-M:
  net -Rs 2,340; why: volatility rose (also: costs ate the edge); hard road". No contract, strike, price or card
  internal.
- The command: `python -m fno school instructor --session <date>` (and `--review <first> <last>`), dry run by
  default.

**Acceptance tests:**
1. Write-once: the same bytes again is a no-op; other bytes are refused.
2. Two runs on the same day give identical bytes.
3. The public counts file passes the record scan and holds no rupee, strike, price or symbol.
4. The "why" lines pass the same privacy test.
5. The review shows every count's denominator, refusals included.
6. A planted cause on the fake fleet appears in the review's counts and in that session's "why" line.
7. Off-switch: with `school.enabled` false the command prints "school off" and writes nothing.
8. An orphan correction (Judge K, judge 501 addendum 1; orchestrator, 22 Oct 2026): a correction whose `corrects`
   SHA-256 names no original the reader can find is counted and alerted in the review and the day's output, never
   dropped silently. INS-e adds this to the reader's `ClosedRead` (today the reader does not list them).

#### Gap list (the design's requirements for v1)

| Requirement | Part |
|---|---|
| P&L attribution (delta, gamma, vega, theta, costs, residual) for every closed trade and ticket, from the recorded snapshots | b (reader a) |
| 13 code-built causes, one primary and up to two secondary, frozen thresholds, winners too | c |
| Hard road and bad driver measured with the controls on every road-slot, abstentions kept (327 correction 2) | c (modifiers), d |
| Paired against N0, RC1 and REF on the same road, day and slot, clustered by session | d |
| Statuses Exploratory, Watching and Not established only (327 correction 3) | a (type), d |
| A measured false-claim rate on null data before trusting a test (325 section 6.2, 327 correction 3) | d test 7 |
| Planted-edge test | d test 8 |
| Feeds the 30-session review and the 20:05 "why" line | e |
| Read-only on records; never changes a decision | a test 5, Boundaries |

**Out of scope, with reason:**
- licences, and the Supported and Confirmed statuses: 327 corrections 3-4 and the owner's decision;
- the condition map's cells by condition tag: they need the frozen tag list and the minimum sample of 325 section
  6.3b, so they wait for v2;
- the regime detector and the recommender: the owner's decision;
- calibration (325 section 6.4): 327 correction 4 allows it only at 100 or more outcomes over 60 or more sessions;
- the Sharpe-like ratio: it needs a capital base per rupee-day, not yet defined for paper accounts; asked below;
- lesson cards and monthly cadence (325 section 6.5): P2+;
- futures causes: no futures in P1.

#### Questions answered (orchestrator, 22 Oct 2026; story text merged at 80625b19)

1. **Reads beyond the dashcam records:** yes. b's snapshots, d's settlement source, A6's events and e's cards are
   recorded, read-only inputs tied to the decision record by SHA-256, so they are within "reads only".
2. **The block bootstrap:** add an optional `block` argument to S2's `resampled_ratios`, its default unchanged, with a
   test that the default output is byte-identical. No second resampler (DRY). `fno/scoreboard/uncertainty.py` is
   therefore one shared file of INS-d.
3. **The command:** a module entry point (`python -m fno.school.instructor`) now, registered under j's `fno school`
   group when j lands. j's builder (session_01CmKJ6taCLzfEGg7wt6RC4N) has been told.
4. **The 20:05 line:** `WhyLineSource` is a port, joined to g's 20:05 section by one line in j's wiring. j's builder
   has been told.
5. **Tickets in the primary paired measure:** the builder's call, as the orchestrator asked. Tickets stay in the
   primary measure, with executed-only beside it. Reason: a ticket is the same idea under the same quotes and laws
   (327 correction 1), refused only by an account limit or the 5-trade cap. Leaving tickets out would make the
   comparison depend on the account limits, not on the rule.
6. **Lane:** lane 1, one judge: Judge K (session_019ZApRwkUiNMKDsf1k4W44z); not a money piece. The two deviations
   from 325 (cause 1's option-implied range, cause 6 on option stops) are accepted as stated.

**Settled in INS-a's build (builder):**
- A cause is a plain `Cause` member: a winner (net >= 0) reads it in its winner form, so the sign of the net is the
  form and no separate flag can disagree with it. `Classification` refuses causes 6 and 9 on a winner.
- The settlement price is read through d's own `IndexSettlementSource` and the records through c's `DashcamStore`,
  unchanged: no wrapper port for either (KISS).
- `CardReplay` and `InstructorStore` are ports with fakes in a. Their real adapters come with the parts that first
  use them: c (the replay over e's drivers) and e (the store over O9's `DataStore`).

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
| C2's margin room for every road, structure and width (per proposal, from the archived SPAN file) | 3.3 law 3; m |

**Out of scope, with reason:**
- futures, calendars and diagonals: probe 5 found no payoff or margin model;
- stocks and extra slots: P3+, and NSE's terms block the survey;
- AI drivers: 327 item 7, after a dry run;
- the instructor (v1 is MS-INS above, built in parallel by the owner's decision of 23 Oct), condition map,
  licences, recommender top 3 and simulator: P2+;
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

## 7. MS-SIM: the simulator (practice only)

**Lane:** 1 (evaluation records: it prices, fills and scores trades, though only as practice) · **Builder:** session_01W2JE3W9xYftEDWTysHkdVC ·
**Orchestrator:** session_01VG1RqxLFUVdvvPuMRYZtDH · **Sources:** response 325 section 8, response 327 correction 6, DESK_DECISIONS
"Simulator and Instructor v1 start now", `research/DATA_SPEND.md`, `research/edge1/RESULTS.md` (impossible-price rule),
`fno/research_engine/simulator.py` (B2's cycle simulator: the pricing-validity ancestor, not reused as an engine).

**Description:** As the statistician and the options strategist, I want the pilot's rule drivers to run unchanged on
history, behind the same `SnapshotSource` interface, so that their plumbing, sample sizes and cost sensitivity can be
practised before forward days exist. A practice result is never evidence: it licenses nothing and counts for nothing.

### 7.1 Fixed rules (owner and orchestrator; each has a named test in 7.4)

1. **Practice only.** No result licenses a driver, counts toward any card or RM1, sets a banner, or moves a map status
   past Exploratory. Every output (stdout, files, records) carries the label `practice (simulator)`. Nothing under
   `fno/school/simulator/` imports the banner, the report sections, `registration` (counting), the instructor's map
   or the licence code, and its records go to a dataset the pilot never reads.
2. **Fresh data stays fresh.** Default windows are a frozen allow-list (`PRACTICE_WINDOWS`) of data DATA_SPEND lists
   as `spent` or `exposed`; anything else is refused with `not_in_data_spend`. A fresh window needs an R1 card and a
   DATA_SPEND update first (outside this story). On 22 Oct 2026 that gives:

   | Road | Window | DATA_SPEND row |
   |---|---|---|
   | NIFTY-M | 2019 to 12 Oct 2026 | NIFTY monthly options, daily closes, `spent` (2019-23 and 2024-26) |
   | NIFTY-W | Feb 2019 to 9 Oct 2026 | NIFTY weekly options, `spent` |
   | BANKNIFTY-M | 2019 to 12 Oct 2026 | BANKNIFTY monthly options, `exposed` |
   | FINNIFTY-M, MIDCPNIFTY-M | none | **not in the register**: closed with `not_in_data_spend`. Reading them would expose unread data. They open only after an R1 card and a DATA_SPEND row (not this story) |

   Windows end at the earlier of 12 Oct 2026 and the day before `school.first_counted`, so the simulator never reads
   the closes of a day the pilot will count (those days are `forward`/`registered` for P1). The 2019-23 15-minute
   candles are `fresh` and are not used (the pilot has only the 15:00 slot). A test reads `research/DATA_SPEND.md`
   and fails if any allow-listed row there is `fresh`.
3. **Pricing honesty.** From daily records (a last-trade close, no bid, no ask, no sizes) the source builds a quote
   only when all hold; otherwise the leg's quote is invalid and the pilot's own gates refuse the trade:
   - the leg **traded that day** (volume above zero; a settlement price is not a trade);
   - the chain passes **EDGE1's impossible-price rule** on the closes (protocol section 7, via `quality.prices
     .impossible_keys`, applied to point quotes: every vertical in [0, width], single-leg bounds). A flagged leg is
     invalid for entry, trigger and exit alike; an exit leg that is invalid waits (`exit_waiting_quote`), stricter than
     EDGE1, which traded impossible exits and flagged them;
   - the bid and ask are the close less and plus the **scenario half-spread** (7.2); a bucket with fewer than 30
     quoted sessions gives `insufficient spread data`: the leg has no quote and the trade is `unavailable`, never a
     zero-spread fill and never borrowed from another bucket;
   - costs come from **C1** with the **Rs 1 pad**, **dated lots** (UDiFF `NewBrdLotQty` from 2024, NSE's circular
     schedule before, the same sources as EDGE1's `lots.py`) and **dated STT** (EDGE1's `stt_history.SCHEDULE`);
   - **no data after the decision time.** A day's snapshot is built from that day's records alone; the driver's history
     is the closes up to and including that day; expiry settlement is read on the expiry day only.
4. **The slot is the close.** History holds one price per leg per day, the last trade (about 15:30). The practice slot
   is therefore "the close", not the pilot's 15:00 capture. Every output says "close slot, not the 15:00 slot". The
   drivers receive the index close as the road's `spot` and the closes as their `SpotPoint` history. This is the
   honest limit of history [strong evidence: the files hold no intraday option price], and it is why a practice
   result can never stand in for a forward one.
5. **AI drivers are never simulated** (the model has seen 2019-26). The runner accepts only `role` rule, control or
   measurement-only cards; any other card is refused with `ai_driver_not_simulated`.
6. **No new NSE or Groww read.** History comes from what we already archive: the NIFTY panel, the archived F&O
   bhavcopy files (UDiFF and legacy) through the hash-checked library, the forward quote store for spreads. A test
   lists the module's imports (no NSE or Groww client, no order call, no Slack).

### 7.2 The spread scenarios (response 327 correction 6)

- **Learned only from our forward captures** (the hash-checked quote store of MS-P1b; NIFTY monthly from 13 Oct 2026,
  the others from 19 Oct, NIFTY weekly from 22 Oct). Never from history, never invented.
- **Bucket** = road underlying x moneyness band x days-to-expiry band. First values (card-frozen, reasoning only):
  moneyness |strike - spot| / spot in [0,1%), [1,2%), [2,4%), [4%, inf); days to expiry 0-7, 8-21, 22-45, 46+.
- **Quantity** = relative half-spread (ask - bid) / 2 / mid, floored at half a tick. A session's value is the median
  over the bucket's two-sided, valid quotes that session, so one session with 200 strikes cannot outweigh the rest.
  Relative, not rupees, because the index level moved 2019-26 (reasoning only; 7.4 test 5 checks that the relative
  spread varies less than the rupee spread inside buckets on the recorded days, or the choice is reversed in Claims).
- **Three labelled scenarios** per bucket: the median, the 75th and the 95th percentile of the session values,
  shown as `median`, `p75`, `p95`. Every practice run is shown under all three; none is "the" result.
- **Fewer than 30 quoted sessions in a bucket reads `insufficient spread data`.**
- **Displayed size: the size gate is not tested in practice** (orchestrator, 22 Oct 2026, Q5, ruling on design A). History
  holds no sizes and none is invented, and no placeholder number is used. A practice quote keeps `bid_qty` and `ask_qty`
  as `None` with `sizes_measured=False` (a field MS-P1a3 adds to `SlotQuote`). Only the practice composition root's
  `QuoteRules(practice=True)` (MS-P1d's seam, imported only by `fno/school/simulator/`) lets such a quote through the size
  and sell-back checks, with the note "size gate not tested in practice". Without that flag the pilot's live laws and
  `SchoolFills` refuse an unmeasured quote, so a practice quote reaching a live path fails closed. Every practice output
  carries the same label.
- **Honest consequence [strong evidence: arithmetic on the recorded days].** On 22 Oct only 8 NIFTY monthly sessions
  and 3 sessions for each other road are recorded. Every bucket therefore reads `insufficient spread data` until about
  24 Nov for the busiest NIFTY monthly buckets, and **much later** for the short-dated and far-strike buckets: the
  0-7 day band only exists in the last week of a cycle (about 5 sessions a month). Until then the simulator can run
  plumbing and sizes (it reports how many legs were unpriceable) but produces no priced result. This story does not
  pool buckets or lower 30 to hide that.
- Forward spreads are measured at 15:00; the practice slot is the close. Labelled: "spread measured at 15:00".

### 7.3 Design (new package `fno/school/simulator/`, one `wiring.py`)

| Component | Interface | Reuses |
|---|---|---|
| `windows.py` | `PracticeWindows.check(road, session) -> None or RefusalReason.NOT_IN_DATA_SPEND` | the allow-list of 7.1 item 2 |
| `history/` | `HistoricalChain` port: `day(road, session) -> DayChain or None` (closes, volume, open interest, expiries, index close). Adapter: `BhavcopyChain` (archived F&O files, UDiFF and legacy; one code path for all three roads) | `NiftyPanel`, `research_data`, the F&O library of `fno.storage.wiring`; EDGE1's day-file and lot readers by one adapter module (see question 1) |
| `terms.py` | `DatedTerms`: lot, STT and C1 costs on a date | EDGE1's lot schedule and `stt_history`; C1 |
| `spreads/` | `SpreadModel.scenarios(bucket) -> Scenarios or InsufficientSpreadData`; `SpreadLearner` over the quote store; `SpreadBucket` | MS-P1b's hash-checked store |
| `source.py` | `HistoricalRoadSource(chain, spreads, scenario)` implements `SnapshotSource`; `HistoricalCatalogue` implements `RoadCatalogue` (history sessions, A7 calendar, dated lots) | `SnapshotSource`, `RoadCatalogue`, `quality.prices` |
| `practice/` | `PracticeRunner.run(window, roads, drivers) -> PracticeReport` for the three scenarios; `PracticeLabel`; the isolated store | a's `FleetRunner` (MS-P1j) built by the simulator's own wiring with its own source, accounts root and store |
| `wiring.py` | the composition root; `python -m fno school practice` | one reserved line in `fno/cli.py`, added with MS-P1j's owner |

### 7.4 Sub-parts, files, order and acceptance tests

Each sub-part is its own branch `story/ms-sim-<part>`, built in order, each judged in lane 1. Files owned are under
`fno/school/simulator/<part>` and `tests/school/simulator/<part>`. Every criterion has good, bad, boundary and empty
cases and a test that fails when the named code is broken on purpose.

**SIM-a Windows and history** · depends on the pilot's contracts (on main)
- Files: `windows.py`, `history/`, `terms.py`.
- Tests:
  1. `PracticeWindows`: a spent day passes; a day after 12 Oct 2026, a day on or after `first_counted`, FINNIFTY and
     MIDCPNIFTY refuse with `not_in_data_spend` (boundary: 12 and 13 Oct).
  2. The allow-list agrees with `research/DATA_SPEND.md` (the test parses the doc; a row turned `fresh` fails it).
  3. `BhavcopyChain` returns the same monthly rows as EDGE1's own reader on the same records (parity test).
  4. A day with no file gives `None` (empty case); a muhurat or special session follows A7.
  5. `DatedTerms`: NIFTY lot 75 before the July 2021 expiry and 50 after; BANKNIFTY 20, 25, 15 at its change
     dates; STT 0.05% on 31 Mar 2023 and 0.0625% on 1 Apr 2023 (both sides of each change).
  6. No import of an NSE or Groww client (import-list test).

**SIM-b Spreads** · depends on the pilot's quote store (MS-P1b, on main)
- Files: `spreads/`.
- Tests:
  1. A bucket with 29 quoted sessions gives `insufficient spread data`, with 30 gives three scenarios (boundary).
  2. The scenarios are the median, 75th and 95th percentile of the session values on a planted bucket with known
     answer (good); an all-one-sided bucket gives insufficient (bad); no data gives insufficient (empty).
  3. A session counts once however many strikes it has (one session with 200 quotes plus 29 with 1 is 30 sessions
     but not dominated by the large one).
  4. Learning reads the recorded quote store only and refuses a hash mismatch (reuses b's checks).
  5. The relative versus rupee spread choice, with the numbers from the recorded days, in Claims.

**SIM-c The historical road source** · depends on a and b
- Files: `source.py`.
- Tests:
  1. `HistoricalRoadSource` and `HistoricalCatalogue` pass a's conformance checks (`check_road_catalogue` and the
     snapshot-source check).
  2. A leg with no volume that day has an invalid quote (good traded, bad untraded, boundary volume 1).
  3. A planted impossible vertical (a 300-wide spread priced at 392, from EDGE1's results) is flagged: the driver
     reaches `refused` or `no_trade`, never a fill; an impossible exit waits.
  4. The quote is close -/+ the scenario half-spread, floored at half a tick; bid is never below zero; both sizes are
     `None` with `sizes_measured=False` and nothing else (no number); a live-mode fill refuses the quote.
  5. Look-ahead: changing any record dated after the session leaves the session's snapshot and every driver's
     decision byte-identical (a mutation test over the chain).
  6. An insufficient bucket gives `unavailable` for that leg's trade, never a zero spread.
  7. Dated lot and dated STT enter the proposal's `max_loss` (a 2022 trade is charged the 2022 STT).

**SIM-d The practice runner and its labels** · depends on a-c and on MS-P1j's fleet runner
- Files: `practice/`, `wiring.py`, the reserved CLI line.
- **Plan (22 Oct 2026, builder; the interface names of MS-P1j's runner are confirmed when it is on main):**
  - **d1 Inputs.** A stores-only `RawFileLibrary` over `build_archive_stores()` with `StoredFilesOnly`; `BhavcopyChain` over the UDiFF and
    legacy files with `index_close` from A10's archived index-close files (criteria 9, 10); `DatedTerms` with EDGE1's circular lots and
    `dated_charges`; the A7 calendar; `PracticeWindows(first_counted)` from the configured `school.first_counted`; a `SpreadModel` learned by
    `SpreadLearner` from `recorded_snapshots` over the recorded sessions. Files: `practice/inputs.py`, `practice/spots.py` (the closes up to the
    session as the drivers' `SpotPoint` history: nothing after the session).
  - **d2 The fleet.** A second instance of MS-P1j's own `FleetRunner` class (no second runner implementation, orchestrator 22 Oct), wired in this
    package's composition root with injected practice dependencies. If j's runner cannot take them as injected dependencies, MS-P1j's builder is asked to open that seam;
    nothing is worked around or copied. The dependencies are: three `HistoricalRoadSource`s (median,
    p75, p95); `build_practice_safety_laws` and `QuoteRules(practice=True)` (criterion 12); accounts under a practice root that is not
    `journal/school`; a practice dashcam dataset; the pilot's drivers from `research/school/cards/` minus any AI-role card (criterion 5).
    Files: `practice/fleet.py`, `wiring.py`. Replay mode, fixed clock, local store: nothing is pushed.
  - **d3 The run and its report.** `PracticeRunner.run(window, roads, drivers)` loops the sessions of a window the catalogue opens, one fleet per
    scenario, and returns a `PracticeReport` with: per scenario and driver the counts (eligible, fillable, executed) and the net after costs;
    the insufficient-bucket list; the unpriceable and unsellable legs; the impossible share per road-day (criterion 14); the label
    `practice (simulator)`, the slot label and `size gate not tested in practice` on every line. Files: `practice/runner.py`, `practice/report.py`,
    `practice/labels.py`.
  - **d4 The command and the real-data dry run.** `python -m fno school practice run --from --to --roads` (one reserved line in `fno/cli.py`, agreed
    with MS-P1j's owner). A dry run on a recorded window on the Drive archive (the container has read access), its output in the Claims with
    counts only. With 8 recorded NIFTY sessions every bucket reads `insufficient spread data`, so the first real run proves the plumbing, the
    labels and the unpriceable counts, not a result.
  - **Order and dependencies.** d1 needs nothing new. d2 needs MS-P1j (the runner) and MS-P1d part 4 (on main). Criterion 13 needs MS-P1a's
    `RoadDay.lots` follow-up (asked of its owner, 22 Oct) and a one-line change in `drivers/proposals.py`. d3 and d4 follow d2. Every file stays under 350
    lines; the runner and the report are separate classes.
- Files: `practice/`, `wiring.py`, the reserved CLI line.
- Tests:
  1. The pilot's rule drivers run unchanged: the driver modules are imported from `fno/school/drivers/`, a test checks
     no driver file is edited by this story (diff-based) and that a practice run and the same card on a recorded
     fixture day take the same code path.
  2. Three scenarios per run, each labelled; an insufficient bucket is listed, never dropped; the counts of legs
     unpriceable are printed.
  3. Every output string and record carries `practice (simulator)` (a test over every printer and record builder).
  4. Isolation: the runner's dataset, account root and receipts folder differ from the pilot's; a test plants a
     practice record and proves the pilot's counting rule, banner, sections, tickets and capture gate do not see it.
  5. An AI-role card is refused with `ai_driver_not_simulated`.
  6. Twice, same bytes (replay determinism) as MS-P1i's comparator.
  7. The import-list test: no banner, report, registration, map or licence module, no order call, no Slack.
  8. The privacy test: public output holds counts only; strikes, prices and card internals go to the practice
     dataset in Drive (write-once, receipt in GitHub), never to the repository.
  9. Stores only: the F&O files and index closes are read through MS-P1b's `StoredFilesOnly` source inside a `RawFileLibrary`
     (`fno/school/roads/wiring.py`), never `build_nse_fo_library`, which falls back to an NSE fetch. A test builds the
     library with a source whose fetch raises and runs a missing day: the road closes, nothing is fetched. Named test: `test_a_missing_day_closes_the_road_and_nothing_is_fetched`.
  10. The index close: legacy-format F&O files carry no underlying price, so `BhavcopyChain` is built with `index_close`
      from NSE's archived index-close files (A10, `build_index_close_files` read through the same stores-only library).
      Named tests: `test_a_legacy_day_takes_its_index_close_from_the_archived_file` (24 Jun 2021: open road) and
      `test_a_legacy_day_with_no_index_close_closes_the_road` (`capture_missing`).
  11. Dated STT across a regime change: a position opened on 31 Mar 2023 and closed on 3 Apr 2023 keeps its two
      fills' own charges and passes `accounts/ledger_fills.py`'s recomputation check; if it does not, MS-P1d's builder
      is asked for a follow-up before SIM-d is offered for judging.
  12. The practice rules: the fleet is built with MS-P1d's `build_practice_safety_laws` and `QuoteRules(practice=True)`
      only in this package's wiring, and a test shows that without the flag the live laws and `SchoolFills` refuse a
      quote with `sizes_measured=False`.
  13. A lot per contract, not per road (judge 509, orchestrator): on 2 Jun 2025 BANKNIFTY-M's two monthlies carry different
      lots after NSE's April 2025 change, and the catalogue (c) closes the road as `lot_mismatch`. SIM-d follows the way strike
      steps are kept per expiry: each expiry keeps the lot the file states for it, and a road closes only when one
      contract's own lot is missing or contradictory. This needs the road day to carry a lot per expiry (a small additive
      follow-up to MS-P1a's `RoadDay`, as `strike_steps` was in MS-P1a2), asked of its owner first. Test with 2 Jun 2025: BANKNIFTY-M open
      with each expiry's own lot, a proposal's units follow the leg's expiry.
      Agreed with MS-P1a's owner (22 Oct): `RoadDay.lots` and `lot_for(expiry)` are built exactly like `strike_steps`/`step_for` (a4, additive,
      `lot` stays the nearest expiry's lot, `lot_for` raises for an expiry it does not name), after MS-P1j merges. MS-P1e's owner changes both
      reads in `drivers/proposals.py` (lines 44 and 45) to `lot_for(plan.expiry)`; fills and margin follow because they read `Proposal.lot`.
      The live catalogue keeps closing a road on mixed lots until a4 is on main, e reads `lot_for`, and a test on the 2 Jun 2025 archive shows
      BANKNIFTY-M's near and far monthlies proposing with their own lots, units, fill costs and margin; turning it on for live is the orchestrator's decision.
      Until then only the practice catalogue fills `lots`.
  14. The report shows the share of impossible legs per road-day, separate from refusals (judge 509: 42-177 of 260-436 traded
      legs on closes, mostly the closes' own staleness). Named test: `test_the_report_counts_impossible_legs_apart_from_refusals`.
      Without it a practice result reads as a full chain.
  15. Separation by test, not convention (orchestrator, 22 Oct): a practice run writes nothing under the pilot's dashcam, accounts, tickets or
      counts paths, and the pilot's readers never read the practice dataset. Two named tests plant a practice record and a pilot record and show
      neither reader sees the other (`test_a_practice_run_writes_nothing_under_the_pilots_paths`,
      `test_the_pilots_readers_never_read_the_practice_dataset`). Every practice record carries `practice (simulator)` in the record itself,
      not only in the report (`test_every_practice_record_carries_the_label`).
  16. Data spend, by name: a window that DATA_SPEND does not list as spent or exposed is refused naming the road and `not_in_data_spend`
      (FINNIFTY and MIDCPNIFTY refused, NIFTY accepted); a run over such a window raises before any session is read, and no
      record is written. Named test: `test_a_window_over_an_unregistered_road_is_refused_by_name`. Practice never consumes a fresh outcome window.

### 7.5 Gap list

| Requirement (task and responses 325 s8, 327 c6) | Covered by |
|---|---|
| Rule drivers unchanged on history behind `SnapshotSource` | c, d |
| Practice only; never licenses, counts, banners or moves a map status | 7.1 item 1; d tests 3, 4, 7 |
| Fresh data stays fresh; R1 card and DATA_SPEND update for any fresh window | 7.1 item 2; a tests 1, 2 |
| EDGE1 validity rule; leg traded that day | c tests 2, 3 |
| Three labelled spread scenarios; 30-session rule | 7.2; b tests 1-3; d test 2 |
| C1 costs, Rs 1 pad, dated lots and STT | a test 5; c test 7 |
| No data after the decision time | c test 5 |
| AI drivers never simulated | d test 5 |
| No new NSE or Groww read | a test 6; d test 7 |

**Out of scope, with reason:** the instructor and the condition map (their own stories); futures, stocks, calendars
(no verified payoff or margin model, P3+); 15-minute slots (the 2019-23 candles are fresh, and the pilot has one slot);
FINNIFTY and MIDCPNIFTY history (not in DATA_SPEND); fitted slippage between the witness quote and the next snapshot
(response 325 8.3; needs the A16 quotes, which do not exist yet); a daily Rs 25,000 stop between slots (a known limit,
as in 3.6).

### 7.6 Questions for the orchestrator (answered 22 Oct 2026)

1. **Reuse of EDGE1's readers** (`research/edge1/edge1study`: `day_files`, `lots`, `stt_history`). They sit under a
   frozen `research/` folder and import by a path trick. My default: one adapter module imports them read-only; I never
   copy or edit them. The alternative is promoting them into `fno/` first, which is another builder's frozen area.
   Say if you prefer the promotion.
2. **Dated costs seam.** The pilot's cost model may read today's STT. If so, dated STT needs a seam in MS-P1d's code (a
   small lane-1 follow-up to its owner). I will check the merged code first and report; I will not edit another
   story's sub-package.
3. **Pooling.** With the 30-session rule and 8 recorded sessions, almost every bucket is insufficient for months
   (7.2). I keep the rule as agreed. If you want a coarser first bucket grid (for example two DTE bands), that is a
   decision for the owner and a card change, not mine.
4. **The close slot** (7.1 item 4) departs from the 15:00 slot. It is the only slot history holds; confirm.
5. **Displayed sizes** (7.2): design A. Sizes stay `None` with `sizes_measured=False`; only the practice flag passes the size checks, labelled "size gate not tested in practice". The first ruling (a sentinel) was withdrawn by the orchestrator.

**Answers (orchestrator, 22 Oct 2026):** Q1 import EDGE1's readers read-only through ONE adapter, never edit or copy
them. Q2 yes: check the merged code, and if dated STT needs a seam, message MS-P1d's builder
(session_014VUoPfMfRWNXyJSnXxB5NL) and copy the orchestrator. Q3 keep the 30-session rule, no pooling (review 139).
Q4 the close slot, labelled "practice at the close; the pilot trades 15:00". Q5 waived and labelled, no synthetic size.
SIM-a to SIM-c start now; SIM-d waits for MS-P1j.

### 7.8 SIM-e: the practice archive (lane 1: records, an outside service, a push)

**Why:** the owner's rule of 16 Oct is that every derived data file lives write-once in Drive with a SHA-256 receipt in
GitHub. SIM-d's practice output is local and git-ignored, so by the orchestrator's hard limit (23 Oct) **no practice
result may be shown to the owner, put in a report or used in a decision** until it is archived. SIM-e archives it and
lifts the limit for archived runs only.

**Design (reuse the pilot's mechanism; no new one):**
- **A dedicated Drive area** `school-practice/`, under the same data store as the pilot's `school/`: O9's `DataStore`
  (write-once, `RawFileConflict` on other bytes), the receipts through the same `ReceiptPublisher` pattern, one receipt per
  file under `receipts/data/school-practice/`. The pilot's readers, seal checker and counts never read that area, and its
  receipt folder is a different folder.
- **A name that can never collide with the pilot's paths:** every practice path is `school-practice/<run id>/<scenario>/...`
  and the area name is not a prefix of, and does not start with, the pilot's `school` area plus a slash or the reverse. A
  test builds every pilot path function (dashcam slot files, counts) over a sample of sessions and proves none starts with
  `school-practice/`, and that a run id with `/`, `..` or an empty name is refused.
- **Run id** = `<first>_<last>_<hash of roads and scenarios>_<code commit>` (the checkout's `HEAD`, short). The same run
  on the same code is the same id; a later commit is a new id, so an old archived run is never touched, and a result that
  changed with the code cannot overwrite the earlier one.
- **What is archived:** the practice dashcam files the fleet wrote (decisions, outcomes, drift per session and scenario) and
  **the report's own text** as `report.txt` (plain UTF-8, every line labelled; Judge H minor c, one name in story and code), so the text the owner reads is itself archived and its SHA-256 is in a receipt.
- **The label stays inside every record:** the archive refuses a file in which any stored line lacks `practice (simulator)`
  (it reads the lines back with `labels`), and refuses a file that is not a gzip of canonical record lines.
- **Idempotent reruns:** archiving the same run again with the same bytes returns the same seals and makes no commit; other
  bytes for an existing key are refused as `rule broken`, nothing written, exactly like the pilot's dashcam.
- **Archiving is explicit:** `school practice run --archive` (default: local only, as today). It runs first, archives
  second, verifies third (each file read back from Drive through the verified cache and compared with its receipt).
- **The limit lifts only for an archived run.** The report's first line says `archived: run <id>, <n> files, receipts
  <folder>, first receipt commit <sha>` only when every file of the run has a verified receipt on the remote; otherwise it
  says `local only, not archived` as now (a run that failed half-way archived is reported partial, never as archived).
  Nothing else changes the limit; the never-tune sentence stays on every report.
- **Privacy:** the repository gets receipts only (path, SHA-256, size); the records and the report are in Drive. A path
  carries dates, a road-set hash and a commit, never a strike, price or card detail.

**Sub-parts** (branches `story/ms-sim-e1`, `e2`, `e3`): **e1** the archive core (`fno/school/simulator/archive/`: run id,
path builder, label check, `PracticeArchive` with a fake store in the tests); **e2** the command and the report line;
**e3** the real run: a small window archived to Drive, read back, rerun to prove it is idempotent, the receipts counted.

**Acceptance tests (named, each with a plant):**
1. `test_a_practice_path_never_starts_with_a_pilot_path_and_the_reverse` (every pilot path function over sample sessions),
   `test_a_run_id_with_a_slash_dots_or_nothing_is_refused`.
2. `test_a_file_without_the_label_on_every_line_is_refused` and `test_a_file_that_is_not_canonical_record_lines_is_refused`.
3. `test_archiving_twice_with_the_same_bytes_returns_the_same_seals_and_makes_no_second_commit`,
   `test_other_bytes_for_an_archived_key_are_refused_and_nothing_is_written`.
4. `test_the_report_text_is_archived_and_its_sha_is_in_a_receipt`.
5. `test_the_first_line_says_archived_only_when_every_file_has_a_verified_receipt` (a missing receipt, a damaged read-back and
   a half-finished run each give `local only, not archived`).
6. `test_a_practice_receipt_is_in_the_practice_folder_and_the_pilots_seal_checker_never_sees_it`.
7. `test_the_default_run_archives_nothing` (no Drive, no push without `--archive`).
8. The import test: only the exact store and publisher names; no order, Slack or Groww path.
9. e3: a real archived window, a rerun with no new commit, every receipt's SHA equal to the Drive file's, counted in the Claims
   (counts and SHA prefixes only).

**Questions for the orchestrator (answered 23 Oct 2026, below):**
1. **The receipts commit and push to `main` by the command**, as the pilot's dashcam does (a data commit). Do you accept
   that for a manual command, or should practice receipts go to a branch?
2. **`ReceiptPublisher` lives in the pilot's dashcam package** (`fno/school/dashcam/publisher.py`), which the simulator's
   isolation test bans. I would import exactly `GitReceiptPublisher` and `ReceiptPublisher` there, one file, by name; or
   MS-P1c's owner moves the publisher to a neutral module (`fno/storage/`). Which?
3. **Run id with the code commit** (above) or a name the owner gives: I recommend the commit, so a changed result is a new run.

**Answers (orchestrator, 23 Oct 2026, text approved):**
1. **Receipts go to `main`** as a data commit, like the pilot's. The command commits only `receipts/data/school-practice/<run id>/` by exact path, never a folder glob, with the record scan on. It pulls before the push; on a refused push it pulls and retries once, then reports "receipts NOT pushed" and leaves the Drive copy as the record.
2. **The publisher moves to a neutral module under `fno/storage/`** (one shared mechanism, no isolation exception). MS-P1c's owner is asked first; if no live owner answers, the move is done here as a pure move, with the old import kept as a re-export only until the dashcam imports from the new place, then removed. Lane 1 for the move (Judge B), with a test that the pilot's dashcam receipts are byte-identical before and after. The archive core takes the publisher through a protocol, so e1 does not wait.
3. **The run id includes the code commit and the digest of the input datasets' receipts**, so new captures also make a new run; it is short in paths (a hash: `<first>_<last>_<12 hex>`). **Retention:** archived runs are never deleted; a run is archived only by explicit `--archive`.
4. Counts files are not archived: they are derived, carry no label and are reproduced by the report, which is archived.

### 7.7 Claims

#### SIM-a Claims (round 1, branch `story/ms-sim-a`; builder session_01W2JE3W9xYftEDWTysHkdVC; the SHA is in the commit carrying this text)

Built: `fno/school/simulator/{constants,windows,terms}.py`, `history/{ports,bhavcopy_chain,edge1}.py`, tests under
`tests/school/simulator/`. Changes to story text: the Q5 ruling (design A) and test 3 below.

| Criterion (7.4 SIM-a) | Code | Tests (all in `tests/school/simulator/`) | Broken-code proof (mutation, caught) |
|---|---|---|---|
| 1 windows: spent day passes, 12/13 Oct boundary, FINNIFTY/MIDCPNIFTY refused, `first_counted` | `windows.py` | `test_windows.py` (7 tests) | `<=` to `<` on the last day; `first_counted - 1 day` to `first_counted`; BANKNIFTY entry renamed |
| 2 allow-list agrees with DATA_SPEND | `windows.py` rows | `test_every_allowed_window_rests_on_a_spent_or_exposed_register_row`, plus a planted `fresh` row | the planted row is read as `fresh` |
| 3 chain: rows, monthly/weekly, board lot never derived, empty and damaged files, index close | `bhavcopy_chain.py`, `ports.py` | `history/test_bhavcopy_chain.py` (8 tests, incl. parity with EDGE1's own `rows_of` on the same records) | monthly flag inverted; `board >= 0`; `want_monthly` inverted |
| 5 dated lots and STT on both sides of each change | `terms.py`, `history/edge1.py` | `history/test_dated_terms.py` (10 cases) | file lot ignored; STT always the 2026 rate; schedule check removed |
| 6 no NSE, Groww, order, Slack, store-wiring, counting or report import | (all of `simulator/`) | `test_isolation.py`, one case per file, plus a planted banner import | n/a (planted import caught) |

- **Test 3 changed.** The story said "`PanelChain` and `BhavcopyChain` return the same closes". I dropped `PanelChain`: the committed
  panel holds NIFTY monthlies only and no lots, so a second chain would duplicate one code path for three roads. The
  parity check is against EDGE1's own reader on the same records.
- **9 of 9 mutations caught.**
- **Real-data run (round 2, with Drive read access, stores only, no NSE fetch; a throwaway script, not committed):**
  `BhavcopyChain` over the archived files read, in 2-4 s a day:
  - NIFTY 2 Jun 2025: current format, 1,620 rows, close 24,716.6, the files state lot 75 (the case judge 500 raised);
  - NIFTY 4 Mar 2024: current format, 1,507 rows, close 22,405.6, monthly 28 Mar and 25 Apr, weeklies 7 and 14 Mar;
  - NIFTY 9 Oct 2026: 1,888 rows, lot 65;
  - NIFTY 24 Jun 2021 and BANKNIFTY 31 Mar 2023: legacy format, 2,070 and 1,152 rows, no lot in the file (so the circular schedule applies), and **no index close**.
  The earlier Claim "no Drive settings in this container" was wrong: I had not checked the environment. Corrected.
  - **Finding for SIM-d:** legacy-format files carry no underlying price, so those days have `index_close=None` and the road closes
    (`capture_missing`) unless the wiring passes `BhavcopyChain(index_close=...)` from NSE's archived index-close files (A10).
    SIM-d's wiring must do that and test it.
- **Round 2 (judge 500):** (1) the circular lot schedule now applies to legacy-format days only; a current-format day with no stated lot has no lot
  (test on 2 Jun 2025: none; with the file's 75: 75). (2) The size sentinel constant is removed from this branch and 7.2 and test 4 describe design A.
  (3) EDGE1 is loaded by file path under the unique package name `ms_sim_edge1study`; `research/edge1` is not on `sys.path` (tests pin both).
- **A requirement for SIM-d (found while reading `fno/storage/wiring.py`):** `build_nse_fo_library` reads the stores
  first and then falls back to NSE. The simulator's wiring must build `DailyFiles` from the stores only, with a test
  whose NSE fallback raises, or "no new NSE read" breaks on a missing day.
- **A finding for SIM-d on dated STT (Q2).** The charges are a mapping passed at wiring (`cfg["charges"]`) and EDGE1's
  `charges_on(date)` already returns one per date, so no seam is needed to price a fill. The risk is
  `accounts/ledger_fills.py`, which recomputes a past fill's charges from the mapping it is given and checks them against
  the stored leg: a position opened under one STT rate and re-read under another would fail that check. Wiring one fleet per session
  with that session's mapping is not enough for an account that spans 31 Mar and 1 Apr 2023. I will test it in SIM-d and
  message MS-P1d's builder only if it fails.
- **Gates at this tip (full run on the SIM-a files):** `pytest -n auto`: 11,733 passed, 16 xfailed, 1 failed:
  `tests/ai/test_fire_and_collect.py::test_a_reveal_that_never_came_or_does_not_match_records_no_forecast`. It passes alone
  and passes on the branch's parent with my files stashed, so it fails only under load. Whether that is a flake or a real defect is not established: the orchestrator said it is a real issue to root-cause and is routing it separately. Outside this story; I did not
  touch it. `ruff check`, `check_imports` (clean, 2,249 files) and `check_records` (clean) pass.
- Self-review by independent review agents: not yet run; I run them on the SIM-c tip, over all three parts.

#### SIM-b Claims (round 1, branch `story/ms-sim-b` on `story/ms-sim-a`; the SHA is in the commit carrying this text)

Built: `fno/school/simulator/spreads/{bucket,model,learner,recorded}.py`, tests in `tests/school/simulator/spreads/`.

| Criterion (7.4 SIM-b) | Code | Tests | Broken-code proof (mutation, caught) |
|---|---|---|---|
| 1 29 sessions insufficient, 30 give three scenarios | `model.py` | `test_29_quoted_sessions_are_insufficient_and_30_give_three_scenarios` | the limit 30 to 29; `<` to `<=` |
| 2 median, 75th, 95th percentile with a known answer; all-one-sided and empty are insufficient | `model.py`, `learner.py` | `test_the_scenarios_are_the_median_75th_and_95th_percentile...`, `test_an_all_one_sided_bucket_and_an_empty_input_are_insufficient`, `test_an_unknown_bucket_is_insufficient...` | 0.95 to 0.9; 0.75 to 0.5 |
| 3 a session counts once; a big session does not dominate; two roads of one underlying on one day count once | `learner.py` | `test_a_session_counts_once...`, `test_two_roads_of_one_underlying...`, `test_a_session_value_is_the_median_of_its_quotes` | session median to max |
| 4 only verified recorded captures; a tampered, missing or incomplete one is skipped with its reason | `recorded.py` over MS-P1b's `CaptureReader` | `test_recorded.py` (4 tests) | the caught exception type changed |
| bucket edges on both sides (1% and 2% and 4% moneyness; 7, 8, 21, 22, 45, 46 days) | `bucket.py` | `test_the_moneyness_band_edges`, `test_the_days_to_expiry_band_edges` | `>=` to `>`; day edges not shifted by one |
| half a tick floor; uncrossed, valid, two-sided only | `learner.py` | `test_a_quote_is_its_half_gap...`, `test_a_one_sided_invalid_or_crossed...` | floor removed; crossed check removed |
| 5 relative against rupee spread, with numbers | none (a measurement) | the run below | n/a |

- **11 of 11 mutations caught.**
- **Criterion 5, round 2 (judge 502 asked for it in the Claims).** My earlier statement that this container had no Drive access was wrong: I had
  not checked the environment. I re-ran the comparison myself (throwaway script, not committed) over MS-P1b's verified `CaptureReader`
  on the recorded sessions of 13-22 Oct 2026, all five roads (16 verified captures read; 39 road-days had none and were skipped).
  For each bucket with at least 3 quotes I took the coefficient of variation of the half-spread (half-tick floor) over all its valid two-sided quotes:
  - the relative half-spread varies less than the rupee one in **41 of 48 buckets**, the same as Judge H's run;
  - the 7 exceptions are FINNIFTY and MIDCPNIFTY far or deep strikes, for example MIDCPNIFTY 2-4% from the money, 22-45 days: 1.17 against 0.81 (115 quotes, 3 sessions);
  - every bucket has only 1-6 sessions. **Some evidence** for the relative choice, not strong evidence; revisit at 30 sessions.
- **Capture period in the label (judge 502, minor a).** `SPREAD_LABEL` now reads "spread learned from forward captures since 13 Oct 2026, measured at 15:00".
  Reasoning only: spreads were probably wider in earlier years, so practice is optimistic. This is why the three scenarios are always shown together.
- **Consequence stated in 7.2 stands:** with 8 recorded NIFTY sessions every bucket reads `insufficient spread data`;
  the code returns exactly that and nothing else.

#### SIM-c Claims (round 1, branch `story/ms-sim-c` on `story/ms-sim-b`; the SHA is in the commit carrying this text)

Built: `fno/school/simulator/source/{catalogue,snapshots,quotes,steps,coverage}.py`, tests in
`tests/school/simulator/source/`. Files changed from the story: the package is `source/` (several small files), not one `source.py`.

| Criterion (7.4 SIM-c) | Code | Tests | Broken-code proof (caught) |
|---|---|---|---|
| 1 conformance of catalogue and source | `catalogue.py`, `snapshots.py` | `test_the_catalogue_and_source_pass_the_pilots_conformance_checks` | n/a (a's checks) |
| 2 traded that day; volume 1 is traded, 0 is not | `snapshots.py` | `test_a_leg_that_did_not_trade...` | `volume > 0` to `>= 0` |
| 3 impossible vertical flagged, both legs unquoted | `snapshots.py` over `quality.prices.impossible_keys` | `test_a_planted_impossible_vertical...` | the flag branch removed |
| 4 close -/+ half-spread, tick-outward, no bid below zero, sizes `None` with `sizes_measured=False` (design A; reworked on MS-P1a3) | `quotes.py` | `test_quotes_and_steps.py` (10 tests, incl. 7.5 at 2%, which floors wrongly without the epsilon) | floor to round; epsilon 0; floor at half a tick removed; sizes changed |
| 5 look-ahead: only the session's own chain is asked for; same day, same bytes; changed close, changed bytes | `snapshots.py` | `test_only_the_sessions_own_chain_is_read`, `test_the_same_day...`, `test_the_digest_covers_the_close...` | the day asked for shifted by one |
| 6 insufficient bucket: no quote, counted, never zero spread | `snapshots.py` | `test_an_insufficient_bucket...` | zero-spread quote substituted |
| 7 dated lot and dated STT | `terms.py` (a), used by `catalogue.py` | `test_a_2022_trade_is_charged_the_2022_stt...`, lot tests | lot ignored in a; STT date fixed in a |
| window, expiries, lot, step | `catalogue.py`, `steps.py` | catalogue tests, step tests | window check; expiry count; expiry cut-off; lot-agreement; modal step; near-the-money group |

- **Mutations: 23 of 23 caught** over a, b and c (two first survived; tests were added and re-run).
- **Self-review by an independent agent** (fresh context, given the diff and the rules, not my conclusions). No blocking
  finding. Each finding checked by me:
  - *Accepted and fixed:*
    1. A weekly expiring on the session is not recorded (A4f takes `e > day`, `fno/quotes/weekly.py:22`; I checked it); monthlies still from today.
    2. The digest ignored `last` and the sizes: two different archives could share a hash. Now hashed.
    3. `priced` counted a leg whose bid rounds to nothing: now `unsellable`.
    4. The window is re-checked in the source, so a hand-built road day cannot read a fresh day.
    5. The index close comes from the nearest expiry's rows, not the first row.
    6. A malformed number makes that format unreadable instead of reading as zero.
    7. A contract listed twice counts once.
    8. The tick constant is shared (DRY).
    9. The weak look-ahead test was cut to its real assertion.
  - *Not changed, with reason:*
    1. **Impossible prices judged on the whole chain, not the band.** Intended and conservative: the card's band is not known to the
       source, a stale far strike can only remove quotes, never add one. The cost is that the pilot's `IMPOSSIBLE_PRICE` road
       closure is not exercised in practice; practice shows the same cases as `coverage.impossible`. Stated here.
    2. **`PracticeWindows(first_counted=None)` default.** The windows already end 12 Oct 2026, before any forward capture; `first_counted`
       only moves the end earlier. SIM-d's wiring passes the configured value, and I add a wiring test there.
    3. **`sys.path` insert in `history/edge1.py`:** accepted in round 1, then removed in SIM-a round 2: EDGE1 is loaded by file path under a unique package name and its folder never joins `sys.path` (judge 500 minor a, fixed; judge 509 minor b).
    4. **Spread learned from Oct 2026 and applied to 2019-26; P95 of session medians.** Disclosed regime assumption, why the
       three scenarios are always shown together. No change.
- **Design A rework (22 Oct, after MS-P1a3 `9ede0d1e`):** quotes carry sizes `None` with `sizes_measured=False`; no placeholder constant exists. `test_the_live_fill_path_refuses_an_unmeasured_quote...` shows E4's `price_leg` refuses it ("quote not valid: no size") without MS-P1d's practice rules, so a practice quote reaching a live path fails closed. The practice-mode pass-through itself is MS-P1d's and is tested in SIM-d. **Not yet run on real data:** the catalogue and source are tested on fixtures; `BhavcopyChain` alone ran on the Drive archive (SIM-a Claims). SIM-d's dry run does the end-to-end run (the container does have Drive access).
- **Gates at this tip:** `ruff check`, `check_imports` (clean) and `check_records` (clean) pass. `pytest -n auto` over the whole repository was run on
  the a tip (11,733 passed, one unrelated load flake, see SIM-a); at this tip `tests/school` passes (1,414 tests); the full run at the design-A tip `3c1a3cc6` (clean worktree, `pytest -q -n auto`) is 12,001 passed, 16 xfailed, 0 failed in 510 s (judge 509 reproduced 12,001).

#### SIM-d1 Claims (round 1, branch `story/ms-sim-d1` on main 2c42886b; the SHA is in the commit carrying this text)

Built: `fno/school/simulator/practice/{stores,index_closes,cached_chain,spots}.py`; `BhavcopyChain`'s index-close lookup now takes `(underlying, session)`.
Tests: `tests/school/simulator/practice/test_inputs.py`, `tests/school/simulator/history/test_bhavcopy_chain.py` (one new test).

| Criterion | Code | Named test | Broken-code proof (caught) |
|---|---|---|---|
| 9 stores only | `stores.build_stored_library` (`StoredFilesOnly`) | `test_a_missing_day_closes_the_road_and_nothing_is_fetched`, `test_the_stores_module_never_builds_a_fetching_library` | a fetching source put behind the stores |
| 10 legacy day takes the archived close | `index_closes.ArchivedIndexCloses` | `test_a_legacy_day_takes_its_index_close_from_the_archived_file` | the close name fixed to NIFTY's |
| 10 no close closes the road | `bhavcopy_chain._close` over the catalogue | `test_a_legacy_day_with_no_index_close_closes_the_road` | n/a (a's rule) |
| spot history: strictly before the session | `spots.ChainSpotHistory` | `test_the_spot_history_is_the_closes_strictly_before_the_session` | last day moved to the session; the usable-close condition removed |
| each day read once | `cached_chain.CachedChain` | `test_the_cached_chain_reads_each_day_once` | cache removed |

- **A fix to my own SIM-a code found here.** `BhavcopyChain` asked for the index close by date only, so BANKNIFTY would have received
  NIFTY's close on a legacy day. The lookup now takes `(underlying, session)`; `test_each_underlying_gets_its_own_index_close_from_the_lookup`
  pins it; the mutation that hard-codes NIFTY is caught.
- **7 of 7 mutations caught** (two survived at first: the coverage check and the spot-history cut-off; a test was added for the first and the mutation string for the second was wrong).
- **Real-data check** (throwaway script, Drive archive, stores only, source "stored files only"):
  - NIFTY 24 Jun 2021 (legacy): index close 15,790.45, 2,070 rows (6.6 s); BANKNIFTY the same day: 34,827.0, 2,224 rows. Each index has its own close.
  - NIFTY 2 Jun 2025 (current format): 24,716.6, 1,620 rows; BANKNIFTY: 55,903.4, 928 rows.
  - BANKNIFTY's 42 sessions of spot history before 24 Jun 2021 (26 Apr to 23 Jun 2021): the first call took 131 s (about 3 s a day, uncached). With the cache every later session reads one new day.
- **Isolation test.** `practice/stores.py` imports `fno.storage.wiring` and `fno.storage.raw_source` to name the NSE datasets (their file names and archive paths). The isolation test allows these two imports for that one file only, with its reason; the file builds no fetching library.
- Gates at the tested tip `01bf888d`: full `pytest -q -n auto` in a clean worktree: **13,841 passed, 16 xfailed, 0 failed** in 522 s; `tests/school/simulator` 133 passed; ruff and check_imports clean; the record scan passed on commit.
- **Question for Judge H (orchestrator's suggestion):** `practice/stores.py` needs the NSE datasets' file names and archive paths. They are class attributes of the NSE source classes in `fno/storage/raw_source.py`, and `daily_files` that wraps them is in `fno/storage/wiring.py`. Moving them to a constants module would change those frozen-adjacent files, which I do not own. Should they move, or does the one-file exception stand? **Judge 515 minor, applied:** the exception now names the exact imports (`daily_files`, `NseDailyFoSource`, `NseLegacyFoSource`, `NseIndexCloseSource`, plus their two modules) for that one file; a plant that adds `build_nse_fo_library` to `stores.py` fails the isolation test (checked on the real file, and `test_a_library_builder_import_in_stores_is_caught_while_the_dataset_names_pass`).

#### SIM-d2, d3 and d4 Claims (round 1, branch `story/ms-sim-d2` on `story/ms-sim-d1`, MS-P1j's seams `6d3aa180` and MS-P1m's factor seam `2992864d`; the SHA is in the commit carrying this text)

Built: `fno/school/simulator/practice/{clock,dated,dashcam,gate,margin,drivers,fleet,window,runner,report,render,wiring}.py` and
`fno/school/simulator/command.py`; tests in `tests/school/simulator/practice/` and `tests/school/simulator/test_command.py`.

| Criterion | Code | Named test | Broken-code proof (caught) |
|---|---|---|---|
| 1 drivers unchanged | `fleet.py` builds the pilot's `SchoolFleet` and `build_school_drivers` | `test_it_is_the_pilots_own_fleet_class_with_the_practice_rules` | `rules=PRACTICE` swapped for LIVE |
| 2 three scenarios, insufficient listed, unpriceable counted | `runner.py`, `report.py`, `render.py` | `test_a_window_runs_every_scenario_over_every_session`, `test_every_line_carries_the_label...` | counts read dropped |
| 3 every line labelled | `render.line` | same | label removed |
| 4/15 isolation | `fleet._refuse_pilot_paths`, runner home | `test_a_home_inside_the_pilots_records_is_refused...`, `test_a_run_writes_nothing_under_the_pilots_paths` | guard removed |
| 5 AI card refused | `drivers.simulable` | `test_an_ai_card_is_refused_by_name...`, `..._the_practice_fleet_refuses_an_ai_card_when_it_is_built` | `simulable` removed; family test removed |
| 11 dated STT across a change | `dated.cfg_on` | `test_a_position_opened_before_the_stt_change_and_met_after_it_keeps_its_own_charges` (31 Mar then 3 Apr 2023, real fills, each leg's charges equal the 31 Mar mapping's) | **(correction: the plant `cfg_on` to `parts.cfg` was not caught at 6634659a; the criterion rested on a strict `xfail`, which fails whatever the cause. Round 2 below catches it.)** |
| 12 live laws refuse unmeasured sizes | `fleet.rules` | `test_without_the_practice_rules_the_live_fleet_closes_every_road...` | n/a |
| 14 impossible share apart from refusals | `report.RoadDayCoverage` | `test_the_impossible_line_gives_the_share_of_legs`, `test_the_impossible_share_is_legs_over_legs...` | share forced to 0 |
| 15 label in the record itself | `dashcam.PracticeDashcam` | `test_every_stored_record_line_carries_the_practice_label`, plain `ReplayDashcam` still reads the file | label removed |
| 16 refused by name before any read | `window.RunWindow.check`, `command.cmd_practice_run` | `test_a_window_over_an_unregistered_road_is_refused_by_name_before_any_session_is_read`, `test_a_refused_window_exits_2_names_the_road_and_builds_nothing` | check removed; last day not checked |

- **Corrections to earlier rulings, found by running it:**
  1. The practice clock is 15:30, not 15:31. At 15:31 all 7 fills of the first smoke run were `stale_seal` (law 6 refuses a fill after the close) while the run looked fine. `test_the_trades_really_fill_none_is_refused_by_a_stale_seal` pins it.
  2. Under the practice rules `executed` read 0 although the fills happened: `fleet/fill.py:79` allocated the shared size under LIVE. MS-P1j's builder fixed it (`FillStep.rules`, 54ef5d40); `test_account_trades_are_executed_not_size_shared...` (first a strict `xfail`) now passes.
  3. `SchoolFleet.run()` read `school.enabled`, a pilot-only switch. MS-P1j's builder moved the check to the pilot's entry points (54ef5d40); `_practice_switch` is deleted and the practice root passes the pilot's configuration unchanged.
  4. The pilot's capture-window rule would close every road at the close (`out_of_window`), so the practice gate keeps the catalogue status and the road-day check only.
  5. The stress-factor file has rows only from 14 Oct 2026 and each is valid for 30 days, so law 3 would refuse every historical entry. Practice uses the file's latest factor (2.1) on that session's own archived SPAN, labelled on every output; law 3 itself is unchanged (MS-P1m's `factor` seam).
  6. The first real-data run made CS1 `unavailable: deadline` on a cold first session (the Drive read ran inside the driver's 60 s). The runner now reads the archive before the fleet runs; `test_the_archive_is_read_before_the_fleet_runs...` fails without it. The rerun had no `unavailable`.
- **Real-data dry run** (`PracticeRunner` through `cmd_practice_run`, Drive archive stores only, recorded captures for the spreads; 4-8 Mar 2024, NIFTY-M, NIFTY-W, BANKNIFTY-M; 154 s, exit 0). Counts only:
  - 4 sessions run (8 Mar was a holiday), 3 scenarios, 12 road-days, **4,710 legs: priced 0, untraded 1,356, impossible 1,276 (27%), unsellable 0, insufficient spread data 2,078**;
  - every driver `no_trade` in every scenario, 0 refused by margin; 24 recorded captures were left out of the spread model (missing or failed a check);
  - every line begins `practice (simulator) |`. No quote can be priced yet: the recorded sessions are far below 30 for every bucket, so this run proves the plumbing, the labels and the unpriceable counts, not a result.
- **Deviations from the story, for the judge:**
  1. Criterion 8 asked for the practice records in a Drive dataset with a receipt in GitHub. They are written locally under `work/school_practice/` (git-ignored), never in the repository, and nothing is pushed; a Drive upload is a later step for the orchestrator to schedule.
  2. The command is registered by two lines in MS-P1j's `fno/school/cli.py`, added in this branch with its builder's agreement.
  3. Isolation exceptions, each exact and with its reason in `test_isolation.py`: `practice/stores.py` (the NSE dataset names), `practice/fleet.py` (`build_road_margin`), `practice/runner.py` (`account_net`, a pure function).
- **A pilot bug the practice run found (reported to MS-P1j's builder and the orchestrator, 23 Oct):** once fills really executed, session 2 of a window stopped with `account unreadable REF@1 (AccountError: a fill before the account's first view)`. `TicketBook.open` records into the ticket ledger, whose accounts are never `view`ed (only the drivers' are), so the first ticket ever recorded for a driver stops the fleet. The pilot goes through the same `books_on`. **Fixed by MS-P1j's builder at `1f767528`** (every store the fleet records into is viewed before any fill; `tests/school/fleet/test_first_ticket.py`). My two tests (criterion 11 and the multi-session runner test) were strict `xfail` until then; both are now plain passing tests, so criterion 11 really runs the 31 Mar to 3 Apr 2023 regime change with positions recorded and read back (before 54ef5d40 it had passed vacuously, because nothing was recorded).
- **Hard limit (orchestrator, 23 Oct; the owner's rule of 16 Oct: every derived data file lives write-once in Drive with a receipt in GitHub):** practice output is local and git-ignored. **No practice result may be shown to the owner, put in any report or used in a decision until practice writes to a Drive dataset with receipts (SIM-e, next).** The report's first line says "local only, not archived: no practice result may be shown to the owner, reported or used in a decision" (`test_the_first_line_of_a_report_says_local_only_not_archived`). `school practice run` is registered in `fno/school/cli.py` by two lines in this branch (`test_school_practice_run_is_registered_in_the_main_command...`); the import sits inside the function so the main command starts as fast as before.
- **Not done:** criterion 13 (a lot per expiry) waits for MS-P1a's follow-up; criterion 7 (diff-based "no driver file edited") is true by construction (no file under `fno/school/drivers/` is touched) and is checked in the judge's diff. **Full suite** (`pytest -q -n auto`, clean worktree, tip `6634659a`, with MS-P1j's follow-up 54ef5d40 and main merged): **14,114 passed, 18 xfailed, 0 failed** in 566 s (the 18 included the two strict xfails, now flipped). **At the tip with MS-P1j's ticket fix, `6b4409a0` (clean worktree, `pytest -q -n auto`): 14,120 passed, 16 xfailed, 0 failed** in 632 s.. ruff, check_imports and check_records clean.

#### SIM-d round 2 (judge 521 FAIL round 1: 2 should-fix, 4 minor; branch `story/ms-sim-d2`, the SHA is in the commit carrying this text)

| Finding | Fix | Test (and the plant it catches) |
|---|---|---|
| 1 criteria 2 and 11 rested on strict xfails; the plant `cfg_on(...)` to `parts.cfg` survived | MS-P1j's ticket fix (`1f767528`) landed, the xfails are plain tests, and tests that need no second session were added | `test_a_session_charges_the_stt_of_its_own_date_on_its_fills` (31 Mar 2023 at 0.05%, 3 Apr 2023 at 0.0625%, each fill's charges equal that date's mapping and are below today's), `test_the_charge_steps_up_across_the_change...`, `test_one_session_under_all_three_scenarios_is_labelled...`; **plant `cfg_on` to `parts.cfg` now caught** |
| 2 DATA_SPEND did not name the spread read of the forward captures | `research/DATA_SPEND.md`: the notes of the A4 row (forward, trial 99) and the A4c/A4f row (registered, trial 99) say the simulator's spread model reads the bid and ask of every recorded session, counted ones included, spreads only, never an outcome, for practice only | n/a (a register edit, lane 1 as the register's rule says; the orchestrator may rule otherwise) |
| a the margin label was fixed text | `margin.margin_label(row)` is built from the factor row actually used; the report carries it | `test_the_margin_label_is_built_from_the_factor_row_actually_used` (a row of 2.4 shows 2.4); plant caught |
| b outcome codes without reasons | the report counts `outcome:reason` (`no_trade:no_expiry_in_window`, `no_trade:rule_not_fired`, `ticket:account_limit`) | `test_a_drivers_outcomes_show_their_reasons...`; plant caught |
| c `refused_for_margin` untested | tested with a margin that fails law 3. **The counter itself was wrong**: a margin failure is an account limit, so the entry becomes `ticket: account_limit` and my counter of outright refusals read 0. It now counts decisions whose law results include a failed margin law, and is named `failed_margin` (the line reads "N decisions failed the margin law") | `test_margin_failures_are_counted_when_law_3_fails`; plant caught |
| d 2019 has no SPAN file | (orchestrator's ruling) the margin-checked window starts on 2 Jan 2020: earlier sessions are refused by name ("N sessions refused: no SPAN archive before 2020"), counted, and not run; a test pins the date to `NseSpanBodSource.first_day` | `test_sessions_before_the_span_archive_are_refused_by_name_counted_and_never_run`, `test_the_span_archive_starts_where_the_practice_says`; plant caught |

- **SF2, the orchestrator's ruling (23 Oct):** learning spreads from the recorded captures is allowed, as a cost input and not an outcome read. `research/DATA_SPEND.md` has a new row for it ("Bid-ask spreads of the 15:00 captures ... cost input for practice only, no outcome"), besides the two notes. **The condition that keeps it clean: practice results are never used to choose, tune or rank a counted driver.** The practice report's second line says it (`test_the_report_header_says_practice_is_never_used_to_tune_a_counted_driver`); plants (line removed; the span filter removed) caught.
- Plants (mine, this round): `cfg_on` bypass, `failed_margin` not counted, reasons dropped, the 2019 line removed: **4 of 4 caught**.
- **Criterion 13 (a lot per expiry), as its own commit after the first verdict:** `HistoricalRoadCatalogue` keeps each expiry's lot in `RoadDay.lots` (MS-P1a4, on main) and closes a road only when one expiry has no lot of its own. Tests: `test_two_expiries_with_different_lots_open_the_road_with_each_expirys_own_lot` (2 Jun 2025, BANKNIFTY-M: 35 and 30, `lot` the nearest's), `test_one_expiry_without_a_lot_of_its_own_closes_the_road...`, `test_the_same_lot_on_both_expiries_still_opens_as_before`, and end to end `test_a_proposals_lot_follows_the_lot_of_its_own_expiry` (every proposal's `lot` is the lot of its legs' expiry, through the pilot's own drivers, which read `lot_for`). Plants (`lots` not passed; the missing-lot closure removed): 2 of 2 caught. The old test that a mixed-lot day closes the road was replaced.
- `tests/school/simulator`: 215 passed; ruff, check_imports and check_records clean. **Full suite at the round-2 tip `32195d2c` (clean worktree, `pytest -q -n auto`, main and MS-P1j's follow-up merged): 14,144 passed, 16 xfailed, 0 failed** in 575 s.

#### SIM-e1 Claims (round 1, branch `story/ms-sim-e1` on SIM-d's passed tip `08bfbc1d` and the approved SIM-e text; the SHA is in the commit carrying this text)

Built: `fno/school/simulator/archive/{names,archive}.py`, tests in `tests/school/simulator/archive/test_archive.py`. The publisher, the data store and the reader come in by protocol, so e1 does not import the pilot's dashcam package.

| Acceptance test (7.8) | Test | Broken-code proof (caught) |
|---|---|---|
| 1 names never collide | `test_a_practice_path_never_starts_with_a_pilot_path_and_the_reverse`, `test_a_run_id_with_a_slash_dots_or_nothing_is_refused`, `test_a_file_place_that_climbs_or_is_absolute_is_refused` | area renamed to `school`; run-id pattern removed; `..` check removed |
| 2 label inside every line | `test_a_file_without_the_label_on_every_line_is_refused`, `test_a_file_that_is_not_canonical_record_lines_is_refused`, `test_a_text_file_needs_the_label...` | label comparison removed; the check not called |
| 3 idempotent, write-once | `test_archiving_twice_with_the_same_bytes...no_second_commit`, `test_other_bytes_for_an_archived_key_are_refused...`, `test_a_drive_conflict_without_a_pushed_receipt_is_refused_too` | SHA comparison removed; early return removed; `RawFileConflict` handling removed |
| 4 report text archived | `test_the_report_text_is_archived_and_its_sha_is_in_a_receipt` | n/a |
| run id follows what the run depended on | `test_the_run_id_is_short_and_follows_everything_the_run_depended_on` | input digest left out of the hash; hash truncated |
| read-back | `test_a_damaged_read_back_is_named` | check removed |
| a path outside the run refused | `test_a_path_outside_the_run_is_refused_before_anything_is_written` | check removed |

- Mutations: **12 of 12 caught.** `tests/school/simulator`: 48 passed in the files I ran (archive and isolation); ruff and check_imports clean. The full suite is run at the e3 tip.
- Not in e1 (e2 and e3): the real stores' wiring, the command's `--archive`, the report's first line, the exact-path receipt commit, and the real Drive run.

#### SIM-e2 Claims (round 1, branch `story/ms-sim-e2`, on main with e1 and the publisher move; Judge H's four minors from judge 526 folded in; the SHA is in the commit carrying this text)

Built: `fno/school/simulator/archive/{files,inputs,outcome,run,session,wiring}.py`, the `--archive` flag in `command.py`, `render(report, status)` taking the first line(s), `DASHCAM_HOME` shared by the fleet and the archive. Tests: `tests/school/simulator/archive/test_session.py` (13) and four more in `test_archive.py`.

| Criterion (7.8) | Test | Broken-code proof (caught) |
|---|---|---|
| 5 first line says archived only when every file has a verified receipt | `test_an_archived_run_says_so_on_its_first_line...`, `test_a_damaged_read_back_gives_local_only...`, `test_a_push_that_fails_midway_is_reported_partial_never_archived` | read-back removed; exit code made 0 when not archived |
| 6 receipt in the practice folder, never the pilot's | `test_a_practice_receipt_is_in_the_practice_folder_and_never_in_the_pilots`, the collision test (now with the instructor folder and the opportunity and marks paths) | n/a (path test) |
| 7 the default run archives nothing | `test_the_default_run_archives_nothing` | `--archive` test made always true |
| 4 report text archived, last | `test_the_report_text_is_the_last_file_and_carries_the_run_and_every_result_line` | report put first |
| idempotent rerun | `test_a_rerun_of_the_same_run_names_the_same_run_and_makes_no_second_commit` | n/a (e1's SHA check) |
| uncommitted code refused before the run | `test_uncommitted_code_is_refused_before_anything_runs`, `test_the_code_commit_is_named_only_for_committed_code` (real git) | dirty check removed; run id taken without `--archive` |
| run id follows the spread model and margin label | `test_the_inputs_digest_follows_every_spread_value_and_the_margin_label` | margin label left out of the digest |
| only dashcam record files and the report | `test_only_dashcam_record_files_and_the_report_are_archived...` | glob widened to every file |

- **Judge H's minors (526):** (a) the archive checks `..`, empty and `.` parts itself (4 cases, store and publisher untouched on a refusal); (b) every record line is decoded as `decode_slot_file` decodes it (a known `type`, a `record` that builds); a line with only a label is refused; (c) `report.txt` is the one name, in the story and the code, and a non-UTF-8 text is refused by name; (d) the collision test covers the instructor folder, `opportunity_path` and `marks_path`.
- **Found by running it end to end, fixed:** the fleet writes an **empty** outcomes file on a day with no closed trade, and my new decode check refused it, stopping every run at its third file. An empty gzip record file is now archived (no line to label); plain text and bad lines are still refused. `code_commit` stripped the first character of the first changed path in its message (`no/a.py`): fixed, with a real-git test.
- **Deviation from the ruling, with the reason:** the run id's input digest is the spread model (every bucket, session and half-spread) plus the margin factor's label, not a digest of the input receipts. The NSE files the window reads are write-once and named by the window, so the window identifies them; the captures grow daily and are what the model hashes. New code or new captures still make a new run id.
- **Two exact-name isolation exceptions** (`test_isolation.py`): `archive/wiring.py` may import `fno.school.dashcam.reader.VerifiedDriveReader` (the receipt-checked read-back; no record, count or seal) and `archive/files.py` the two constants `DASHCAM_FOLDER` and `SLOT_FILE_SUFFIX`. `VerifiedDriveReader` stays where it is (orchestrator's ruling, 23 Oct: move it only if generic). It is school-specific: it raises `StaleSeal`, a school contract error that the seal checker, the instructor reader (`instructor/reader.py:92`) and the comparison (`instructor/outputs/comparison.py:45`) catch by name. A neutral copy would need a new error type and changes to those lane-1 catchers, which is a different change from the publisher's pure move, so it is not done here.
- **Run id digest (orchestrator's ruling 1, accepted):** the NSE inputs are write-once and named by the window, so window + roads + scenarios + the clean code commit + the spread-model and margin hash identify the run.
- **Exact-path commit:** the recorder in `wiring.py` commits only `receipts/data/school-practice/<run id>/` (its pull refuses any other unpushed work; a refused push is retried by the shared recorder up to its `PUSH_ATTEMPTS` = 3 tries, as everywhere in the repository, orchestrator's ruling on judge 531 minor c; then the file stops the run with the reason). One commit per file.
- **Mutations:** 8 of 9 caught; the ninth (`problem is None` in `archived`) was a redundant condition (a problem always stops the loop before the file count reaches the total), so it was removed.
- **Gates at the merged tip `99101322`:** full suite 14,387 passed, 16 xfailed, 0 failed; ruff, `check_imports`, `check_numbers` clean.
- **Round 2 (judge 531 FAIL round 1: one should-fix, four minors; the SHA is in the commit carrying this text):**
  - *Should-fix:* `build_practice_archive` now takes the checkout and its git runner (`repository`, `git`), and `tests/school/simulator/archive/test_wiring.py` builds it for real over a fake env, Drive store, cache and git (5 tests): the recorder's folder is exactly `receipts/data/school-practice/<run id>`; `git add` and `git commit` get only that pathspec and the pending-receipts `status` is limited to it; the reader is `VerifiedDriveReader` over `DATA_AREA` and the built cache. Judge H's two surviving plants (recorder widened to `receipts/`, reader swapped for the store) are caught, plus a changed reader area and a dropped git runner.
  - *(a)* a zero-byte `.jsonl.gz` is refused (only a real, empty gzip member is accepted). *(b)* the real-git test adds an untracked file in a new folder (`fno/newpkg/b.py`) and matches the file's own name, so dropping `--untracked-files=all` (which would show only the folder) is caught. *(c)* the line above is corrected. *(d)* the archived `report.txt` ends with the same "left out of the spread model" lines the run prints, from one shared function (`left_out_lines`).
  - 7 of 7 new plants caught.
- **e3 so far (branch `story/ms-sim-e3-code-commit`).** First real archived run, 4-6 Mar 2024, NIFTY-M, NIFTY-W, BANKNIFTY-M, run after 16:15 IST from a clean detached worktree of main `8c5effca`: exit 0, `archived: run 20240304_20240306_4490ad2e299b, 28 files`; 28 receipt files and 28 commits on main, all under `receipts/data/school-practice/<run id>/`; an independent Drive re-read of all 28 files gave 0 SHA or size mismatches. Every driver result is `no_trade` (no_valid_quotes, no_expiry_in_window, n0, rule_not_fired), 0 executed: about 8 recorded sessions leave every spread bucket "insufficient", so this proves the plumbing, not a result.
- **The run id named HEAD, which the run's own receipt commits move (found by that run).** After it, HEAD was the last receipt commit, so a rerun of the same code would have named another run and archived 28 files again. Not rerun. **Round 1 fix** (last commit that changed the code paths) **failed Judge H, judge 533:** in a shallow clone `git log -1 -- <paths>` names the boundary commit, and the cloud containers clone at depth 50 while the run's own publisher unshallows the clone, so a run and its rerun would still differ. **Round 2 fix (orchestrator's ruling):** the code is named by content, `code_identity`: a digest of `git rev-parse HEAD:fno HEAD:tools HEAD:config.yaml HEAD:requirements.txt`. Tree ids need no history, so the same code gives the same id in any clone, on any branch, before and after a receipt commit; uncommitted changes to those paths are still refused (the file named). Tests (real git): a data commit and an empty commit leave the id unchanged; each of the four paths changed (committed) changes it and (uncommitted) is refused; a `--depth 2` clone gives the full clone's id, the same id after its own receipt commit and the same after `git fetch --unshallow`; commits holding none of the code, and no commit at all, are refused by name. Plants caught: HEAD instead of trees, any one path dropped (four plants), dirty check off, only the first path hashed.
- **Known limit (judge 533 minor b, orchestrator's ruling):** `requirements.txt` holds `>=` ranges, so the id names the requirement text, not the installed library versions. Reasoning only: not measured whether a minor-version change moves any practice number.
- **Orphan run (orchestrator's ruling, 23 Oct):** `run 20240304_20240306_4490ad2e299b`: archived under the HEAD-based id, not reproducible by id; superseded by the fixed-id run. Its 28 receipts stay on main, never deleted (write-once), and it is not counted as e3's evidence. No README exists in the practice receipt area, so this line is its only note.
- **Not done (e3):** the fixed-id run, its rerun with no new commit, and the receipts counted. Until e3 passes, no practice result is shown or used.

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

### MS-P1b Claims (round 1, code at 2ed9bbbf; builder session_01F1RVMF8MNngi97JVNs99L5)

**Gates on the pushed tree:** `pytest -n auto` 10,449 passed, 16 xfailed; `ruff check`/`format`, `check_imports`,
`check_records` clean. School tests in all: 345 (contracts, roads, quality).

| Criterion | Test (all under `tests/school/`) | Broken-code proof (mutation applied, test failed) |
|---|---|---|
| 1. Five roads on a trading day, none on a holiday | `roads/test_catalogue.py::test_five_roads_open_…`, `test_no_road_on_a_day_that_is_not_a_trading_day[holiday, weekend, muhurat only]` | catalogue's trading-day check removed |
| 2. Each reason from a planted fixture | `test_each_capture_fault_closes_the_road_with_its_reason[*]` (missing, incomplete, out_of_window, hash_mismatch, expiry_mismatch), `test_a_lot_the_source_cannot_find…`, `quality/test_gate.py::test_an_impossible_price_in_the_band_closes_the_road` | own hash check, lot check, expiry check, incomplete check, impossible-price closure each removed |
| 3. Exactly one reason | `test_two_faults_give_the_earlier_reason_only` (all 10 ordered pairs), `quality/test_gate.py::test_every_fault_at_once…` | gate's "closed keeps its reason" removed |
| 4. Capture gate boundaries | `quality/test_capture_gate.py`: 10/10 vs 9/10, <10 sessions, 949/950/951/1000 of 1,000 legs | `>` to `>=` (95.0% passed), 9-of-10 and session-count conditions weakened |
| 5. Conformance | `check_road_catalogue`, `check_snapshot_source` in `test_catalogue.py::test_conformance…` | (a's checks) |

Round 1 claimed "25 mutations, 25 caught"; judge 482 planted 33 and 9 survived, so that claim was wrong (see round 2).

**Self-review (two independent review agents), what was done:**
- *Fixed:* a store outage was turned into `expiry_mismatch` (now propagates; missing archive settings raise
  `RawFilesNotConfigured` at build); parse errors outside the try (now `capture_incomplete`); lot of 0 accepted; an
  absent capture cached for the run (not any more); vertical rule checked neighbours only, which a wide quote can hide
  (now all pairs, judged among the band's legs); capture-gate report crashed on an unreadable snapshot (now a closed
  session); a sidecar of another capture or road was not refused; quotes shared mutably (now read-only view); `in_window`
  truthy test; float noise at a bound; line printed 95.01% as "95.0%" (two decimals); the default `--through` could be a
  day with no captures yet.
- *Not changed, with reason:* the order check that needs the quote file (it missing, its row count) runs after the
  sidecar's window check (documented in `capture.py`; the file must be read to know). Expiry-day cases are not
  separately tested (they use the recorder's own `monthlies`/`nearest_weeklies` unchanged).

**Decisions for the orchestrator/judge (reasoning only, flagged openly):**
1. *Impossible price* is EDGE1's vertical rule adapted from a single close to a **bid-ask range**: impossible only if no
   price inside both legs' ranges satisfies 0 <= worth <= width. Judged on mids, whole chains flag 8-61 legs a road-day (neighbour pairs) and 9-87 (all pairs); in the band only
   MIDCPNIFTY flags (15 legs on 21 Oct, 6 on 22 Oct) (judge 482's figures, reproduced; round 1 said 8-72); judged on ranges, **0 of 716 band legs on the 9 road-days of 21-22 Oct** did.
2. A road-day **closes `impossible_price` if any leg in the road's band is impossible**; a leg observation also excludes
   impossible legs (kept for report use, so the 95% test and the closure agree). Story 3.5 gives no day-level rule; the
   alternative is a share threshold. The band default is 10 steps (RC1's widest) until MS-P1h freezes the card value.
3. An unreadable NSE expiry listing closes the road `expiry_mismatch` (no other code fits; nothing is opened on
   unconfirmed expiries). A Drive outage is never a closure.
4. Lots come only from the **session's own** A20a copy (none before 21 Oct), so NIFTY 14-19 Oct and BANKNIFTY/FINNIFTY/
   MIDCPNIFTY 19 Oct close `lot_mismatch`.
5. The a-builder's fixtures start BANKNIFTY at 15:00:00; the recorder's window for the other indices opens 15:01, so such a
   snapshot is `out_of_window` here (A4: NIFTY 14:55-15:10; A4c/A4f: 15:01-15:13, +60 s grace for the recorder's last
   instant). No contract change needed; a/j fixtures should start inside the road's window.

**Real output (read-only `python -m fno.school.quality.command --through 2026-10-22`; counts only, stored files, no
network read of NSE or Groww; nothing written):**
```
NIFTY-M through 2026-10-22: snapshots 2 of 10 (capture_missing 4, lot_mismatch 4); legs 168 of 168 (100.00%); gate closed
BANKNIFTY-M through 2026-10-22: snapshots 2 of 10 (capture_missing 7, lot_mismatch 1); legs 168 of 168 (100.00%); gate closed
FINNIFTY-M through 2026-10-22: snapshots 2 of 10 (capture_missing 7, lot_mismatch 1); legs 90 of 128 (70.31%); gate closed
MIDCPNIFTY-M through 2026-10-22: snapshots 2 of 10 (capture_missing 7, lot_mismatch 1); legs 167 of 168 (99.40%); gate closed
NIFTY-W through 2026-10-22: snapshots 1 of 10 (capture_missing 9); legs 84 of 84 (100.00%); gate closed
```
Reading: no road can pass yet (history is short, as expected). **FINNIFTY is the one to watch: only 45 of its 64 band
legs are two-sided and valid on each of 21 and 22 Oct (70%), so it will fail the 95% test on thin quotes unless that
changes.** Every other road's legs are at or near 100%. [strong evidence: counts above; reasoning only: what the next
sessions will do.]
### MS-P1f Claims (round 1, branch `story/ms-p1-tickets`, on top of `story/ms-p1-contracts`; the SHA is in the commit carrying this text)

| # | Criterion | Code | Tests (and the plants they catch) |
|---|---|---|---|
| 1 | Tickets: the same quotes and laws, never in an account, never in rupees | `rules.py`, `book.py`, `rupees.py` | `test_rules.py`, `test_book.py`. Plants: the room check, the running view, rank order, ties, the account-limit ticket, the brake added to a's `ACCOUNT_LIMITS`, the ticket laws, the first reason, accepted-only trades, one lot, the binding filter, the book's law refusal, recording only fills, tickets only, and the rupee filter |
| 2 | eligible >= fillable >= executed over a fixture day | `counts.py` | `test_counts.py`. Plants: the laws term, the ticket laws, the executed rule, the denominator, uniqueness |
| 3 | A shared displayed size is counted; no unservable fill is summed | `shared_size.py` | `test_shared_size.py`. Plants: the fit check, the size use, the side's size, the fixed order |
| 4 | A refused ticket stays in the denominator | `counts.py` | `test_counts.py` (`TICKET, PASS, MISSING` row and the fixture day) |
| 5 | Conformance | n/a | f implements no a port; its fakes pass a's checks |

- **Gates on this tree:** reported in the hand-off message; the full suite, ruff, `check_imports` and `check_records`.
- **Round 1b (after a's round 2, orchestrator's answers of 22 Oct):**
  - built on a's frozen split: `ACCOUNT_LIMITS` comes from `fno/school/constants.py`;
  - a trade refused only by an account limit is now `ticket: account_limit` (Q1, yes);
  - the daily stop and the brake refuse, with no ticket;
  - `book.fill_cash` is replaced by a's `FillResult.cash` (Q2, yes);
  - j's running-view requirement is written into MS-P1j (Q3).
- **Plants:** 24 planted, 24 caught (after round 1b). In round 0, two survivors led to one fix each: a redundant `eligible and`
  removed, and a test fixture with asymmetric bid and ask sizes.
- **Self-review** (an independent agent on `756e6545..75c12954`): 1 blocking, 6 should-fix and 4 minor findings.
  - Fixed:
    - **Blocking:** a ticket filled with no law check. `TicketBook.enter` now takes the sealed law results and
      refuses on a binding law; tickets are only made by `classify`, after the same laws.
    - **Ordering:** each check now sees the trades accepted this slot, and a refused trade frees its place for the
      next-ranked rule.
    - **Shared size:** per-leg minimums were wrong for structures. Now whole fills are allocated, any number per owner.
    - **Weak tests:** two tests that could not fail are replaced; the conformance claim is corrected.
    - **Minor:**
      - `TicketLedger` is its own type;
      - `totals` refuses duplicate rows;
      - an `unavailable` decision is documented as not eligible;
      - a two-lot proposal raises, as a driver bug the fleet isolates.
  - The two questions raised in round 1 (account-cap tickets, the duplicated cash arithmetic) were answered by the
    orchestrator and built in round 1b.

### MS-P1c Claims (builder session_01WeFYCqffRe7et1nfSJyuv5, branch `story/ms-p1-dashcam`)

Round 1, built on a's tip 756e6545. Files: `fno/school/dashcam/` (names, publisher, reader, store, seals, counts,
replay, wiring), `tests/school/dashcam/` (a real git remote and a local-folder Drive; production classes otherwise).

| Criterion | Code | Test (fails when the code is broken on purpose) |
|---|---|---|
| 1 write-once; `ReplayConflict` "rule broken" | `store.DriveDashcamStore.seal` | `test_the_same_records_again_are_a_no_op_with_the_same_seal`, `test_other_records_for_a_sealed_key_are_a_replay_conflict_reported_as_rule_broken`, `test_a_conflict_in_the_receipt_alone...` (Drive untouched) |
| 2 stale seal: not pushed, pushed late, other SHA-256 | `seals.SealChecker.check` | `test_seals.py` (6 tests incl. a forged commit and an earlier time) |
| 3 counts file: scan clean, no strike, price or symbol | `counts.PublicCountsFile` | `test_the_file_passes_the_record_scan_and_holds_only_codes_and_whole_numbers` |
| 4 replay reads exactly what was sealed | `replay.ReplayReader`, `reader.VerifiedDriveReader` | `test_replay_reads_back_exactly_the_records_sealed`, tamper and stale-cache tests |
| 5 conformance | `check_dashcam` | `test_the_conformance_check` |

Broken-code proof: 10 mutations (conflict handler, each seal check, the push check, the read-back hash, the counts
rewrite guard, a price leaking into the counts, the reader's own-file check) each fail a named test; one survivor
(reader) was found and a test added.

Self-review (an independent review agent, read-only) found 8 points. Accepted and fixed, with tests: a seal is now
checked against the remote's receipt (commit, SHA-256 and time), not trusted (2, 6); a failed push is pushed by the
rerun (3); a conflict is judged on the remote receipt before Drive is touched (4); a rerun in a fresh checkout
returns the existing seal and writes no second receipt (5); the counts slot is validated (7). Partly accepted (1):
`pushed_at` is the receipt commit's own time, which is never later than the push; it stays so because a rerun must
return an equal seal. A fill is made only after `seal` returns (so after the push); the fill port (d) must also
call `SealChecker` with its own fill time. Not done (7, 8): the counts file's exists-then-write is not atomic across
two processes (one writer per session in the fleet), and counts are not tied to a sealed SHA-256.

Limits for others: `ReceiptPublisher` pushes `receipts/data/school/` only, to `main`, through A16f's committer
(refuses a checkout carrying other unpushed changes). Nothing commits the counts file; the join-up (j) must commit
`research/school/counts/` with its own push. No Drive or git is touched when `school.enabled` is false (nothing here
runs until j calls it).

Round 1 follow-up (orchestrator, 22 Oct 2026; both open items accepted):
- The proof that a seal came before its fill is that the seal's receipt exists on the remote, with the sealed SHA-256, when `SealChecker` runs at fill time; `pushed_at` is labelled "commit time, not push time" and is a secondary check only.
- Assumption: the counts file is written by one process only (the join-up's single runner); j tests it.

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

### MS-P1i Claims (round 1, code at 0b655751; builder session_01F1RVMF8MNngi97JVNs99L5)

Built on a's round-2 tip 8c7ba1d9 (not 756e6545): round 2 added the fleet contract and `FakeFleet` this harness needs.
Gates on the tree: `pytest -n auto` 10,310 passed, 16 xfailed (before the last test-only edits; school tests rerun
green), ruff, `check_imports`, `check_records` clean.

| Criterion | Test (`tests/school/acceptance/test_acceptance.py`) | Broken-code proof |
|---|---|---|
| 1. Each planter gives its exact reason code | `test_each_planter_gives_its_exact_reason_code_and_opens_nothing_for_it[*]` (7 faults), `test_a_wrong_reason_code_is_not_accepted`, `test_a_fault_check_fails_when_the_fleet_does_not_catch_the_fault` | stale seal made on time, refused entry under the cap, quote removal and road closure made no-ops: each fails |
| 2. Comparator fails on one changed byte | `test_the_comparator_fails_on_one_changed_byte_in_a_record_file_or_the_counts_file`, `test_two_runs_of_one_recorded_day_are_byte_identical…` | comparator returning no differences fails |
| 3. Planted refusal survives two runs, in both sections' inputs and every denominator | `test_the_planted_refusal_survives_two_runs_and_is_in_both_sections_inputs_and_every_denominator`, `test_the_refusal_is_in_the_counts_file_as_not_executed` | counts file's "executed" forced to 0 fails |
| Four fill checks | `test_an_unsealed_fill_is_caught`, `…over_cap…`, `…away_from_the_touch_or_without_a_quote…`, `…duplicate_fill…` (each plants a bad ledger entry) | each check replaced by `assert True` fails |

11 harness/planter mutations applied, 11 caught (the first run left 2 alive, "sealed file unchanged" and the counts
file; a test was added for each and both are now caught).

**For story j:** `tests/school/acceptance/rig.py` defines `Rig` (fleet, dashcam, ledger reader, snapshot reader, counts
file, section-input reader, denominator reader). j writes `real_rig(scenario)` and calls the same functions in
`harness.py`: `run_fault` for each of `all_faults()`, `check_fills`, `check_replay_twice`. The scenario is plain data
(`fno/school/acceptance/scenario.py`); `recorded_day()` (5 roads, CS1 and DR1 trading, N0 not) starts every snapshot at
15:02, inside all five roads' windows.

**Limits, said plainly [reasoning only for what j will find]:**
1. On the fake fleet the closure faults (expiry mismatch, lot mismatch, impossible price) are planted as the road's
   status; the real detection of those is part b's tests, and j's real rig must plant them as bad captures through
   b's classes so the same expectation (every driver on the road: `road_closed` with that reason) holds.
2. A missing quote is accepted either as a `refused/missing_quote` decision (law 5) or as a refused fill, because the
   fake fleet has only the max-loss law; the real fleet may use either path.
3. The counts file, section inputs and denominator on the fakes are derived from the sealed decisions file; parts f and
   g own the real ones, and j's rig must supply theirs.
4. The replay-conflict fault is checked at the dashcam (other bytes for a sealed key raise `ReplayConflict`, the file is
   unchanged). A fleet rerun never reaches that path, because it skips what is sealed.

### MS-P1b Claims, round 2 (judge 482 FAIL round 1: two should-fixes, two minors; builder session_01F1RVMF8MNngi97JVNs99L5)

**SF1, strike step per expiry (done).** `quality/strikes.py::strike_steps` gives each expiry its own step (most common
gap of its listed strikes, the smaller on a tie); `band_keys(snapshot, band_steps)` builds the band per expiry in that
expiry's own steps, around that expiry's own money; the gate and the capture gate use it. A capture with an expiry of
under two strikes is `capture_incomplete`. Tests: `tests/school/quality/test_strikes.py` (two steps, tie, mode not
least-common, one step for all expiries fails, the FINNIFTY shape of 49 strikes at 50 and 25 at 100 gives 42 and 42
band legs). Real data, read-only run of the committed code on the recorded days (21 and 22 Oct):

```
FINNIFTY-M  steps by expiry [50.0, 100.0]  band legs by expiry [42, 42]     (round 1 gave 64 legs a day)
all other roads: one step on both expiries, band legs [42, 42]
```
A pytest on the Drive-only files cannot run in the suite (the test run removes every real credential, by design), so the
real-data check is this run; the synthetic test pins the same shape.

**Contract question for the orchestrator (to a's builder):** `RoadDay.strike_step` is one float, so it stays the
*nearest expiry's* step. A driver that steps out on a later expiry needs that expiry's own step. Smallest change:
`SlotSnapshot` (or `RoadDay`) carries `strike_steps: Mapping[date, float]` and drivers read the step of the expiry they
use. `strike_steps(snapshot.quotes)` already computes it, so a can move it into the contract or drivers can call it.

**Effect on the finding about FINNIFTY (worse, stated plainly):** with a full band on both expiries FINNIFTY has 95 of
168 band legs valid and two-sided over 21 and 22 Oct (56.55%), not 70%. It fails the 95% bar by a wide margin. The gate
is unchanged.

**SF2, the nine surviving plants (done).** `tests/school/roads/test_sidecar_and_row_checks.py` plants each fault in the
capture itself (oracle: the plant, not the code): an A4-invalid leg that keeps its bid, ask and sizes is not counted
(32 band legs, 31 passed); a sidecar with failures but `complete: true`; spot 0, negative, nan, inf, None, text, a list;
a capture that finished before it started (and one that took no time is fine); a capture stamped a day early, a day
late, started yesterday and finished today, and finished tomorrow; times written in UTC (open) and IST wall-clock under a
UTC label (out of window), and a zone far behind IST that dates the start a day earlier (same session in IST).
`test_strikes.py` kills the least-common-gap plant. The locale-free month label plant is equivalent here (the locale in
the tests is fixed; `MONTHS` is a tuple), as the judge noted.

**Mutations now:** the first set (24, adapted to the new code) and the judge's seven families plus others (14), 38 in
all, all caught, none surviving. Round 1's "25 of 25" is withdrawn: it was a smaller set than the judge's 33.

**Minor (a):** corrected above. **Minor (b):** the unreadable-listing case cannot carry its detail in `RoadStatus`
(one closure code, by contract); reports that need to tell it from a true mismatch need a field on the contract.


### MS-P1b Claims, round 2b (judge 483 FAIL round 1: three should-fixes, two minors)

1. **Leg denominator (fixed).** `RoadQualityGate(listing, band_steps)` takes the scheduled legs from
   `ListedContracts` (`roads/listed_contracts.py`: the previous session's archived NSE F&O file, stored files only, no
   new read): the contracts of the road's expiries inside the recorder's 5% band of the spot, then the band of the
   listed strikes in each expiry's own step. A scheduled leg the capture lacks is observed and not passed. Tests
   (`quality/test_scheduled_legs.py`): the judge's plant, one dropped near-money strike, gives 12 scheduled and 11 passed
   (not 12 of 12); a whole strike dropped on both kinds and expiries gives 12 and 8; captured extras beyond the listing
   are not scheduled; the band follows the listing when the money strike is dropped; an unreadable listing raises
   `ListingUnavailable`, and the capture-gate report counts that session as failed (`expiry_mismatch`), not a crash.
2. **Drive outage (fixed).** `requests.RequestException` (which includes `requests.JSONDecodeError`, also a
   `ValueError`) now passes through the expiry source before the parse catch, so a proxy's HTML page from Drive raises
   and closes nothing. Only an unreadable listing file (`ExpiryListUnavailable`, a damaged zip, bad rows) closes as
   `expiry_mismatch`. Tests: `roads/test_listed_contracts.py` (non-JSON reply raises through both readers; damaged file
   is `ExpiryUnavailable`/`ListingUnavailable`).
3. **Capture checks without a failing test (fixed, together with judge 482's).** Each now has a plant whose oracle is the
   plant: the failures list (`complete: true` with failures), recorded equals expected (32 rows, 32 recorded, 40
   expected; and 31 against 32), expected above zero (an empty chain that expected and recorded nothing), spot finite and
   above zero, finish before start, and the start and finish date checks separately (started yesterday and finished today
   catches the start check alone). Minor (b): only the exact word `true` makes a leg valid (`True`, `yes`, `1`, empty,
   `maybe` do not).
4. **Minor (a)** corrected in round 2 above (8-61 neighbours, 9-87 all pairs, in the band only MIDCPNIFTY).

**Mutations:** 38 (round 2) plus 9 more for this round (the denominator from the capture, two-sided on the leg count,
expected above zero, recorded equals expected, `valid != "false"`, JSON error as closure, damaged zip, unreadable
listing in the report, the recorder band on the listing): all caught, none surviving. One more (a redundant
`except` in the listing reader) survived because the store is read outside the try, so the clause was dead; it is
removed.

**Real output, read-only, after the change:**
```
NIFTY-M through 2026-10-22: snapshots 2 of 10 (capture_missing 4, lot_mismatch 4); legs 168 of 168 (100.00%); gate closed
BANKNIFTY-M through 2026-10-22: snapshots 2 of 10 (capture_missing 7, lot_mismatch 1); legs 168 of 168 (100.00%); gate closed
FINNIFTY-M through 2026-10-22: snapshots 2 of 10 (capture_missing 7, lot_mismatch 1); legs 95 of 168 (56.55%); gate closed
MIDCPNIFTY-M through 2026-10-22: snapshots 2 of 10 (capture_missing 7, lot_mismatch 1); legs 167 of 168 (99.40%); gate closed
NIFTY-W through 2026-10-22: snapshots 1 of 10 (capture_missing 9); legs 84 of 84 (100.00%); gate closed
```
The scheduled legs now come from NSE's listing and equal the captured band on every road-day, as the judge saw, so the
counts do not move; the difference is that a dropped strike would now show.
### MS-P1m Claims (round 2, branch `story/ms-p1m-margin-rows`; round 1 claims are response 328)

Judge 491 (J, round 1) FAIL: one should-fix and three minors. Judge 492 (B, round 1) FAIL: one should-fix (tests
only) and a note. Each was checked and fixed in this one round 2.

| Finding | Check | Fix | Test (plant caught) |
|---|---|---|---|
| Should-fix: an open trade on its own expiry day froze its account (REF and RC1 lose about one session in five) | agreed: `rules.py:143` prices open trades first; `calculator.py:62` refused expiry day | expiry day priced with SEBI's extra 2% ELM (above) | `tests/nse_margins/test_expiry_day.py`: hand-worked 104,000 and 64,675 a lot; any other day unchanged; before 20 Nov 2024 and after expiry refuse; an account holding an expiring trade enters another road (plants: extra 0, its date, `<=` for `==`, longs charged, a flat rate, the wiring on A14's rule, the record's label dropped) |
| Minor 1: `nov_per_lot_rs` untested | agreed | - | `test_the_record_carries_each_per_lot_figure_in_its_own_field` (3,250.00 / -975.00 / 26,000.00) |
| Minor 2: the unset factor file untested | agreed | - | `test_no_factor_file_in_config_refuses_by_name_never_a_default_factor` |
| Minor 3: `manifest()` outside the named refusals | agreed | wrapped, class name only | `test_an_unreadable_manifest_refuses_by_its_class_name_only` (plant: `except KeyError`) |

| Judge 492 should-fix: four shape plants survived (PDS, CDS, CCS with the other leg sold; a wing checked on the call side only) | agreed | - | `test_each_spread_accepts_its_own_shape_and_refuses_the_other_leg_sold` [4], `test_a_fly_or_condor_with_only_its_put_wing_off_width_is_refused` [SF, SC, BF]; all 5 plants now caught |
| Judge 492 note: the gap script fixed FINNIFTY at a 50-point step (November's strikes are 100 apart) | agreed | each expiry's own step from its listed strikes near the index | rerun: 14,800 comparisons, none skipped (the 1,064 skipped before were FINNIFTY's); only the FINNIFTY row moves (SC 66% to 75%, PCS 96% to 97% and min 0.87 to 0.85, CCS 92% to 94%, CDS 10% to 5% and 0.88 to 0.87, PDS 12% to 10% and 0.90 to 0.87); the lowest ratio stays 0.76, so the decision holds |

- **Real data:** NIFTY weekly SF 100 expiring 13 Oct 2026 (index 22,363.35): exposure 1,16,289.42 a lot from the
  adapter, the same as a hand computation (4% on each at-the-money short x 65).
- **Plants this round:** 8 of 8 caught, plus judge 491's two and judge 492's five survivors now caught.
- **Gates:** on the head named in the message to the judges.


### MS-P1f Claims, round 2 (judge 481, FAIL round 1: two should-fixes and two minor findings)

| Judge 481 finding | Fix | Test (plant caught) |
|---|---|---|
| 1. No test pinned that tickets stay out of the running view | none needed in the code (only trades enter `accepted`); the rule is now in the docstring | `test_a_ticket_never_enters_the_slot_s_running_view` (the judge's plant 2: a non-refused decision appended) |
| 2. Shared size: no rupee path, a name-biased order, tickets could take an account's size | `allocate` serves accounts first, in a seeded order recorded with its seed. `fill_status` gives `unavailable: size_shared`. `counts_for(size_shared=)` makes it fillable, not executed. `account_net` leaves out and names unservable outcomes, keyed by (driver, fill). Two MS-P1j requirements added | `test_shared_size.py` (seeded order, independent of the given order; no name wins every session; accounts before tickets; equal fills of two owners); `test_two_accounts_on_one_displayed_size_sum_only_the_servable_one`; plants: sort by name, tickets mixed in, session dropped from the seed, size_shared ignored, wrong set, no exclusion |
| Minor (a): plant 21 survived | a trade row with an account-limit refusal | the `(TRADE, CAP, filled)` counts row (plant 21 caught) |
| Minor (b): a braked driver was shown `open_risk` | `DRIVER_STOPS` reasons are named first | two rows in `test_any_other_refusal_stays_refused_with_the_first_reason`; plant: the stop-first rule removed |

- **Found while fixing:** two accounts filling one structure at one touch give equal `FillResult` values, so a set of
  fills could not tell them apart. Unservable fills are keyed by (owner, fill). The test asserts the two fills are
  equal and that only one is left out.
- **Shared file:** `fno/school/constants.py` gains one additive line, `UnavailableReason.SIZE_SHARED`, by the
  orchestrator's ruling 2(c). Part a is not on `main` yet, so it rides with f.
- **Plants:** 33 planted, 33 caught, the judge's two survivors among them.

### MS-P1f Claims, round 2 addendum (judge 490, Judge H)

| Judge 490 finding | Fix | Test (plant caught) |
|---|---|---|
| 1. A refusal could be named by an account limit when a binding law also refused | `rules.named_refusal`: a stop, else a trade-validity law, else the first account limit | rows in `test_any_other_refusal_stays_refused_with_the_first_reason`: open risk with max loss gives `max_loss`; bucket with daily stop gives `daily_stop`; margin, unprotected and brake give `brake`; first in order within a group. Also `test_an_account_limit_is_named_only_when_account_limits_alone_refused`. Plants: binding dropped, stops dropped, last instead of first |
| 2. Empty law results passed | `classify` raises; `ticket_laws_pass(())` is False; `first_binding_refusal(())` raises; `counts_for` raises for a trade or ticket without results | `test_no_law_results_never_pass`; `test_a_ticket_record_without_law_results_is_never_filled`; `test_a_trade_or_ticket_without_law_results_is_never_counted`. Plants: each guard removed |
| 3. A name-biased order | already fixed in round 2 (judge 481): the seeded order, accounts before tickets | `test_shared_size.py` |
| Minor (a): results came from the caller | `TicketBook.enter(record, file_sha256, snapshot, seal, at)` reads the sealed `DecisionRecord.law_results` | `test_book.py`. Plant: only the first result read |

- **Signature change**, for j: `TicketBook.enter` now takes the sealed decision record and its file's SHA-256. It no
  longer takes `(sealed, results)`.
- **Plants:** 39 planted, 39 caught over f's tests.

MS-P1c round 2 (orchestrator and Judge J early findings, each checked and fixed; merged a's tip 32fdbdde):
- **Shallow clone (defect, reproduced and accepted):** `git log --diff-filter=A` in a shallow clone returns the boundary
  commit as the receipt's add commit, so a rerun names the wrong commit and a real seal is refused. `GitReceiptPublisher`
  now fetches the rest once (`git fetch --unshallow`, detected with the research engine's `Git.is_shallow`) or raises
  `ShallowClone` naming the command; `SealChecker` turns that into `StaleSeal`. Tests with a depth-1 clone:
  `test_a_shallow_clone_names_the_real_add_commit_not_its_boundary_commit`,
  `test_a_shallow_clone_that_cannot_be_deepened_is_refused_by_name`.
- **Five surviving plants, now caught:** a Drive-level conflict after a failed push
  (`test_a_rerun_with_other_records_after_a_failed_push_is_a_replay_conflict`); `published()` without its fetch
  (`test_published_fetches_a_receipt_another_checkout_pushed_after_this_one_cloned`); no `--diff-filter=A`
  (`test_a_receipt_file_touched_again_still_names_the_commit_that_added_it`); the counts session and slot filter
  (`test_records_of_another_session_or_slot_are_not_counted`); the counts slot validation
  (`test_a_slot_that_is_not_a_time_never_reaches_a_path`).
- **Dead code removed:** `_identity` and `SealChecker.is_valid` (tests only) in `seals.py`.
- **a's `find`:** `DriveDashcamStore.find(session, slot, kind)` (my earlier `sealed`, renamed to the contract's name): the
  seal of a file whose receipt is on the remote, else None (`test_find_*`, and a's conformance check).

### MS-P1e Claims (round 1, branch `story/ms-p1-drivers`, built on a's tip 756e6545; the SHA is in the commit that carries this text)
| # | Criterion | Code (`fno/school/drivers/`) | Test in `tests/school/drivers/` (broken-code proof: the plant it catches) |
|---|---|---|---|
| 1 | Each family fires at its threshold, not just below | `families_directional.py`, `families_condor.py` | `test_families.py` per family: CS1 mean, DR1 high/low, DB1 at 1.0001x and 0.9999x of the implied straddle, WS1 1-3 sessions, PS 30-45 days (plants: equal mean fires, strict high, DB1 session count, WS1 window +1) |
| 2 | 19 sessions: "not enough history"; 20: a trade | `history.py` `spot_window` | `test_19_sessions_of_history_is_not_enough_and_20_is_` for CS1, DB1, DR1; today's and later spots, and a duplicated session, are never history (plants: `>= length - 1`, `<= session`) |
| 3 | N0 always `no_trade: n0` | `controls.py` `NothingDriver` | `test_n0_gives_no_trade_n0_on_every_road_and_day` (plant: other reason) |
| 4 | RC1: same seed same draw, another seed another, same caps | `controls.py` `RandomDriver`, `draw_seed` | `TestRandomControl` (seed equals SHA-256 of session, driver, road; 60 draws all within the cap and protected; all six shapes drawn; plant: seed ignores the road) |
| 5 | PS5 and KL1 match EDGE1's frozen parameters | `families_condor.py` `Edge1Control`, cards | `test_ps5_and_kl1_keep_edge1s_frozen_parameters` against `edge1study` (`TARGET_SHARE`, `WIDTHS_BY_INDEX`, `structure("SC3").offset`, 30-45 days, T21 = `EXIT_MIN_DAYS`) (plants: target 0.4, offset 0.02) |
| 6 | Every `no_trade` carries a reason from a's enum | `scope.py`, `Decision` | `test_every_no_trade_carries_a_reason_from_the_enum_...` over 5 roads x 3 histories x all drivers |
| 7 | Conformance | all drivers | `test_the_driver_passes_the_conformance_check` per driver and road (a's `check_driver`) |
| 8 | Exits are E4's `ExitRule` classes | `exits.py` (`ProfitTarget`, `StopLoss`, `ExitOnDay`) | `test_exits.py`: half credit exact, WS1 1.5x not 2x, T21 day, 10 sessions, 21 days held, expiry, un-judgeable prices never fire, year-end calendar (plant: target x1.1) |
| 9 | Cap holds at the touch the fill uses | `proposals.py` | `test_proposals.py` (independent B2 recompute at the touch; wide spreads force narrower wings; plant: touch check removed) |
Review and decisions (reasoning, with evidence):
- **Independent review agent found, and I fixed:** (a) calendar ending 31 Dec 2026 raised `CalendarError` in exits and in DB1/WS1/PS5/KL1 entry: a rule whose day the calendar cannot work out is now not reached and never blocks price or expiry rules; entry returns `no_expiry_in_window`. Exits are tested with a year-end calendar (`test_exits.py`), entry for WS1, DB1 and PS5 in `test_oracles.py` (before round 2 only exits were tested; the first Claims text said entry too, which was wrong). (b) The ATM strike could be far from spot: it must now be within 2 steps, else no expected move. (c) A duplicated session made a longer window: de-duplicated. (d) Ranked cards had no `expected_net_rs`, silently scoring 0: now a required card number, 0.0 with a stated reason (EDGE1 found no edge), so scores tie and the fleet's tie-break ranks. (e) Vacuous and loose tests tightened; dead code removed.
- **Not changed:** `review_exit` does not check a position against the driver or road: a's conformance check hands every driver one fixture position, and pairing is the fleet's job. PS5 and KL1 enter on the decision slot, EDGE1 entered the next trading day: a known difference, the slot design has no later fill.
- **Departures from the story text, for the orchestrator:** CS1, DB1, DR1 and WS1 cards hold one open position per road (`max_open_per_road: 1`; the story states it only for PS2-4); REF and RC1 are unlimited as written, so C2's Rs 30,000 bucket will refuse most later REF entries [reasoning only]; "20-session" windows are the 20 earlier recorded spots, not today's; PS2-4 wing limits are 1, 3 and 40 strike steps, so the ladder collapses where the widest wing under the cap is under 3 steps; a missing ATM straddle uses `no_valid_quotes` (a's new code; after the merge of a's final tip). Exits are priced at the touch without exit charges (the school fill adds them); DR1's "spot back through the mean" has no E4 rule and is a small predicate.
- **Real output sample:** no recorded day is reachable here (Groww quote files are Drive-only; the snapshot source is part b's). Counts only, from the Black-Scholes fixture chain, 5 roads x 3 histories, 126 decisions: N0 15 `n0`; REF 15, RC1 15, PS2/3/4 12 each, WS1 3, CS1 8, DR1 8 trades; DB1 8 `rule_not_fired`; CS1, DB1, DR1 4 each `not_enough_history`; KL1 and PS5 3 each `no_expiry_in_window`.
- **Gates:** pytest, ruff, `check_imports`, `check_records` on the pushed SHA (suite count in the message to the orchestrator).
- **Orchestrator's answers (22 Oct 2026):** the one-open-position limit on CS1, DB1, DR1 and WS1, unlimited REF and RC1 (REF entries refused by C2's bucket become `account_limit` tickets, a j requirement), PS5 and KL1 entering at the slot, and the driver-and-road pairing check left to j are accepted. PS3 and PS4 collapse into one trade on a road where the widest wing under the cap is under 3 strike steps: both are recorded, the cards say so, and they are one family, not counted twice. The `NO_VALID_QUOTES` code came with a's final tip and is now used (`no_structure_under_cap` stays for a structure that cannot be built under the cap).
- **Expiry-day entries (orchestrator, 22 Oct 2026; margin data has no row on an expiry day):** no driver enters on an expiry day. WS1 needs its expiry strictly after the session, so its first entry day is the session before expiry (`test_on_the_expiry_day_itself_there_is_no_entry`, `test_it_enters_one_to_three_sessions_before_the_weekly_expiry[1-True]`); REF and RC1 need `min_dte: 2`; CS1, DB1, DR1, PS2-4, PS5 and KL1 enter 20 or more days out. No card change was needed.
**Round 2 (judge J's 14 surviving plants, tip in the commit carrying this text).** `tests/school/drivers/test_oracles.py` kills each with an independent oracle (hand-worked numbers or the story's table, never the code under test); all 14 plants are caught (plant script run on this tip):
cap at exactly Rs 10,000 (`>=`) by building the same plan under a cap equal to its loss and one paisa less; score ignoring `expected_net_rs` by 500 / max loss, also through a ranked card with 500; the exit value priced on the wrong side by a hand-worked fixture (short bought back at the ask 11, long sold at the bid 4, lot 30, entry Rs 95, net -115); RC1's twin mapping (condor on monthly roads follows the ladder, on the weekly road WS1, vertical and fly follow CS1, DR1) by exits that differ between the twins; the WS1, DB1 and PS5 calendar-gap entries; `own_positions` ignoring the road; RC1's `min_dte` (never an expiry with under 2 days left); DB1 at exact equality (no trade) and just above (trade); `MAX_ATM_STEPS` at 2 against 3; PS3's wing at 3 steps (PS2 100, PS3 300, PS4 wider); and the payoff-bounds check at the touch (a fly never costs more than its wing width). DRY: `session_days.py` now uses `TradingDays.next_after` and `last_on_or_before`; only the counting and stepping back remain (`TradingDays` has none), and the tests use the real `TradingDays` over a fixture `SessionCalendar`.

### MS-P1f follow-up (test only, judges 481.2 and 490.2)

- `tests/school/tickets/test_rupees.py`: an account outcome whose exit the shared displayed size could not serve is
  left out of `account_net` and named; an exit that fits beside the others is summed. Plant: `account_net` ignoring
  the exit. It survived before this test; it is caught now.


### MS-P1g Claims (builder session_01WeFYCqffRe7et1nfSJyuv5, branch `story/ms-p1-sections`)
Round 1, built on a's tip 756e6545. Files: `fno/school/reports/` (inputs, banner, lines, today, evening, maker,
wiring), `tests/school/reports/` (with golden files), and the reserved lines in `fno/forecast_lab/page_wiring.py`:
the import of `with_school_sections` and the `return` of `build_report_maker` wrapped in it (two lines: Python needs
the import).
| Criterion | Code | Test |
| 1 flag off: both editions byte-identical (golden) | `wiring.with_school_sections` returns the maker itself when `school.reports` is false | `test_with_the_flag_off_the_edition_is_byte_identical_to_the_golden_files[morning, evening]`, `test_with_the_flag_off_the_maker_itself_is_returned_unwrapped`; the golden files were made from the unwrapped `ReportMaker` before any change (text, SHA-256 of the picture and of the details page, alerts, verdicts) |
| 2 flag on: sections appear and say Paper | `SchoolReportMaker.make`, `lines.paper_title` | `test_with_the_flag_on_the_edition_text_gains_its_section_and_the_page_files_stay_identical`, `test_both_sections_are_report_sections_and_say_paper` |
| 3 no green reachable | `Banner` has two members (a); `banner.banner_for` | `test_banner_has_no_green_and_every_input_maps_to_red_or_amber`, `test_the_banner_is_red_on_a_closed_road_or_no_candidate_else_amber` |
| 4 a planted refusal appears in the evening section | `evening._problems` | `test_a_refusal_planted_in_the_input_appears_in_the_evening_section` |
| 5 no contract, strike or card internal | the sections print codes, rupees and counts only | `test_no_contract_strike_price_or_card_internal_appears_in_either_section` (plants strikes, expiry, bid, premium, card and snapshot hashes) |
| 6 NSE-terms line and no-latency label in both | `lines.footer` | `test_both_sections_carry_the_nse_terms_line_and_the_no_latency_label` |
Broken-code proof: 8 mutations (flag check, banner rule, footer, ticket in rupees, controls shown, the exception
guard, a strike in a line, counts of controls) each fail a named test.
Design points to judge:
- The sections go into the Slack message text only; the picture and the details page are the signed-off page,
  untouched, so the signed-off design needs no change. A section that raises never stops the edition: one alert names
  the exception class (`school {edition} section not made (...)`), the plain edition is posted.
- "Today" is a plan from yesterday's data (response 325 section 9.21): its input port gives the roads and the planned
  trades; only `role: rule` drivers are shown, controls and measurement-only drivers never are. The fleet total counts
  every non-ticket outcome (controls included) and is labelled as separate hypothetical accounts; tickets are never in
  rupees and appear only in the counts.
- The day's inputs (`TodayInputs`, `DayInputs`) are ports: roads, the dashcam's records (c's replay reader), the
  counts (f) and the driver roles (e). They are wired by MS-P1j. Until then, a flag turned on gives the alert
  "the school's day inputs are wired by MS-P1j" and no section (`test_a_flag_turned_on_before_the_inputs_are_wired...`).
- Banner words (red: do not trade real money today; amber: paper only) are response 325 section 7.3's.
MS-P1g round 2 (judge 484 FAIL, round 1; each finding checked against the code and fixed):
1. **The school must never stop an edition (accepted):** `with_school_sections` now lives in `guard.py`, which imports
   nothing of the school at load time; the school's wiring and the `school` settings are read inside its `try`. A bad
   block, a missing or unknown key, a wrong kind, no block, an unreadable config or an import failure gives the plain
   signed-off edition (identical bytes) and one alert. `page_wiring.py` imports the guard (still the two reserved
   lines). Tests: `test_a_bad_school_block_gives_the_plain_edition_and_one_alert_naming_the_class` (5 cases x 2
   editions, including the judge's three plants), `test_an_import_failure_of_the_school_wiring...`,
   `test_a_bad_real_config_never_stops_the_edition`.
2. **Controls and the fleet total (accepted; orchestrator's decision, 22 Oct):** the evening candidates, the banner and
   the fleet total are rule drivers only; controls and measurement-only drivers have their own labelled lines
   ("Control (not in the fleet total)", "Measurement only (not in the fleet total)"). Tests:
   `test_when_only_a_control_trades_the_evening_is_red_and_the_fleet_total_stays_zero` (the judge's case),
   `test_measurement_only_drivers_have_their_own_line...`, `test_a_rule_drivers_trade_keeps_the_evening_amber...`.
3. **Minors (accepted):** `test_the_real_report_maker_is_built_through_the_school_guard` runs the real
   `build_report_maker` with its heavy parts stubbed and shows it goes through the guard (removing the call fails it);
   the failure alert carries only the exception class and a fixed text, never its message
   (`test_a_failure_alert_never_repeats_the_exceptions_message` plants a contract key and a strike).
Broken-code proof: 7 mutations of the new code (the guard's `except`, the candidate role filter, the fleet total, the
alert text, the `page_wiring` call, the flag check, the controls' lines) each fail a named test.
### MS-P1a2 Claims (round 1)
| Item | Code | Test (plant caught) |
|---|---|---|
| Per-expiry steps | `contracts/roads.py` `RoadDay.strike_steps`, `step_for` | `test_road_steps.py`: a later expiry's own step; no borrowing; wrong steps refused (a missing expiry, zero, a wrong nearest step, an extra expiry); still hashable. Plants: each check removed, borrowing allowed, the field hashed |
| Closed-road detail | `RoadStatus.detail`, `constants.ROAD_DETAIL_INPUT` | `test_a_closed_road_carries_its_detail_and_an_open_one_none`; `test_the_detail_is_recorded_in_the_decision_inputs`. Plant: an open road with a detail allowed |
| Conformance | `check_road_catalogue` | `test_the_catalogue_check_refuses_an_open_road_without_every_expiry_s_step`. Plant: the steps check removed from conformance |
- **Plants:** 7 planted, 7 caught.
- **Change for b:** `check_road_catalogue` now needs `strike_steps` for every recorded expiry on every open road.
- **Records:** neither layout nor bytes change.
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
### MS-P1d Claims, round 2 (judge 486 by Judge I: FAIL in round 1, 2 should-fixes and 1 minor; Judge B's findings follow)
| Judge 486 finding | Fix | Test (and the plant it catches) |
| 1. Any review row lifted the brake | "Pause till monthly review": a row dated from the engagement up to the day before the first Saturday of the next month is a `ReviewFileError`, never a lift (`accounts/brake.py`, `first_review_day`) | `test_brake_state.py::test_a_row_before_the_monthly_review_is_an_error_never_a_lift` (engaged 3 Nov: 4 Dec and 3 Nov refused, 5 Dec lifts), `test_the_review_is_the_first_saturday_of_the_next_month` (year end included), and the account view raising on an early row. Plant: the check removed |
| 2. No store meant settlement waited for ever, with no alert | `execution/wiring.py`: no store raises `SettlementStoresNotConfigured`, by name. To avoid a second version, b's `build_archive_stores` (the owner's Drive as a fallback) replaces this check once MS-P1b merges | `test_settlement.py::test_settlement_with_no_store_stops_by_name_never_waits_forever`. Plant: the check removed |
| Minor: no test of the charges cross-check | none needed | `test_school_accounts.py::test_a_leg_whose_charges_differ_from_c1_s_is_refused_before_any_write`. Plant: the check removed |
- **MS-P1j note:** settlement runs before the session's first `view` (added under MS-P1j).
- **Plants:** 41 planted, 41 caught (with the per-vertical plant below).
**Judge 488 (Judge B, PASS in round 1 at 96704ef8) notes, built at the orchestrator's request:**
| Note | Change | Test (and the plant it catches) |
| The impossible-price check must test each vertical, not only the total | `safety/quote_laws.py`: each bought-sold pair of one type and expiry is checked (on its quoted range since the owner's decision below; first at the mids). The total at the touch stays strict | `test_limits.py::test_a_stale_vertical_never_hides_behind_another_in_the_total` (a condor whose call vertical is worth -3 at the mids, while the total sits inside its bounds) and `test_a_vertical_worth_zero_passes_and_less_than_zero_refuses` (boundary). Plant: the vertical check removed |
| Acceptance 1's wording | Criterion 1 in this story now says the stop and the brake refuse at their limit | no code change |
- **MS-P1j note:** j switches d's settlement store to b's `build_archive_stores` once both parts are on main.
- **Owner's decision (22 Oct 2026, relayed by the orchestrator) between judge 486 addendum 1 (Judge I) and judge 488.1
  (Judge B): "ranges".** A vertical is impossible only when the dearer leg's ask less the cheaper leg's bid is below 0,
  or the dearer leg's bid less the cheaper leg's ask is above the width: the same meaning of impossible as b's gate.
  The mid rule of 9ed80bc7 is replaced, and B's 488.1 test (mid above the width, touch inside) is withdrawn, since that
  data is valid under ranges and the touch check still governs the fill. Tests in `test_limits.py`:
  `test_a_stale_vertical_never_hides_behind_another_in_the_total` (B's condor, refused at -2 on ranges),
  `test_a_vertical_whose_range_overlaps_its_payoff_is_valid` (I's condor: 1.5/2.5 against 1.0/4.0, not refused), and
  one boundary test for each bound. Plants: each bound dropped in turn, both caught.
### MS-P1h Claims (builder session_01WeFYCqffRe7et1nfSJyuv5, branch `story/ms-p1-card`)
Round 1, built on a's tip 756e6545. Not finished: the D6 rows and the ledger row wait (see "Open" below).
| 1 a card registered after a decision makes that day not counted | `counting.CountingRule._frozen_before` | `test_a_card_registered_after_the_decision_makes_that_day_not_counted`, `test_a_card_committed_in_the_decisions_own_commit...`, and on real git `test_a_card_edited_after_the_decision_makes_the_decision_not_counted` |
| 2 a changed card SHA-256 refuses counting | `CountingRule.verdict` (driver card vs its D6 row) | `test_a_changed_driver_card_sha256_refuses_counting`; a row registered after the decision: `test_a_version_row_committed_after_the_decision_is_not_counted` (real D6 `Versions`) |
| 3 five roads on one day are one cluster | `clusters.session_clusters`, `common_road_days` | `test_five_roads_on_one_day_form_one_cluster_and_count_as_one_session`, `test_the_common_group_holds_only_road_days_every_control_has_counted` |
| 4 `read_card` accepts the card | `research/school/CARD_P1.md` | `test_read_card_accepts_the_card_as_a_measurement`; the cost block hash: `test_the_card_names_the_charges_block_that_config_yaml_holds` |
Broken-code proof: 3 mutations (own-commit rule, driver card SHA check, first counted session) each fail a named test.
D6 change (orchestrator-approved 22 Oct 2026, flagged for the judge: it touches D6's `fno/books/version_registry.py`,
`fno/books/versions_cli.py`): `is_known_book` accepts the three books or `school:<driver code>@<version>`
(`SCHOOL_BOOK_PREFIX` named at the top; `BOOKS` untouched). Tests `tests/versions/test_school_books.py`: a school id is
accepted, a malformed one refused, the three books and the existing rows parse and render byte-identically, each
school version has its own order. The existing 308 tests of `tests/versions`, `tests/school`, `tests/decisions` pass.
Trial accounting (orchestrator, 22 Oct): one measurement card, one ledger trial, no Holm family; PS5 and KL1 point at
their EDGE1 trials 94 (BANKNIFTY SF TP50) and 76 (NIFTY SC3 EXP), read from `research/ledger.csv`.
Open: part e's card files do not exist yet, so no driver card SHA-256 or D6 row can be written; the ledger row
(trial 99) is written by `factory register` when the orchestrator says. First counted session: unset by design.
MS-P1h round 2 (judge 480 FAIL, round 1; each finding checked against the code and fixed):
1. **First counted session (blocking, accepted):** `CountingRule` no longer takes the date from settings. It reads
   `school.first_counted` from `config.yaml` as committed at the decision's own commit and requires the commit that
   first wrote that value (git pickaxe, the research engine's `Git`) to be a strict ancestor of the decision's commit
   (`first_counted_not_frozen_before`, `no_first_counted_session`, `before_first_counted_session`). Tests on real git,
   including the judge's plant: `test_a_first_counted_session_moved_back_after_the_decision_never_re_counts_it`,
   `..._moved_later_after_the_decision_never_un_counts_it`, `..._set_after_the_decision_does_not_count_it`,
   `..._written_in_the_decisions_own_commit_is_refused` (fake-history twins in `test_counting.py`).
2. **Card versions (accepted):** a decision counts under the card's last commit strictly before it
   (`CountVerdict.card_commit`); a later version applies to later decisions only
   (`test_a_later_card_version_applies_only_to_later_decisions`, `test_a_card_edited_after_the_decision_leaves_it_counted...`).
   The test forcing a card edit on a `charges:` change is removed; the card's cost hash is now checked against
   `config.yaml` as committed at the card's last commit (`test_the_cost_block_named_by_the_card_...`).
3. **Card text (accepted):** "EDGE1: 24 variants (trials 71-98) found no edge after costs; this does not prove no edge
   exists" replaces "98 counted trials"; the band and the impossible-price bound are frozen as part b's own
   (orchestrator, 22 Oct: one source of truth): 10 strike steps (`fno/school/quality/band.py` `DEFAULT_BAND_STEPS`,
   b's tip 183783bd) and `impossible_keys` (`fno/school/quality/prices.py`, judged on bid-ask ranges, not mids);
   PS5's road (BANKNIFTY-M) and KL1's (NIFTY-M) are named (`test_the_card_freezes_the_pieces_judge_480_named`).
   Part e's cards must carry `band_steps: 10`. b is not on this branch, so the pin test
   (`test_the_cards_band_is_the_quality_gates_constant`) skips here and runs once main holds b: j should check it
   ran. Whether 10 steps is wide enough for the 1-expected-move shorts is reasoning only (a leg outside the band is
   still checked by the quote gate when the trade is made).
4. **DRY (accepted):** `GitCardHistory` and the test's `RegistryHistory` are gone; one adapter, `GitCountingHistory`,
   wraps `fno/research_engine/ledger.Git` (`is_ancestor`, `commits_touching`, `committed_text`,
   `first_commit_containing`), and the tests use `Git` itself, also for D6's `Versions`.
Minors: (a) and (b) the two weak tests are replaced by `test_the_card_says_how_the_first_counted_session_is_set_and_proved`
and a pinned `CARD_COMPONENT` (`test_the_version_component_name_part_e_must_use_is_pinned`; also kills the renamed
constant plant); (c) the CLI `_book` is tested (`tests/versions/test_school_books_cli.py`); (d) the common group is no
longer called "frozen once": the card and `clusters.py` say it is computed at report time, per card version.
Broken-code proof: 8 mutations of the new code (tree read at HEAD, strict check, card version selection, date check,
driver SHA check, the CLI guard, the component name, the pickaxe) each fail a named test.
MS-P1h round 3 (judge 480 addendum 1, owner: "fix, then Judge H re-checks only those fixes"; each point checked and fixed):
1. **Should-fix, a charges change without a new card version (accepted):** `test_the_charges_block_in_force_matches_the_cost_hash_frozen_in_the_current_card_version`
   compares the `charges:` block of `config.yaml` at HEAD with the hash in the current card; a change fails CI until a
   new card version is cut. Versions apply forward only, so no earlier decision is touched. Checked by changing a
   charge in `config.yaml`: the test fails; restored: passes.
2. **Minor (a), one spelling (accepted):** `GitCountingHistory.first_counted_at` no longer pickaxes one spelling. It
   reads the parsed value at every commit of the history that touched `config.yaml` and takes the commit that began
   the value's current run, so aligned, commented and quoted lines are found. A value that is in the tree but whose
   writing commit is not found raises `FirstCountedError`, a value that is not a date raises, and a shallow clone
   stops by name; nothing counts silently. Tests: `test_the_value_is_found_whatever_its_spelling` (5 spellings),
   `test_an_aligned_value_counts_decisions_after_it`, `test_a_value_that_is_not_a_date_raises...`,
   `test_a_value_in_the_tree_that_no_commit_of_the_history_wrote_raises`, `test_a_shallow_clone_stops_counting_by_name`,
   `test_a_value_set_again_after_a_change_is_dated_by_its_latest_run`.
3. **Minor (b), traded legs outside the band (accepted):** the card now says the impossible-price rule on the band's
   legs measures capture quality, and that a traded leg outside the band is checked per proposal at the touch by part
   d's `ImpossiblePriceLaw` (`fno/school/safety/quote_laws.py`, on story/ms-p1-fills; refusal `impossible_leg_price`),
   beside law 5's quote gate. The judge's point that law 5 itself does not check impossible prices is right and the
   card says so. d is not on this branch: `test_the_law_the_card_names_for_traded_legs_exists_in_part_d` skips here
   and runs once d is on main (j should check it ran).
4. **Minor (c), quoted date (accepted):** `test_a_quoted_date_counts_like_a_bare_one` and the quoted spellings above
   (plant on `_as_date` caught).
Broken-code proof: 5 mutations of the new code (text kept as text, the run reset, the not-found raise, the shallow
stop, the unreadable raise) each fail a named test.
5. **Card known limits (orchestrator, 22 Oct):** §6 of the card states that the expiry-day ELM is not modelled, so a
   driver holding a position into its expiry day gets a `margin_room` refusal on every new entry that day; the blocked
   entries become `account_limit` tickets; reports show the `margin_room` share per road on expiry days; the fix is P2's
   (P0 probe 4). Pinned by `test_the_card_freezes_the_pieces_judge_480_named`.

**Follow-up `story/ms-p1-drivers-tests` (judge 489 minors).** `test_quotes_and_estimates.py`: every ranked card's `expected_net_rs` is pinned at 0.0 (CS1 at 500 fails it; plant caught) and every family says `no_valid_quotes` when its road has no quotes while the same day trades with them (11 drivers; plant: `quotes_missing` off, caught for DR1, PS5 and KL1). One small code change came with it, because the test showed a gap: DR1, PS5 and KL1 do not read the expected move, so a road with no quotes was reported as `no_structure_under_cap`; `ProposalBuilder.quotes_missing` (D2's own listing test) now tells the rule driver to say `no_valid_quotes`. A structure listed but over the cap still says `no_structure_under_cap` (tested).
**Structure codes (orchestrator, 22 Oct 2026; MS-P1m accepts only SC, SF, BF, PCS, CCS, CDS, PDS).** `test_structure_codes.py` checks every proposal of every driver (and 80 RC1 days) against the definition of each structure: accepted code, leg count, kinds and sides, far leg further out, equal wings, fly on one strike, condor on two. Per family: PS5 SF; KL1, REF, WS1, PS2-4 SC; DB1 BF; DR1 CDS or PDS; CS1 PCS or CCS; RC1 all six. One fix came out of it: RC1's condor could draw both shorts on the same strike (reach 0), which is an SF fly labelled SC; it now draws at least one step (plant caught).

### MS-P1h registration follow-up (orchestrator, 22 Oct 2026; branch `story/ms-p1-card-registration`, lane 1)

Built from main (card v1 and the 12 part-e cards on main), in this order so each row names what is already committed:
1. **Driver cards frozen** (commit 0deda30b): the 12 cards of part e carry `band_steps: 10`, the band the comparison card
   freezes (part b's `DEFAULT_BAND_STEPS`); they had 0, 5, 20 and 40, which the card says must be 10, and nothing in
   `fno/school` reads the field. The "DRAFT" line becomes a frozen line. This edits part e's files: it is the freeze
   step the story gave h ("draft until h freezes them"); e's tests pass unchanged.
2. **Comparison card version 2** (0c0f1b24; orchestrator's decision, 22 Oct, before any counted day, none exists): §6
   now says each proposal's margin models the expiry-day ELM (SEBI 2024/132 para 5.6; part m), priced rather than
   refused, with k = 2.1 stacked on it conservatively (A14c's open item); the factory block is `version: 2`; §1 lists
   every driver card with its SHA-256; the ledger trial is named. v1 (merged earlier, never registered or counted) said
   the ELM was not modelled. Part m was passed by both judges but may not be on main when this merges: the text states
   the decision, not code that exists on this branch.
3. **D6 rows** (c0c2775d): 12 rows `school:<driver id>`, version 1, from 22 Oct 2026, `registered_in_commit` the commit
   that holds the cards and card v2, components `card_sha256` (the driver card file) and `comparison_card_sha256`
   (CARD_P1 v2's SHA-256), reason naming trial 99 and "CARD_P1 v2"; written with `python -m fno versions register`.
   First counted session stays unset (`config.yaml` untouched).
4. **Ledger row, trial 99** (the code `factory register` calls, `IdeaRegistration.register`): ledger, gate-log `idea`
   row, `research/LEDGER.md` (row and total 99), `research/DATA_SPEND.md` (a `registered` row for the pilot's quotes and 99
   on the NIFTY A4 row). Trial 99 was still free on main (maximum 98) when written; re-check at merge.
- **Gap for the orchestrator:** `python -m fno factory register CARD_P1` cannot be used: `read_idea` reads only
  `research/ideas/<id>.md`, and the card lives in `research/school/`. `factory report` (`read_all_ideas`) therefore does
  not see CARD_P1: trial 99 is not listed among the measurements and the expected-false-passes line counts it as a
  test (0.01 more at alpha 0.01). Fix options: move the card into `research/ideas/` or let `read_all_ideas` also read
  `research/school/CARD_P1.md` (an R1 change). Not done here.
- **Tests** (`test_registered_cards.py`, `test_card.py`): every card carries the frozen band and is not DRAFT; every card
  file is in D6 with its own SHA-256, in the card's table, and in the registration commit as it is; every row names
  the comparison card as committed at its own registration commit, version 2; trial 99 is in the ledger, the gate log
  and the data-spend register; the card's §6 text is pinned to v2. Plants: a changed D6 driver hash fails one test, an
  edited card file fails three, a changed comparison hash fails one.
- `tests/research/test_ledger_guard.py` pins the ledger's trial ids (1..98); bumped to 1..99 with the registration (the
  full suite on the first push of this branch failed only there).

### MS-P1b follow-up (after a2 and Judge I's judge 483 Addendum 1; builder session_01F1RVMF8MNngi97JVNs99L5)
On `story/ms-p1-roads-followup`: `main` merged (a2 included); the catalogue fills `RoadDay.strike_steps` with every recorded
expiry's own step from `quality/strikes.py` (`Capture.strike_steps()`; `strike_step` stays the nearest expiry's), tested
for a two-step chain (`day.step_for`) and for every road on a good day; `prices.py` carries the judge's mids figures;
an expiry with fewer than two strikes makes the capture `capture_incomplete` (tested).
### MS-P1i Claims, round 2 (judge 487 FAIL round 1: one blocking, one should-fix, two minors)
Built on `main` (a merged) plus part b's round-2b tip fdbea6c7, because the planters now sit on b's real input types.
**1. Blocking, the closure planters (fixed; the orchestrator's ruling).** A `Scenario` is now the data the detectors read,
not a verdict: `snapshots` (what each road's capture holds), `listed_expiries` (what the archived NSE listing says each
road records), `lots` (the session's dated lot copy, units per expiry), the drivers and the seal timing. There is no
road status in it.
- *Expiry mismatch:* the capture's contracts and expiry list carry dates a week later than the listing's.
- *Lot mismatch:* the lot copy gives the later expiry another lot than the earlier one, so there is no single lot.
- *Impossible price:* two strikes of one expiry and type are quoted so that the dearer leg's whole bid-ask range sits
  below the cheaper leg's bid (b's `impossible_keys`: the vertical cannot be worth 0 to its width).
The same reason codes are expected. The fake rig runs b's real classes over them: the scenario's snapshots are written as
the recorder writes them (sidecar, quote file, canonical marker) and read back by `CaptureReader`; `RecordedRoadCatalogue`
compares the expiries with the listing and the lot copy; `RoadQualityGate` closes the road on the price. Tests:
`test_the_closure_planters_change_the_data_the_detectors_read_never_a_verdict` (the planted data differs, and the clean
chain has no impossible leg while the planted one has) and
`test_the_real_detectors_name_the_planted_reason_before_any_driver_decides` (b's catalogue says `expiry_mismatch` and
`lot_mismatch`; its gate says `impossible_price`). **For j:** `real_rig(scenario)` writes `snapshots` as captures through
the real recorder writers, `listed_expiries` as the archived F&O file and `lots` as the archived `fo_mktlots.csv`, then
runs the real fleet; the planters are used unchanged.
**2. Should-fix, the nine unproven checks (fixed).** `tests/school/acceptance/test_harness_checks.py` feeds a bad run or
rig to each and sees it fail: the closure leak, a position opened for a refused entry, stale-seal fills reaching the
ledger, a rerun that fills again or seals other decisions, a scheduled decision with no sealed outcome, a trade
decision over the cap, the refused entry's exact reason, the fill-path reason, and a partial fill.
**3. Minors (fixed).** (a) The fill-path reason is matched on the planted driver's own fill (fills are one per trade
decision, in decision order; conformance's `check_fleet` holds the counts equal), and a test shows a reason on another
driver's fill does not count. (b) `check_no_invented_fills` now covers exits (at the touch of the road's snapshot);
a settlement (exit reason `expiry`) is priced at intrinsic against NSE's file, not a quote, and stays with part d's
settlement tests, said in the check's docstring and tested to be skipped.
**Mutations:** 16 applied to the harness, planters, scenario and capture writer (the nine checks, exits, the own-fill
tie, the three planters as no-ops, the key shift, the writer's valid flag), 16 caught, none surviving (two survived
first, and a test was added for each). Tests: 42 in `tests/school/acceptance/`.
**Limits that remain:** the counts file, section inputs and denominator on the fakes are derived from the sealed
decisions file (f, g and j supply the real ones); a missing quote is accepted as a law refusal or a refused fill; the
replay-conflict fault is checked at the dashcam.
### MS-P1d follow-up Claims (branch `story/ms-p1d-margin`; part 1, on MS-P1m; the MS-P1b part follows once b is on main)
| Item (orchestrator, 22 Oct 2026) | Change | Test (and the plant it catches) |
|---|---|---|
| Law 3 on MS-P1m's margin per trade | `safety/margin_law.py`: C2's `MarginRoom`, unedited, on the `StressedMargin` the fleet builds once per run (`safety/wiring.build_margin(cfg)` = MS-P1m's `build_road_margin`). The margin-row file check (`MarginRows`) is gone. An unreadable margin refuses, with the note "margin not checked: <MS-P1m's named cause>" (`C2Law.unchecked_note`) | `test_margin_law.py` (plants: note dropped, unreadable input passes, C2's own refusal reported as no data) |
| C2's inputs from MS-P1m's terms and factories | `safety/c2_inputs.road_terms`: a `RoadTradeTerms` per trade (index, one expiry, one unit per leg, lots, lot, its shape checked by MS-P1m); C2's proposal and open trades come from `road_proposal`/`road_open_trade`, so C2's units and margin read one source | `test_c2_s_units_and_margin_come_from_one_set_of_terms` (plant: the terms' lot set to 1, MS-P1m's 840 vs 54,600 case); `test_equal_c2_terms_on_two_indices_get_their_own_margins`; `test_terms_of_two_expiries_or_a_leg_ratio_are_refused_before_c2` (plant: the expiry guard dropped) |
| School terms never reach the desk's two `TradeTerms(**asdict(...))` codecs | no code; pinned | `test_terms_never_reach_desk_codecs.py`: the round trip fails on school terms, no school module imports either codec, and the school's three composition roots load neither (fresh interpreter) |
- **Expiry day:** MS-P1m now prices a held trade on its own expiry day with SEBI's extra 2% ELM (`expiry_day_exposure.py`)
  instead of refusing it, so the expiry-day known limit planned for MS-P1j no longer applies; nothing is added there.
- **Structure codes:** MS-P1m's terms accept only SF, SC, BF, PCS, CCS, CDS and PDS in their own shapes; any other
  refuses under every C2 law (routed to e by the orchestrator).
- **Still to come, once MS-P1b is on main:** `_verticals` on b's vertical-range function with its 1e-9 tolerance
  (tests at the bounds +/- 1e-12), and settlement on b's `build_archive_stores`.
- **Plants:** 6 planted on this part, 6 caught.
- **Judge 494 (Judge I, round 1) should-fix, test only:** `test_a_held_trade_s_entry_net_is_its_cash_flow_in_c2_s_max_loss`:
  a held credit spread counts in the open-risk cap at C2's own held maximum loss for its `entry_net`; at the cap, no
  credit refuses and twice the credit passes. Plant: `entry_net` replaced by 0 in `c2_inputs` is caught. The MS-P1j
  requirement on `LawResult.note` (never to Slack; counted by cause) is added.
MS-P1h, Judge H's two notes on the registration (judge 493; orchestrator, 22 Oct 2026; on `story/r1-cards-anywhere`):
1. **Ledger row 99, `protocol_commit`** (note a): filled with 0c0f1b24, the commit that froze comparison card v2.
   `test_the_ledger_row_of_trial_99_names_the_commit_that_froze_card_version_2`: the card at that commit is version 2,
   the commit is an ancestor of HEAD, and every D6 row's `comparison_card_sha256` is that card's SHA-256.
2. **`comparison_card_sha256` is now checked** (note b; the orchestrator chose to enforce it): `CountingRule` compares
   each D6 row's `comparison_card_sha256` with the SHA-256 of the comparison card as committed at the card version in
   force at the decision (`CountingHistory.card_sha256_at`, one more `git show`), and a mismatch, or a row with no such
   component, does not count (`comparison_card_mismatch`; the verdict still names the card version). A later card
   version therefore counts only for decisions made after rows naming it are registered; a decision already made keeps
   the verdict of its own history. The card text is unchanged by this (any edit to it is a new version, so it would
   need new rows). Tests: three in `test_counting.py` (a mismatch, a row without the hash, a later version needing
   rows that name it), two on real git (a card edited later: earlier decisions keep counting, later ones do not until
   rows naming the new version are registered; a row naming a card nobody committed), and
   `test_the_real_rows_and_the_real_card_pass_the_counting_rule_once_a_first_counted_session_is_set` (the 12 real rows
   and the real card judged by the real rule on the real history, with only the unset first counted session
   supplied). Plants: dropping the comparison check fails 5 tests; changing one real row's comparison hash fails 3.

### MS-P1d follow-up Claims, part 2 (branch `story/ms-p1d-verticals`, from main 390d7131 with MS-P1b merged)
| Item (orchestrator, 22 Oct 2026) | Change | Test (and the plant it catches) |
|---|---|---|
| DRY: the per-vertical check calls b's function | `safety/quote_laws.py`: `ImpossiblePriceLaw` calls b's `impossible_keys(snapshot, among=<the proposal's legs>)` (`quality/prices.py`); d's own `_verticals` copy is gone. One rule for b's gate and d's law: every same-type pair of one expiry within [0, width] on the quoted ranges, and no bid above what the option can be worth. Judged on the proposal's own legs only, so a broken vertical elsewhere in the chain never refuses it. The law's value is now the count of flagged legs | `test_limits.py`: B's and I's condors, both bounds, `test_the_law_judges_only_the_proposal_s_own_legs` (plants: the whole chain judged; b's rule ignored) |
| b's 1e-9 tolerance at both bounds | b's `TOLERANCE` (no copy) | `test_the_lower_bound_has_b_s_tolerance`, `test_the_upper_bound_has_b_s_tolerance`: bound +/- 1e-12 passes, 2e-9 beyond refuses (plants on b's constant: 0 and 1e-6, both caught) |
| Settlement on b's stores | `execution/wiring.build_settlement_source` reads `roads.wiring.build_archive_stores` (the service account's Drive, else the owner's, else `RawFilesNotConfigured`); d's `SettlementStoresNotConfigured` is gone | `test_settlement_with_no_store_stops_by_name_never_waits_forever` (plant: no store) |
- **Plants:** 5 planted, 5 caught.

### MS-INS Claims (the instructor v1)

Empty until INS-a is built. Each part's round adds its subsection here: the criteria met with test names and
broken-code proof, the self-review findings, and a real output sample (counts only).

#### INS-a Claims (round 1, branch `story/ms-ins-contracts`; the SHA is in the commit that carries this text)

| Criterion | Met by | Test (`tests/school/instructor/`) |
|---|---|---|
| 1 path with its snapshots in order; a ticket read as a ticket | `reader.PathReader._path` | `test_reader`: `..._three_snapshots_in_order`, `a_ticket_is_read_as_a_ticket...`, `a_weekend_inside_the_hold...` |
| 2 a correction read once | `reader.latest_outcomes`, `PathReader.closed_between` | `test_reader`: `a_correction_sealed_on_a_later_session...` (two separate seals), `..._in_the_same_file_is_read_once` |
| 3 a snapshot hash mismatch is a data fault, never numbers | `PathReader._snapshot` | `test_reader`: `a_snapshot_whose_hash_differs...` and every fault case below |
| 4 empty | `PathReader.closed_on` | `test_reader`: `a_session_with_no_outcome_file_gives_nothing` |
| 5 reads only | the reader holds no write path; the dashcam fake refuses writes after the fixtures | every `test_reader` test (`WriteRefusingDashcam`); the whole run again in INS-e |
| 6 imports | the school's import test walks `fno/school/` | `test_types`: `the_school_import_boundary_covers_the_instructor` |
| 7 conformance | `fakes.py`, `adapters.py` | `test_ports` (fakes, `RecordedSnapshotArchive`, `RecordedEventCalendar`) |
| types refuse the impossible | `contracts.py` | `test_types` (identity to Rs 0.01 at the boundary, NaN, 2 secondaries, 3 statuses, 13 causes, loser-only causes, interval and dates) |

**Data faults (each a test):**
- entry decision missing or not a trade or ticket of its kind;
- entry seal mismatch;
- a held trading session with no sealed decisions file;
- a snapshot missing on a session with no closure record for the road;
- a snapshot hash mismatch;
- settlement missing or naming another file;
- an exit record that is missing, or that names another driver or reason.

A road closed by a sealed closure record is not a fault: its step merges (`sessions_skipped`).

**Broken-code proof:** 13 plants, each run against the instructor tests, 13 caught. The plants: the snapshot, entry-seal and settlement hash checks removed; corrections kept; the entry-kind check loosened; the closure rule, the unsealed-session fault and both exit-record faults removed; calendar days walked instead of NSE sessions; the identity's NaN guard reversed; the paired-row date order and the path's road check removed. A first round left the entry-kind plant alive; the parametrized `an_outcome_whose_decision_was_not_its_kind...` test was added for it.

**Self-review (one independent review agent on the diff).** Six findings:
1. **Blocking: corrections across files.** Accepted. A dashcam file is written once, so a correction can only be sealed on a later session. `closed_between` now applies corrections across a range, tested with two separate seals; the old test rewrote a sealed file, which the real store cannot do.
2. **Should fix: a missing road record treated as a closure.** Accepted. Only a sealed closure record now merges a step; otherwise the session is `snapshot_missing`.
3. **Should fix: missed sessions.** Accepted. The reader walks A7's calendar, and a trading session without a decisions file is `session_not_sealed`.
4. **Should fix: NaN passed the identity check.** Accepted. NaN is now refused, and `PairedRow` also checks its interval, mean and dates.
5. **Minor: exit records not checked.** Accepted. An exit record that is missing or mismatched is now a fault.
6. **Should fix: test and spec gaps.** Accepted. Criterion 5's docstring now says the full run is checked again in e; the import pointer test was added; the files-owned list and the story text were updated.

From the reviewer's minor list, `HeldPath`'s road check and `PairedRow`'s dates were done. The double read of the entry day's file is left as is: one extra cached read, and merging the two reads would join two single-purpose functions.

**Real output sample:** none possible yet. The fleet (MS-P1j) has sealed no dashcam file, so `build_path_reader().closed_on(<day>)` has nothing to read. The first real sample comes with INS-e's dry run once j seals a day. The fixture run gives counts only: 1 path, 3 snapshots, 0 faults (`test_reader`).

**Gates:** the full gate run on the merged tree is in the push message to the orchestrator.

### MS-P1d follow-up Claims, part 3 (branch `story/ms-p1d-entries`): the read-only ledger read for j

| Item (orchestrator, 22 Oct 2026) | Change | Test (and the plant it catches) |
|---|---|---|
| `SchoolAccounts.entries(driver_id) -> tuple[LedgerEntry, ...]` for j's `LedgerReader` (a3), so settlement can run before the session's first `view` | `accounts/school_accounts.py`: under the account's lock, pulled from Drive once per run (`_locked`, shared with the writer), reads `PositionBook.entries()` in the order recorded, after the same unit-for-unit ledger check `view` makes; writes nothing (no account opened, no equity row, no push); an account never opened gives () | `test_entries.py`: entries match the ledger in order (plant: order reversed); nothing written and no push, the next session's row still written by `view` afterwards (plant: entries opening the account); one pull per run under the lock, a held lock refuses (plant: no pull); a failed pull stops with E2c's `PrivateFilesUnavailable`; half a record raises (plant: the check dropped) |

- **Plants:** 4 planted, 4 caught. The Protocol's conformance check is added once a3 (j's builder) is on main.

#### INS-a Claims, round 2 (judge 501 FAIL round 1: two should-fixes, four minors; orchestrator's ruling on SF2)

| Finding | Fix | Test (`tests/school/instructor/`) |
|---|---|---|
| SF1: a damaged sealed file crashed the reader | `PathReader._read` catches `StaleSeal`. A damaged decisions file is `sealed_file_damaged` on each path that needs it (the entry day or a held day); a damaged outcomes file goes in `ClosedRead.unreadable`, and the other days still read | `test_reader`: `a_damaged_held_day_is_a_fault...`, `a_damaged_entry_day_is_a_fault_not_a_crash` (and not "entry missing"), `a_damaged_outcomes_file_is_reported_and_the_other_days_still_come_back` |
| SF2: per-day reads counted a correction twice | One resolver, per the ruling: `closed_on(d)` is `closed_between(d, d)`. An original is read on its close day as its latest correction sealed up to today (the reader's clock), and a correction is never a path on its own day | `the_days_closed_on_add_up_to_closed_between_over_the_range` (a correction inside the range and one after it); `a_correction_sealed_later_replaces_its_original_on_the_original_close_day`; `a_chain_of_corrections_ends_at_the_latest`; `a_correction_sealed_after_today_is_not_yet_read` |
| (a) mid-range outcome | none needed | `an_outcome_sealed_mid_range_is_read` |
| (b) the trading-day filter | none needed | `a_muhurat_only_session_inside_a_hold_is_not_required` |
| (c) the exit-day check, the snapshot ID, the adapter's closed road | none needed | `an_exit_day_closed_for_the_road_is_a_missing_snapshot`, `a_snapshot_with_the_right_hash_but_another_id_is_a_mismatch`, `test_ports`: `the_archive_itself_refuses_a_closed_roads_capture` |
| (d) pinned bytes | none needed | `test_types`: `an_instructor_file_has_pinned_bytes...` (gzip time zero, no name) |

- **The judge's six surviving plants and six new ones, all caught.** The new ones: the `StaleSeal` catch; corrections emitted on their own day; "today" cut to `last`; days after `last` emitted; one correction followed instead of the chain; `unreadable` emptied.
- One extra plant survived on the first run: removing the entry-day damaged check. The test now also requires the fault to say "damaged", not "entry missing".
- **The clock:** the reader takes a's `Clock`. The wiring passes `IstClock` (`now_ist`) and the tests a `FixedClock`.
- **Known effect, as the ruling says:** a day's tally recomputed after a later correction can change.
### MS-P1d follow-up Claims, law order (branch `story/ms-p1d-law-order`, from main)
| Item (orchestrator, 22 Oct 2026, on j's finding) | Change | Test (and the plant it catches) |
| The first named reason is the root cause: on BANKNIFTY-M a missing quote came out as `max_loss` (it fails closed without the leg's mid) ahead of `missing_quote` | `safety/wiring.py`: protected, the four quote-gate laws, impossible price, then max loss, bucket, open risk, new risk per day, margin room, daily stop, brake. Every law still runs and every reason is kept; only the order changes | `test_laws.py`: the order pinned (plant: the old order); a missing and a one-sided quote name their quote reason first, with `max_loss` still in the list (plant: the gates after max loss); a valid quote with too large a loss still names `max_loss` alone (plant: a gate that refuses a valid quote); the margin test reads results by law name, not by position |
- **Plants:** 2 planted (old order; a gate refusing a valid quote), 2 caught. f's `named_refusal` (first in order within a group) now names the quote reason within trade validity too.

#### INS-b Claims (round 1, branch `story/ms-ins-attribution`, on INS-a; the SHA is in the commit that carries this text)

| Criterion | Met by | Test (`tests/school/instructor/attribution/`) |
|---|---|---|
| 1 hand-computed spread | `attribute.attribute`, `greeks.greeks`, `points.snapshot_point` | `test_attribute`: `the_hand_computed_put_spread` (every intermediate value in its docstring; found independently by finite differences, and again by the review agent with its own Black-76) |
| 2 pure forward move | `add_step` | `a_pure_forward_move_has_no_vega_and_no_theta` |
| 3 pure time step | `add_step` | `a_pure_time_step_has_only_theta` |
| 4 identity | `Attribution.__post_init__`; the residual from fill-measured costs | `on_random_paths_the_residual_is_the_mid_to_mid_pnl_less_the_greeks` (200 paths) |
| 5 merging | `attribute` (incomplete middle points, plus closed-road sessions) | `a_middle_snapshot_missing_a_leg_merges_its_step`, `a_session_the_road_was_closed_counts_as_a_merged_step` |
| 6 unsolvable volatility | `add_step` | `an_unsolvable_volatility_puts_that_legs_step_in_the_residual`, `..._at_the_steps_end...` |
| 7 settlement last step | `points.settlement_point` | `a_settled_positions_last_step_ends_at_intrinsic_with_no_vega` |
| 8 poor fit at the boundaries | `is_poor_fit` | `poor_fit_needs_both_rs_200_and_a_quarter_of_the_components` (Rs 200 and 25%, at and beyond) |
| 9 one snapshot | `attribute` | `entry_and_exit_on_one_snapshot_is_costs_only` |
| 10 broken-code proof | below | |
| Greeks with a rate | `greeks.greeks` | `test_greeks` (finite differences, both kinds, r = 6.5%); `at_a_652_rate_theta_carries_its_rate_term` (pinned) |
| no attribution without data | `attribute` | `a_faulted_path_or_a_missing_entry_or_exit_mid_is_not_attributed`, `legs_on_two_expiries_are_not_attributed`, `a_nan_price_on_an_unrelated_strike_does_not_spoil_the_forward` |

**One deviation from the text:** `greeks.py` wraps B1's `Black76`, the project's one pricer and inverter, directly. It does not call G13's `pricing.black76_price` and `pricing.implied_vol`, because those take whole days and the attribution needs minutes to 15:30. The Black-76 gamma, vega and theta are new. The delta repeats G13's formula in years.

**Broken-code proof:** 17 plants over two rounds, all caught. They cover the leg signs, Greeks taken at the step's end, the theta time sign, the half in gamma, the merge rule, the spread, vega at expiry, the theta rate term, the expiry close time, the poor-fit boundary, the exit-mid check, the finite filter, the two-expiry guard, closed-road merges, the spread sign and the exit spread's snapshot. In round 1 the theta rate-term plant survived; `test_greeks` (r = 6.5%) was added for it. In round 2 the two-expiry plant survived, because missing quotes refused the path first; the test now quotes both expiries.

**Self-review (one independent review agent; it re-derived the hand numbers itself):** no blocking finding.
1. **Should fix: the spread came from the record, whose basis is not fixed.** Accepted. The spread is now measured from the fills against the path's own mids, and a test shows the record's value is ignored.
2. **Should fix: a NaN price on any strike spoiled the forward.** Accepted. Mids and forwards are now finite or None.
3. **Should fix: a settlement treated every leg as being on the near expiry.** Accepted. Paths with legs on two expiries are not attributed (law 1 refuses those anyway).
4. **Minor: closed-road sessions were not counted in `steps_merged`.** Accepted.
5. **Minor: the rate test was loose.** Accepted. It is pinned to Rs 0.01.
6. **Minor: the random test proved less than claimed.** Accepted. Its docstring now says what it checks.
7. **Minor: spec and DRY.** Accepted. The file list and the deviation above are recorded.

The integer-day parity forward was checked and is negligible (about 0.0003 points per 100 of call minus put). It is noted in `points.py`.

**Thresholds:** `POOR_FIT_RS = 200` and `POOR_FIT_SHARE = 0.25` sit in `attribute.py`. INS-c writes `research/school/INSTRUCTOR_V1.md` and its test pins every threshold to the card, these two included.

**Rebased onto INS-a round 2 (a2c26465), as the orchestrator ordered.** A corrected trade is attributed once, as its
correction, on its original close day, and nothing is attributed on the correction's own day
(`test_corrected.py::test_a_corrected_trade_is_attributed_once_on_its_original_day`, through a's real resolver).
b reads only `HeldPath`, so a's new `ClosedRead` result changes nothing in b's code.

**Orchestrator's ruling on the deviation (22 Oct 2026):** wrapping B1's `Black76` directly is accepted. It reuses the
one pricing model rather than adding a second, and G13's helpers take whole days, not minutes.

**Real output sample:** none yet, as in INS-a (no sealed day). Fixture: the hand-computed spread gives delta -286.32, gamma -45.61, vega -52.53, theta +24.99, residual +10.74, costs 86.00 and net -434.73.

#### INS-b Claims, round 2 (judge 503 FAIL round 1: one should-fix, one minor; orchestrator's ruling)

| Finding | Fix | Test |
|---|---|---|
| SF: the residual trusted `outcome.net`. A net moved by Rs -500 read as residual -494.59 | `contracts.net_matches_fills`: the net must be its fills' cash to Rs 0.01. Otherwise the reader gives the path the named fault `net_mismatch_fills`, and `attribute` returns None, never forcing the gap into the residual | `test_reader`: `an_outcome_whose_net_is_not_its_fills_cash_is_a_fault` (the Rs -500 case), `the_net_is_checked_to_a_paisa` (Rs 0.01 passes, Rs 0.011 is a fault); `test_attribute`: `a_net_that_is_not_its_fills_cash_is_never_attributed` |
| Minor: a stale docstring | `attribute.py`'s module docstring now says the spread is measured from the fills and `slippage_vs_mid` is not read | none needed |

- **Fixtures.** The test outcomes' nets were arbitrary numbers. They are now their fills' cash: `builders.outcome` computes it, and a correction is `builders.refilled`, another exit price with the net that follows from it. That is how the new check showed every fixture had been inconsistent.
- **Size limit.** With the new tests, `test_reader.py` passed 350 lines. It is split, unchanged: the shared fakes go to `reading.py`, the correction and net tests to `test_corrections.py`, the damaged-file, mid-range and muhurat tests to `test_damaged.py`. The test names cited for INS-a now live in those files. 88 instructor tests before and after the split.
- **Plants: 3 of 3 caught.**
  - the check removed from `attribute`;
  - the check removed from the reader;
  - the tolerance made strict.
### MS-P1d follow-up Claims, part 4 (branch `story/ms-p1d-practice`, on the law order and a3 9ede0d1e): practice quote rules, design A
Replaces the earlier part 4 (744299d6, never merged), which waived the size laws outright. Built on a3's
`SlotQuote.sizes_measured` and `RefusalReason.SIZE_NOT_MEASURED` (a3 must merge first, then the law order, then this).
| Item (orchestrator, 22 Oct 2026, design A) | Change | Test (and the plant it catches) |
| Only practice rules map an unmeasured size to "no size limit", at the E4 boundary | `execution/quote_rules.py`: `QuoteRules.sizes` passes a measured size as recorded; unmeasured gives `math.inf` (no limit) under practice and `None` live; `desk_view.execution_snapshot(..., rules)` reads sizes through it. No sentinel number | `test_practice_fills.py`: a practice entry on an unmeasured quote fills at the same touch, units and charges as a measured one, and a practice exit closes (plant: practice gives no size; plant: the fill ignores its rules) |
| Live refuses an unmeasured quote at the fill with its own reason | `QuoteRules.size_not_measured` (live, unmeasured, and two-sided by a's rule); `desk_view.size_unmeasured` names those contracts; `entry_gate` names them `size_not_measured` before A4's problem; a fifth quote-gate law; `SchoolFills(..., rules=LIVE)` | the live port refuses the same entry `(size_not_measured,)` and a live exit waits; the live laws refuse it alone; conformance row for the new law (plant: the check dropped) |
| A quote missing a side's price stays one-sided | the reason needs `two_sided`, so a missing bid or ask (or `valid=False`) stays `one_sided_quote` under either rules | missing bid and missing ask on both ports; missing, no-ask and invalid under the practice laws (plant: the two-sided condition dropped) |
| Practice size and sell-back laws pass with the note | `QuoteGateLaw._note`: `size gate not tested in practice` only when a size law passed under practice rules on an unmeasured quote; a measured size is judged as live and carries no note | practice on unmeasured passes with the note on both size laws; measured too small refuses and measured enough passes, under both rules, with no note (plants: note dropped; note on measured sizes) |
| Live cannot reach practice; no sentinel | `PRACTICE` built only in `execution/practice_wiring.py` (`build_practice_fill_port`); `safety/practice_wiring.py` builds the laws with it through `laws_with` | AST test: only `simulator/` and the two practice roots import a `practice_wiring`, only the two safety roots call `laws_with`, `practice=True` only in the execution practice root; the live root's five quote laws are all `LIVE`; no `10**9` or `SIZE_GATE_WAIVED` in `fno/` |
- **Plants:** 6 planted, 6 caught (listed above).
- **Judge 488.6 note 1 (Judge B: PASS), fixed at the root:** `QuoteRules` is keyword-only (`kw_only=True`), so a
  positional `QuoteRules(True)` raises `TypeError` (tested). The isolation scan covers all of `fno/`, not only the
  school, and now also refuses any `QuoteRules(...)` call outside `quote_rules.py` (LIVE) and the practice root, so a
  computed `practice=` cannot slip past the text check. Plants: a module outside the school building
  `QuoteRules(practice=bool(1))`, one importing the practice root, and the positional form allowed: 3 caught.
- **a3 round 2's `check_fill_port_unmeasured` (judge 506) on the real live port** (a3 696f2db7 merged in):
  `test_practice_fills.py::test_the_live_port_passes_a3s_unmeasured_check` on `SchoolFills` with `LIVE`: entry refused
  `(size_not_measured,)`, exit waits. Plant: `LIVE` built with practice rules, caught.
- **a3's `check_ledger_reader` on `SchoolAccounts`** (part 3's promised conformance): `test_entries.py::test_school_accounts_pass_a3s_ledger_reader_check` (plant: entries cut to the first, caught).
- **Outside my files, for f's builder:** `tickets/shared_size.py` reads `ask_qty`/`bid_qty`, which are `None` on an unmeasured quote; under practice it should treat that as no size limit, as the fill port now does.


### MS-P1d follow-up Claims, settlement fixture determinism (branch `story/ms-p1d-settle-determinism`, from main)

Judge K saw `test_settlement.py::test_each_index_settles_at_intrinsic_against_its_own_price[BANKNIFTY]` fail once
under `-n auto`: the fill's `rests_on` and a second build of the fixture file had different SHA-256s.

- **Root cause (reproduced):** the test fixture `settlement_folder` wrote its zip entry with `writestr(<name>, ...)`,
  which stamps the entry with the wall clock (2-second resolution). The test builds the file twice (`tmp_path` and
  `tmp_path / "again"`), so two builds straddling a 2-second boundary differ; xdist load makes that likelier. Built
  2.1 s apart, the old fixture gave 66c22c68... and 9e8454c0...
- **Not production:** no `writestr` in `fno/school`, `fno/desk/settlement.py` or `fno/storage/raw_source.py`; the
  settlement fill reads the archived file's bytes as stored. The same file settled twice, 2.1 s apart, gives an equal
  `FillResult` (`rests_on` d700cfa2...). The other zip fixture (`tests/school/roads/test_listed_contracts.py`, b's)
  has the same pattern but compares no hashes.
- **Fix:** the fixture stamps its entry with the file's own trading day (`ZipInfo`), so the same arguments always give
  the same bytes.
- **Test:** `test_the_settlement_fixture_is_the_same_bytes_at_any_wall_clock_time` builds the file under two clocks
  (zipfile's clock patched, about 3 years apart) and requires one SHA-256. Plant: the old plain-name `writestr`,
  caught.
#### INS-c Claims (round 1, branch `story/ms-ins-causes`, on INS-b; the SHA is in the commit that carries this text)

| Criterion | Met by | Test (`tests/school/instructor/causes/`) |
|---|---|---|
| 1 a plant per cause, each primary | `rules.verdicts`, `classify.causes_of` | `test_rules`: `each_plant_gives_its_cause_as_primary` (13 cases) |
| 2 every threshold at and just beyond | `thresholds.py` | `each_threshold_at_and_just_beyond` (21 cases: 1.645, 2, 3 of 4 and fewer than 3 measurable, 40%, 1.25x, 1x, 1 sd, gross 0, delta 0) |
| 3 winner forms; 6 and 9 never on a winner | `rules._share` and the winner branches | `a_winner_reads_the_winner_forms...`, `a_flat_result_fires_no_component_cause` |
| 4 precedence with four firing; 2-5 by size | `classify.ordered` | `the_precedence_with_four_causes_firing...`, `causes_2_to_5_are_ranked_by_the_size...` |
| 5 unclassified | `causes_of` | `the_neutral_loser_is_unclassified...` |
| 6 a later record names the first | `Classifier.classify(corrects=)` | `test_classify`: `a_later_classification_names_the_one_it_replaces` |
| 7 modifiers and "not testable" | `classify.modifier` | `the_modifiers_from_ref_and_rc1...` (8 cases) |
| 8 card equals code | `INSTRUCTOR_V1.md` thresholds block | `test_card` (block equal to `THRESHOLDS`; each card's stop) |
| 9 empty | `EvidenceBuilder.build` | `test_evidence`: `a_path_without_an_entry_or_snapshots...` |
| terms from real prices | `terms.py`, `market.py`, `evidence.py` | `test_evidence` (z against the ATM volatility, stance of a credit spread, market moves, A6's known-on rule, stop, hold to expiry with settlement, replay, off-touch and impossible-price faults, noise band) |
| wiring | `build_classifier` | `test_wiring` |

**Not testable is counted, never guessed:** a rule returns None when its input is missing, and `Classification.not_testable` lists those causes.

**Two limits, both in the card:**
- cause 13 is not testable in production until MS-P1j can replay a sealed session (`NotYetReplayable`);
- cause 11 holds to expiry.

**Broken-code proof:** 28 plants over two rounds, all caught. They cover every rule's boundary and condition, the order, the size ranking, the modifiers, the not-testable list, the known-on date, the hold value, the off-touch check, the stance, `z`, the cause-10 scope, the market expiry and its clock time, the event and direction shortcuts, the flat result, and the wiring's stops. The size-ranking plant survived the first round; the test `causes_2_to_5_are_ranked...` was added for it.

**Self-review (one independent review agent):** no blocking finding.
1. **Should fix: cause 10 fired whenever the attribution was missing.** Accepted. Cause 10 now reads only path faults and off-market fills; a missing attribution leaves causes 2-5 and 12 not testable.
2. **Should fix: the market move inflated across an expiry.** Accepted. It now uses an expiry alive over the whole window and the clock time between captures.
3. **Should fix: cause 12's basis was unstated.** Accepted. Cause 12 compares the mid-to-mid P&L, now written in the card and the table.
4. **Should fix: cause 13 not testable in production, unstated.** Accepted. It is now stated in the card, with a wiring test and this Claim.
5. **Minor: causes 7 and 2 reported "not testable" when the answer was known.** Accepted. They now answer "no" when there is no event, or the trade is not directional.
6. **Minor: a flat result fired causes 3-5.** Accepted. It now fires none of them.
7. **Minor: the settled path's market window.** Accepted. It is documented in `market.py` and the card.
8. **Minor: duplicated wiring.** Accepted. One `_archive` helper.
9. **Minor: missing edge tests.** Accepted. The edge tests were added.

**Real output sample:** none yet (no sealed day). Fixture: the model-priced put spread closing at F = 980 classifies with cause 11 not testable until its expiry settles, and the modifier `hard_road` when both controls lost (`test_classify`).

#### INS-c Claims, round 2 (judge 510 FAIL round 1: one should-fix, eight branches; one minor)

All in `tests/school/instructor/causes/test_branches.py`. Each test fails when its branch is broken; the judge's
eight plants were re-run, 8 of 8 caught.

| Judge 510 branch | Test |
|---|---|
| 1 cause 2's range edge `|z| <= 1.645` (the boundary named: 1.645 fires, 1.6451 does not) | `cause_2_holds_up_to_and_including_the_range_edge` |
| 2 cause 5's winner form needs "not long premium" | `a_winning_debit_never_reads_time_decay_earned` |
| 3 cause 11's winner form needs a target exit | `a_winner_closed_by_its_stop_is_never_a_whipsaw` |
| 4 the tail order, 9 before 12 | `costs_rank_before_noise_in_the_tail` |
| 5 the directional boundary is inclusive (the boundary named: the 1% dollar delta at exactly the share of the maximum loss, with a binary-exact share so floating point cannot blur it) | `the_directional_boundary_is_inclusive` |
| 6 the lognormal drift -s^2/2 | `the_noise_band_is_centred_by_the_lognormal_drift` (a long ATM call's band mean is about 0) |
| 7 the ATM strike nearest the forward | `the_atm_volatility_is_read_at_the_strike_nearest_the_forward` (a skewed lowest strike is never read) |
| 8 the impossible-price half of cause 10, alone | `an_impossible_price_alone_is_a_data_fault_with_fills_at_the_touch` (the fill is at the impossible touch, so the off-touch half sees nothing) |

### MS-P1j Claims (round 1, branch `story/ms-p1j-fleet`; builder session_01CmKJ6taCLzfEGg7wt6RC4N; the SHA is in the commit carrying this text)
| Requirement | Where | Test (and the plant it catches) |
| One sealed decision per scheduled (road, driver), sealed before any fill; only the card's roads are scheduled | `runner.py`, `decide.py` (`SlotRoads.only`) | `test_the_fleet_conforms` (a's `check_fleet`), `test_a_driver_is_scheduled_only_on_its_card_s_roads` (plant: every road scheduled) |
| A rerun seals nothing twice, asks no driver again, and records nothing twice | `runner.py` `_finish`, `fill.py`, `ledgers.Recorded` | `test_rerun.py`: after the fills, after an exit, after the outcomes' seal, after the counts' write; plants: the rerun branch off, a recorded entry filled again, recorded again, a recorded exit recorded again, drift not sealed, the commit skipped |
| A crash anywhere between the seal and the commit is completed as one clean run would | the same | `test_a_rerun_before_the_close_writes_the_clean_run_s_counts`: identical counts files and ledgers to a clean run, over a shared size |
| The running view: a second road's laws see the first road's accepted trade | `running_view.py`, `decide.py` | `test_the_slot_s_caps_see_the_trades_already_accepted` (plant: an empty running view) |
| The pairing check before `review_exit`: another driver's position, or another road's snapshot, is `unavailable: driver_error`, never an exit | `decide.py` | two tests (plants: each check off) |
| Shared size: entries first (accounts, then tickets), exits from what is left; only what is served is recorded | `fill.py`, `tickets/shared_size.py` (`OwnedFill.is_exit`, ranked last) | `test_two_accounts_on_one_displayed_size_one_entry_is_size_shared_and_stays_counted`, `test_entries_take_the_shared_size_before_exits_and_an_exit_without_size_waits`, `test_a_ticket_the_shared_size_cannot_serve_is_not_opened` (plants: no allocation, an unserved entry recorded, an unserved exit closed, exits ranked with entries, an unserved ticket opened) |
| `is_ticket` on every outcome from the ticket ledger | `outcomes.py` | `test_a_rule_beyond_the_slot_limit_is_a_ticket_in_its_own_ledger_and_its_outcome_says_so` (plant: the flag lost) |
| Settlement before the session's first view | `runner.py`, `settle.py` | `test_an_expired_position_settles_before_the_session_s_view_and_its_outcome_is_sealed` now records the open positions at the view: none (plant: no settlement) |
| `school.enabled` is the only switch, off by default; the CLI builds nothing when it is off | `runner.py`, `cli.py` | `test_off_prints_the_school_off_line_and_writes_nothing`, `test_the_run_command_with_the_switch_off_prints_the_off_line_and_builds_nothing` (plants: each check off) |
| Earlier spots only from the session's own committed canonical captures before it (orchestrator's ruling) | `history.py` | the history tests (plants: the session itself taken, an incomplete capture taken) |
| Quote-refusal share per road; margin causes by name, never a note | `quote_share.py` | `test_parts.py` |
| i's harness on the real wiring | `tests/school/acceptance/real_rig.py`, `test_acceptance_real.py` | skips until d's `SchoolAccounts.entries` is on `main`; see the finding below |
- **Plants:** 21 planted on the fleet, 21 caught. The first set left 4 uncaught: the rerun branch, a rerun filling
  again, the CLI switch, the exit's snapshot check. Each now has its own test, and the "recorded twice" plants are
  checked by counting record calls, because the fakes ignore an equal entry twice and d's store refuses one.
- **Self-review (an independent review agent; the round-2 code is its answer).** Accepted, with the evidence:
  1. a rerun after the fills served the shared size again over the leftovers only, so the entry that lost the size
     on the first run was recorded too (reproduced: 2 entries on 30 units);
  2. a rerun counted the fills recorded before a crash as not executed (reproduced);
  3. a crash after the outcomes' seal lost the drift and the counts for good;
  4. exits were recorded before `allocate` and competed with entries, against MS-P1d limit 2.
  The fix is a design change, not a patch: the finish is rebuilt from the sealed records and the ledgers on every run,
  and `rerun.py` is gone. Also accepted: `ledgers.opening_of` and `SlotFills.unservable` were dead code (both
  removed), and the settlement test did not prove the order (it does now).
- **Not changed, with the reason (for the judges):**
  - an account `view` that raises (a corrupt account) stops the whole session loudly, not sealed as `driver_error`:
    it is not the driver's fault, and a's reasons have no account-fault code;
  - `MidUnknown` or `EntryNotSealed` raised while the outcomes are built stops the outcomes' seal: the ledger and
    the dashcam disagree, which is a stop, not a guess. Every rerun stops the same way until it is fixed.
- **Known limits (reasoning only):**
  1. A crash after a settlement is recorded and before the decisions' seal leaves that settlement without an outcome
     record; the account itself is right. Closing it needs a record time on ledger entries (a's `LedgerEntry`), so it
     is put to the orchestrator.
  2. A rerun after 15:30 prices the entries the size could not serve again, and law 6 makes them `stale_seal`, so
     only their fillable count can differ from a clean run's (what executed never does; tested). A record of the
     fill time would close it.
- **`account_net`'s unservable set:** with the round-2 design no ledger ever holds an unservable fill, so there is
  nothing to pass. Its exclusion stays as a second guard. Put to the judges: "passes `unservable_fills` to
  `account_net`" is met by construction rather than by a call.
- **Finding from the real acceptance run (d's function; put to the orchestrator):** merged with d's entries branch,
  8 of 9 real acceptance tests pass. The "missing quote" fault comes out as `max_loss`, because the quote gates run
  after the laws that read the missing mid (`max_loss` with no value). With the gates moved first, all 9 pass.
- **End-to-end dry run (22 Oct 2026, recorded captures only, replay mode, no Drive write, no commit):**
  - 42 decisions sealed, 16 trades filled;
  - no-trade reasons: 12 not enough history, 3 no expiry in window, 3 no structure under the cap, 3 no valid quotes,
    5 N0;
  - 0 quote refusals;
  - replayed twice: all 45 files byte-identical (round 1).
  Round 2 (e56b5622, merged with d's entries branch) gives the same 42 and 16. Two replays give 69 byte-identical
  files (round 2 also lists the replay's account and ticket files). A rerun into the same folder seals nothing,
  fills nothing and changes no file.
- **Gates:** `pytest -n auto` 11795 passed; `ruff check`, `ruff format --check`, `check_imports`, `check_records`
  clean.
### MS-P1j Claims, round 3 (the orchestrator's rulings of 22 Oct 2026 on round 2, and Judge I's note; main merged in)
| Ruling | Change | Test (and the plant it catches) |
| b: a settlement never lacks its outcome | a's `LedgerEntry.recorded_for` (a session date, not a clock time, so replays stay byte-identical; set on every fleet entry and on the ticket book's). `settle.settle_expired` settles, then rebuilds the session's exit records from the ledgers: every expiry closing recorded for this session, this run's and a crashed run's alike | `test_a_crash_between_a_settlement_and_the_seal_still_seals_its_exit_and_outcome_on_the_rerun`, `test_a_settlement_recorded_for_an_earlier_session_is_never_sealed_again`, `test_an_expired_ticket_settles_in_its_own_ledger_and_its_outcome_is_sealed_as_a_ticket` (plants: no rebuild, every session's settlements, an account or a ticket settlement without its session) |
| b: the accepted limit is marked | a rerun whose finish runs after 15:30 adds "rerun after 15:30, fillable may differ" to the session's marks file (`<counts>.marks.txt`, committed with the counts); g's `DayInputs.marks` and the evening section show it under the banner | `test_a_rerun_after_15_30_is_marked_and_the_evening_section_shows_the_mark`, `test_a_rerun_of_a_complete_session_after_15_30_adds_no_mark` (plants: never marked, always marked, the evening hiding marks) |
| c: no ledger holds an unservable fill | (by construction, round 2) | `test_no_ledger_ever_holds_more_than_the_displayed_size_could_serve`: three accounts and their tickets on 60 units, then exits beside entries; every session's recorded units fit |
| d: a ticket never blocks a real entry; a road is never ticketed twice | the card decides on the account's own positions; on a road with an open ticket, a ticket is asked again with real plus tickets, and a "no" (the card's own holding rule) is the record | `test_a_held_ticket_never_blocks_a_real_entry_on_its_road`, `test_the_same_road_is_never_ticketed_twice` (plants: real decisions seeing tickets; no second ask) |
| e: a loud stop, never silent | every account and ticket-ledger read and record goes through `books.account_call`; a failure stops the run with "stopped: account unreadable <driver> (<error class>)", nothing sealed; `school run` exits 1, so the daily run's step alerts #fno-desk through its existing path and the run log keeps the line | `test_an_unreadable_account_stops_the_session_by_name_and_seals_nothing`, `test_the_run_command_exits_1_on_a_stop_so_the_daily_run_alerts` (plants: the view unguarded, exit 0 on a stop) |
| f: PreviousSlotToday | labelled on the banner, the road line and every plan line: "plan from <date> 15:00 data, indicative prices, not today's quotes" (g's `TodayInputs.source`; **touches g's today.py and inputs.py**) | `test_every_08_50_line_names_its_source_and_the_plan_writes_no_record`: dashcam, accounts, tickets and counts files hash-identical after the plan (plant: lines unlabelled) |
| f: g's sections connected, the inputs passed in | the lab's reserved line passes `inputs=school_report_inputs` (`fno/school/report_entry.py`, which imports nothing at load); g's guard and wiring call it inside the guard only with `school.reports` on. **Touches g's guard.py and wiring.py (one parameter) and the lab's page_wiring.py reserved line.** g's reports never import the fleet | `test_both_sections_render_from_the_real_inputs_passed_in_by_the_caller` (no alert); `test_the_real_report_maker_is_built_through_the_school_guard` checks the lab passes them (plants: the inputs ignored, the lab passing none) |
| f: i's harness reads card.roads | **touches i's `Scenario.scheduled`** and a's `FakeFleet`: only each card's own roads; real_rig's ALL_ROADS workaround is gone. The recorded day's cards now name the five roads their docstring says they drive; the planted refused entry, whose card names one road, gets one row | `test_a_card_limited_to_one_road_is_scheduled_only_there_by_the_harness_and_the_fleet`, the fleet's `test_a_driver_is_scheduled_only_on_its_card_s_roads` (plants: the scenario or the fake fleet ignoring card.roads) |
| Judge I: every reason a decision carried | `quote_share.reason_counts` and the line "refusal reasons, a decision can have several" per road; the three counts keep the one named refusal | `test_quote_share.py` (plant: the named reason only). Round 2's Claims said `test_parts.py` covered the quote share: that was wrong, no test did; this file adds them |
- **Real acceptance on the real wiring, main merged (d's law order and `SchoolAccounts.entries`):** 9 of 9 pass.
- **Dry run of 22 Oct on round 3 (replay, recorded captures only):**
  - 42 decisions sealed, 16 fills, 0 quote refusals;
  - two replays give 69 byte-identical files;
  - a rerun into the same folder seals and fills nothing and changes no file.
- **Gates:** `pytest -n auto` 12087 passed; ruff, format, `check_imports` and `check_records` clean.
- **Plants (round 3):** 17 planted, 17 caught (the first run missed the ticket settlement; its test was added).
- **Not changed, with the reason:** a missing entry mid while the outcomes are built still stops them; a ledger and dashcam that disagree are a stop, not a guess.
### MS-P1j Claims, round 4 (Judge B's notes, judge 507; Judge I's judge 506 on the live fleet; a3 696f2db7 merged in)
| Note | Change | Test (and the plant it catches) |
| Judge 506: a live run never trades on an unmeasured quote | `slot.plan_slot` closes a road whose snapshot holds any quote with `sizes_measured` False, as `road_closed: sizes_not_measured` (a's new `ClosureReason`), before the quality gate and before any driver sees it | `test_a_live_road_whose_capture_holds_an_unmeasured_quote_closes_by_name_and_never_trades` (plant: the guard off) |
| Judge 507 note 2: a slow first SPAN read must never be a driver's deadline | Not a warm-up: the root cause is that the limit timed the fleet's own laws. `DriverStep` now isolates and times only the driver's code: its decisions (with the hypothetical ticket asks), then its exit reviews, each with the limit. The laws run between them untimed. A law that raises is now the fleet's own loud error, never a false `driver_error`. A failed SPAN read already refuses each entry by name (`margin_room`, "margin not checked: <cause>") while exits go on, so closing the road would only block exits | `test_a_slow_law_never_counts_against_the_driver_s_time_limit` (plant: round 3's `decide.py`, laws inside the limit), `test_a_driver_s_exit_reviews_have_their_own_time_limit` |
| Judge 507 note 1: the commit-only branch | killed by round 3's `test_a_rerun_of_a_complete_session_after_15_30_adds_no_mark` (plant: the whole fast path removed, which fails it) | as named |
| Judge 507 note 2 / the orchestrator: `allocate` reads sizes through d's `QuoteRules` | **waits for d's part 4** (`QuoteRules` is on `story/ms-p1d-practice`, not on `main`). Until then `allocate` reads a missing size as 0: no size, no fill, which is right for the live fleet; and the live fleet now never sees an unmeasured quote (above) | built after d's part 4 merges |
- **Evidence (round 4):**
  - real acceptance on the real wiring: 9 of 9;
  - 22 Oct dry run: 42 decisions and 16 fills; two replays give 69 byte-identical files;
  - plants: 3 planted (the guard off, the laws inside the limit, the fast path removed), 3 caught;
  - `pytest -n auto` 12097 passed; ruff, format and `check_imports` clean.
### MS-P1j Claims, round 5 (d's part 4 on main: sizes through `QuoteRules`)
| Item (Judge B 507 note 2; orchestrator, 22 Oct 2026) | Change | Test (and the plant it catches) |
| `allocate` and f's shared size read sizes through d's one rule | `tickets/shared_size.allocate(..., rules=LIVE)` reads each displayed size with `QuoteRules.sizes`: live, an unmeasured or missing size serves nothing (no fill, no ticket; never unlimited, never a crash); practice, an unmeasured size has no limit. The fleet passes `LIVE` by name; only a practice root may pass practice rules | `test_under_live_rules_an_unmeasured_size_serves_no_fill_and_no_ticket`, `test_under_practice_rules_an_unmeasured_size_has_no_limit`, `test_a_measured_size_is_the_same_limit_under_either_rules` (plants: the old direct read, a missing size read as unlimited, practice as the default) |
| Round 2's ranking of exits after entries had no unit test of its own | — | `test_an_exit_is_served_only_from_what_the_entries_leave` |
### MS-P1j Claims, round 6 (Judge K, judge 512 FAIL round 1: two should-fixes and a minor)
| Finding | Change | Test (and the plant it catches) |
| Should-fix 1: `build_fleet` was never tested; a replay sealing into Drive passed every test | By construction, not by a mode switch (orchestrator): the one root became three. `fleet_wiring.fleet_on(cfg, FleetStores)` wires what both share and builds no store that writes; `wiring.build_fleet(cfg)` is the record root and the only one that builds the Drive dashcam, the account sync and the committer; `replay_wiring.build_replay_fleet(cfg, session, folder)` hands in scratch stores under its folder and imports none of the real ones. The CLI picks the root; `RunMode` no longer reaches the builder | `tests/school/fleet/test_wiring.py`: the replay root and the shared builder import none of the three builders, nor the record root; a replay built while all three refuse to exist (patched where they are defined and in the record root) still builds, with every store (dashcam, accounts, tickets, counts) under its folder, no committer, no sync and the fixed clock; the record root builds all three (plants: the replay root sealing on Drive, syncing accounts, committing, or going through the record root) |
| Should-fix 2: six guards survived deletion | — | `tests/school/fleet/test_guards.py`, one each: a decision naming another road is the driver's error (plant: `_check_identity` removed); the opportunity file is write-once (plant: the check removed); drift rows only for served entries (plant: every entry); a ticket entry takes size before an account's exit, in either given order (plant: the two flags swapped); the quote share counts a quote refusal that the named reason (a stop) hides (plant: the share from the named reason); a position is not settled on its own expiry day, even with its price known (plant: `<` to `<=`) |
| Minor: four survivors are equivalent or replay-only | — | Equivalent today (reasoning only, not tested): (1) all of a driver's positions passed to `decide` (every driver's card filters by road and holding itself); (2) the 08:50 plan's rule-only filter (g's section filters by role again); (3) a missing mid read as 0.0 (no path reaches it: a refused leg has no fill, and an outcome needs its entry's sealed mids, else it stops). Replay-only: (4) the replay store's conflict check, which never runs in the record (c's dashcam has its own, judged in MS-P1c) |
- **Plants (round 6):** 10 planted (Judge K's six, plus four on the replay root), 10 caught.
- **The 22 Oct replay through the new root** gives the same 69 files, byte for byte, as round 5's.

### MS-P1g follow-up: the instructor's why lines, and two items folded in (branch `story/ms-p1g-why-lines`, lane 1)

- **Why lines** (asked by the MS-P1j builder; agreed with the MS-INS builder): `DayInputs.why(session)` returns MS-INS
  part e's lines for the session's closed trades, or `()` without a source. The 20:05 section shows them verbatim under
  the header "Why (the instructor's words):", right after the counts and before the fleet total; none, no header. A line
  is kept only when its leading token (the driver id) is a rule driver (`role_of`); controls and measurement-only
  drivers keep their own labelled lines (orchestrator's decision on judge 484). The section does not scan the text for
  strikes or prices: the source's contract is that a line holds a driver id, a road, the net and cause words only.
  Tests (`test_sections.py`): verbatim and in place, no lines no header, a control's or measurement-only line left out,
  only controls leave no header. Plants: the role filter off, the empty-case header, the section call removed (all
  caught).
- **Merge order:** main's `SealedDayInputs` (j's file) gets a `why` returning `()` here (three lines), so the two
  j tests that render the evening with the real inputs stay green; the MS-P1j builder's `story/ms-p1j-ins-wiring` has the
  real `why` at the same place, so merging main into it takes theirs.
- **Runbook step for MS-P1j** (orchestrator, judge 495): written into MS-P1j's "Implements" list: a new comparison-card
  version needs new D6 rows (one per driver version) registered before its decisions count; until then every decision is
  `comparison_card_mismatch`.
- **Empty hash pinned** (orchestrator, judge 495): `test_a_card_deleted_after_the_rows_hashes_to_nothing_and_no_decision_counts_under_it`:
  a commit with no card gives `""` (never the hash of nothing), and a decision under a deleted card is
  `comparison_card_mismatch`; the plant (hashing an empty text) is caught.
- **Tickets in the why lines (orchestrator's call, 23 Oct 2026):** part e will write a ticket's line with no rupees
  ("ticket (hypothetical, account limits relaxed)" plus cause words). The section shows ticket lines, and keeps a guard:
  a ticket line (`<driver> <road> ticket ...`) that holds a rupee figure (`Rs 90`, a rupee sign, "rupees") is refused,
  because a ticket is never shown in rupees (judge 481). Tests: a ticket line without a figure is shown, five forms with
  a figure are refused, a trade's line keeps its rupees; plants: the figure check removed, the guard off (both caught).
  `test_the_pinned_format_is_what_the_instructors_why_line_writes` pins the leading `{driver} {road}{ticket}: net Rs `
  form against `why_line.LINE` and skips until part e is on main; it is to be updated to part e's new ticket form when it
  lands (the INS builder tells the g builder).

MS-P1g why lines, round 2 (judge 517 PASS with minors; orchestrator, 23 Oct 2026; each accepted):
1. **The stub is deleted** (`SealedDayInputs.why` in `fno/school/fleet/report_inputs.py`): a merge with j's ins-wiring would
   have left two `def why` and let the stub replace j's. This branch merges after j's ins-wiring; until then the two j
   tests that render the evening with the real inputs fail here (they need `why`), by design.
2. **An unknown driver is withheld and counted, never raised:** a line whose first word is not a known driver id gives
   "N why line(s) withheld: unknown driver"; the rest of the section stays.
3. **A line with a strike or a price is withheld and counted** ("N why line(s) withheld: strike or price"): a strike
   with its type, the words strike or premium, a price given as a number, "at <number>". Part e's own words ("bad
   price or data", "net Rs -1,400") are kept. Tests plant each form.
4. **Runbook:** `starts_on` strictly later than the book's previous row (above); the by-name sentence is re-attributed
   to the orchestrator (23 Oct) and the j builder builds it. Plants: the unknown-driver catch, the leak check and the
   notes are each removed (all caught).


### MS-P1j seams for the simulator (SIM builder's request; orchestrator, 23 Oct 2026: lane 1, Judge B, then Judge I for the third seam, which touches the live gate; branch `story/ms-p1j-sim-seams`)
| Seam | Change | Test (and the plant it catches) |
|---|---|---|
| One construction of the books | `fleet_wiring.books_on(cfg, stores, fills)`: the driver accounts and the ticket ledger under `stores.home`, filled through the given port; `fleet_on` calls it with the pilot's fill port, and the practice root will call it with its own | `test_books_on_builds_the_accounts_and_tickets_under_the_home_with_the_given_fill_port`, `test_fleet_on_builds_its_books_through_books_on` (plants: books_on ignoring its port; fleet_on building its own) |
| The replay dashcam's encoding is overridable | `ReplayDashcam.encode` and `decode` (defaults `encode_slot_file` and `decode_slot_file`); `seal` and `read` go through them; the write-once and seal logic is not copied | a labelled subclass writes `"label": "practice (simulator)"` on every line, the pilot's `decode_slot_file` and a plain `ReplayDashcam` read the same records, write-once still holds; `read` uses a subclass's `decode` (plants: seal or read bypassing them) |

| The live gate's quote rules are the fleet's own (orchestrator, 23 Oct 2026, 01:50 UTC) | `SchoolFleet.rules: QuoteRules = LIVE`, passed into `plan_slot`: under the live rules (every pilot root) a road whose capture holds an unmeasured quote still closes as `sizes_not_measured` (judge 506); only `QuoteRules(practice=True)`, which the simulator's practice root passes (`execution/practice_wiring.PRACTICE`), lets it through for MS-P1d's practice laws. d's isolation test already refuses practice rules outside the practice roots | `test_only_the_practice_rules_open_a_road_whose_capture_holds_unmeasured_quotes`; the live test unchanged (plants: the guard ignoring the rules, the guard always skipped, the runner not passing its rules, practice by default) |

| The fleet's rules reach the shared size (the SIM builder's finding, 23 Oct 2026) | `FillStep.rules` (no default) is the fleet's own `rules`, passed to `allocate`: under the practice rules an entry on unmeasured sizes was judged by the live rules and became `size_shared` (executed 0 while the fills happened). No other fleet code names the rules (the fill port and the ticket book use their own port's) | `test_under_the_practice_rules_an_entry_on_unmeasured_sizes_is_executed_not_size_shared` (plants: the step on the live rules; the runner passing the live rules) |
| The fleet has no switch (orchestrator, 23 Oct 2026) | `school.enabled` moves out of `SchoolFleet.run()`: the pilot's record root returns `SwitchedOff` (the school-off line, nothing built) when it is off; the CLI no longer forces the switch on a copy of the config for a replay, whose root has none. The simulator's practice command runs the same fleet without a switch. No other reader of `settings.enabled` in `fleet/` | `test_the_pilot_s_record_root_with_the_switch_off_prints_the_off_line_and_builds_nothing` (a's `check_fleet_off`), `test_the_fleet_itself_has_no_switch_and_runs`, `test_the_run_command_with_the_switch_off_prints_the_off_line_and_builds_nothing`, `test_a_replay_runs_with_the_pilot_s_switch_off_and_on_the_config_as_given` (plants: the fleet keeping the switch, the record root ignoring it, the replay forcing it on) |

- **The pilot is unchanged:** the 22 Oct replay is byte-identical to round 5's (69 files).
- **Plants:** 13 planted (4 on the first two seams, 4 on the rules at the gate, 5 on the fill rules and the switch), 13 caught.


#### INS-d Claims (round 1, branch `story/ms-ins-paired`, on INS-c; the SHA is in the commit that carries this text)

**What the owner should read first [some evidence: simulations run through the real comparison code; the markets are
assumed, not measured].** In v1 no driver can read Watching (ruling D). The 30-session P2 review will show every
driver as Exploratory or Not established, with the mean and the bound as descriptive numbers. The edges below would
take this long to show a positive bound (hold 10, batch 15, 500 seeds; the share of runs with a bound above 0):
| Edge per trade (return on risk) | 30 sessions | 60 | 120 | 250 | 500 |
|---|---|---|---|---|---|
| +1.0 | 61% | 100% | 100% | 100% | 100% |
| +0.3 (Rs 3,000 per Rs 10,000 maximum loss) | 22% | 51% | 85% | 98% | 100% |
| +0.1 | 11% | 17% | 27% | 42% | 66% |
| +0.03 (325's "+Rs 300 a trade") | 7% | 10% | 13% | 13% | 18% |
- **+Rs 300 a trade needs many years.** +0.1 needs more than 500 sessions.
- **No bound before N sessions** (from the cards: 2 batches of 1.5 x the pair's longer hold, at least 10 sessions):
  - against N0: WS1 20; CS1, DB1 and DR1 30; PS2-4 and RC1 46; PS5 54; REF 78; KL1 100;
  - against RC1 (hold 15): 46, PS5 54, KL1 100;
  - against REF (hold 26): 78, KL1 100.
  - The review prints these in those words.
**Why no Watching in v1: the skewed-seller null [some evidence], measured with the shipped code (round 2).**
- **The fake driver** (`nulls.seller_slots`) is a credit seller at zero edge:
  - 5 roads, one open trade per road, held for the card's hold;
  - the full maximum loss with probability p, else a small win;
  - 60% of a session shock shared across roads.
- **The grid:**
  - share of runs with a bound above 0, 2,000 seeds per cell;
  - batch 1.5 x the hold, at least 10;
  - every hold the cards hold, p 0.05 to 0.2;
  - at the first session count with a bound (2 batches), at twice that, at 120 and at 250 sessions;
  - the upper end of the 95% Wilson interval in brackets.
| Hold (batch) | p 0.05 | p 0.1 | p 0.15 | p 0.2 |
|---|---|---|---|---|
| 3 (10), 20-250 sessions | 11.9-31.4% (33.5%) | 9.2-16.0% (17.6%) | 8.4-11.0% (12.4%) | 7.6-9.2% (10.5%) |
| 10 (15), 30-250 | 18.5-36.3% (38.4%) | 13.1-22.6% (24.5%) | 10.8-16.0% (17.6%) | 9.6-14.1% (15.7%) |
| 15 (23), 46-250 | 19.2-40.4% (42.6%) | 16.2-25.3% (27.3%) | 13.2-18.4% (20.1%) | 10.5-14.6% (16.2%) |
| 18 (27), 54-250 | 25.1-37.1% (39.3%) | 15.6-21.6% (23.4%) | 12.8-17.0% (18.7%) | 7.7-15.0% (16.6%) |
| 26 (39), 78-250 | 19.2-43.4% (45.6%) | 16.0-22.1% (24.0%) | 14.3-17.5% (19.3%) | 9.4-16.8% (18.5%) |
| 33 (50), 100-250 | 25.3-37.8% (39.9%) | 17.2-23.8% (25.7%) | 13.7-17.0% (18.7%) | 9.4-14.2% (15.9%) |
- **The worst case** is 43.4% (upper end 45.6%): p 0.05, hold 26, 120 sessions. Seller rows print "up to 46%", and add
  that rarer full losses can be worse. A test pins that cell at or under 46% and above 40%.
- **Correction of round 1:** the first table here came from a separate 4-road script, not the shipped 5-road code. Its
  hold-10, p-0.1, 30-session cell (14.9%) is 22.6% (24.5%) with the shipped code, as Judge K found (judge 516).
- **What does not fix it** (round 1, 4-road script): batches of 20 or 30, a 97.5% t and a 99% t.
- **The cause is the skew, not the sparseness:** a symmetric ±1 payoff gives 4-5%, a positive skew 2%.
**The Gaussian null, Gaussian only (2,000 seeds a cell; upper end in brackets).** It passes at the batch rule. It does
not cover skewed payoffs.
| Hold, batch | 30 sessions | 60 | 120 |
|---|---|---|---|
| 3, 10 | 5.4% (6.5%) | 5.6% (6.7%) | 5.9% (7.1%) |
| 5, 10 | 6.5% (7.7%) | 6.4% (7.6%) | 6.7% (7.8%) |
| 10, 15 | 7.2% (8.5%) | 6.8% (8.0%) | 7.5% (8.7%) |
| 15, 23 | no bound | 6.5% (7.7%) | 7.6% (8.9%) |
| 18, 27 | no bound | 5.9% (7.0%) | 7.7% (9.0%) |
| 25, 38 | no bound | no bound | 7.0% (8.3%) |
| 33, 50 | no bound | no bound | 6.1% (7.2%) |
- **Sensitivity:** shared shock 0.3 or 0.9, or return spread 1.0, stays at or under 9.0% (upper end).
- **Batch = hold** fails: 10.3-11.0% at 120 sessions. A test pins hold 15.
- **The first method** (S2's bootstrap, 5-session blocks): 27%.
- **Live test:** `test_nulls` re-checks the Gaussian gate at every hold the cards hold, read at test time (today 3,
  10, 15, 18, 26 and 33), so a v2 card re-runs it.
| Criterion | Met by | Test (`tests/school/instructor/paired/`) |
|---|---|---|
| 1 hand-computed pairs | `series.paired_series` | `test_series`: `the_hand_computed_pairs...` (both measures) |
| 2 one point per session | `paired_series` | `five_roads_on_one_session_are_one_point` |
| 3 abstention 0 and counted | `series.value` | the hand test |
| 4 the cut | `paired_series` | `the_series_stops_at_the_first_open_pair...`, `an_open_ticket_cuts_the_per_opportunity_series_but_not_the_executed_only_one` |
| 5 the v1 ladder; never Watching | `status.status` | `test_status`: `the_v1_ladder...`, `v1_never_assigns_watching...`, `no_v1_module_assigns_watching`, `a_row_says_in_words...` |
| 6 three statuses in the type | a's `MapStatus` | `test_types` |
| 7 null calibration | `nulls.py` | `test_nulls` (the Gaussian gate at the cards' holds, the skewed seller, the rejected rule) |
| 8 planted edge | `nulls.share_watching` | `a_planted_edge_of_one_shows_a_positive_bound`; the power table |
| 9 empty | `compare` (no common day, no row) | `test_compare`, `test_series`: `only_the_common_road_days...` |
| bound | `status.batch_bound` | `the_hand_computed_bound_on_three_batches` |
| holds and batch | `holds.py`, `shapes.py` | `each_cards_frozen_hold`, `a_pairs_batch...`, `rc1_holds_as_long_as_its_longest_rule_twin...` |
| robustness | `values.py`, `series.py`, `compare.py` | `a_road_day_missing_from_a_map_is_unavailable...`, `a_non_finite_return_is_refused`, `a_driver_with_no_slots_yet...` |
**Self-review (one independent agent).** One blocking finding, the skewed null, led to ruling D above. The other
findings were all fixed:
- no row for a pair without common days, and a missing driver handled;
- a missing slot is unavailable, never a crash;
- non-finite returns refused;
- an open ticket does not cut the executed-only series;
- RC1's hold from its rule twins (15);
- the monthly cycle is 36 days, so REF's hold is 26;
- unavailable slots after the cut are documented as counted in `unavailable`.
**Contracts:** `PairedRow` holds a one-sided `bound`, the `batch` and a `note`. S2's files are untouched.
**Broken-code proof:** 14 plants before the ruling, all caught. The ruling's own pieces are pinned by the tests above:
the ladder, no Watching anywhere, the notes and the seller flag.
#### INS-d Claims, round 2 (judge 516 FAIL round 1: two should-fixes, one minor)
| Finding | Fix | Test |
| SF1: the printed "up to 21%" was false | The cause: the round-1 table came from a separate 4-road script, never re-run with the shipped 5-road `seller_slots`. The full grid is now measured with the shipped code: every hold the cards hold, loss chances 0.05-0.2, at 2 batches, at twice that, at 120 and at 250 sessions, 2,000 seeds a cell (the table in "INS-d Claims (round 1)", rewritten). The true worst case is 43.4% (upper end 45.6%). `SELLER_FALSE_POSITIVE_PCT` is now 46 (code, card and test agree), and seller rows add "(rarer full losses can be worse)" | `test_nulls`: `the_skewed_seller_null_fails_the_gate_and_its_worst_case_is...` (the worst cell pinned above 40% and at or under 46%); `the_round_1_table_cell_measured_with_the_shipped_code` (your 22.6%) |
| SF2: the card said REF 25, the story said 35 days and REF/RC1 25 | The card: holds 3, 10, 15, 18, 26 and 33. The story: the 36-day cycle, RC1 15 from its twins, REF 26 | none needed (the holds are tested from the cards: `each_cards_frozen_hold`) |
| Minor: a pair present with an empty common set | none needed | `test_compare`: `a_pair_present_with_an_empty_common_set_gives_no_row` |
**What the owner should know [some evidence: a simulation].** For a credit seller that rarely loses its full maximum
loss (a 5% chance), this descriptive bound looks positive about 2 runs in 5 even with no edge. Rows print that rate.
The rarer the loss, the more misleading a short sample looks. That is the peso problem, and it is why v1 has no
Watching.

| Every account the fleet records into is opened first (the SIM builder's finding, orchestrator's ruling, 23 Oct 2026) | The fleet viewed only the driver accounts, so the first ticket ever recorded for a driver stopped the run ("account unreadable ...: a fill before the account's first view"; hidden until the fill rules fix let entries be recorded). `Books.stores` names every store the fleet records into (the driver account and the ticket ledger), and one step, `SchoolFleet._open`, views each before any fill; no separate path for tickets. a's contract now says it (`AccountPort.record`: an account no view opened refuses), a's `FakeAccounts` enforces it as d's store does, and a's `check_account_port` checks it | `tests/school/fleet/test_first_ticket.py` on d's real `SchoolAccounts` and `SchoolFills`: a driver's first-ever ticket on a fresh ledger records and the session completes; session after session the ledgers stay open and record; the fleet's ticket tests now fail on a fake that refuses as the real store does; `test_a_ticket_ledger_no_view_opened_refuses_the_ticket_as_the_real_store_does` (plants: tickets not viewed, caught by both the fakes and the real stores alone; `stores` without the ticket ledger) |

- **The pilot's records are unchanged:** in the 22 Oct replay every sealed record, count and driver account file is
  byte-identical to round 5's; the new files are each driver's ticket ledger, now opened by the session's view. Two
  replays are identical.
- **Plants:** 16 planted (4 on the first two seams, 4 on the rules at the gate, 5 on the fill rules and the switch, 3 on the ticket ledgers), 16 caught.

### MS-P1a4 Per-expiry lots · lane 1 (the lot decides size, cost and margin; Judges B then I) · builder: MS-P1a's owner (session_01CmKJ6taCLzfEGg7wt6RC4N), branch `story/ms-p1a4-lots`
Why (the SIM builder, Judge H on the archive): NSE changes a lot from a given expiry, so for a while an index's two
monthlies carry different lots (BANKNIFTY-M, 2 Jun 2025). One lot per road day loses the road for that stretch.
| Item (orchestrator, 22 Oct 2026) | Change | Test (and the plant it catches) |
| `RoadDay.lots` and `lot_for(expiry)`, built like `strike_steps` and `step_for` | `lots: Mapping[date, DatedLot]` (hash=False): when given, it names every recorded expiry, each above zero, and the nearest's is `lot`. `lot_for` gives that expiry's own lot, never another's. Without `lots`, every recorded expiry carries `lot`, which is exactly what a catalogue that closes a road on mixed lots states (every catalogue today); an expiry the road did not record has none | `tests/school/contracts/test_road_lots.py` (plants: borrowing the nearest lot, the checks removed, an unrecorded expiry given the lot, lots in the hash) |
| e's two reads (drivers/proposals.py) | `road_day.lot_for(plan.expiry).units` for both the units and C2's candidate builder | `test_a_proposal_on_the_later_expiry_is_sized_with_that_expiry_s_own_lot`: REF on the later expiry proposes with that expiry's doubled lot (plant: the nearest's lot) |
| b's catalogue fills one lot per expiry | **Not needed, so not changed:** without `lots`, `lot_for` already gives every recorded expiry the catalogue's one lot, which b guarantees by closing a road on mixed lots. Changing b would add a line that says nothing new | a's conformance check now asks every open road for every recorded expiry's lot, and the nearest's is `lot`; b's real catalogue passes it unchanged |
| The live catalogue keeps closing a road on mixed lots | unchanged | — |
- **Plants:** 6 planted, 6 caught.
- **Later, not in a4:** lifting the live closure needs a test on the 2 Jun 2025 archive showing BANKNIFTY-M's near
  and far monthlies each proposing with their own lot, units, fill costs and margin (orchestrator).
### MS-P1j seams for the simulator (SIM builder's request; orchestrator, 23 Oct 2026: lane 1, Judge B, then Judge I for the third seam, which touches the live gate; branch `story/ms-p1j-sim-seams`)
| Seam | Change | Test (and the plant it catches) |
| One construction of the books | `fleet_wiring.books_on(cfg, stores, fills)`: the driver accounts and the ticket ledger under `stores.home`, filled through the given port; `fleet_on` calls it with the pilot's fill port, and the practice root will call it with its own | `test_books_on_builds_the_accounts_and_tickets_under_the_home_with_the_given_fill_port`, `test_fleet_on_builds_its_books_through_books_on` (plants: books_on ignoring its port; fleet_on building its own) |
| The replay dashcam's encoding is overridable | `ReplayDashcam.encode` and `decode` (defaults `encode_slot_file` and `decode_slot_file`); `seal` and `read` go through them; the write-once and seal logic is not copied | a labelled subclass writes `"label": "practice (simulator)"` on every line, the pilot's `decode_slot_file` and a plain `ReplayDashcam` read the same records, write-once still holds; `read` uses a subclass's `decode` (plants: seal or read bypassing them) |
| The live gate's quote rules are the fleet's own (orchestrator, 23 Oct 2026, 01:50 UTC) | `SchoolFleet.rules: QuoteRules = LIVE`, passed into `plan_slot`: under the live rules (every pilot root) a road whose capture holds an unmeasured quote still closes as `sizes_not_measured` (judge 506); only `QuoteRules(practice=True)`, which the simulator's practice root passes (`execution/practice_wiring.PRACTICE`), lets it through for MS-P1d's practice laws. d's isolation test already refuses practice rules outside the practice roots | `test_only_the_practice_rules_open_a_road_whose_capture_holds_unmeasured_quotes`; the live test unchanged (plants: the guard ignoring the rules, the guard always skipped, the runner not passing its rules, practice by default) |
- **The pilot is unchanged:** the 22 Oct replay is byte-identical to round 5's (69 files); full suite 13800 passed.
- **Plants:** 8 planted (4 on the first two seams, 4 on the rules), 8 caught.

**Round 2, addendum (the orchestrator's conditions on judge 516, sent before the round-2 push):**
- **Reproducible seeded runs:** `tools/ins_seller_null.py` runs the seller grid (`nulls.seller_cells` and
  `seller_cell`, fixed seeds 0-1999) through the shipped code and writes `research/school/instructor_seller_null.csv`.
  Its rerun reproduced every one of the 96 cells exactly.
- **The printed rate comes from those runs:**
  - `test_the_printed_seller_rate_is_the_committed_grids_worst_upper_end_and_the_grid_covers_the_cards` checks that
    the grid's cells are the cards' holds today and that the printed 46 is the worst upper end rounded up;
  - `test_the_grids_worst_cell_recomputes_from_the_same_seeded_runs` re-runs the worst cell and matches the file to 4
    decimals.
- **Why 14.9% did not reproduce:** it came from a separate 4-road script. The shipped `seller_slots` drives all 5 roads
  and gives 22.6%.

| The fleet's rules reach the shared size (the SIM builder's finding, 23 Oct 2026) | `FillStep.rules` (no default) is the fleet's own `rules`, passed to `allocate`: under the practice rules an entry on unmeasured sizes was judged by the live rules and became `size_shared` (executed 0 while the fills happened). No other fleet code names the rules (the fill port and the ticket book use their own port's) | `test_under_the_practice_rules_an_entry_on_unmeasured_sizes_is_executed_not_size_shared` (plants: the step on the live rules; the runner passing the live rules) |
| The fleet has no switch (orchestrator, 23 Oct 2026) | `school.enabled` moves out of `SchoolFleet.run()`: the pilot's record root returns `SwitchedOff` (the school-off line, nothing built) when it is off; the CLI no longer forces the switch on a copy of the config for a replay, whose root has none. The simulator's practice command runs the same fleet without a switch. No other reader of `settings.enabled` in `fleet/` | `test_the_pilot_s_record_root_with_the_switch_off_prints_the_off_line_and_builds_nothing` (a's `check_fleet_off`), `test_the_fleet_itself_has_no_switch_and_runs`, `test_the_run_command_with_the_switch_off_prints_the_off_line_and_builds_nothing`, `test_a_replay_runs_with_the_pilot_s_switch_off_and_on_the_config_as_given` (plants: the fleet keeping the switch, the record root ignoring it, the replay forcing it on) |
- **The pilot is unchanged:** the 22 Oct replay is byte-identical to round 5's (69 files).
| Every account the fleet records into is opened first (the SIM builder's finding, orchestrator's ruling, 23 Oct 2026) | The fleet viewed only the driver accounts, so the first ticket ever recorded for a driver stopped the run ("account unreadable ...: a fill before the account's first view"; hidden until the fill rules fix let entries be recorded). `Books.stores` names every store the fleet records into (the driver account and the ticket ledger), and one step, `SchoolFleet._open`, views each before any fill; no separate path for tickets. a's contract now says it (`AccountPort.record`: an account no view opened refuses), a's `FakeAccounts` enforces it as d's store does, and a's `check_account_port` checks it | `tests/school/fleet/test_first_ticket.py` on d's real `SchoolAccounts` and `SchoolFills`: a driver's first-ever ticket on a fresh ledger records and the session completes; session after session the ledgers stay open and record; the fleet's ticket tests now fail on a fake that refuses as the real store does; `test_a_ticket_ledger_no_view_opened_refuses_the_ticket_as_the_real_store_does` (plants: tickets not viewed, caught by both the fakes and the real stores alone; `stores` without the ticket ledger) |
- **The pilot's records are unchanged:** in the 22 Oct replay every sealed record, count and driver account file is
  byte-identical to round 5's; the new files are each driver's ticket ledger, now opened by the session's view. Two
  replays are identical.
- **Plants:** 16 planted (4 on the first two seams, 4 on the rules at the gate, 5 on the fill rules and the switch, 3 on the ticket ledgers), 16 caught.


### MS-P1j follow-up: a comparison card mismatch is loud (orchestrator's ruling, 23 Oct 2026; branch `story/ms-p1j-card-mismatch`; Judges B then K)
A comparison card edited without D6 rows naming it makes every later decision `comparison_card_mismatch`: kept in the
denominator, never counted. That must never be silent.

| Item | Change | Test (and the plant it catches) |
|---|---|---|
| One line after the decisions' seal | `fleet/card_check.CardMismatchCheck`: each sealed decision put to h's `CountingRule` at the seal's receipt commit; when any is `comparison_card_mismatch`, one line: "comparison_card_mismatch: N of M decisions do not count until D6 rows name card v<K>; see the MS-P1j runbook" (K read from the card's own `version:` at its commit). A rerun says it again | `test_card_check.py`, on real git with h's fixture: the card edited with no rows naming it gives the line with v3 (plant: the version not read); the run carries it, a rerun repeats it, no dashcam file changes (plants: the fresh run or the rerun dropping it) |
| Only that cause | a decision not yet counted (first counted session unset), or counted, gives no line | the unset and the counted cases give no line (plant: every not-counted verdict named) |
| Exit 1, so #fno-desk is alerted | `SessionRun.warnings` (a's contract, additive; never on a run that did not run); `school run` prints each and exits 1 | `test_the_run_command_prints_the_line_and_exits_1` (plants: exit 0, the line hidden) |
| The record checks, a replay does not | the record root passes `build_card_check(root)` (h's rule over the repository's git and D6's versions); a replay's seals name no commit the rule could judge, so it passes none | `test_the_record_root_passes_the_check_and_a_replay_has_none` (plant: the record root without it) |

- **No record changed:** the check only reads the sealed records, the repository's git and D6's rows.
- **Plants:** 7 planted, 7 caught. Judge B's survivor (judge 507.7: N forced to M) is now caught by `test_the_line_counts_only_the_mismatched_decisions_among_the_session_s`: one mismatched decision among three gives "1 of 3".
- **Judge K's survivor (judge 520: `seal.commit` replaced by HEAD):** caught by `test_rows_registered_after_the_seal_never_clear_the_decisions_it_sealed`: rows naming the new card, committed after the seal, would count these decisions at HEAD; at their own seal's commit they still warn.
#### INS-e Claims (round 1, branch `story/ms-ins-outputs`, on INS-d; the SHA is in the commit that carries this text)
| Criterion | Met by | Test (`tests/school/instructor/outputs/`) |
| 1 write-once | `store.DriveInstructorStore` (receipt per file, same bytes a no-op, others refused, damaged bytes never read) | `test_store` (conformance, the folder, damaged bytes, a refused Drive write); `test_run`: `a_session_is_attributed...written_once` |
| 2 two runs, identical bytes | `run.InstructorRun` | `test_run` (a rerun leaves every file identical) |
| 3 the public counts file | `public_counts.InstructorCountsFile` | `test_counts_and_command`: `the_counts_file_holds_codes...passes_the_record_scan`, `..._written_once` |
| 4 the "why" lines' privacy | `why_line.py`, `labels.py` | `test_run`: `the_why_line_names...no_contract`; `a_winners_why_line_reads_the_winner_form...` |
| 5 every denominator, refusals included | `comparison.SealedDecisions.outcome_counts`, `review.py` | `test_review`: `the_review_shows_every_denominator...` |
| 6 a planted cause in the review and the "why" line | `review.driver_summary`, `WhyLineSource` | the same test; `test_run` |
| 7 off-switch | `command.run` | `the_switch_off_prints_school_off_and_does_nothing` |
| 8 orphan corrections counted and alerted | `PathReader.orphan_corrections`; the review's last line | `test_corrections`: `a_correction_naming_nothing_is_listed_as_an_orphan...`; `test_review` (its count printed) |
**Also built (from the boundaries and the rulings):**
- **Re-checks.** A classification waiting for its expiry's settlement (cause 11), or for its controls to close (the modifier), is classified again on each later run. A changed one is written as a new record naming the first (`test_run`: `a_classification_waiting_for_its_expiry...`). Cause 13 never triggers a re-check: it waits for MS-P1j.
- **The comparison over sealed decisions.**
  - h's `CountingRule` judges each decision at its seal's commit.
  - `common_road_days` gives the pairs.
  - RC1 against N0 is the live null in every review (`rc1_is_compared_with_n0_only_as_the_live_null`).
  - A session with no readable decisions file is listed, never skipped silently.
- **Rupees.** Account trades only: net, maximum drawdown, worst day and worst trade. Tickets are never summed in (`tickets_are_never_summed_into_rupees`).
- **The review text** starts with the plain P2 line (orchestrator's condition 4). Every paired row carries its notes: "descriptive, not a test", "no bound before N sessions", and the seller-shape false rate.
- **The command.** `python -m fno.school.instructor --session D [--write]` and `--review FIRST LAST [--write]`, a dry run by default. Its real run on today's main prints "school off" (the school's switch is off). That is the honest result; no real record exists to read yet.
**Known limits:**
- **Unfilled entries.** An entry decided as a trade that never filled stays open until MS-P1j reports its fill status. `CountedComparison.rows` takes the `unfilled` set; j's wiring supplies it.
- **The three counts.** f's eligible, fillable and executed counts need j's fills. The review shows every decision's outcome code, the denominator with refusals, until j supplies them.
**Broken-code proof:** 15 plants, all caught after one added test:
- the store's conflict and damage checks;
- the dry run;
- the re-check trigger and its `corrects`;
- tickets in rupees;
- RC1's single pair;
- the unsealed list;
- the counts' correction filter;
- the off-switch;
- the write-only counts file;
- the winner labels (survived until the winner "why" test was added);
- orphans (caught in `test_corrections`).
**Real output sample:** the fixture's "why" line, `CS1@1 BANKNIFTY-M: net Rs -140; why: ...`. On real data: "school off".
**The interfaces agreed with MS-P1j's builder (23 Oct 2026; j wires them after j merges):**
- `run_instructor_session(config, session, write=True)`: j's one entry point. j calls it after the session's outcomes
  file is sealed and before its counts commit. It attributes, classifies, writes the instructor's files and the public
  counts file. Tested with fakes.
  - j wraps it in isolation: the instructor can never stop the school's record.
  - With write=False (j's replay) it writes nothing at all.
  - A rerun returns a session already written, as written (`a_rerun_after_later_sessions_returns_the_session_as_written`).
- `build_why_lines(config=None) -> WhyLineSource`, with `lines(session)`. It reaches g's 20:05 section through a `why`
  port in g's day inputs; the render line is g's.
- `CountedComparison.rows(..., unfilled=)`: keys `(driver_id, road, entry session)` of every fired entry that never
  fills, both size-shared and refused fills.
- `build_review(..., counts=)`: any `counts(session) -> tuple[OpportunityCounts, ...]`, which j's sealed day inputs
  satisfy. The review prints eligible, fillable and executed per driver, or "three counts not supplied".
**Ticket lines (orchestrator's ruling, 23 Oct 2026, from g's builder; judge 481's rule):** a ticket's "why" line
carries no rupee figure. It reads "<driver> <road> ticket (hypothetical, account limits relaxed): why: ...". Account
trades keep "net Rs". Every line starts "<driver id> <road>", one space apart, which g's section relies on; that format
is stable. Test: `test_counts_and_command::a_ticket_line_never_carries_rupees`. g keeps its own filter as a second
guard.
#### INS-e Claims, round 2 (judge 522 FAIL round 1: two should-fixes, six untested branches, one minor; the SHA is in the commit that carries this text)
| Finding | Fix | Test |
| SF1 orphans missing from the day's output; the window search raised false alarms | `PathReader.orphan_corrections()` scans every session from `RECORD_START` (22 Oct 2026, the first dashcam day) to today, so a correction is an orphan only if no outcome on file anywhere carries its id. `SessionResult.orphans` is filled on every day run, and the command prints "ALERT: corrections naming no outcome on file: N". Files are read once per run (a cache). | `test_corrections::an_orphan_is_a_correction_naming_no_outcome_on_file_from_the_start_of_the_record`; `test_round2::the_days_run_lists_orphan_corrections`; `test_counts_and_command` (the ALERT line) |
| SF2 a corrected outcome was picked up only while its record waited, and its attribution never rewritten | Each attribution and classification now carries `outcome_sha256`, the SHA-256 of the outcome record it read. The re-check takes the latest record per position from the first counted session (or 90 days back). It runs again when that outcome's SHA changed or the record waits, writes a new attribution (`corrects` = the old attribution's SHA) for a corrected outcome, and writes a classification only if it differs. | `test_round2::a_corrected_outcome_is_re_attributed_and_re_classified_even_when_nothing_waited`; `::an_unchanged_record_is_never_written_again` |
| SF3 six untested branches | one test each | `test_round2`: `the_modifier_alone_makes_a_record_wait`, `an_unchanged_record_is_never_written_again`, `rc1_is_one_of_the_two_controls_on_a_road_slot`, `only_counted_decisions_are_paired`, `a_damaged_decisions_file_is_listed_as_unsealed`, `the_maximum_drawdown_is_the_deepest_fall_from_a_running_peak` (100, -300, 50, -100 gives -350 by hand) |
| Minor: sum through f's `account_net` | `review.py` takes `net_rs` from `account_net(mine).net` | `test_review` unchanged, passing |
**Broken-code proof (round 2):** I planted 10 faults, one at a time, and the tests caught every one:
- `waiting`'s modifier half removed;
- the unchanged guard forced true;
- the corrected check forced false;
- the attribution's `corrects` blanked;
- orphans left out of the day run;
- RC1 dropped from the controls;
- the orphan scan narrowed to today;
- a damaged decisions file read as empty;
- the drawdown taken from zero instead of the peak;
- every decision counted regardless of h's verdict.
**Known limits:** the same two as round 1 (the unfilled entries and the three counts come from j's wiring after j merges). The 90-day look-back applies only while `first_counted` is unset. Judge K's intermittent `test_settlement[BANKNIFTY]` under -n auto is in MS-P1d's files, outside this diff.

#### INS-e follow-up, round 2: each session computed as of itself (branch `story/ms-ins-adopt`, lane 1; judge 525 FAIL round 1; orchestrator's ruling of 23 Oct 2026: build the cut-off, drop adoption)

**The defect** (found by MS-P1j's builder):
- `DriveInstructorStore.write` puts the file on Drive first and publishes its receipt after.
- If a run stopped between the two, the rerun recomputed, and it read "today": corrections up to the clock, controls' corrected results, settlements published since.
- Its bytes then differed, and write-once Drive refused them for good.

**The root cause and fix:** the file was not a pure function of fixed inputs. Each session's run now reads only what was sealed or known by that session:
- `PathReader.closed_on` and `closed_between` take `as_of`: corrections come only from outcome files of sessions up to it, never the clock. The run passes its own session for the day's paths, the controls (`_nets`) and every re-check.
- `EvidenceBuilder.build` and `Classifier.classify` take `as_of`: the hold-to-expiry value (cause 11) counts only for an expiry before that session, because its settlement is published after the expiry day's close.
- A rerun therefore computes the same bytes. The write-once store takes equal bytes as a no-op and publishes the missing receipt. No unreceipted file is ever trusted.
- Round 1's `recover`/adoption is removed: the port, store, fake and conformance check are back as on main.
- A later correction reaches a later session's file as a re-check (part e's design), never the earlier session's.

| Criterion | Test (`tests/school/instructor/outputs/test_cutoff.py` unless named) |
|---|---|
| A crash between the Drive write and the receipt, then a later correction and a published settlement, then a rerun: the same bytes, one receipt per file, no conflict | `a_run_stopped_before_its_receipt_reruns_after_more_records_to_the_same_bytes_and_one_receipt_each` (on main's code: `InstructorConflict` on the attribution file) |
| A later correction leaves the earlier session's result unchanged and reaches the later session's file | `a_later_correction_reaches_a_later_sessions_file_never_the_earlier_sessions` (fails on main's code) |
| A re-check reads only corrections sealed by its own session | `a_re_check_reads_only_corrections_sealed_by_its_own_session` |
| The controls are read as of the session (REF corrected afterwards: the same result) | `the_controls_are_read_as_of_the_session` |
| The reader's cut-off; no session given reads up to today (the review) | `the_reader_reads_corrections_sealed_up_to_the_session_it_is_given` |
| Hold to expiry counts only from the session after the expiry | `holding_to_expiry_counts_only_from_the_session_after_the_expiry`; `test_run::a_classification_waiting_for_its_expiry...` (written again at the first session after the expiry, not before) |
| A rerun after the settlement is recomputed to the same result | `test_run::a_rerun_after_later_sessions_returns_the_session_as_written` |
| A written session's unreadable files are reported as of that session; a later session's damaged file is that session's (judge 525.2's minor; test only, lane 2) | `a_written_sessions_unreadable_files_are_read_as_of_that_session` |

**Broken-code proof:** 5 plants, all caught:
- the day's paths read up to today;
- the re-check's paths read up to today;
- the controls read up to today;
- the hold allowed on the expiry day;
- the reader ignoring `as_of`.

The re-check and controls plants survived until their own tests were added.

**What is still not pure [reasoning only, not tested]:**
- **Late or failed source reads.**
  - The fleet's own sealed settled outcome proves the settlement was archived by its session, so a settled path's settlement is always there.
  - But a hold for an expiry before the session reads d's settlement source, and the reader reads the snapshot archive. If either is missing at the first run (an evening archive that failed and was backfilled, or Drive unreachable and read as "missing"), and the run also stopped before its receipt, the rerun can differ. That ends in a loud `InstructorConflict`, never a silent rewrite.
  - Making these pure needs "known at" times in d's settlement source and the archive, which are other stories' ports.
- **Out-of-order runs.** A re-check reads earlier sessions' instructor files by their receipts. If session S runs before S-1's file has its receipt, and S is then rerun after S-1 is fixed, S can differ. MS-P1j runs sessions in order.
- **Orphans** are read up to today, but they are an alert line only, never written into a file.

**For MS-P1j's deferred store:** it needs no `recover`; it rebases on this once it lands.


### MS-P1j follow-up: the instructor wired in (MS-INS part e; orchestrator's hand-off, 22 Oct 2026; branch `story/ms-p1j-ins-wiring`, on part e's 63cabe67)
Signatures agreed with the INS builder (session_01LH7m9r5TCAKgZbeHVYkiTD). Lane 1 (the fleet's record path), so two
judges. It merges after part e.

| Item | Change | Test (and the plant it catches) |
|---|---|---|
| The instructor's session run, after the outcomes' seal and before the counts' commit | `SchoolFleet.after_outcomes` (default `no_step`): called once the outcomes and drift files are sealed, and again on a rerun of a complete session before its commit (the instructor is write-once and same-bytes). The record root passes `IsolatedSessionStep("instructor", run_instructor_session(cfg, session, write=True), #fno-desk alert)`; its counts file lands in `research/school/counts/instructor/`, inside the folder j's one commit takes | `test_session_step.py`: the step sees the sealed outcomes and no counts file yet (plants: never run; run after the counts) and runs again on a rerun (plant: skipped on a rerun) |
| It can never stop the school's record | `IsolatedSessionStep`: a failure or a time-out (300 s) is one alert naming the class or "time limit", never the message; the counts are still written and committed | a failing and a slow step each give one alert and the counts file (plant: the step not isolated) |
| A replay runs no instructor | The replay root passes no step and imports nothing of `instructor.wiring` (its Drive store and receipts) | `test_wiring.py`: the import check now covers `instructor.wiring`; the replay's step is `no_step`; the record root's is the instructor's run (plants: the replay running it; the record root without it) |
| `unfilled` for the paired comparison | `fleet/unfilled.UnfilledEntries(first, last)`: every sealed trade or ticket decision whose position its ledger never opened, as (driver, road, entry session); `wiring.build_unfilled_entries(cfg)` over the record's stores | `test_unfilled.py`: the size-shared entry is unfilled and the served one is not, tickets alike, no-trades never, sessions outside the range left out (plant: everything filled) |
| The "why" lines for g's 20:05 section | `SealedDayInputs.why(session)` from part e's `build_why_lines(cfg)`, passed in by `build_report_inputs` | `test_the_day_inputs_pass_the_instructor_s_why_lines_through_and_none_without_a_source` (plant: dropped) |
| f's three counts in part e's review | none: `SealedDayInputs.counts(session)` already serves them | — |

- **Judge B's note (judge 507.5), the root fix:** the counts' commit took the whole counts folder, so a timed-out
  instructor's `.<name>.part` would have been swept in. Now `fleet/counts_commit.SessionFilesCommitter` commits only the
  session's named files (its own three and the instructor's counts file, named by the record root) through a's
  `OwnedPathsCommitter`; `SessionCounts.files(session)` lists them. Second guard: `.gitignore` ignores
  `research/school/counts/**/.*.part`. Test on real git (a clone of a bare origin):
  `test_only_the_session_s_named_files_are_committed_never_a_stray_part_file` commits the session's files and the
  instructor's, never a stray `.part` nor an un-ignored stray file beside them (plant: the folder committed, caught).
  Judge B's should-fix (judge 507.9): `test_the_record_root_names_the_instructor_s_counts_file_in_the_counts_commit`:
  the record root's `SessionCounts.files(session)` names the instructor's counts file and a replay's does not (plant:
  the record root naming no instructor file, caught).
- **Not in this change, by agreement:** g's `DayInputs.why` and the render line in `evening.py` are g's builder's;
  part e's `command.py` passing `unfilled=` and `counts=` is the INS builder's.
- **Plants:** 9 planted, 8 caught; the ninth (closings counted as openings in `unfilled`) was equivalent, so the
  redundant filter was removed rather than kept untested.

#### Round 2 (Judge K, judge 523; orchestrator's ruling: one committer per run). Rebuilt on part e's 136f5890 and main
Judge K's should-fix: past its 300 s the instructor's thread kept running and committed and pushed its receipts itself
(`GitReceiptPublisher`), beside the run's own counts commit in the same checkout (`.git/index.lock`, an interleaved
pull). Root cause: the step's work did its own writes and git. Now the work only reads and computes; every write runs on
the run's own thread, and only when the work ended in time; one commit takes everything.

| Item | Change | Test (and the plant it catches) |
|---|---|---|
| The work writes nothing | `fleet/session_hook.StagedSessionStep`: `work(session)` runs under the limit and returns its writes, which run on the run's thread; a work past its limit (or failing) is one alert and its writes are never run. `instructor_step_wiring.instructor_work` runs part e's session run over `fleet/deferred_store.DeferredInstructorStore` (writes kept until `flush`) | `test_an_instructor_finishing_after_its_limit_has_nothing_committed_and_the_alert_says_time_limit` (real git: the late work's file is never written, not on `main`, the checkout clean, the alert says "time limit"); `test_the_instructor_s_work_writes_nothing_and_reads_through_its_run_s_receipts` (plants: the work writing in the thread; the writes run on the thread; the deferred store passing writes through) |
| No git write on the thread, not even a fetch | `dashcam/publisher.RemoteReceipts` (now `fno/storage/receipt_publisher.py`, after the publisher move, judge 527): `refresh` (fetch, deepen) split from `find` (log and show only); `GitReceiptPublisher.published` is both, unchanged. `fleet/run_receipts.RunReceipts`: `published` and `publish` only `find`; the run fetches once on its own thread (`prepare`). It reaches part e's path reader's dashcam and the instructor's store through new optional `publisher`/`store` parameters on part e's builders (default: unchanged, so part e's own command still commits and pushes) | `test_the_step_s_lookups_and_publish_only_read_and_only_refresh_fetches`; `test_a_receipt_pushed_since_the_run_s_fetch_is_seen_only_after_the_next_refresh` (real git); `test_the_run_s_receipts_reach_the_path_reader_s_dashcam_and_the_store` (plants: a lookup fetching; the store, the run or the path reader without the run's receipts; no prepare) |
| One commit takes the instructor's files | `fleet/counts_commit.SessionFilesCommitter` commits exactly the named files anywhere in the checkout (`NamedFiles` on O9's `GitManifestRecorder`); the record root names `instructor_files(session)`: the instructor's counts file and its two session receipts | `test_a_named_file_outside_the_counts_folder_is_committed_and_its_unnamed_neighbour_is_not`; `test_an_instructor_in_time_is_written_on_the_run_s_thread_and_taken_by_the_one_commit` (one commit); `test_the_step_s_files_are_its_counts_file_and_its_two_session_receipts` (plants: the folder swept; the receipts not named) |
| A write or fetch that fails | named by class, one alert each; the school's record goes on | `test_a_failing_write_or_prepare_alerts_by_class_and_the_work_never_runs_after_a_failed_prepare` (plant: a write failure raised) |
| Minor a: a stale decisions seal | `UnfilledEntries` leaves that session out, as part e's `sealed_decisions` leaves its decisions out of the comparison and names it unsealed | `test_a_session_whose_decisions_file_fails_its_receipt_is_left_out_as_the_comparison_leaves_it_out` (plant: not caught) |
| Minor b: `unfilled` with the school off | `build_unfilled_entries` builds the dashcam and the books (with the account sync, as `entries` pulls from Drive) itself, never the fleet | `test_unfilled_entries_read_the_record_s_stores_even_with_the_school_off` (plant: through the fleet) |

- **Limits [reasoning only]:** the writes run on the run's thread without the step's time limit, bounded by Drive's own
  timeouts: a limit there would bring back a late write. A crash between the instructor's Drive write and the run's
  commit leaves its receipt uncommitted, as before in part e (a rerun writes the same bytes, or alerts a conflict).
- **The pilot's record is unchanged:** the 22 Oct replay is byte-identical (105 files); a replay runs no step.
- **Judge K's note (via the INS builder): one path reader per run.** The path reader caches the files it read, so the
  step's work builds a new one on every session call, never one held across runs:
  `test_every_session_call_builds_its_own_path_reader_never_one_held_across_runs` (plant: a run held across calls,
  caught).
- **Judge K's minor (judge 523.1):** `test_an_unpushed_commit_of_another_writer_still_blocks_the_push`: a commit of
  another writer not yet on main makes the pull refuse and nothing reaches main (plant: `NamedFiles.owns` forced to
  True, caught).
- **Plants:** 15 planted, 15 caught. Gates: in the commit message of the tip.

#### Round 3 (Judge B, judge 507.13 SF1; owner: fix and one more check): a refused counts commit is loud
The runner dropped the counts commit's outcome and `school run` exited 0, so a refused push (three lost races, a pull
refused for other unpushed changes, a hook refusal) was silent; it now carries the instructor's receipts too. On main
before this branch for the counts alone.

| Item | Change | Test (and the plant it catches) |
|---|---|---|
| Never silent | `SessionFilesCommitter.commit` returns None when the files are on `main`, else the refused line (O9's own refusal text, naming the files); `SessionCounts.commit` alerts "counts NOT pushed <session>: <line>; the next run of the session pushes them" to #fno-desk (the record root's sender) and returns it; the runner carries it in `SessionRun.warnings` on the first run and on the rerun, so `school run` prints it and exits 1; nothing says done (the CLI's lines are decisions sealed and fills only) | `test_a_refused_push_is_alerted_printed_and_exits_1_then_the_rerun_pushes_it` on real git (plants: the first run or the rerun dropping it; no alert; the refusal hidden; the record root or `fleet_on` without the alert) |
| The rerun completes it | `NamedFiles`: with nothing new to commit, a named file committed here and not on `main` is pushed; the run's earlier unpushed commits under its run paths (the counts folder, the instructor's receipts) are its own, so they never block a later commit and go up with it (Judge B: exact names alone would block every later commit) | the same test (rerun once the push works: exit 0, the file on `main`); `test_an_earlier_session_s_unpushed_counts_never_block_a_later_session_and_go_up_with_it`; `test_the_record_root_alerts_a_refused_counts_commit_and_owns_its_earlier_unpushed_ones` (plants: the leftover never pushed; the run paths dropped, in the committer or the record root) |

- **Plants:** 9 planted, 9 caught.


### MS-P1c follow-up: a stored slot file is adopted, never sealed over (orchestrator's go, 23 Oct 2026; branch `story/ms-p1c-adopt`; Judges B then K)
The window (found by the INS builder in the instructor's store; the same in the dashcam): `DriveDashcamStore.seal` puts
the file on Drive, then pushes its receipt. A run that stops between the two leaves a file with no receipt on `main`;
a fresh container's `find` is None, the runner decides again, and if its records differ every rerun is a
`ReplayConflict` (uncaught: the session never fills, writes outcomes or counts). Reproduced on real git with the
production store and publisher [strong evidence]. A rerun can differ, so "the inputs are frozen" cannot be proven:
each driver's 60 s wall-clock limit [strong, from the code]; a canonical 3 pm marker, a recorded quote file, the day's
archived SPAN file or the 15:15 capture landing between the two runs [some evidence, from the code].

| Item | Change | Test (and the plant it catches) |
|---|---|---|
| Adopt, never seal over | `DashcamStore.recover(session, slot, kind, belongs)` (a's contract): `find`, else a stored file is adopted when `dashcam/adoption.adoptable` passes: it decodes, re-encodes to the same bytes, holds only the kind's records, of this session and slot (an outcome names no session: a settlement fills on its expiry day), and every record is the writer's own; then its receipt is written from its own bytes and published under an "adopted" commit | `test_adoption.py` on real git: `test_the_stuck_session_is_adopted_and_its_stored_records_stand` (what the rerun decides now is a `ReplayConflict`, the stored records stand); each refusal (unreadable, not canonical, another kind, another slot, another session, not this fleet's) raises with its reason and publishes nothing; a settlement's outcome is adopted (plants: no check; published before the check; another key's file; each check dropped; outcomes judged by their fill date) |
| The fleet's own (the orchestrator's addition 1) | `SchoolFleet._belongs`: a decision's driver is this fleet's and names that driver's card SHA-256 as frozen now; an exit, outcome or drift row's driver is this fleet's | `test_a_stored_file_of_another_card_version_stops_the_run_by_name_and_fills_nothing` (plants: the card version ignored; every record accepted) |
| Loud stop by name (addition 2) | `DashcamStuck` "dashcam stuck: stored file unverifiable <session> <slot> <kind> (<why>)": the run's status `stopped: ...`, the CLI exits 1 (the alert), nothing sealed or filled | the same test (plant: the stop not caught) |
| The runner adopts where it writes | `recover` for the decisions (an adopted file takes the rerun path over the sealed records) and before sealing the outcomes and the drift; the "all finished" check stays a pure `find` | `test_a_rerun_completes_the_session_from_its_stored_decisions_not_what_it_would_decide_now`; `test_a_rerun_after_a_stop_at_the_drift_file_adopts_it_and_writes_the_counts` (NIFTY road, the stored rows differ from the rerun's) (plants: the decisions on `find`; the drift on `find`) |
| Fakes as strict as Drive | a's `FakeDashcam` refuses other bytes over a stored file, receipt or not, and adopts through the same `adoptable`; `ReplayDashcam.recover` is `find` (a local file is its own seal) | `check_dashcam` now asserts `recover` for the fake, the real store and `ReplayDashcam` (plant: the fake adopting unchecked) |

- **Readers never adopt:** reports, `unfilled`, the instructor's reader and the entry mids keep `find`; only the
  writer's rerun adopts.
- **The pilot's record is unchanged:** the 22 Oct replay is byte-identical (105 files).
- **Plants:** 13 planted, 13 caught (the drift plant first survived on a BANKNIFTY test, whose drift is empty; the
  test now uses a NIFTY road with differing rows).
- **Round 2 (Judge B, judge 528 SF1): the fleet's own check on every row kind, tested.**
  `test_a_stored_row_of_a_driver_outside_the_fleet_stops_the_rerun_and_seals_nothing_of_its_kind` (exit, outcome,
  drift): a stored, unreceipted file with one row of a driver outside the fleet stops the rerun as "stopped: dashcam
  stuck: stored file unverifiable ... (a record that is not this fleet's ...)" and nothing of that kind is sealed
  (plants: `_belongs` true for every non-decision row, all three fail; the drift row's driver misread, the drift one
  fails). Test-only change.

MS-P1g why lines, round 3 (j's ins-wiring is on main, 486b0f4f; main merged in): the stub is gone and `SealedDayInputs` has
one `why` (j's). `test_the_pinned_format_is_what_the_instructors_why_line_writes` now runs against part e's real
templates (`LINE`, `TICKET_LINE`): a trade's line starts "<driver> <road>: net Rs ...", a ticket's "<driver> <road> ticket
(hypothetical, account limits relaxed): why: ...", both are shown with no withheld note, and the ticket form holds no
rupee figure. The two j tests that needed `why` pass again.

#### INS-e follow-up: the review's sources from MS-P1j (branch `story/ms-ins-review-sources`, lane 1, Judge K; after MS-P1j's ins-wiring, 486b0f4f)
Part e's two known limits are closed: the unfilled entries and f's three counts.
- `review_wiring.build_review_sources(config)` builds `ReviewSources(unfilled, counts)`:
  - `unfilled` is MS-P1j's `build_unfilled_entries`;
  - `counts` is MS-P1j's `SealedDayInputs.counts`, which reads the counts file each session's run commits.
  - It is a separate composition root because MS-P1j's `fno/school/wiring.py` imports the instructor's `wiring.py`. This root imports MS-P1j's, and only the command's entry point imports it, so there is no cycle.
- `python -m fno.school.instructor --review FIRST LAST` now does two things:
  - it passes the range's unfilled entries to `CountedComparison.rows`, so an entry that fired but never filled counts as the driver's miss, as 327 asks;
  - it prints eligible, fillable and executed per driver instead of "three counts not supplied".
- Without sources (a test, or a caller that passes none), the review behaves as before. Read-only: nothing new is written.
| Criterion | Test |
|---|---|
| The sources are MS-P1j's unfilled entries and the committed counts file (none when none is committed) | `test_review_wiring::the_review_reads_ms_p1j_unfilled_entries_and_the_committed_three_counts` |
| The review asks for the range's unfilled entries, passes them to the comparison and prints the supplied counts | `test_review::the_review_command_passes_the_unfilled_entries_and_prints_the_supplied_three_counts` |
| The command's entry point gives the review its sources | `test_review_wiring::the_commands_entry_point_gives_the_review_its_sources` |
**Broken-code proof:** 5 plants, all caught:
- unfilled not passed to the comparison;
- counts not passed to the review;
- the sources not built;
- the counts read from the repository root instead of the given one;
- the entry point passing no sources.

**Known limits (judge 530's minors, parked by the orchestrator on 23 Oct 2026; reasoning only):**
- **A written review is not rerunnable.** `--review --write` writes the paired file under the range's last session. It depends on today's ledgers and corrections, so the same range written again after a later correction is refused by write-once, for that key, for good.
  - The cut-off reader could bound the corrections.
  - The unfilled entries come from MS-P1j's ledgers, which have no "as of".
  - Until fixed: write a range's review once, after its last session's fills; a dry run is always allowed.
- **A review that covers a session before its fills** counts that session's fired entries as unfilled. Run a review only over sessions whose run has finished.
**Real output:** `python -m fno.school.instructor --review 2026-10-22 2026-10-23` prints "school off": the school's switch is off. That is the honest result; no sealed day exists to review yet.
