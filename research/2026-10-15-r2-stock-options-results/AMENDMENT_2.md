# R2 pre-run amendment 2 (15 Oct 2026): details fixed while writing `study.py`

Same status as amendment 1: ledger trial 53 stays one trial; `PROTOCOL.md` (unchanged) governs, then amendment 1, then
this file. **Written before any data of this study was parsed.** The raw files were copied to a local cache and each
copy's SHA-256 checked against its manifest row (file counts only, as `PROTOCOL.md` section 11 allows); no row,
value or column of them was read. Each item below is a choice the protocol and amendment 1 leave open, fixed with no
outcome in view; none changes a threshold.

1. **One name per company.** NSE's `symbolchange.csv` (Drive snapshot of 13 Oct 2026): a symbol seen on a day becomes
   the latest symbol it was renamed to after that day. Applied to the F&O files, the board-meeting rows, A12's filings
   and the corporate-actions list; the Nifty 500 list (12 Oct 2026) already uses current symbols.
2. **Denominator of criterion 1.** The decision window's events that pass the exclusions of `PROTOCOL.md` section 4
   (and of amendment 1 D3) are the "eligible events"; the excluded ones are counted by reason, never in the share. A
   structure that cannot be built on an analysed event (strike not listed, a leg with close 0 or no trades, debit at
   least the width) stays in the denominator as not fitting.
3. **Price not positive or not below the width.** A debit structure whose debit is 0 or less, or an iron condor whose
   credit is 0 or less (stale closes), is untradable for that event ("price not positive", counted). An iron condor
   whose credit is at least its wider wing is untradable like a debit spread at its width (a riskless credit is a
   stale-price artefact). Both stay in the denominator.
4. **Extra exclusion reasons** beside the protocol's, all counted: no stock-future close on the entry session (no
   underlying price); no listed expiry at least 5 sessions after R; the stock's options not listed on R or K0 not
   listed on R (counted as "corporate action", amendment 1 D3); in the current format, the K0 contract's lot column
   empty on R ("lot unknown on R"). A session in the range without a readable F&O file stops the run (no event is
   ever counted under a wrong reason because a file is missing).
4a. **Filing match.** A12's filing counts for a meeting only if its `period_end` is at most 120 days before D (a late
   or revised filing of an older quarter in the search days is not this event's filing).
5. **Both formats on one day (1 Jan - 5 Jul 2024).** The current format is used; the legacy file of those days is read
   only for the lot-size validation. The validation compares the legacy rule's output (3 of 5 sessions) with the column
   on every F&O stock-session of the overlap; a session where the rule gives no value counts as a miss.
6. **Stage 0's lot-unknown share** = decision-window events left out as "lot unknown" / all decision-window events of
   F&O stocks. **Coverage** counts any results meeting of the stock with D in the quarter
   (before the reschedule rule of amendment 1 D1).
7. **Sessions.** Days with an F&O file from 1 Jan 2019. Days NSE's calendar does not list as regular sessions (for
   example a muhurat session) are kept, because NSE published a file for them, and the run prints them.
8. **Correlation sample.** Events with R in 2019-2021 of F&O stocks, lot known or not (the move needs no lot), leaving
   out an event whose derived legacy lot of the future F (section 7) differs between entry and R (an F&O adjustment);
   each event left out is counted by reason. Clusters as section 7.
9. **Kish counts** use the ICC of |m| (negative values as 0), on the decision-window events analysed and, per
   structure, on the events that pass criteria 1 and 2 per event.
10. **Snapshot.** Symbols as NSE's event calendar and the previous session's F&O file write them. Each stock's lot is
    the chosen expiry's own (its future's lot column on the previous session, else its option rows'). A leg with no
    row in the previous session's file has 0 contracts (lowest tercile), counted; if more than 20% of quoted legs have
    none (for example an expiry-date mismatch), the capture is not used. Not quoted, each counted: a leg not listed in
    Groww's chain, one whose answer arrives at or after 15:00 IST (nothing is asked after that), and one whose request
    fails (never treated as a one-sided quote); a stock whose expiry, lot or chain cannot be had is counted as
    skipped. A crossed quote (ask below bid) counts as one-sided. One Groww `get_quote` per leg, 0.15 s apart. The
    snapshot refuses to start outside 14:00-15:00 IST on a session or without the owner's Drive sign-in.
11. **Writes.** The board-meeting day lists through A12's own librarian (amendment 1 D1); the raw Groww answers to
    Drive's `raw/groww/derivatives/stock-option-quotes/<YYYY>/<MM>/<DD>/` only. The repository gets `results.json`,
    `results.md`, A12's manifest rows and counts.
12. **Runs once, frozen.** `study.py --run` refuses to run when `results.json` or `results.md` exists, when any script
    file's SHA-256 is not in `FREEZE.md`, when the folder has uncommitted changes, or when a raw file is not cached.
