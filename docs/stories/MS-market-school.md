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

**Files owned:** `fno/school/instructor/{__init__,contracts,ports,reader,fakes,wiring}.py`,
`tests/school/instructor/test_reader.py`, `tests/school/instructor/conformance.py`.

**Implements:**
- frozen types: `HeldPath` (one closed trade or ticket: its outcome record, its entry decision record, its exit record
  if any, and the snapshots of every session held, entry to exit), `Attribution`, `CauseTag`, `Classification`,
  `PairedRow`, `MapStatus`;
- `MapStatus` has exactly three members: `exploratory`, `watching`, `not_established` (327 correction 3);
- `PathReader.closed_on(session) -> tuple[HeldPath, ...]`: the trades and tickets whose outcome was sealed that
  session. A corrected outcome is read through its latest correction; the original stays on file;
- ports, each with an in-memory fake that passes `conformance.py`:
  - `SnapshotArchive`: over b's `SnapshotSource`;
  - `SettlementArchive`: over d's `IndexSettlementSource`;
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

**Files owned:** `fno/school/instructor/attribution/` (`greeks.py`, `steps.py`, `attribute.py`),
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
- **Costs:** every leg's C1 charges (entry and exit `FilledLeg.charges`) plus the spread paid against the mids (the
  outcome record's `slippage_vs_mid`).
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

**Files owned:** `fno/school/instructor/causes/` (`terms.py`, `thresholds.py`, one module per rule group, `classify.py`),
`research/school/INSTRUCTOR_V1.md`, `tests/school/instructor/causes/`.

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
| 12 | Normal noise | net within 1 standard deviation of the position's own model outcome: entry volatilities held (sticky strike), lognormal over `T_held`, 201 frozen quantiles | the same rule |
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

**Files owned:** `fno/school/instructor/paired/` (`values.py`, `series.py`, `status.py`, `nulls.py`),
`tests/school/instructor/paired/`.

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
- **Interval:**
  - the mean and a two-sided 90% interval from a moving-block bootstrap over sessions;
  - blocks of 5 sessions, 10,000 resamples, a fixed seed;
  - blocks of 2 and 10 shown as a sensitivity.
- **Status (`MapStatus`):**
  - `exploratory`: below 30 valid counted sessions;
  - `watching`: 30 or more and the interval's lower end above 0, labelled "not a claim, no licence";
  - `not_established`: 30 or more otherwise.
- **Live null:** every review also compares RC1 with N0 on the same days, so the null's own rate of looking good is
  visible.

**Acceptance tests:**
1. Hand-computed: 3 sessions x 2 roads, with abstentions, against each control.
2. A session's five roads make one series point (series length = sessions).
3. An abstention counts as 0 and in the abstention count.
4. The cut at an open pair.
5. Status boundaries: 29 and 30 sessions, and a lower end of exactly 0.
6. `MapStatus` has exactly three members, so no Supported or Confirmed can be built.
7. **Null calibration (327 correction 3):** 200 seeded null fleets on fakes, with zero edge, a shared market within
   each session (correlation 0.6 across roads) and 10-session holds. The share reaching `watching` at 30 sessions is
   reported in Claims and must be 10% or less. If it is higher, the block length is revised and re-frozen before any
   counted session.
8. **Planted edge (325 section 6.2):** a hidden fake driver with a known edge in return on risk (the +Rs 300-a-trade
   example, and a large one). The sessions needed to reach `watching` in 80% of 200 seeds go into Claims, so the owner
   sees how long such an edge takes. The large edge must reach it within 30 sessions.
9. Empty: no common road-day gives no row.

#### INS-e Outputs: records, the 30-session review and the "why" line · `story/ms-ins-outputs`

**Files owned:** `fno/school/instructor/outputs/` (`store.py`, `review.py`, `why_line.py`, `command.py`),
`tests/school/instructor/outputs/`.

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

#### Questions for the orchestrator (before code)

