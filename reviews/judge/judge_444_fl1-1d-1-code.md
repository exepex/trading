# Judge 444: FL1-1d-1 code, the two editions (story/fl1-1d-two-editions at 506b2481)

**Verdict: FAIL: 1 should-fix finding and 3 minor.** The editions, records, confirmation and O1 removal are well
built, and both live dates are null. The one gap: the editions now run outside O1's `Alerted`, and a crash before the
post sends no alert at all.

## Checked myself
- **Gates:** on 506b2481 merged with today's `main` (no conflicts), one run:
  - 9,150 passed, 16 xfailed;
  - `ruff check` clean; 1,711 files formatted;
  - imports clean; record scan clean (7,423 files).

  Strong evidence.
- **8 planted mutations, all caught:**
  - no 09:15 cutoff;
  - the not-live check off;
  - a verdict confirmed twice;
  - a correction without its alert;
  - the morning reading today's issue instead of the previous session's;
  - today's check not marked provisional;
  - "not archived" treated as settled;
  - a failed post not alerted.
- **O1's `lab_close` removal, under the O1 builder's conditions:**
  - it is gone from `DAILY_RUN_STEPS`, `LIVE_STEPS`, the wiring and `config.yaml`;
  - `test_old_run_logs.py` reads an old entry;
  - CLAUDE.md's daily-run step no longer names it.
- **Rules.** The new CLAUDE.md section has exact stored prompts, says "the owner creates them, no session does", and
  gives the commit rule for its own receipts only, with the pull-and-retry-once rule. Each edition's
  `forecast_lab.live_from` is null.
- **Limits stated honestly:**
  - `NoTodayCloses` until A4h exists, so the evening checks nothing yet and says why on the page;
  - the morning confirmation mostly reads "not archived yet" until 1d-2's index-close fetch.

## Finding

**Should-fix 1. A crash before the post sends no alert: the report is missed in silence.** Strong evidence: a probe.
- `build_edition` raises `RuntimeError(UNSYNCED)` when G13b's Drive records cannot be read verified. A composer can
  also raise (Drive, the calendar, a damaged record).
- Neither `EditionRun.run` nor `cli._edition` catches either case.
- My probe, an `EditionRun` whose composer raises the UNSYNCED error: the exception escapes, and `alerts.sent == []`.
- Under O1, `Alerted` caught that and alerted #fno-desk once. The editions run from the owner's routines, and the
  routine section's step 4 posts by hand only lines that read "alert NOT sent". A traceback is neither, so the owner
  gets no report and no alert.
- Fix: catch any exception around building and running the edition (in `cli._edition`, or a wrapper in the wiring).
  Send one #fno-desk alert naming the edition, day and error type, print "alert NOT sent" when it cannot be sent, and
  exit 1. Test both: a raising composer, and a raising build.

## Minor
1. **CLAUDE.md's F&O output line** still says #fno-forecast takes "the forecast lab's 09:15 and 15:45 reports".
   Update it to the morning and evening editions.
2. **The 09:15 cutoff is checked once, before composing.** A slow compose (Chromium may take up to 90 s) started at
   09:14 posts after the open. Check it again just before `_post`.
3. **The morning routine starts at 08:38 and the owner's slot is 08:50 (bcbbc454).** That is consistent if the post
   lands by about 08:50. Record the measured compose-and-post time on the first live mornings, so the owner can
   confirm the start minute.
