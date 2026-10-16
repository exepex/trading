# Judge 309: E2e, one BookSheet port in the pack step (story/e2e-book-sheet at 2d5dbf65)

**Verdict: FAIL, 1 should-fix and 1 minor. Lane 1** (it changes what a book's decision reads). The port is small and
right. The should-fix is in the shared snapshot reader that this change promotes to "every book".

## Gates (run myself on 2d5dbf65 merged with today's `origin/main`, local 1226afba)
- `pytest -q -n auto`: **7,813 passed, 15 xfailed** (231 s).
- `ruff check` clean; `ruff format --check`: 1,412 files formatted; `check_imports` ok; `check_records` clean
  (6,752 files).
- New files: `book_sheet.py` 19 lines, `pack_snapshot.py` 32, `tests/packs/test_book_sheet.py` 86. All under 350.

## Claims checked

| Claim | My evidence | Result |
|---|---|---|
| A sheet's result lands in its book's private pack under `evaluation` | `private_pack.py` (the `evaluation` key is added only when given); test passes | MET |
| A book without a sheet is byte-identical | Mutation 2 (key always present) fails 15 tests | MET |
| A failing sheet refuses only its own book's pack, with one alert; the others are written and kept | `packs.py` `_write_private`; `keep` skips missing paths (`private_files.py:75-80`, "a file not written locally is skipped"); `written()` lists only existing files. Mutation 1 (exception not caught) fails 2 tests | MET |
| Never silent without a sender | Mutation 3 (refusal not printed or sent) fails 2 tests | MET |
| One sender in the daily run | O1's sender-graph test passes on the merged tree | MET |
| `canonical_snapshot` returns the pack's snapshot, so "a later capture can never be read in its place" | **NOT MET**, see should-fix 1 | NOT MET |

## Findings

**Should-fix 1. `canonical_snapshot` checks the pack's file, then reads whatever the canonical marker names.** Strong
evidence: code read, plus a planted run.

`pack_snapshot.py:23-32` does two separate things:
- it verifies that `<snapshot_id>.csv` (the pack's recorded ID) hashes to the pack's `csv_sha256`;
- it then returns `RecordedSnapshots(quotes).snapshot(day)`, which reads the `.canonical` marker and parses the
  snapshot the marker names (`quote_snapshots.py:95-102`).

Nothing ties the two together. My plant (script `scratchpad/plant_e2e.py`, run with `python -I` in a temporary store):
- the store holds the pack's snapshot `nifty_20261016_145500` (the real 16 Oct NSE file) and a later
  `..._150500`, whose 21,950 CE bid is changed to 9,999.99;
- the marker names the later one;
- the pack records the first, with its correct SHA-256.

Result: `canonical_snapshot` passed the hash check and returned the later capture: the 21,950 CE 27 Oct bids came back
as `[9999.99, 11.55]`, not the pack's.

The marker is write-once by rule, so in normal days the two agree. But this function is now the shared guarantee for
Book 1, F5's sheet and decider, and F6's, and its docstring promises more than the code does. The gap was already in
Book 1's code since E5b; this change moves it, and now every book depends on it.

Fix: parse the verified bytes of the pack's own `snapshot_id` (its CSV, already hashed, and its `.meta.json`) instead
of following the marker. Or, at least, refuse when the parsed snapshot's ID differs from the pack's. Add the direct
unit test the claims say is missing: a marker naming another capture is refused or ignored, a wrong hash is refused,
and the good case passes.

**Minor 1. No story text.** No `docs/stories/` file or criterion describes E2e. It was agreed inside F5's and F6's
texts, which I judged, so this is minor. Add a short E2e paragraph with these criteria to `E-paper-desk.md` (E2c's
section) so the port has its own record.

## My mutations (all restored; `git status` clean)
1. Sheet exception not caught: 2 failed.
2. `evaluation` key always present: 15 failed.
3. Refusal neither sent nor printed: 2 failed.
4. Hash check dropped in `canonical_snapshot`: 1 failed.
