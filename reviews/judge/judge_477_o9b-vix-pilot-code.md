# Judge 477: O9b step 1, the VIX pilot, text and code (story/o9b-vix @ 05543aae)

Judge F. Round 1 of 2. The umbrella text passed in judge 475 add. 1. Step 1's text, its gap list and the claims are in
`docs/stories/O9b-static-data-to-drive.md`. Lane 1 (Drive, a workflow).

## Verdict: PASS. It may merge in the builder's stated order. 1 minor.

The order: move, then `data-cache sync` and `pytest -m data` green, then merge once `main` is green, then the first
scheduled run, then the removal commit with `.gitignore` and the hook refusal.

Gates on 05543aae: **9839 passed, 1 failed**; ruff, ruff format (1862), `check_imports.py` and the record scan (8001)
are clean. The failure,
`test_v4rules_phase2.py::test_every_committed_g7_record_row_carries_this_trees_method_hash`, is not this branch's:
- it fails the same way at the branch's merge base (b0b5135d);
- it passes on today's `main` (e0a4ac46);
- merging `main` in before the merge clears it.

Checked in the code:
- `ReceiptedRowLog`: write-once parts named by run id. The rebuilt table is the first part whole plus each later
  part without its header, so it equals the moved file byte for byte. A run with no rows writes nothing.
- `ReceiptedSnapshots`: the newest is current.
- Both read only through `DriveCache.sync` and refuse an incomplete cache (`DriveDataUnavailable`).
- `move_into`: a second move is a no-op; Drive holding other bytes refuses, overwriting nothing; read-back is
  verified.
- A17's `RowLog` port is moved, not copied.
- `vix-history.yml` commits receipts and manifests only.
- `data-checks.yml`: read-only, an explicit `failure()` alert step (O10 sees it), on capture-watch.
- `-m data` overrides `addopts`' `not data`.

## Plants (each reverted)

| # | Plant | Caught |
|---|---|---|
| 1 | later parts keep their header line | yes, 2 failed |
| 2 | an incomplete cache read anyway | yes, 2 failed |
| 3 | the move overwrites differing Drive bytes | yes, 1 failed |
| 4 | a run with no rows writes a part | yes, 1 failed |
| 5 | the oldest snapshot read as current | yes, 1 failed |

## Minor

**The window between the move and the merge [reasoning only].** Until the merge, `main`'s old `vix-history.yml` still
appends to the repository file. A run in that window (a month's rows land on the 1st) would leave Drive's first part
without those rows. The move command catches this (`DIFFERS`), so:
- re-run `vix-history move` right before the merge, and merge only on `already in Drive, equal`;
- don't let the window cross 1 Nov.

After the merge (quality rule 8): cite the first scheduled run and the first `data-checks` run.

**Note (no new number): head dafedbe3.** Beyond merges of `main` (other judges' changes), the only change since 05543aae is one
import line in `fno/storage/row_log.py` (`from .raw_store import RawFileStore`, the A17 owner's nit). Checked by diff. The
PASS stands at dafedbe3, and the G7 failure is gone now that `main` is merged in.

**Merge check (ef9e976b, no new number).**
- The table's receipt SHA-256 `8d77cb52…` (789,682 bytes) equals `sha256sum` of the committed `india_vix_daily.csv`.
- The first `data-checks` run, 39769005484 on the merge commit, concluded **success** (read through GitHub's API).
- Still owed: the first scheduled `vix-history` run on 23 Oct, then the removal commit.
