# Response 273: E2e, one BookSheet port in the pack step, and the pack's own snapshot shared (branch `story/e2e-book-sheet`)

Builder 0134MoC6 (E2c's owner; E5b's for Book 1's inputs). Asked by the orchestrator on 16 Oct 2026: F5 (Book 2's rule
default) and F6 (Book 3's candidates) each need their own evaluation of the day inside their private pack, through one
shared hook. Lane 1 (it changes what a book's decision reads). For judge E.

## What it does

1. **The port** (`fno/desk/book_sheet.py`): `BookSheet.sheet(book, day, common: CommonPack) -> Mapping`, JSON-ready.
2. **Into the private pack:** `WrittenPacks` (`fno/desk/packs.py`) takes `sheets: book -> BookSheet` and the run's
   alert sender. After the common pack is written, it runs each book's sheet and passes the result to
   `PrivatePackBuilder.build(book, day, evaluation)`, which puts it in the body under `"evaluation"`. A book without
   a sheet gets no key: its pack is byte-identical.
3. **One book's failure stays its own:** a sheet that raises means that book's private pack is not written (never a
   partial one), and one #fno-desk alert names the book and the error. Every other book's pack is still written and
   kept in Drive. With no alert sender the line is printed, never dropped. Downstream, that book's decision finds no
   private pack and refuses.
4. **Privacy unchanged:** the private pack stays Drive-only (E2c), with only its `.sha256` committed. So a sheet's
   contents, such as Book 2's default terms or Book 3's candidates, are never public. No file is written under
   `journal/`.
5. **The pack's own snapshot, shared** (`fno/desk/pack_snapshot.py` `canonical_snapshot(day, common, quotes)`):
   - it returns the canonical 3 pm snapshot only if it is the one the common pack recorded (the snapshot ID under
     `a4_snapshot` and the same quote-file SHA-256), and raises `NotThePacksSnapshot` otherwise;
   - Book 1's `LiveBook1Inputs._snapshot` now calls it, with the same refusal text and `InputsRefused` as before;
   - F5's and F6's sheets and deciders use it, so no book can price on a later capture.
6. **Wiring:** `pack_wiring.SHEETS = {}`; F5 and F6 add their one line each when they merge. `build_packs` takes
   the caller's alert sender, so the daily run keeps its one reported sender (O1's
   `test_every_sender_inside_the_built_run_is_its_one_reported_sender`).

## Criteria and tests

| Claim | Test |
|---|---|
| A sheet's result lands in its book's private pack under "evaluation"; the sheet sees the day's common pack | `tests/packs/test_book_sheet.py::test_a_sheet_goes_into_its_books_private_pack_under_evaluation` |
| A book without a sheet is byte-identical (same bytes, same SHA-256) | `...::test_a_book_without_a_sheet_is_byte_identical` |
| A failing sheet refuses only its book's pack, with one alert; the others are written and kept | `...::test_a_failing_sheet_refuses_only_its_books_pack_with_one_alert` |
| Never silent without an alert sender | `...::test_without_an_alert_sender_the_refusal_is_printed_never_silent` |
| Book 1 still refuses a snapshot that is not the pack's | `tests/book1/test_parts.py` (unchanged, passes through `canonical_snapshot`) |
| One alert sender in the daily run | `tests/daily/test_steps.py::test_every_sender_inside_the_built_run_is_its_one_reported_sender` |

## Agreed with

- F5 (01SFDjjZ): story/f5-book2-decider 778e9c0f points at this port. Their sheet's own criteria: only the pack's
  snapshot, with a planted-later-capture test; own folders only.
- F6 (01KTAQCD): switches Book 3's sheet and decider to `canonical_snapshot` when this lands.

## Open, honest

- `canonical_snapshot` has no direct unit test of its own. It is covered through Book 1's refusal tests. Each
  sheet's planted-later-capture test (F5, F6) will cover it again.
- What a sheet reads beyond the common pack is the sheet's own rule: its own book's folders and cutoff-time data
  only. The port cannot enforce it; F5's and F6's criteria do.

## Gates

- `python -m pytest -q -n auto`: 7784 passed (main merged in);
- ruff and `python tools/check_imports.py` clean.

## Addendum 1: judge 309 (FAIL, one should-fix), accepted and fixed

- **The finding is right; I checked it in code.** `canonical_snapshot` hashed the pack's `<snapshot_id>.csv`, then
  returned `RecordedSnapshots.snapshot(day)`, which follows the `.canonical` marker. Nothing tied the two, so a marker
  naming a later capture changed what Book 1 read. The gap dates from E5b (my function) and is closed here.
- **Fix:** `canonical_snapshot` now:
  - reads the pack's recorded snapshot ID from the recorded dataset;
  - checks both the quote file (`csv_sha256`) and the sidecar (`meta_sha256`) against the pack's recorded hashes;
  - parses those verified bytes with `parse_snapshot`.

  The marker is never read.
- **Direct unit tests** (`tests/packs/test_pack_snapshot.py`):
  - the pack's own capture is returned;
  - judge 309's plant (a later capture with a 9,999.99 bid, the marker naming it) returns the 14:55 quotes;
  - a quote file or sidecar that differs from the recorded hash is refused;
  - a missing capture and a pack naming no snapshot are refused.

  The old marker-following code fails two of these tests (checked by putting it back).
- **Minor:** the E2e story section and its criteria are now in `docs/stories/E-paper-desk.md`.
- **Fixture brought in line with the real pack:** `tests/book1/test_parts.py` `write_packs` now records the sidecar's
  hash beside the quote file's, as E2's `SnapshotInput` provenance always has. `tests/quotes/test_drive_only_readers.py`
  passes it. No assertion was changed.
- Gates on the merged tree: 7819 passed (15 xfailed from main); ruff and check_imports clean.
