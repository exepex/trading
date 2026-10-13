# Response 54: story A11 claims, revisions of NSE files

**Status: built, tested and run on real data; awaiting the judge.** Builder: Claude (builder session, claims number
54). Story: `docs/stories/A-data-foundation.md#a11`, issue exepex/trading#86.

## Verdict in one line

A later NSE version of an archived file is now saved in Drive's `revisions` area under the same path with its time
and SHA-256, never over the raw file. A point-in-time reader and a latest reader pick the right version. Both are
proven on the real 12 Oct 2026 index-close rewrite. A8's sweep and a new `data-revisions sweep` save what they find,
and `data-coverage` counts the revised days.

## Correction to the story's context (strong evidence)

NSE's rewrite of `ind_close_all_12102026.csv` added **21** indices, not two (Nifty Capital Goods and Nifty
Telecommunications are two of them; others include Nifty Next 100, Nifty Power, Nifty50 USD). It **changed none** of
the 146 rows the first version had: NIFTY 50 (close 22,363.35) and India VIX (15.25) are byte-identical in both. So no
result built on NIFTY 50 or India VIX closes for 12 Oct changes (test
`test_the_real_rewrite_added_indices_and_changed_no_existing_row`).

## Design (orchestrator decision, kept)

- **Revisions area** `fno-research/revisions/` beside `raw/` (`wiring.REVISIONS_AREA`). Each version sits at
  `<raw path>/<YYYYMMDDTHHMMSS+0530>_<sha256><ext>`. Example:
  `revisions/nse/indices/index-close/2026/10/ind_close_all_12102026.csv/20261012T232010+0530_e8e8f6ec…ee621.csv`.
- **Index** (append-only, committed): `research/data/manifests/revisions/<dataset>.csv` with columns
  `date,path,sha256,size_bytes,available_from,last_modified,found_at`. It is committed by A10's `GitManifestRecorder`
  (same folder, same hooks, no `--no-verify`).
- **When a version became available** (`available_from`): NSE's Last-Modified for those bytes when it gives one (the
  bytes were public from then), else the time we fetched them (an upper bound, so no look-ahead).
- **Classes, each new and behind existing interfaces:**
  - `RevisionArchive` (`fno/storage/revisions.py:113`) compares the bytes with the raw file's manifest SHA-256. It
    falls back to hashing the raw file itself when there is no manifest row. It saves only a version it has not seen.
  - `VersionedRawStore` (`fno/storage/versioned_store.py:20`) is a read-only `RawFileStore`, so it plugs into
    `RawFileLibrary` and every other reader unchanged.
  - `RevisionCapturingSource` (`fno/storage/revision_source.py`) is a `RawFileSource` decorator.
- **Wiring** only in `fno/storage/wiring.py` (`build_revision_archive`, `build_versioned_reader`,
  `build_revision_capturing_source`) and `fno/composition.py` (`build_last_write_sweep`).
- **Full GET, not HEAD, for detection.** My own check today: HEAD on `fao_participant_oi_09102026.csv` returned 200
  with the same Last-Modified as GET, twice. So I could **not** reproduce "HEAD is unreliable". The full read is still
  the right design:
  - a rewrite is only proven by a SHA-256;
  - the bytes are needed to keep the version;
  - NSE's pacing is one request per second (`fno/http_pacing.py:17`), so for files of a few KB to a few hundred KB a
    GET takes no longer than a HEAD.

## Criteria

| # | Criterion | Status | Evidence |
|---|---|---|---|
| 1 | Later version stored under a revisions area with the same path, a revision timestamp and its SHA-256; raw never overwritten (test) | MET | below |
| 2 | Point-in-time reader and latest reader, both tested on the real 12 Oct 2026 case (both versions archived, fingerprints recorded) | MET | below |
| 3 | A8's rewrite sweep stores what it finds as revisions | MET (code, test, real run) | below |
| 4 | Coverage reports revisions per dataset; size, lint, imports, tests pass | MET | below |

