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
2. **"Newest scored close is 2026-10-21, expected 2026-10-22 (stale)" had a real cause in G13b's coverage.**
   - 20 Oct was an NSE holiday (Dussehra). The 21 Oct issue, whose N1 aims at 22 Oct, was never made: the back-fills
     ran to 20 Oct and live issues began with 22 Oct's. (The 16 Oct issue's N3 does aim at 22 Oct.)
   - The G13b builder back-filled the 21 Oct issue on 23 Oct evening (receipts at fe7c4099). It is not scored yet.
   - The page could not tell "no forecast was made" from "a forecast was made and not scored". It now can, from the
     forecasts themselves, live or back-filled.
3. **"Its result appears in tomorrow morning's report" was wrong on a Friday.** The next morning report that checks
   the day is Monday's.
4. **The morning picture failed with a bare "ImportError".** The run's own log is not readable from here, so the
   missing module is not known (reasoning only: Pillow, from `requirements.txt`, was not importable in that run's
   Python). The alert now names the module.

## What changes

1. **The single-file read is O9's** (story/o9-sync-file, on `main` at 787a67a6; the orchestrator: one builder per
   function, so no second reader in `fno/forecast_lab`):
   - `DriveCache.sync(<receipted file>)` now brings exactly that file, verified.
   - A sync that matches nothing is now a problem, not an empty success.
   - `A4hTodayCloses` keeps its `sync(<file>)` calls and keeps every problem for `why_missing`. The page says "A4h's
     close of <day> was not read (<each problem>)", never a silent "not read".
   - An older copy on disk is never used once a sync has reported a problem.
   - `GiftSection` already treated a problem as "not out yet (or not verified)" and is unchanged.
   - The tests now use O9's real `DriveCache` and `ReceiptFolder` with receipts written by its `DataStore`, never a
     fake cache.
2. **The coverage gap is said as such.** `HistorySource.targets` (G13b's live and back-fill records of the current
   method version, scored or not) tells whether a forecast was made for the expected session. When none was, the
   line reads: "no forecast was issued for <day>, so it has no score (a gap in the record, not a late score; newest scored
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
   - `plain.YES_NO` and `plain.VERDICTS` are exposed for the designer's page, so both read one source.
4. **A failed trim names the missing module**: "the picture could not be trimmed: ImportError (module PIL)".

## The 23 Oct verdict, by hand (strong evidence: A4h's verified record, this morning's verified record)

| Index | Close | Most likely | Inside | Almost certainly | Inside | Right |
|---|---|---|---|---|---|---|
| NIFTY | 22,600.00 | 22,530-22,800 | yes | 22,280-23,020 | yes | yes |
| BANKNIFTY | 54,287.35 | 54,500-55,190 | no (212.65 below) | 53,860-55,760 | yes | yes |

## Tests

- New and changed tests:
  - A4h's close and GIFT through O9's real cache: not out yet, damaged, the recheck, and the words for each problem;
  - `targets`: back-fills and unscored issues count, while another method version, a not-eligible row and another
    method do not;
  - a back-filled but unscored day reads "(stale)", and a day with no forecast reads as a gap;
  - the Friday evening names Monday's report;
  - no forecast for today;
  - the yes/no verdicts;
  - the trim's module name.
- Mutations: 10 of 10 caught (one survivor, an older disk copy used past a problem, got its test).
- Real data, read-only, on 23 Oct evening:
  - Closes: 22 Oct NIFTY 22,687.65 and BANKNIFTY 54,925.70; 23 Oct 22,600.00 and 54,287.35. 26 Oct names its two
    missing receipts.
  - `targets` now includes 22 Oct for both indices, from the back-fill. The newest scored day is still 21 Oct, so the
    line says "(stale)" until G13b's score run, which is correct.

## Other stories' tests touched (the text change only)

- MS-P1g's goldens, `tests/school/reports/golden/{morning,evening}.txt`, pin the unwrapped lab maker's text. They were
  regenerated from that same maker, and the regeneration first asserted that the picture hashes, the alerts and the
  verdict count in `files.json` are unchanged. The diff is the title's definition and the record's words only.
- `tests/e2e_acceptance/test_replay_lab.py`: the replay's Drive holds no 15 Oct issue. Its evening now says "today:
  not checked (no forecast was issued for today)", and its status line gives the gap wording, both correct for that
  data.
