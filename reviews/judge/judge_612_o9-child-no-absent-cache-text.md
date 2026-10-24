# Judge 612: O9-child, the Drive store never caches an absence, story text (story/o9-child-no-absent-cache @ 97fc5c30b)

**PASS (text; 3 minor, one a condition for the code round). Lane 1** (Drive, every reader and writer of the record).
Judge F, own session (session_01A8XfbTUVgeeEpqatHaWbtP). Labels: strong, some, reasoning only.

## Facts and rules checked

| Item | Result | My evidence |
|---|---|---|
| `_child` caches an absence | TRUE | `google_drive.py:71-81` stores `None` under the key; `get` uses `_file_id(fresh=False)` (`:83-100`) |
| Writes already re-check | TRUE | `google_drive_upload.py:44-47` `_fresh_child` pops the key, used by `put` and `_create_folder` |
| The dry run's receipt is the step's own | TRUE | f1cd35fb1 ("step price_ranges") adds `banknifty_through_2026-10-22_rows002415_ea232e876681.csv.sha256`: `2026-10-23T09:50:06Z` (15:20:06 IST), writer `pricerange`, run `20261023T094954Z-6417f3`; the public log shows `price_ranges` failed, `command:exit_1` |
| The bug, reproduced on main | TRUE | `tests/dr1/fake_drive.py`, two stores on one fake Drive: A `get` → None; B `put`; B reads the bytes; A still answers `get` None, `file_id` None and `checksums` {} |
| Found IDs stay cached | SOUND | the record is write-once; `replace_contents` keeps the ID; a reader never deletes or moves |
| The DryrunDrive-only fix rightly rejected | YES | the same two-instance order happens in a real run for the first file of a new folder (a writer's `DataStore` and a reader's `DriveCache` are separate instances, `build_data_store` / `build_drive_cache`) |
| D1-D5 catch the bug | YES | D1's plant (`_child` caching `None`) fails D1 and D4's cold case; D2's counting fake fails "never cache"; D4 is shown red on main first |
| Gap list, cases, sample | PRESENT | the orchestrator's four asks mapped; good/bad/boundary/empty per criterion; a cold-cache rehearsal rerun as the real sample |
| Doc-reading tests (trial merge with main) | PASS | 864 passed, 14 xfailed; record scan clean (9,203 files) |

## Minor

1. **Condition for the code round: test every read path, not only `get`.** My reproduction shows `file_id`
   (`fresh=True`) and `checksums` failing the same way, because the cached absence is a folder's. `folders`,
   `metadata` and `_listing` walk the same `_child`. `DryrunDrive` uses all of them (`rehearsal/drive.py:40-61`). The
   fix in `_child` covers them. D1 must assert, on instance A after B's write, that `get`, `file_id`, `checksums`,
   `folders` and `metadata` all see the new file. A code round without those assertions is a should-fix.
2. The text says `file_id(fresh=True)` "keep[s] its own re-check". Today that re-check pops only the file's key, not
   the folders', so a fresh lookup also returns None under a cached-absent folder (reproduced). Reword it to "re-checks
   the file's own key; the folders are covered by the new rule".
3. Cost is "reasoning only", as labelled. The real sample's Claims should give the rehearsal's Drive list-call count
   before and after, if `DriveSession` can count them cheaply.

## Plants

None (a text round). D1-D5's plants and my own are run at the code round.

## Notes

- Deadline: no should-fix, so the code can start now for dry run 1 (Sun 25 Oct 12:00 IST).
