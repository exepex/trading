# Judge 481: MS-P1f, tickets and the three counts

**Scope:** story/ms-p1-tickets at a8329a5e (builder session_01CmKJ6taCLzfEGg7wt6RC4N), diff 8c7ba1d9..a8329a5e only
(part a's round 2 is Judge B's). Story MS-market-school.md part f and "MS-P1f Claims". Lane 1. Round 1 of 2.
Judge K (session_019ZApRwkUiNMKDsf1k4W44z).

**Verdict: FAIL.** 2 should-fix, 2 minor. The ticket rules, the stops and the counts are right; the shared-size
criterion is not met end to end, and a plant on the running view survives.

## Criteria
| # | Criterion | Result | Evidence |
|---|---|---|---|
| 1a | Tickets come only from `classify()`, after the same laws | MET | `rules.py:24-37`; `TicketBook.enter` raises on a non-ticket and refuses on a binding law before any fill (`book.py:43-50`); plants 10, 11, 15 caught |
| 1b | Refused only by `ACCOUNT_LIMITS` gives `ticket: account_limit` | MET | `rules.py:44`; a's split in `constants.py:133-136`; plant 1 (stops added to the limits) caught |
| 1c | Daily stop and brake refuse, no ticket | MET | `first_binding_refusal`/`ticket_laws_pass` bind every non-account reason; plant 8 (brake relaxed) caught; minor b on the reason shown |
| 1d | Tickets never in an account, never in rupees | MET | own `TicketLedger` type; `account_net` filters `is_ticket` (plant 22 caught) |
| 1e | `FillResult.cash` used | MET | `book.py:24` is the only cash use; no copy of the arithmetic in `tickets/` (grep); plant 12 caught |
| 2, 4 | eligible >= fillable >= executed; refusals stay in the denominator | MET | `counts.py`; `scheduled` counts every row, duplicates refused; plants 16-20 caught; minor a |
| 3 | Shared displayed size counted; no report sums unservable fills | PARTLY | finding 2 |
| - | Gates | MET | see Notes |

## Findings
1. **Should-fix: no test pins that tickets stay out of the slot's running view.** Plant 2 (`classify` appends any
   non-refused decision, tickets included, to `accepted`) passes all 271 school tests. Real P1 path: the top-ranked
   rule is an `account_limit` ticket; with the plant its risk enters the bucket, open-risk and new-risk view of the
   next rule and takes one of the 5 places, so a valid trade is wrongly refused or ticketed. Expected: a test where
   an account-limit ticket ranks before a passing trade and the trade's check sees `accepted == ()`.
2. **Should-fix: criterion 3 holds only inside `allocate`; nothing that sums rupees uses it.**
   - `account_net` (`rupees.py`, "the only rupee sum") takes `OutcomeRecord`s and has no servability input, and
     `OutcomeRecord` carries none. Two accounts on one displayed size are both summed. The story's "a report sums
     only the servable fills" has no code path.
   - The fixed order is the driver id's sort order (`shared_size.py:39`): `CS1@1` always beats `REF@1`
     (`test_shared_size.py:25`), so the same driver loses every contention, and the comparison against the
     reference rule is biased by a name. Tickets enter by whatever owner label the caller gives, so a ticket can
     take the size an account trade needed.
   - Expected: the rupee sum excludes (and names) every outcome whose entry or exit was unservable, with a test
     of two accounts on one size; an order that favours no driver by name and serves account trades before tickets
     (or keeps tickets out of the allocation), or the orchestrator's recorded ruling on the order.
     [reasoning only on the fair order; the missing link is checked]

**Minor (fix with the round):**
- (a) Plant 21 survives: counting a trade's laws with the ticket rule. A trade never carries a refusal after
  `classify`, so it is untested rather than wrong; one `TRADE` row with an account-limit refusal pins it.
- (b) A braked driver whose open-risk law runs first is shown `refused: open_risk` (`test_rules.py:89`). The
  08:50 section then hides why the driver stopped. Prefer a `DRIVER_STOPS` reason when present.

## Plants
26 planted, 24 caught. Survivors: plant 2 (finding 1), plant 21 (minor a).

## Notes
- **Gates (my run, python3 with the routine setup):** pytest -n auto 10,356 passed, 16 xfailed (a first run with my plants running alongside had 14 kill-rerun failures; `tests/e2e` alone 42 passed, then the clean full run above); ruff check and format, check_imports, check_records clean; largest file 64 lines.
- The ticket-for-stopped-driver rule changed from the earlier story text ("or on a driver stopped for the day") by
  the orchestrator's ruling against reviews 138/139 ("relax only account-level cash/bucket limits"); section 3.2,
  the contracts table and part f now agree.
- With 5 roads and 5 new trades a slot, `trade_limit` tickets cannot occur in P1; only `account_limit` ones can.
- `TicketBook` records under the decision's `driver_id` in the ticket ledger; part j must set `is_ticket` on the
  outcome record from it, or `account_net` sums tickets. Worth a line in j's story.
