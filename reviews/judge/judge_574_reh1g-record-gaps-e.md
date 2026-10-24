# Judge 574: REH1g, DRY2's rehearsal gaps G1, G2, G4, code (story/reh1g-record-gaps @ f9562dfe1)

**FAIL (round 1 of 2; 2 should-fix, 2 minor). Lane 1** (what a rehearsal may see of the record: no look-ahead).
Judge E, independent of judge B. Labels: strong, some, reasoning only.

## Criteria

| # | Criterion | Result | My evidence |
|---|---|---|---|
| C1 | 3 pm record lists the repository's sidecars; raw file by name, hash-checked | MET | `record_store.py:29-38`; the only `DriveOnlyQuoteStore` in the rehearsal path is `quote_wiring.py:38`; the real-builder test passes |
| C2a | A row counts from its first-parent commit on `origin/main` | PARTLY | Branch-only, merged-later and exact-second cases hold (tests and E8 caught). But some files are dated by another manifest's row (SF1), and committer time is not pinned (SF2) |
| C2b | An A9 file is its dataset's (day, URL) row | MET | My read-only check: 12,582 rows of 19 dataset manifests map back from `path_for(day)` to their own key; no nested dataset prefixes; no duplicate (day, URL) in any top-level manifest |
| C2c | A `path` row (cues, candles) matches only that path in the raw area | NOT MET | Revision-log and filings rows match too (SF1) |
| C2d | The rehearsal's Drive is wired with the rows | MET | `drive_wiring.py:23-24`; the test passes |
| C3a | Scheduled read: 60 s before to 10 min after | MET | `serving.py:26-27`; edges exact to the microsecond; E2 caught. "First answer" is not pinned (minor 2) |
| C3b | Paced read: nearest within ±60 s, earlier wins a tie, never twice, in order, waits for its time | MET | `serving.py:37-46`; E1 (`>=`), E4 (tie to the later copy) and E6 (no lower bound) caught; waits at `recorded_cues.py:48`, `recorded_preopen.py:39` |
| Gates | trial merge with main 4044524 (base = main: the tree is f9562dfe1) | MET | ruff and format clean (2,442 files); imports clean; record scan clean (8,992 files); full suite **15,143 passed, 15 xfailed** (41 min) |
| QR2-6 | gap list, self-review, plants, cases, real sample | PARTLY | Present. The real sample is reproduced: 16 Oct close 22:40:15 UTC, KOSPI 03:23:35 UTC, made-up file None. The C2c claim is false (SF1) |

## Findings

1. **Should fix: rows of the A11 revision log (and of `filings/outside-layout.csv`) are indexed as archive `path` rows.
   They override the A9 row's date, so the original file shows up hours to days late.**
   `research/data/manifests/revisions/*.csv` has a `path` column naming the *original* raw file. The revision's own
   bytes live in Drive's `revisions` area. `_index` keeps every `path` row (`manifest_rows.py:63`), and `seen_at`
   prefers it (`:40-41`). My read-only run on this record:
   - span-bod 21 Oct: its A9 row is from 20 Oct 02:23 UTC, but it is seen only from 24 Oct 00:34 UTC.
   - index-close 12 Oct: 01:54 UTC becomes 12:52 UTC. A rehearsal of 13 Oct's 08:38 morning would again say
     NOT_RECORDED, the G2 symptom.
   - index-close 23 Oct: 17:01 UTC becomes 19:36 UTC.

   No look-ahead (a revision is always later), and no DRY2 23 Oct row is hit today. But the rule is wrong for every
   file that has a revision, and A11's sweeps add more [strong: reproduced]. Fix: index `path` rows only from the
   manifests whose writer archived that path (`global-cues/`, `groww-candles/`). Test: a revision row for the 16 Oct
   close leaves `seen_at` at its A9 row's commit.
2. **Should fix: the no-look-ahead date is not pinned to the committer time.** My plant E3 (`author-time` in place of
   `committer-time`, `manifest_rows.py:89`) passed all 98 rehearsal tests: the fixture's `git()` sets the author and
   committer dates the same. A rebased or cherry-picked commit keeps an older author time, so that bug would show a
   row before main held it, which is the look-ahead C2a forbids [strong: plant survived]. Fix: one commit whose
   author date is earlier than its committer date, asserting `seen_at` is the committer date.

## Minor

1. Three top-level manifests have no `RAW_SOURCES` entry, so their files are never visible: `announcements`,
   `board-meetings` and `india-vix-history` (7,966 + 7,966 + 195 rows). The `filings/` subfolder manifests are also
   left out. No rehearsal routine reads them (grep: only `cli.py`), but the gap list should name them out of scope.
2. Two "first" rules are unpinned. E5 (`recorded_closes.py`, `later[-1]` for `later[0]`) and E7 (`_keep` keeps the
   latest commit) both survived. No test has two answers within 10 min, or two rows with one key; no real manifest has
   such a duplicate today.

## Plants

8 planted, 5 caught, 3 survived (each run alone on `tests/rehearsal`, restored and `__pycache__` cleared). Caught:
E1 `saved >= last`, E2 strict lower edge in `is_near`, E4 tie to the later copy, E6 no lower bound on AROUND, E8
`seen < now`. Survived: E3 author time (SF2), E5 latest answer and E7 latest row (minor 2).

## Notes

- G4 edges also checked by reading: each URL and each pre-open part has its own `ServedOnce`; one cue session per
  process (`global_cues/wiring.py:275-284`); self-review item 5 holds (`routines.py:35`: the only cue job).
