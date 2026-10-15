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
