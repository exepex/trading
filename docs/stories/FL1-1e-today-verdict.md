# FL1-1e: the evening's verdict for today (23 Oct 2026 fixes)

Lane 1. Builder: session_01FWkBH4zNAEFSEpjUzVEgnd. Asked by the orchestrator after the owner's complaint about the
20:05 edition of Fri 23 Oct. Branch `story/fl1-1e-today-verdict`, for Judge E.

## What went wrong on 23 Oct (root causes, strong evidence)

1. **"Today's close was not read" was false.**
   - A4h's record `data/closes/2026/10/2026-10-23.json` was in Drive, with its receipt on `main` (committed by the
     desk run's `close_read` step at 15:40 IST). Its NSE stamp was "23-Oct-2026 15:30", and its SHA-256 matched.
   - `A4hTodayCloses` called O9's `DriveCache.sync(<file path>)`. `sync` takes a folder:
     `ReceiptFolder.under(prefix)` returns nothing when the prefix is not a folder. So the report was empty, with no
     problem, nothing was downloaded, and the close read as missing.
   - Every evening since A4h merged (22 Oct) was affected. GIFT Nifty in the morning used the same call, so it could
     never have been shown either.
   - The tests missed it because their fake cache accepted a file path.
2. **"Newest scored close is 2026-10-21, expected 2026-10-22 (stale)" was wrong framing.**
   - No forecast targets 22 Oct. G13b's back-fill ends with the 19 Oct issue, and its live issues begin with 22 Oct's
     (aimed at 23 Oct). The 20 and 21 Oct issues do not exist (asked of the G13b builder).
   - A day without a forecast can never be scored. That is a gap in the record, not a late score.
3. **"Its result appears in tomorrow morning's report" was wrong on a Friday.** The next morning report that checks
   the day is Monday's.
4. **The morning picture failed with a bare "ImportError".** The run's own log is not readable from here, so the
   missing module is not known (reasoning only: Pillow, from `requirements.txt`, was not importable in that run's
   Python). The alert now names the module.

## What changes

1. **One verified single-file read**, `fno/forecast_lab/verified_file.py` (`VerifiedFiles`):
   - the file's own receipt, then `drive.get`, then the SHA-256 check;
   - no receipt means "not out yet" (None);
   - a receipted file that Drive lost or changed raises `Unverified` (missing or damaged), never a value.

   A4h's close, GIFT Nifty and the editions' own records all use it, and the records lose their copy of the same
   steps. `page_wiring.verified_files()` builds it over the Drive and receipts O9's cache uses.
   - A damaged A4h record is named as such ("could not be read verified"), never as "not read".
   - The storage-level guard (a `sync` that matches nothing becomes a problem) is O9's module. The orchestrator is
     asking its owner, so it is not in this branch.
2. **The coverage gap is said as such.** When the expected session has no issued next-session forecast, the line
   reads: "no forecast was issued for <day>, so it has no score (a gap in the record, not a late score; newest scored
   close <day>)". When a forecast was issued and is not scored, the line still says "(stale)".
3. **The evening answers its title first** (owner, through the orchestrator, 23 Oct). The Slack text:
   - The title line defines the word: "Right = the close fell inside the “almost certainly” range."
   - Each index line starts with today. When it is checked: "today: closed 22,600.00 (NSE's close; the official file
     confirms it in Monday's morning report) · inside “most likely”: yes · inside “almost certainly”: yes → ✓ right".
   - When it is not checked: "today: not checked yet (NSE close not read); result in Monday's morning report". With
     no forecast: "today: not checked (no forecast was issued for today)".
   - The record reads: "past 30 days (back-tested 30): inside “almost certainly” 25 of 30".
   - The morning's check of the previous session uses the same words.
   - The confirming morning report is named from the calendar's next session: "tomorrow's" only when that is the next
     calendar day, otherwise the weekday ("Monday's").
   - The page model gains `IndexView.unchecked` (close not read, or no forecast) and `PageView.next_session`.
   - The picture is the designer's (frozen at d8f0440). The designer gets these exact words to adopt; the picture does
     not change in this branch.
4. **A failed trim names the missing module**: "the picture could not be trimmed: ImportError (module PIL)".

## The 23 Oct verdict, by hand (strong evidence: A4h's verified record, this morning's verified record)

| Index | Close | Most likely | Inside | Almost certainly | Inside | Right |
|---|---|---|---|---|---|---|
| NIFTY | 22,600.00 | 22,530-22,800 | yes | 22,280-23,020 | yes | yes |
| BANKNIFTY | 54,287.35 | 54,500-55,190 | no (212.65 below) | 53,860-55,760 | yes | yes |

## Tests

- Real O9 parts (a local Drive folder, the receipts written by O9's `DataStore`) replace the fake caches in the A4h
  and GIFT tests.
- New tests:
  - verified, not out yet, missing, damaged;
  - the damaged record's words;
  - the wiring;
  - the true-stale and gap wording;
  - the Friday evening naming Monday;
  - no forecast for today;
  - the yes/no verdicts;
  - the trim's module name.
- Mutations: 8 of 8 caught. They removed the SHA check, turned "missing" into None, dropped the damaged-record words,
  ignored "issued", always reported "close not read", always said "tomorrow", judged by the 50% range, and dropped the
  module name.
- Real data, read-only, on 23 Oct: the fixed reader returns NIFTY 22,687.65 and BANKNIFTY 54,925.70 for 22 Oct, and
  22,600.00 and 54,287.35 for 23 Oct. For 24 Oct (no session) it returns nothing.
