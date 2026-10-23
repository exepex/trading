# Judge 534: O9b step 2, the G4 margins to Drive, text and code (story/o9b-margins @ 162df9c8)

Judge F. Round 1 of 2. Lane 1 (money and risk inputs: C2's and C4's margin reads; Drive; two workflows). Labels:
**strong**, **some**, **reasoning only**.

## Verdict: PASS. It may merge in the stated plan. 1 note.

The plan: Tue 27 Oct 11:00-13:30 IST, after step 1b merges and `main` is merged in, with `margins move` before and
after, and the orchestrator's go.

Gates on 162df9c8: **14584 passed, 0 failed**, 1 skipped, 16 xfailed; ruff, ruff format (2337), `check_imports.py`
and the record scan (8783) are clean.

Checked in the code:
- New port `TableSource` (`FileTable`, `ReceiptedTable`). `ReceiptedTable` turns any `RuntimeError` or `OSError`
  (Drive's network included, the step 1b lesson) into `TableUnavailable`, naming the class only.
- **C2** (`fno/risk/margins.py`) raises `RiskInputError` and **C4** (`validity_margin.py`) raises `MarginProblem`, so
  an unreadable table refuses the trade: fail closed, no fallback (owner, 23 Oct).
- Both read one config key, `risk.margins.table`.
- A14c's evidence CSV goes through `ReceiptedSnapshots` before its factor row, so the row's `evidence_sha256` is the
  receipt's.
- The workflows commit receipts only.
- The two blocking points from the owner's A14/C2/C4 review are built in:
  - the catch-up move (step 1b's shared files);
  - a part without its last newline is refused at write and at read (`TableFileBroken`).
- Evidence files move with `exact=True`, never caught up.

## Plants (each reverted)

| # | Plant | Caught |
|---|---|---|
| 1 | `ReceiptedTable` catches `RuntimeError` only (a network error escapes) | yes, 1 failed |
| 2 | C4 fails open: an unreadable table gives no rows | yes, 1 failed |
| 3 | C2 fails open: an unreadable table gives no rows | yes, 3 failed |
| 4 | the read-side last-newline guard off | yes, 2 failed |

## Note (for the owner, not a finding)

From the merge on, a Drive outage at decision time refuses every trade that needs a margin (C2 and C4 fail closed).
This is the owner's 23 Oct choice ("no fallback") and the safe direction. It means Drive's availability is now a
trading-day dependency, so a Drive sign-in that expires (O9's known risk) stops the desk until it is renewed. The
data-checks job and C4's own refusal lines make it visible the same day [reasoning only].

After the merge (quality rule 8):
- the first `nse-margins` and `stress-factor` scheduled runs on the Drive path;
- the first desk day's C2 and C4 margin reads.
