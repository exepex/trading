# Response 70: story E4, fill model and exits: builder's claims

Builder session, 14 Oct 2026. Story: `docs/stories/E-paper-desk.md` E4. For the judge (`docs/JUDGE.md`) and ChatGPT.

**Verdict in one line:** E4 is built as `fno/desk/` (9 modules, 845 lines, largest 129), 32 tests in `tests/desk/`,
15 of 15 planted defects caught. Paper only: the desk reads recorded A4 quotes and never touches a provider or broker.
Two money-safety points are open for E3 and the owner (section 4); I did not build past the story text on them.

## 1. What was built

| Module | Job |
|---|---|
| `snapshot.py` | Reads one A4 capture **by snapshot ID** (E3's 15:15 capture is not the canonical one): bid, ask, sizes, A4 `valid`, `quote_age_unknown` (no provider timestamp). Refuses a quote file whose SHA-256 differs from the recorder's `csv_sha256`, a meta naming another ID, a capture from another day, a contract recorded twice. Interface `ExecutionSnapshotSource`, adapter `RecordedExecutionSnapshots`. |
| `pricing.py` | One leg against the snapshot: buy at the ask, sell at the bid, only on a valid quote whose size at the touch covers **all** units (no partial leg fills). Pad = 0: crossing the spread is the slippage. |
| `execution.py` | Point-in-time guard; priced leg -> E1 `Fill` (C1 charges via `Fill.priced`, never re-implemented) + desk row; closing order (shorts bought back first, protection sold only when no short is left); legging cost. |
| `entries.py` | `EntryDesk.enter(order, snapshot, journal)`: gates, then protection first, then shorts; first failure unwinds what filled at the same snapshot. |
| `status.py` | Open positions derived from E1's ledger + desk events (no extra mutable state): exit ordered, protection unverified. |
| `exit_rules.py` | `ExitRule` strategy: `ProfitTarget`, `StopLoss` (on net if closed now at the touch, every charge included), `TimeExit` (N calendar days before expiry; 0 = expiry day). Numbers come from the playbook (D1). |
| `exits.py` | `ExitDesk.review(book, snapshot, journal, rules)`: settlement check, protection check, exit rules, close or pending exit, alerts. |
| `records.py`, `csv_log.py` | `journal/<book>/account/desk_fills.csv` and `desk_events.csv`, append-only, idempotent by ID, crash-safe; writes only through the book's locked E1 writer. |
| `wiring.py` | Composition root (added to CLAUDE.md's list). |

E1 change (behaviour unchanged, its 119 E1+C2 tests pass): the crash-safe file helpers moved from `fno/books/account.py`
to `fno/books/files.py` so the desk reuses them (DRY), and `AccountWriter._check_lock` became public `require_lock`.

## 2. Acceptance criteria, claims and evidence

| # | Criterion | Claim | Test (all in `tests/desk/`) |
|---|---|---|---|
| 1 | Fill price = snapshot ask (buy) / bid (sell), hash in the row | Met. Hand computation: fly premium (150 + 140 - 71 - 60.5) x 65 = Rs 10,302.50, cash = 5,00,000 + premium - C1 charges of the 4 fills; each row carries snapshot ID, the SHA-256 recomputed from the stored file, decision ID, `quote_age_unknown`. A `last` of 999 in every row is never used. | `test_entries.py::test_each_fill_is_at_the_snapshot_ask_or_bid_with_its_hash_and_protection_first` |
| 2 | Failed short after protection: unwind, legging cost, not opened | Met. Unwind order: short bought back at the ask first, then protection sold at the bid. Legging cost = Rs 162.50 of spread (hand) + 6 orders' charges; E1 shows the trade closed. Also: second protective leg failing after the first (unwind, nothing opens); an unwind leg without bid size stays as an exit order. | `test_a_short_leg_failing_after_protection_unwinds...`, `test_a_second_protective_leg_failing...`, `test_an_unwind_leg_without_bid_size...` |
| 3 | Missing exit quotes: pending exit + alert, never last/stale | Met. The quoted short is bought back; the unquoted short is pending; protection is **held** (never sold while a short is open); alert sent once; next snapshot closes the rest. | `test_exits.py::test_missing_exit_quotes_give_a_pending_exit...` |
| 4 | Unquotable protection: `protection_unverified`, book opens no new risk until resolved, closed only when every exit fill is recorded | Met. Book 1's next entry is refused naming the trade; Book 2 is not blocked; after the next valid quotes close every leg, Book 1 opens again. | `test_unquotable_protection_marks_the_position...` |
| 5 | Exit rule reached closes at the next valid quotes and records it | Met for target, stop and time. Net if closed is checked against a hand computation (the rule fires exactly when its threshold is crossed by Rs 0.01). Price rules are not judged at the snapshot that opened the trade. | `test_an_exit_rule_reached_closes...` (4 cases), `test_price_rules_are_not_judged...` |
| 6 | Never calls an order function | Met. AST: no `fno/desk` module imports a provider or `growwapi`, none calls `place_order`/`modify_order`/`cancel_order`/`order`. Run: a full entry + exit through `wiring.py` with `get_provider` and `growwapi` replaced by a trap that fails on any attribute: zero calls. | `test_safety.py` (2 tests) |

Beyond the criteria (asked by the orchestrator or found while building):
- **C2 is not bypassed (issue #85):** an entry needs an ok C2 `RiskDecision` for the same book, trade and day. Tested
  with the real `build_risk_manager` and a margin row of 1 Sep 2026: C2 refuses ("older than 7 days"), E4 fills
  nothing and records `not_opened` with C2's reasons; with a 13 Oct row the same trade opens.
- **Point in time:** a snapshot that finished after the run's clock is refused before anything is written ("a plant
  that fills at a later quote" is mutation 1 below); a decision committed at or after the execution snapshot started
  is refused; an exit is never priced from a snapshot older than the position's last fill.
- Incomplete snapshot: no new risk. Expired leg before its exit: `settlement_needed` + alert, never priced.
- Reruns repeat nothing (entry and exit review; E1 fill IDs `<trade>:<open|unwind|close>:<contract>`); a half-written
  desk line is dropped; desk writes without the lock are refused; desk files stay in the book's account folder.

## 3. Mutation check (each planted defect must fail a test)

`scratchpad/mutate.py` (not committed) planted 15 defects one at a time and ran `tests/desk`: **15 caught, 0 missed**:
fill at a later quote (clock check removed), fill at the last price, fill at the mid, C2 refusal ignored, size check
removed, invalid quote accepted, protection sold before shorts closed, protection_unverified not blocking, hash not
checked, decision after snapshot accepted, older snapshot accepted for exits, no unwind on partial fill, shorts filled
first, expired leg priced, price rules judged at the opening snapshot.

## 4. Open points (honest limits; not built, for E3, the orchestrator or the owner)

1. **Max loss at execution prices (money safety; some evidence).** C2 approves on the decision snapshot's mids with
   B2's Rs 1 pad; E4 fills at ask/bid, possibly 15 minutes later. With half-spreads above Rs 1 or a move, the real
   worst case can exceed Rs 10,000 while C2 said "within" (4 legs x Rs 2 extra x 65 units = Rs 520). E4 does not
   re-run C2 (building C2's `Market` with per-leg IV from a snapshot is E2/E3 work). **Proposal:** E3 re-runs C2
   and C4 on the execution snapshot before calling E4. Asked the orchestrator (alternative: an entry price limit in
   E4); building nothing until decided.
2. **Shared liquidity across books (reasoning only).** Each book sees the full displayed size; three books buying the
   same contract at one snapshot could together exceed it. Kept so books never affect each other's fills (12.6
   firewall), but it is optimistic for scoreboard B.
3. **Size units:** A4's `bid_qty`/`ask_qty` are taken as units (contracts x lot size), as Groww's and NSE's quantity
   fields are understood (reasoning only, not verified against a live Groww response). If they were lots, the size
   check would be too strict (safe side).
4. **Settlement at expiry is not modelled:** a leg still open after expiry is reported (`settlement_needed`), never
   priced. Holding to expiry needs NSE's final settlement price as an input: a follow-up if any playbook holds to
   expiry. A `TimeExit(0)` exits on expiry day at the 15:15 quotes.
5. **A partial exit leaves quoted shorts closed and the rest pending**; the pending legs keep risk overnight (bounded
   by the held protection). That is the story's rule; E6 measures pending-exit delays from `desk_events.csv`.

## 5. Checks run on the merged tree before push

`python -m pytest -q` (full suite), `ruff check fno tests tools`, `ruff format`, `python tools/check_imports.py`:
results in the commit message and the message to the orchestrator.
