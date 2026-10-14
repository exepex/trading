# Judge 83: story C4, hard-validity checks (branch, before merge)

Date: 14 Oct 2026 (UTC). Branch `story/c4-hard-validity` at 3f311f8 (7e1bc8c merged with main; draft PR #96). Claims:
`reviews/claude/response_83_c4-hard-validity.md`. Story: `docs/stories/C-code-roles.md` C4.

## Verdict: FAIL, three must-fixes

The independent arithmetic is good:
- a payoff grid in place of the proposer's formula;
- charges read from the table directly;
- 12 reference vectors;
- the override always refused;
- books 2 and 3 failing closed.

But:
- **my own wrong proposal passes**: a wrong lot size with a consistent claim;
- three of C2's limits are trusted, not recomputed;
- tampering with the snapshot's sidecar is untested.

## Gates (my runs, `python -B`, caches cleared)

- Full suite: 2,649 passed. Ruff and imports: clean.
- `git merge-tree` with `main`: clean.

## The story's own check: my new wrong proposal

**Wrong lot size, consistently claimed.**
- The proposer prices a correct SF for NIFTY's old lot of **75 units** (the current lot is 65), and its claimed
  maximum loss is consistent with 75 units: Rs 4,056.23 against the correct trade's Rs 3,540.57.
- **C4 passes it.** `ValidityProposal.lot_size` comes from the proposal, and C4 recomputes the loss with the same
  number of units, so a wrong lot size is never seen.
- A wrong lot size scales every rupee of risk, margin and P&L, and lot sizes change (NSE revises them).

**Must-fix 1:** check the lot size against an independent source: NSE's own contract data for the day, or the
committed `config.yaml` `lot_sizes` with its date and source. Add a seeded wrong proposal with a lot of 75.

## My plants (`tests/checks` and `tests/decisions`, 129 tests)

| Plant | Result |
|---|---|
| The loss tolerance at Rs 5 | caught (4 failed) |
| The legs' cutoff not checked | caught (1 failed) |
| STT charged on purchases too | caught (33 failed) |
| Exit charges left out of the maximum loss | caught (34 failed) |
| The "permitted on the day" check off | caught (2 failed) |
| The date check off | caught (3 failed) |
| **The sidecar (meta) hash not compared** | **not caught** |

**Must-fix 2 (criterion 4):** the sidecar holds the capture's start time, which the date and cutoff checks use. A
sidecar rewritten to move a late capture before the cutoff must fail. Add a test with a tampered sidecar and the quote
file intact.

## The orchestrator's points: rulings

1. **"All C2 limits": must-fix 3, for all three trusted limits, not only margin and stress.**
   - Today C4 recomputes the maximum loss per trade and the open-trade count. It takes the drawdown brake, the stress
     limits and the margin room from C2's recorded verdicts (`risk_verdicts_ok`, a boolean).
   - That is not independent: a C2 bug that passes a trade passes C4 too. Criterion 1 ("a limit breach is blocked")
     and the story's "all C2 limits" are not met.
   - C4 must recompute each from raw inputs with its own arithmetic:
     - the drawdown brake from the book's committed ledger;
     - the stress losses from the legs, on its own pricing grid;
     - the margin room from the margins file and the account.
   - Margin is where today's A14 work found real errors. Write it on A14's three-part format (scan, NOV, exposure;
     judge 75) once A14 merges, or now on the current format with the test updated when A14 lands.
   - One seeded breach per limit.
2. **The contract with E3: they fit, on one condition.**
   - C4 runs inside D3's decision run, on the common pack's A4 snapshot (`PackCaptures` with
     `PackSnapshotSchedule`). Those are the mids D2 priced with, and C4's verdict is stored in the record
     (`validity.c4`).
   - E3 fills at the 15:15 execution capture, whose mids differ from the 15:00 ones. **E3's `ValidityGate` must read
     the committed decision record's completed C4 pass.** It must never re-run C4 against the execution capture: that
     would fail every leg's "price equals the mid" check and block every trade.
   - Say this in both stories. E3's next round must implement the gate that way, with a test.
3. **The monthly expiry as the latest listed expiry of its month in the snapshot: accepted for now, as a stated
   limit.**
   - A4 records only the monthly chains it chose, so the rule agrees with A4. But it is not independent of A4's
     expiry choice: if A4 picked a wrong expiry as "monthly", C4 would accept it.
   - Should fix: check against NSE's own listing (A5's listed expiries from the F&O file).
4. **My new wrong proposal:** the lot size of 75, above. Not caught; must-fix 1.

## Per criterion

| # | Criterion | Result |
|---|---|---|
| 1 | Seeded wrong proposals blocked, a limit breach included | **PARTLY**: 17 seeded ones are caught, but the trusted limits and the lot size are not checked (must-fixes 1 and 3) |
| 2 | A correct proposal passes with every check's numbers | MET (3 structures) |
| 3 | No path turns a failure into a pass | MET (`override` raises for owner, desk and judge) |
| 4 | Tampered and absent evidence fail | **PARTLY**: the quote file's hash and a missing file are tested; the sidecar is not (must-fix 2) |
| 5 | At least 10 reference vectors, to Rs 0.01 | MET (12; I did not recompute them by hand) |
| 6 | Constitution mode | Fails closed until D5 (`WaitsFor`); not checkable yet, as stated |
| 7 | Book 2 envelope | Fails closed until D4; as stated |

**Independence:** `validity_money.py` imports nothing from `fno.costs`, `fno.research_engine` or `fno.risk` (test, plus
the builder's fresh-interpreter check). My plants on the charge formula are caught by the reference vectors.

## Project rules

- New modules in `fno/checks/`, wired in `fno/checks/wiring.py` (listed in CLAUDE.md).
- D3's `validity.c4` is filled.
- No orders and no secrets.
