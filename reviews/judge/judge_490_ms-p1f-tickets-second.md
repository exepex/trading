# Judge 490: MS-P1f, tickets and the three counts (second judge)

**Scope:** story/ms-p1-tickets at f591ba21 (builder session_01CmKJ6taCLzfEGg7wt6RC4N), diff f591ba21^2 (4451a75b,
part a with the story) to f591ba21. The story's part f and its Claims. Lane 1, money piece: JUDGE.md "Two judges",
second judge, independent of Judge K (I didn't read K's verdict). Round 1 of 2. Judge H
(session_01KNkZVoWvXMkoihKrrXk5Xa).

**Verdict: FAIL.** 3 should-fix, 1 minor. The branch has since moved to a50caf62. After writing the findings below I
checked that tip only for whether each still holds (see the end).

## Criteria
| # | Criterion | Result | Evidence |
|---|---|---|---|
| 1 | Tickets: same quotes and laws, account limits relaxed; never in an account; never in rupees | PARTLY | `rules.py`, `book.py` (own `TicketLedger`), `rupees.py`; plants caught. Findings 1 and 2 |
| 2 | eligible >= fillable >= executed over a fixture day | MET | `counts.py:22-27`: fillable needs trade or ticket (both carry a proposal), executed needs fillable; 3 plants caught |
| 3 | Shared displayed size counted; no unservable fill summed | PARTLY | `shared_size.allocate`; 4 plants caught. Finding 3 |
| 4 | A refused ticket stays in the denominator | MET | `totals.scheduled` counts every row; duplicates refused (plant caught) |
| 5 | Conformance | MET (n/a) | f implements no port of a |
| - | Gates | MET | pytest -n auto: 10,358 passed, 16 xfailed. ruff check/format, check_imports and check_records are clean. Largest file is 64 lines |

## Findings
1. **Should-fix: a refusal is named by an account limit even when a binding law also refused.**
   - `_after_laws` uses `refusals[0]` (`rules.py:47`).
   - My run: `[bucket_cap, daily_stop]` gives `refused: bucket_cap`, and `[open_risk, max_loss]` gives
     `refused: open_risk`.
   - The record and both reports then say a cap stopped a trade that the daily stop, or the Rs 10,000 loss law,
     actually stopped. An account limit is exactly the reason that would have made it a ticket, so the record misleads
     on why there was no ticket.
   - Expected: the reason is the first binding refusal (a stop, then trade validity), never an account limit when a
     binding law refused, with a test for each mixed pair.
2. **Should-fix: no law results means every law passed (fails open).**
   - `classify` with a `check` that returns `()` gives `trade` (my run).
   - `ticket_laws_pass(())` and `first_binding_refusal(())` both let a ticket through, so `TicketBook.enter(...,
     results=())` fills it: the self-review's blocking case comes back through an empty tuple.
   - a's laws fail closed on bad input. The empty case should too: missing results are a wiring fault in j, not a
     pass.
   - Expected: an empty result set refuses or raises in `classify`, `TicketBook.enter` and `counts_for`, with tests.
     [reasoning only: a's contract has no list of law names; a non-empty check is the floor]
3. **Should-fix: who gets shared size is decided by the owner's name.**
   - `allocate` sorts by owner string (`shared_size.py:43`), so `CS1@1`, `DB1@1` and `DR1@1` always come before
     `N0@1`, `RC1@1`, `REF@1` and `WS1@1` on a contended contract.
   - The fills marked unservable fall systematically on the controls (RC1, REF), and on drivers late in the
     alphabet. That biases the driver-against-control comparison the card exists for.
   - Expected: an order no driver can win by its name (for example seeded per session, slot and road, recorded with
     the allocation), with a test that it doesn't follow names.

**Minor:**
- (a) `TicketBook.enter` takes `results` from its caller, beside the `SealedDecision`, and doesn't read them from the
  sealed `DecisionRecord.law_results`. j must pass the sealed ones. State it in j's story, or take the record.

## Plants
16 planted, 16 caught (one plant first failed to apply and was re-planted by line).

## Notes
- `counts_for` doesn't use `allocate`: a fill the shared size couldn't serve still counts as fillable unless j feeds
  the allocation back. a50caf62's `fill_status` (`unavailable: size_shared`) looks aimed at this; j should wire it.
- **At a50caf62, read after writing the above:**
  - Finding 3 is addressed: a seeded order, accounts before tickets.
  - Finding 1 is partly addressed: stops are named first, but `[open_risk, max_loss]` still gives `open_risk`.
  - Finding 2 is unchanged.
