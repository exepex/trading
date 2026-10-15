# Response 110: story E1b, capital top-up to the Rs 20 lakh account (story text for the judge's check before code)

Builder: Claude, 15 Oct 2026. Branch `story/e1-topup` from `origin/main` (5a86aad). Story text:
`docs/stories/E-paper-desk.md` section E1b. Lane 1 (money: E1's ledger, C2, C4). Per quality rule 1 this push holds
the story text only; code starts after the judge's check passes.

## What the story does, in short

- **A new ledger entry kind, `capital_top_up`:** a dated row appended once per book. It brings the book to the books'
  `paper_account_rs` (Rs 20 lakh, a Rs 15 lakh top-up for each committed book); the 13 Oct opening rows are untouched.
- **Capital is the opening plus top-ups dated on or before a day.** Every reader of the old "starting cash" moves to
  capital: E1, C2 (risk view, `paper_account`), C4 (its own ledger read), P10 (Home's profit and loss) and S2's
  reconciliation.
- **The brake measures drawdown of profit and loss only.** The capital is constant across the closed-equity series, so
  a top-up never makes a new high and never lifts a braked book.
- **A command, `python -m fno account top-up`, computes the amount** and refuses a book at size, above it, not started,
  or with an open position. The orchestrator or owner runs it once after the PASS and the merge; I never run it on the
  real journal.

## Choices the judge should check (my reasoning, labelled)

1. **Capital is constant across the brake's series (shift, not step).** A step on the top-up day would make the top-up
   a new high: wrong per judge 105 minor 4. A constant shift keeps the drawdown identical to profit and loss. Reasoning
   only, tested in criterion 4.
2. **A top-up is refused while the book has open positions.** The day's equity row is written from the unmarked state,
   which is exact only for a flat book. All three books are flat today (no fill ever made), so this costs nothing now.
   Reasoning only.
3. **The amount is computed (size − capital), never typed.** This removes the chance of a mistyped Rs 1,50,000. If the
   books' size changes later, a new top-up brings the book to the new size; a decrease is refused (out of scope).
4. **The entry is idempotent by its day (`top_up_<date>`) and by "already at size".**
5. **`starting_cash` is renamed `capital`** in E1's state and every reader, because the name would otherwise lie
   (CLAUDE.md: names say what things do). This touches C2, C4 (own read), P10 and S2 code; all are in the gap list.

## Depends and blocked

- The code needs C5's `paper_account` rule and the books profile (`story/c5-risk-buckets`, judge C re-checking
  b929743). I will build on main once C5 is merged, or on C5's branch if the orchestrator prefers.
- Running the command on the real journal is not mine to do: lane 1 data, after the merge.

## Questions for the owner

None new. The per-book reading of the brake is the orchestrator's decision, owner to confirm, as in C5.

## Addendum 1: judge 110 (FAIL on d309de6, 1 should-fix, 3 minor), each checked

| Item | My check | Change to the story text |
|---|---|---|
| SF1: a top-up dated by day counts for the whole day | True. C4's `_filled_by` (`fno/checks/validity_account.py`) counts a row without a time zone for the whole cutoff date, so a 17:00 top-up would pass a replay of that day's 15:00 decision that was refused live | The row's `filled_at` is the write instant (IST, offset included). Capital = the opening plus top-ups written at or before the decision cutoff, in E1, C2 (the day at `DESK_DECISION_TIME`) and C4 (its cutoff). P10 stays end of day. Criteria 1, 3 and 5 test 17:00 against 15:00 on T and T + 1, and 10:00 on T. I chose the timestamp rule alone, not a time-window refusal: one rule, no second mechanism (reasoning only) |
| Minor 1: amount restores capital, not equity | Agreed | Scope and criterion 1 say so, with the Rs 10,000-loss example |
| Minor 2: target source; a second top-up | Agreed | Scope names `risk.profiles.books.paper_account_rs`; raising it is a lane-1 config change and an owner decision; criterion 8's output line names "a further top-up" |
| Minor 3: C4 parses a top-up between fills as a fill | True: `account_facts` runs `_trades(rows[1:])` over every row after the opening | C4 design line: trades only from fill and settlement rows; criterion 5 tests a top-up row between two fills |

**One disagreement, stated:** judge 110's project-rules section says the real-journal run is "never by the builder".
The orchestrator's later instruction, citing the owner's rule of 15 Oct 2026 ("1 B": builders run their own
commands), is that I run it after the merge and record its output. The story text follows the owner's rule and says
so.
