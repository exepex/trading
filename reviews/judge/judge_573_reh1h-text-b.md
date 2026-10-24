# Judge 573: REH1h story text, files a routine archives in its own run (story/reh1h-archive-serving @ 19ed7aa7a), judge B

**FAIL (round 1 of 2 for the text; 1 should-fix, 4 minor). Lane 1, quality rule 1 (text first).** Judged by reading
(the branch adds only the REH1h section, `docs/stories/REH1-rehearsal-mode.md:707-781`, over REH1g's f9562dfe1).

## Criteria (is each one complete, testable and safe?)

| # | Check | Result | My evidence |
|---|---|---|---|
| Why | the facts it rests on | MET | my read-only run of REH1g's index on the trial merge: 23 Oct rows reached main at 19:55:20 (fo-bhavcopy), 19:55:29 (participant OI), 19:55:39 (FII/DII by session), the 22 Oct close at 01:06:53 IST on 23 Oct; DRY2 e3-e5 as stated; `lab close` reads participant OI and the F&O files (`forecast_lab/page_wiring.py:69-76`) |
| Design | one new class behind the existing session seam, nothing outside `fno/rehearsal/` | MET | `nse_wiring.rehearsed_session` is the one seam; the guard checks the session by `isinstance` (`guard.py:43`), so a subclass of `NotRecordedSession` passes it |
| H1 | served at the row's commit | PARTLY | testable for e3 and e4; e5 is left conditional (minor 1) |
| H2 | never before the record held it | MET | the wait to the commit time is a look-ahead bound (the row is written after the Drive write: `manifest_folder.py:96-108`); boundaries named |
| H3 | changed or missing copy refused | MET | testable as written |
| H4 | one copy or none; ambiguous refused | MET | `FiiDiiCashSource` and `FiiDiiCashBySessionSource` share one URL (`snapshot_source.py:80,104`), so the case is real |
| H5 | empty cases NOT_RECORDED | PARTLY | see minor 2 |
| H6 | nothing reaches the real record | MET | reads through `RecordFiles` (`record_drive.py`, read-only `record_view()`); writes only through `DryrunDrive`; a real-composition test named; owner's `dryrun/` rule held; no new post |
| Gap list | every requirement covered or out of scope with a reason | NOT MET | finding 1 |

## Findings

1. **Should fix: the two G2b requirements are quoted from a text that is not in the repository.** The gap list
   (`:765-766`) quotes "a file the real routine itself archived ... served once the replay clock nears its row's
   commit" and "Until then, those reads stay NOT_RECORDED, which is honest and never a fetch". I searched every remote
   branch's `docs/` and `conversations/` (`git grep`): neither sentence exists; DRY2 has no G2b; the only written G2b
   is the handover's row 5 (`docs/HANDOVER_2026-10-24.md:99`: "served by a recorded NSE-archive source near their
   row's commit time"). A gap list must be checkable against its design (rule 2), and CLAUDE.md puts every such brief
   in the repository [strong]. Fix: cite handover row 5 and add the orchestrator's G2b brief to the repository (for
   example DRY2's gap list) word for word, or quote only what is written.

## Minor

1. H1 for FII/DII is conditional ("if its taker sends only that one request"). It can be settled now: the library
   sends one GET per file with no warm-up page (`raw_source.py:148`). Make H1 unconditional for e5 and drop the "Only
   if" in the gap row.
2. H5 and the "not published" row say such a read is NOT_RECORDED, but with the 10-minute forward window a read that
   saw a 404 on the day is served if a row lands within 10 minutes (after the wait). No look-ahead, but the line then
   differs from the day's; say so and make it a boundary case.
3. The answer must carry `headers` (`raw_source.py:139` reads Last-Modified in `fetch_published`); the design says "a
   200 with those bytes". Name `headers` empty (so "last written" is None, as the release-check row expects).
4. REH1h reuses REH1g's A9 index; judge 572's finding 1 (revision rows) touches only the path index, so REH1h needs no
   change for it, but its tests should run on the fixed REH1g.

## Plants

None (text only). The eight planned plants cover the wait, the window, the hash check, the `url_for` check-back, the
nearest row, the ambiguity, the old wiring and HEAD; I add one: a row committed exactly at now + 10 min.

## Notes

- The out-of-scope reasons hold: `corporate-actions-by-symbol` and the filings librarian are not run by the four
  routines (`rehearsal/routines.py`); G5's HEAD stays as accepted at the handover.
- The builder, session_01Mt6dcBU5kp2htdPN2KmiZH, launched this judge (no shared context); builders never merge.