### 1. Revisions area, raw file untouched

- `RevisionArchive.capture` is at `fno/storage/revisions.py:130`. It writes the bytes first, then the index row, so a
  row always has its file. The revision path is `Revision.revision_path` (`revisions.py:40`).
- Test `test_a_later_version_is_kept_under_the_same_path_with_its_time_and_sha256_and_the_raw_file_never_changes`
  covers:
  - the exact path `…/ind_close_all_12102026.csv/20261012T232010+0530_<sha>.csv`;
  - the raw bytes unchanged after the capture;
  - the same version captured again adds no second row.
- Other tests:
  - a version with no Last-Modified counts from the time it was found, and a third version is appended;
  - a file the raw archive lacks is not a revision;
  - an unfingerprinted raw file is compared by its own bytes.
- Real run (13 Oct 2026, 18:22 IST):

  ```
  $ python -m fno data-revisions sweep index-close --from 2026-01-01 --to 2026-10-12
  REVISION 2026-10-12 nse/indices/index-close/2026/10/ind_close_all_12102026.csv: NSE's newer version kept as
    nse/indices/index-close/2026/10/ind_close_all_12102026.csv/20261012T232010+0530_e8e8f6ec16018d437c97aa302c17aae033d262b1a030101ecdf887d1be4ee621.csv
    (17552 bytes, available from 2026-10-12 23:20:10+05:30)
  revisions sweep: 192 files read, 1 new revisions, 0 unanswered
  manifest rows committed and pushed (1 file(s))
  ```

  Of the 192 index-close files for 2026, only 12 Oct differed from the archive. A second run read the file again and
  saved nothing ("0 new revisions", "nothing new to commit"). The raw manifest row for 12 Oct is still `fc847998…`.

### 2. Point-in-time and latest readers on the real case

- `VersionedRawStore.version` is at `versioned_store.py:29`. It returns the newest revision with
  `available_from <= as_of`; with `as_of=None` it returns the newest of all. A revision whose bytes do not match the
  indexed SHA-256 raises `StoredCopyDamaged`; it is never returned.
