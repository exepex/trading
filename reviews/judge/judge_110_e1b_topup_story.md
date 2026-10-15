# Judge 110: story E1b text, the capital top-up to Rs 20 lakh (quality rule 1; judge C)

Date: 15 Oct 2026 (UTC). Branch `story/e1-topup` at **d309de619c799035ce0b5f7486a5166d44437703** (text only:
`docs/stories/E-paper-desk.md` E1b, response 110). Checked against:
- the owner's "2 B" (15 Oct), "Paper account Rs 20 lakh" (14 Oct) and the orchestrator's "brake per book" (owner to
  confirm);
- judge 105 minor 4;
- the code it changes (E1 `fno/books/`, C2 `fno/risk/book_view.py` and `caps.py`, C4
  `fno/checks/validity_account.py`, P10 `home_inputs.py`, S2 `reconcile.py`).

## Verdict: FAIL (text), 1 should-fix; 3 minor

The design is right:
- **History stays as written.** A new ledger kind is appended; nothing earlier changes.
- **The amount is computed**, never typed.
- **The brake is unaffected by algebra.** Capital is constant across the closed-equity series, so a top-up shifts the
  whole series and never makes a new high. Drawdown is measured on profit and loss only.
- **Refusals cover the risky states:** an open position, already at size or above it, not started, no lock.
- **C4 reads the ledger independently.**

I checked the reader list against the code. `grep` for `starting_cash`, `LEDGER_OPENING` and `opening_row` outside E1
finds exactly the readers it names: C2 `caps.py:100` and `book_view.py`, C4 `validity_account.py`, S2
`reconcile.py:30`, P10 `home_inputs.py:52`.

## Should-fix

**1. A top-up must carry its time, and count only from that instant.**
- **The gap.** The story dates a top-up by day: "capital ... dated on or before a day"; C2 uses "capital (as of the
  decision day)". C4's own ledger read (`_filled_by`, `validity_account.py:61-63`) treats a row with no time zone as
  filled by the cutoff for the **whole day**.
- **The consequence.** Say a top-up is run at 17:00 IST on session day T, after that day's 15:00 decision:
  - live, at 15:00, the book had Rs 5 lakh and was refused by `paper_account`;
  - any later C4 or C2 recomputation of T (D3's replay, an audit) sees Rs 20 lakh and passes.

  The record and its replay then disagree, the point-in-time failure the project guards against everywhere else.
- **Fix.**
  - The `capital_top_up` row's `filled_at` is the write instant, time-zone aware in IST.
  - Capital is "the opening plus top-ups written at or before the decision cutoff", in E1, C2 and C4 alike. C2 takes the
    cutoff it already uses; C4 its `cutoff`. P10 can stay by day (end-of-day figures).
  - Test: a top-up at 17:00 on T is not capital for T's 15:00 decision, a replay of T still refuses, and the top-up
    counts from T+1 (or from a later same-day cutoff).
  - Alternatively, the command refuses on a session day between 14:50 and the end of that day's fills, and the
    timestamp rule still applies. Either way, say which.

## Minor

1. **Say what the amount is.** It restores **capital**, not cash or equity: amount = target − capital. A book with
   realised losses before the top-up keeps them. That is correct, and the text should say so in criterion 1, so nobody
   later "tops up to Rs 20 lakh of equity".
2. **Name the source of the target.** The command's target is `risk.profiles.books.paper_account_rs`, so a later config
   change would allow a second top-up. Raising that number is a lane-1 config change and an owner decision, and a second
   top-up should be named as such in its output line. One sentence.
3. **C4's opening check must accept top-up rows after the opening.** `account_facts` requires row 0 to be the opening
   and treats every other row as a fill (`_trades(rows[1:])`). The design says capital rows "never count as trades", so
   criterion 5 should include a C4 test with a top-up row between two fills (today that row would be parsed as a fill
   and fail on `trade_id`/`side`).

## Project rules

- Lane 1: E1 money records and the `journal/` data. The run on the real journal is by the orchestrator or the owner
  after the merge, never by the builder, and committed and judged as data.
- Order: built on `main` after C5 merges (orchestrator's decision), since it renames `starting_cash`, which C5's
  `PaperAccountSize` reads.

**Verdict: FAIL for d309de619c799035ce0b5f7486a5166d44437703** (story text) on should-fix 1. A re-check needs only the
capital definition, criteria 3-5 and the C4 design line.