1. **Reads beyond the dashcam records:** the attribution needs b's snapshots, d's settlement source, A6's events and
   e's cards. All are read-only recorded inputs. Is that within "reads only the sealed dashcam records and counts"?
2. **The block bootstrap:** S2's `resampled_ratios` fixes 20-day blocks, which is too long for 30 sessions. Should I
   add an optional `block` argument to S2's function (S2's lane-1 file, its default unchanged), or keep a separate
   20-line resampler in `paired/series.py`? I propose the argument (DRY).
3. **The command:** `python -m fno school` is j's reserved line. Should INS-e register `instructor` under j's group
   when j merges, with a module entry point until then?
4. **The 20:05 line:** `WhyLineSource` is a port. Joining it to g's evening section is one line in j's wiring, agreed
   with g's and j's owners. Agreed?
5. **Tickets in the primary paired measure** (idea quality), with executed-only beside it: confirm.
6. **Lane:** one judge (evaluation records; no money, fill, limit or exit path). Confirm.

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
- **Displayed size** for a synthetic quote is the bucket's median displayed size over the same sessions (same 30-session
  rule), so E4d's size gate still bites. The history holds no sizes; this is labelled.
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
| `history/` | `HistoricalChain` port: `day(road, session) -> DayChain or None` (closes, volume, open interest, expiries, index close). Adapters: `PanelChain` (NIFTY panel) and `BhavcopyChain` (archived F&O files, UDiFF and legacy) | `NiftyPanel`, `research_data`, the F&O library of `fno.storage.wiring`; EDGE1's day-file and lot readers by one adapter module (see question 1) |
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
  3. `PanelChain` and `BhavcopyChain` return the same closes for a day both hold (cross-check on recorded days).
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
  4. The quote is close -/+ the scenario half-spread, floored at half a tick; bid is never below zero.
  5. Look-ahead: changing any record dated after the session leaves the session's snapshot and every driver's
     decision byte-identical (a mutation test over the chain).
  6. An insufficient bucket gives `unavailable` for that leg's trade, never a zero spread.
  7. Dated lot and dated STT enter the proposal's `max_loss` (a 2022 trade is charged the 2022 STT).

**SIM-d The practice runner and its labels** · depends on a-c and on MS-P1j's fleet runner
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

### 7.6 Questions for the orchestrator (answers needed before SIM-a code unless marked)

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
5. **Displayed sizes** (7.2): the bucket median stands in for the unknown history. Confirm, or say the size gate is
   waived in practice and labelled so.

### 7.7 Claims

Empty until a part is built; each part keeps its own Claims subsection under the pilot's `## Claims` below.

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

### MS-P1d follow-up Claims, part 3 (branch `story/ms-p1d-entries`): the read-only ledger read for j

| Item (orchestrator, 22 Oct 2026) | Change | Test (and the plant it catches) |
|---|---|---|
| `SchoolAccounts.entries(driver_id) -> tuple[LedgerEntry, ...]` for j's `LedgerReader` (a3), so settlement can run before the session's first `view` | `accounts/school_accounts.py`: under the account's lock, pulled from Drive once per run (`_locked`, shared with the writer), reads `PositionBook.entries()` in the order recorded, after the same unit-for-unit ledger check `view` makes; writes nothing (no account opened, no equity row, no push); an account never opened gives () | `test_entries.py`: entries match the ledger in order (plant: order reversed); nothing written and no push, the next session's row still written by `view` afterwards (plant: entries opening the account); one pull per run under the lock, a held lock refuses (plant: no pull); a failed pull stops with E2c's `PrivateFilesUnavailable`; half a record raises (plant: the check dropped) |

- **Plants:** 4 planted, 4 caught. The Protocol's conformance check is added once a3 (j's builder) is on main.

### MS-P1d follow-up Claims, law order (branch `story/ms-p1d-law-order`, from main)

