# Judge 572: REH1g, DRY2's rehearsal gaps G1, G2, G4, code (story/reh1g-record-gaps @ f9562dfe1), judge B

**FAIL (round 1 of 2; 1 should-fix, 4 minor). Lane 1** (the rehearsal's no-look-ahead reads of the real Drive record).

## Criteria

| # | Criterion | Result | My evidence |
|---|---|---|---|
| C1 | 3 pm record lists sidecars and markers from the repository; raw file read by name, hash-checked | MET | `record_store.py:34-38`; real-builder test passes; plants Pf (listing `{}`) and Pl (A4b's store back) caught; my run lists the Claims' 9 names for 23 Oct |
| C2a | a row counts from the committer time of its first first-parent commit on `origin/main` | PARTLY | right for A9 and cue rows (Pa, Pg caught; 16 Oct close 22:40:15 UTC and KOSPI 03:23:35 UTC reproduced); wrong for every revised file (finding 1); Pj survives (minor 1) |
| C2b | an A9 file is its dataset's (day, URL) row | MET | my script: 12,582 rows of the 20 RAW_SOURCES manifests map back through `path_for` and `_a9_key`; the fo_secban 22/23 Oct test passes |
| C2c | a `path` row (cues, candles) matches only that path in the raw area | NOT MET | `_index` takes `path` rows from every manifest under `manifests/`, so `revisions/*.csv` and `filings/outside-layout.csv` count too, and win over the A9 row (finding 1) |
| C2d | the rehearsal's Drive is wired with the rows | MET | `drive_wiring.py:23`; test passes; Pn (receipt branch off) caught |
| C3a | scheduled reads: 60 s before to 10 min after | MET | `serving.py:26-27`; Ph (`<` at +10 min) caught |
| C3b | paced reads: nearest within 60 s, never twice, never back in time, waits | MET | Pd (`>=`), Pi (lower bound dropped), Pe (pre-open wait) and Pm (cue wait) caught |
| QR2-6 | gap list, self-review, broken-code proof, cases, real sample | MET | sample reproduced on my trial merge; rejections checked below |
| Gates | trial merge with origin/main 404452481 | MET | ruff, format (2,442 files), imports, record scan (8,992 files) clean; 15,143 passed, 15 xfailed; new files 46-153 lines |

## Findings

1. **Should fix: revision-index rows date the raw file, later than its A9 row.** `manifests/revisions/index-close.csv`
   and `span-bod.csv` have a `path` column: the raw path whose later NSE version was found. `_index`
   (`manifest_rows.py:59-66`) indexes them as path rows and `seen_at` (`:40-41`) prefers them to the A9 row. My
   read-only run on the trial merge: `raw/nse/derivatives/span-bod/2026/10/nsccl.20261021.i1.zip` is seen at 24 Oct
   00:34:09 UTC (the revision row), though its A9 row reached main on 20 Oct 02:23 UTC; `ind_close_all_23102026.csv`
   at 19:36:03 UTC instead of 17:01:15; the 12 and 21 Oct closes likewise. A rehearsal between the two times says
   NOT_RECORDED for a file the day held: G2's own "visibility fault", growing with each revision sweep [strong]. It
   errs late, never early (no look-ahead); no test has a revision row. Fix: index `path` rows only from the manifests
   whose `path` names a raw file (global cues, Groww candles), never `revisions/` or `filings/outside-layout.csv`
   (deleted trial files), or take the earliest of both kinds; test a revision row committed after the A9 row.

## Minor

1. **Pj survives:** `committer-time` read as `author-time` passes all 98 rehearsal tests (the tests set both dates
   equal). Add one row whose author date is earlier than its committer date.
2. **Pc survives:** `_a9_key` without the trailing `/` passes; it changes no row today (my script), but
   `fii-dii-cash`/`-by-session` and `fpi-daily`/`-by-session` are prefix pairs. One test pins it.
3. `announcements`, `board-meetings` and `india-vix-history` have no RAW_SOURCES entry, so their files are never
   visible. No routine of the four reads them (my grep); say so under Limits.
4. Limit 2 says manifest rows "are not written this way today", but the routines' `pull --no-rebase` then `push
   HEAD:main` puts earlier main commits on the second-parent side: hence the 16 Oct close dated 3 h 38 min after its
   commit (the Claims' own sample). Late only; reword it.

## Self-review rejections (my check)

- #5 holds: only `build_job` and `build_preopen` build the cue session (`global_cues/wiring.py:191,284`); of the four
  routines only `rehearse preopen` runs one (`rehearsal/routines.py`). #8 (no git) holds: the checkout runs `git
  rev-list` on `origin/main` before any step (`checkout.py:50`). #10 (partly) holds: behaviour tests catch Pd, Pe, Pi, Pm.

## Plants

16 planted, one at a time, each restored and `__pycache__` cleared: 10 caught (Pa look-ahead, Pd, Pe, Pf, Pg, Ph, Pi,
Pl, Pm, Pn). Survived: Pj, Pc (minors 1, 2); Pb (keep the later of two equal keys) and Pk (`top_level` dropped) are
equivalent on today's data.

## Notes

- Hunted: no write path (`ListedQuoteRecord.put` reaches `RecordReader.put`, which raises; raw reads use
  `record_view()`); no new post; holidays and empty days end NOT_RECORDED; every time compared is tz-aware.
- REH1g was finished by session_01Mt6dcBU5kp2htdPN2KmiZH, which launched this judge (no shared context); builders never merge.
