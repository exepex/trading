# Response 195: story E4d, a book's entries at one snapshot share its displayed size (story text for the judge)

Builder: Claude (E4c's builder; the orchestrator gave E4d to this session on 15 Oct 2026). Branch
`story/e4d-shared-size`, started from E4c's head `b1de45e9` because E4d extends E4c's `entry_problems`. Until E4c
merges, this branch's diff against `main` includes E4c. Story text first; the code is in addendum 1.

## Why (strong evidence: code read)

- `entry_problems` checks one entry's legs on their own (`fno/desk/entry_check.py`).
- `DeskSteps.fill` loops over a book's orders at one snapshot (`fno/desk/daily_steps.py`).
- Book 1's orders are every traded opportunity of the day (`fno/books/book1_orders.py`).

So two approved strategies that share a contract would both fill against size only one could take. ChatGPT review 123
(Q2) named this, and the orchestrator chose to fix it rather than list it.

## Design choices for the judge to check

- **No new state.** The units a book has already taken come from its own committed desk fill rows at this
  `snapshot_id`. That makes a rerun count the same units, because fills are idempotent by fill ID.
- **The protective sell-back need is counted on the bid side,** so the capacity E4c checks stays honest across
  entries. Reasoning only: this is conservative, since that sell-back is not an order. The alternative is to count only
  real opening fills. I chose the conservative rule because E4c's purpose is that every bought protection can be sold
  back at that snapshot.
- **The new code is recorded only when the leg would pass alone.** E4c's codes keep priority, so the reason names the
  true cause.
- **Never pooled across books or shadow accounts** (E1's firewall).

**Renamed from response 193** (orchestrator, 15 Oct): 193 is the S3/S6 ChatGPT request. Numbers now come from the
orchestrator.

## Addendum 1: the code (after judge 201's story-text PASS)

Branch `story/e4d-shared-size`; `main` (with E4c) merged in, one README conflict (both lines kept). Judge 201's two
notes are folded into the story text: the records are kept in Drive after each entry (E2c), and every fill row at the
snapshot counts by its side, an unwind's closing fills included.

**What changed**
- `fno/desk/entry_check.py` (87 lines):
  - `taken_units(fill_rows, snapshot, trade_id)` returns (contract, side) to the units the book's other trades took at
    this snapshot. Every row counts by its side (buy = ask size, sell = bid size). Each protective leg still held adds
    its sell-back need on the bid side: units bought, less the units sold back by any later row of the same trade and
    contract at the snapshot.
  - `entry_problems(..., taken=None)`: a side that fails alone keeps E4c's code; one that fails only with the units
    already taken records `size_shared_in_book`.
- `fno/desk/entries.py`: `EntryDesk.enter` reads its own journal's fill rows, so only this book's records count.
- `fno/constants.py`: `SIZE_SHARED_IN_BOOK` (344 lines).
- `tests/desk/conftest.py`: the guard double `check_passed` takes the new optional argument.

**One tightening of the story text (judge, please check):** a row counts only if both its `snapshot_id` and
`snapshot_sha256` match the snapshot. The id alone could repeat across days (the tests reuse "exec"). The hash pins the
exact recorded snapshot, and every fill row at it carries that hash (`FillMaker.record`). The story text now says so.

**Tests:** `tests/desk/test_shared_size.py`, 13 tests.

| Criterion | Test |
|---|---|
| 1 | 65 + 65 against bid size 100 (the orchestrator's fixture), 129: the second is `not_opened`, reason `size_shared_in_book (<contract>, 65 units, 65 already taken in this book at this snapshot)`, `refused_by_check`, no fill or ledger row; 130 and 131: both open |
| 2 | the same two flies in Book 1 and Book 2: both open |
| 3 | two lots (130 units) against 100: E4c's `short_leg_not_sellable`, 130 units |
| 4 | a rerun of both: the same outcomes, no `refused_by_check`, fill rows unchanged. A crash after t1's fills and before its event: the rerun opens t1 and nothing fills twice |
| 5 | a long call holds 25200 CE (no sell row), and a later vertical sells 25200 CE at the bid: refused at bid size 129, opens at 130 |
| 6 | no number in the event row is a bid, ask or size of the snapshot |
| 7 | `entry_problems` with no map, or an empty one, equals E4c's result; all 26 E4c tests pass unchanged |
| judge 201 | `taken_units` unit test: an unwind's sell-back and buy-back rows counted, a sold-back wing holds nothing, another snapshot id, another hash and the trade itself left out |

**Plants (8 of 8 caught):**
1. the trade counting itself (2 failures);
2. no sell-back need (2);
3. no hash match (1);
4. taken ignored (4);
5. unwind rows skipped (1);
6. the shared code before E4c's (1);
7. no protective closing-side check (10);
8. sold-back units not subtracted (1).

**Gates:** `ruff format`, `ruff check fno tests tools`, `python tools/check_imports.py` clean. The full suite with
`-n auto` on the merged tree: see the message to the orchestrator for the exact SHA and count.

**Honest limits**
- **Reasoning only:** within one entry no two legs share a contract in STR1's structures (fly, LC, LP, CCS, PCS), so
  an entry's own legs are not summed against each other.
- **Test-only shape:** the criterion-5 test sells 25200 CE with a vertical labelled CCS that buys 25000 CE. The check
  reads only legs and sides, and the decision market has no 25400 quote.
- **The alert:** it is E4c's path (`refused_by_check`, tested in `tests/timetable/test_entry_check_alert.py`). E4d sets
  the same field and does not add a second timetable test.
- **Out (unchanged):**
  - exits at the same snapshot (they run after the fills);
  - pooling across books;
  - a short leg's buy-back depth.