| Item (orchestrator, 22 Oct 2026, on j's finding) | Change | Test (and the plant it catches) |
|---|---|---|
| The first named reason is the root cause: on BANKNIFTY-M a missing quote came out as `max_loss` (it fails closed without the leg's mid) ahead of `missing_quote` | `safety/wiring.py`: protected, the four quote-gate laws, impossible price, then max loss, bucket, open risk, new risk per day, margin room, daily stop, brake. Every law still runs and every reason is kept; only the order changes | `test_laws.py`: the order pinned (plant: the old order); a missing and a one-sided quote name their quote reason first, with `max_loss` still in the list (plant: the gates after max loss); a valid quote with too large a loss still names `max_loss` alone (plant: a gate that refuses a valid quote); the margin test reads results by law name, not by position |

- **Plants:** 2 planted (old order; a gate refusing a valid quote), 2 caught. f's `named_refusal` (first in order within a group) now names the quote reason within trade validity too.

### MS-P1d follow-up Claims, part 4 (branch `story/ms-p1d-practice`, on the law order and a3 9ede0d1e): practice quote rules, design A

Replaces the earlier part 4 (744299d6, never merged), which waived the size laws outright. Built on a3's
`SlotQuote.sizes_measured` and `RefusalReason.SIZE_NOT_MEASURED` (a3 must merge first, then the law order, then this).

| Item (orchestrator, 22 Oct 2026, design A) | Change | Test (and the plant it catches) |
|---|---|---|
| Only practice rules map an unmeasured size to "no size limit", at the E4 boundary | `execution/quote_rules.py`: `QuoteRules.sizes` passes a measured size as recorded; unmeasured gives `math.inf` (no limit) under practice and `None` live; `desk_view.execution_snapshot(..., rules)` reads sizes through it. No sentinel number | `test_practice_fills.py`: a practice entry on an unmeasured quote fills at the same touch, units and charges as a measured one, and a practice exit closes (plant: practice gives no size; plant: the fill ignores its rules) |
| Live refuses an unmeasured quote at the fill with its own reason | `QuoteRules.size_not_measured` (live, unmeasured, and two-sided by a's rule); `desk_view.size_unmeasured` names those contracts; `entry_gate` names them `size_not_measured` before A4's problem; a fifth quote-gate law; `SchoolFills(..., rules=LIVE)` | the live port refuses the same entry `(size_not_measured,)` and a live exit waits; the live laws refuse it alone; conformance row for the new law (plant: the check dropped) |
| A quote missing a side's price stays one-sided | the reason needs `two_sided`, so a missing bid or ask (or `valid=False`) stays `one_sided_quote` under either rules | missing bid and missing ask on both ports; missing, no-ask and invalid under the practice laws (plant: the two-sided condition dropped) |
| Practice size and sell-back laws pass with the note | `QuoteGateLaw._note`: `size gate not tested in practice` only when a size law passed under practice rules on an unmeasured quote; a measured size is judged as live and carries no note | practice on unmeasured passes with the note on both size laws; measured too small refuses and measured enough passes, under both rules, with no note (plants: note dropped; note on measured sizes) |
| Live cannot reach practice; no sentinel | `PRACTICE` built only in `execution/practice_wiring.py` (`build_practice_fill_port`); `safety/practice_wiring.py` builds the laws with it through `laws_with` | AST test: only `simulator/` and the two practice roots import a `practice_wiring`, only the two safety roots call `laws_with`, `practice=True` only in the execution practice root; the live root's five quote laws are all `LIVE`; no `10**9` or `SIZE_GATE_WAIVED` in `fno/` |

- **Plants:** 6 planted, 6 caught (listed above).
- **a3's `check_ledger_reader` on `SchoolAccounts`** (part 3's promised conformance): `test_entries.py::test_school_accounts_pass_a3s_ledger_reader_check` (plant: entries cut to the first, caught).
- **Outside my files, for f's builder:** `tickets/shared_size.py` reads `ask_qty`/`bid_qty`, which are `None` on an unmeasured quote; under practice it should treat that as no size limit, as the fill port now does.

