# Judge 507: MS-P1j, the fleet join-up (first judge)

**Scope:** story/ms-p1j-fleet at 7f757504 (builder session_01CmKJ6taCLzfEGg7wt6RC4N); the MS-P1j section and its
Claims. It covers `fno/school/fleet/*`, `fno/school/wiring.py`, `fno/school/cli.py`, two lines in `fno/cli.py`, the
tests, and two touches of f (`OwnedFill.is_exit`; `TicketBook.price`/`open`/`close`). Lane 1, money piece (fills,
exits, records): first of two judges, independent of judge K. Round 1 of 2. The builder's round-3 list (already ruled
by the orchestrator) is not re-raised.

**Verdict: PASS.** Nothing blocking, no should-fix. Notes below.

## Gates (my run)
- pytest -n auto: 11795 passed, 9 skipped (the real acceptance test until d's `entries` merges), 16 xfailed.
- `ruff check`, `ruff format`, `check_imports` and `check_records` (8372 files) are clean.

## The three checks asked for
1. **A crash anywhere between the seal and the counts' commit is completed once.**
   - A sealed session is never decided again: `dashcam.find(DECISIONS)` leads to `_finish`.
   - `_finish` is rebuilt from the sealed records and the ledgers (`Recorded`). A recorded opening or closing is read
     back, never re-priced. A recorded position is never opened again. Outcomes and drift are each sealed once. The
     counts are write-once, so other text raises `ReplayConflict`, never a silent overwrite. A crash after the counts'
     write only commits.
   - The size allocation is seeded by (session, slot, road), so a rerun serves exactly what one clean run would.
2. **Entries before exits.** `allocate` ranks (is_exit, is_ticket, seeded owner). An account entry it cannot serve
   is `size_shared` and stays in the denominator. A ticket it cannot serve is not opened. An exit it cannot serve
   fills nothing and waits. No ledger holds an unservable fill.
3. **Pairing and settlement.** A decision of another driver, road or session, or a position of another driver or
   reviewed on another road's snapshot, makes that driver's whole slot `unavailable: driver_error`, never an exit.
   Expired positions settle before the session's first `view`, and the settlement exit records are sealed with the
   decisions.

## Plants: 11 on the fleet, 8 caught
- **Caught:** recorded entries re-priced; recorded entries opened again; an exit closed without size; an unservable
  entry recorded; exits ranked with entries; the counts never written; settlement after the first view; a rerun
  skipping the finish.
- **Survived, equivalent today:**
  - Recorded exits re-priced: a closed position is no longer in `still_open`, so the recorded fill is used anyway.
  - Outcomes sealed every run: sealing the same records again is a no-op, and outcomes are rebuilt deterministically
    from the ledgers.
  - The commit-only branch removed: before 15:30 the counts' write is a same-text no-op that then commits.
    - After 15:30, refused entries would re-price as `stale_seal` and the write would raise `ReplayConflict`, so the
      branch matters there. Round 3's "rerun after 15:30" test should also kill this plant.

## Notes (no action in this round)
- **Margin time inside the first driver's limit.** The first margin check of a session downloads and parses the SPAN
  file inside the first driver's 60-second limit. I measured it on 21 Oct: download 9.1 s for 9.1 MB, and 2.3-2.6 s
  to parse each of the four indices, about 19 s in all. That is inside the limit, but a slow Drive day could time out
  the first driver alone. Warming the margin before the driver loop would remove the case [reasoning only].
- **Unmeasured sizes (a3, for SIM-c).** `_displayed` reads a missing size as 0, so a quote whose sizes were not
  measured can never serve a fill in `allocate`. That is correct for live fills. The simulator must not route its
  unmeasured history through this allocation, or every simulated fill becomes `size_shared`.
- **The real acceptance test** (9 cases) skips until d's `SchoolAccounts.entries` (judge 488.4) merges. I did not
  see it pass. That should be shown before j merges.