- Both real versions are committed as test fixtures: `tests/fixtures/nse/revisions/ind_close_all_12102026.first.csv`
  (SHA `fc847998…`, read from Drive's raw area) and `…rewritten.csv` (SHA `e8e8f6ec…`, NSE today). They are small
  (16 to 18 KB) and follow the precedent of A8's committed participant-OI fixtures.
- Test `test_point_in_time_and_latest_readers_on_the_real_12_october_rewrite`:

  | Reader | Returns |
  |---|---|
  | as of 12 Oct 15:30 IST | first version |
  | as of 23:20:00 (one second before the rewrite) | first version |
  | as of 23:20:10 | rewritten version |
  | as of 13 Oct 09:00 | rewritten version |
  | latest | rewritten version |
  | a never-revised file | its raw bytes |
  | a missing file | None |

- Test `test_the_committed_records_hold_both_real_versions`: the committed manifest row is `fc847998…`, and the
  committed revision row is `e8e8f6ec…`, 17,552 bytes, available from 23:20:10 IST.
- Real check against Drive (service-account reads, each SHA-256 checked):

  ```
  $ python -m fno data-revisions versions index-close --day 2026-10-12 --as-of 2026-10-12T15:30
  latest: …/20261012T232010+0530_e8e8….csv sha256 e8e8f6ec16018d437c97aa302c17aae033d262b1a030101ecdf887d1be4ee621
  as of 2026-10-12 15:30 UTC+05:30: raw sha256 fc847998c9d8bfa461ddad1770dc610086eadea3d442f1dfe515ae76b83c7f25
  $ … --as-of 2026-10-13T09:00   ->  as of 2026-10-13 09:00: …e8e8….csv sha256 e8e8f6ec…
  ```

### 3. A8's sweep stores what it finds

- `build_last_write_sweep(archive)` (`fno/composition.py:149`) now gives `LastWriteSweep` a `RevisionCapturingSource`.
  `LastWriteSweep` itself is unchanged (open/closed). Each file is read in full:
  - a version that differs is saved as a revision;
  - its Last-Modified still feeds the sweep log and the availability rule (judge 16), exactly as before.
- `python -m fno participant-oi sweep` prints the revisions saved and the new count. It commits the index rows in a
  `finally` block, and exits 1 when anything moved, went unanswered or was saved.
- Tests:
  - `test_the_wired_sweep_reads_files_in_full_and_stores_a_rewrite_as_a_revision`: the real composition function,
    with only NSE faked; the moved write is logged, the revision is stored and the raw bytes are unchanged.
  - `test_the_sweep_command_alerts_on_a_moved_write_and_on_no_answer`, updated: the summary line and one commit per
    run.
- Real run: `python -m fno participant-oi sweep` over all 1,929 recorded files was still running when this was
  committed; its result is added to this file in a follow-up commit.

### 4. Coverage, size, lint, imports, tests

- `CoverageDataset.revisions` and `DatasetCoverage.revised` (`fno/storage/coverage.py:63,137`) add a "revised" column
  and one line per revised day. Revisions never make the result incomplete: a rewrite is NSE's doing, not a gap.
  Test: `test_coverage_reports_revisions_per_dataset`. The existing coverage test was updated for the new last column
  (`tests/test_coverage.py`, "no sha" is now `[-2]`).
- Real run:

  ```
  $ python -m fno data-coverage --from 2026-10-01 --to 2026-10-12
  dataset                                    from         to expected present missing damaged no sha revised
  nse/indices/index-close              2026-10-01 2026-10-12        7       7       0       0      0       1
  (the other five datasets: 0 revised)
  revised (later NSE versions in revisions/) nse/indices/index-close 2026-10-12: 1
  result: complete
  ```

- Checks:
  - `python -m pytest -q`: 1,134 passed;
  - `ruff check fno tests tools`: clean;
  - `ruff format`: applied;
  - `python tools/check_imports.py`: clean;
  - file sizes: `revisions.py` 157 lines, `versioned_store.py` 41, `revision_source.py` 57, `revisions_cli.py` 96,
    `wiring.py` 332 (under 350, but close: the next storage story should move revision wiring into its own module or
    split `wiring.py`).

## What is not done, and what could be wrong (please check)

1. **Versions between our reads are lost.** If NSE rewrites a file twice between two sweeps, only the last is kept.
   Run the sweeps often enough for the research's needs (A8's sweep is monthly).
2. **Last-Modified is trusted.** A stale CDN copy with an older Last-Modified than the raw file would be indexed as a
   "later" version that the point-in-time reader returns before the raw file's own time. This has not been seen.
   Guarding against it needs the raw file's own publication time, which the manifests do not record.
3. **Coverage counts revisions from the committed index; it does not re-read their bytes from Drive.**
   `data-revisions versions` and every read through `VersionedRawStore` do verify them against their SHA-256. A judge
   wanting a full byte check of all revisions should ask for a small `data-revisions check`. With one revision today,
   I judged it not worth the code yet.
4. **No reader uses the versioned store yet.** A8's `PointInTimeParticipantOi`, the panel builder and P6's publishing
   path still read the raw area. Wiring them is B5's (research) and P6's (publishing) decision. The readers exist,
   are tested and are one call away (`wiring.build_versioned_reader(as_of)`).
5. **Orphan file after a crash (minor).** A crash between saving a revision's bytes and appending its row, for a
   version without Last-Modified, would leave an unindexed file in Drive on the next run (its time-based name
   differs). It is harmless: readers use only indexed rows, and nothing is overwritten.
6. **Other detectors.** The release recorder's `REWRITTEN` and `data-fingerprints --spot-check`'s "NSE REWRITE" still
   only report. Wrapping their sources in `RevisionCapturingSource` is one line each in the wiring. I did not do it
   because the criterion names only A8's sweep.
