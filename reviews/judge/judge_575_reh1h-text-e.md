# Judge 575: REH1h story text, files a routine archives during its own run (story/reh1h-archive-serving @ 19ed7aa7a)

**FAIL (round 1 of 2, text; 1 should-fix, 3 minor). Lane 1** (serves the record's files into a rehearsal: a wrong
rule is a look-ahead). Judge E. Text-only (one `.md` file, 76 added lines on top of REH1g's f9562dfe1): judged by
reading, no suite. Labels: strong, some, reasoning only.

## Criteria (rule 1: the text against G2b, the owner's decisions and REH1's frame)

| # | Check | Result | My evidence |
|---|---|---|---|
| T1 | Covers G2b as written | MET | G2b's two sentences are REH1g's own first text (`b5ab43ef6`, story lines 625-630); both mapped (H1/H2, H5) |
| T2 | The "why" is true | MET | My read of `manifest_rows` on origin/main: fo-bhavcopy 23 Oct 19:55:20, participant-oi 19:55:29, fii-dii-cash-by-session 19:55:39 IST; 22 Oct index-close 01:06:53 on 23 Oct, all as written |
| T3 | No look-ahead | MET | H2: served only at or after the row's commit, which is after the day's Drive write; the upper bound 10 min, boundaries exact |
| T4 | No real Drive write; dryrun only | MET | H6: real Drive only read (`RecordFiles`), writes via `DryrunDrive` under `dryrun/<run_id>/`, a test on the real `build_librarian` composition |
| T5 | One new class behind an existing seam | MET | `nse_wiring.rehearsed_session` is the one seam (`storage/wiring.py:162-164`); it extends `NotRecordedSession` |
| T6 | Criteria testable, with good/bad/boundary/empty | PARTLY | H1-H6 each testable; H2's lower-bound rule rests on a false premise for one of H1's three targets (SF1) |
| T7 | Gap list complete; out-of-scope reasons true | MET | 404s: every row of the 23 top-level manifests has status 200 (none recorded); filings and by-symbol: no routine command in `routines.py` reads them; release-check reason matches `forecast_lab/release.py:36` (`fetch_published`, no store) |

## Findings

1. **Should fix: H2's "more than 60 s before now is not served ... the library already reads that file from the
   stores through REH1g's G2" is false for the FII/DII snapshot, one of H1's three targets.** `data-snapshot
   fii-dii-cash-by-session` is a `SessionFiledTaker` (`storage/wiring.py:234-239`, `COVERED_SESSION` in
   `content_checks.py:90-94`), and `SessionFiledTaker.take` fetches first, always: the path depends on the session read
   from the copy (`session_filed_taker.py:43-49`). No store is read before the request. So a rehearsal whose
   by-session step reaches the request more than 60 s after 19:55:39 (a slow step before it, a late start) gets
   NOT_RECORDED, though the record holds the copy and G2 already shows its file. The same applies to the fo-ban-list
   and the NSDL by-session report [strong: code read]. Fix: give the session-filed (fetch-first) takers their own
   rule in the text, for example the latest row for that URL committed on or before now on the replay day; or keep
   the 60 s and say the limit plainly, with its effect on e5. Add the case (a by-session read at commit + 61 s) to H2's
   boundary tests.

## Minor

1. H1's condition on the FII/DII request can be settled now: `FiiDiiCashSource.url_for` returns the one API URL
   (`snapshot_source.py:80-85`) and `_response` sends one GET with no warm-up page (`raw_source.py:144-147`).
2. The wait's clock is not named. The evening's waits run on the replay clock, but the text should say whether they
   use the skipping waiter or a real sleep (G3 was decided as real speed for the pre-open only).
3. A repeat request for the same URL in one run (a retry, a second step) gets the same copy again. That differs from
   REH1g's paced `ServedOnce` rule. Right for a scheduled read, but say so in H4.

## Plants

None (text round). The eight planned plants cover the wait, the window, the SHA-256 check, the `url_for` round trip,
nearest vs first, the ambiguity refusal, the old session wired back and HEAD.

## Notes

- H2 inherits REH1g's finding SF1 (judge 574): a file with an A11 revision row is shown by G2 only from the revision's
  commit (e.g. span-bod 21 Oct from 24 Oct 06:04 IST, though its row reached main on 20 Oct). In that gap neither the
  store nor this session answers. Fixed in REH1g, H2 holds as written.
- The guard's entry is named in Design but not in a criterion. H6's test should include the guard listing the new class.
