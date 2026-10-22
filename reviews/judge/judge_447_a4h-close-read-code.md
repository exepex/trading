# Judge 447: A4h, today's index close read after 15:30, code (story/a4h-close-read @ 2098a06d)

Judge F (independent). The story text passed in judge 440 addendum 2. Claims:
`reviews/claude/response_312_a4h-close-read-code.md`. Code commit 9fb8618c; head 2098a06d. Lane 1 (NSE, Drive, O1's
steps). Labels: **strong**, **some**, **reasoning only**.

## Verdict: FAIL (1 should fix, 1 minor). Everything else meets the story.

What meets the story, checked:
- The stamp rule decides whether a read counts (today, 15:30 or later), and refusals carry no level.
- Regular sessions only. A special session prints `nothing written:`, so O1 records it `refused`.
- Write-once records in O9's store, with the step's own receipts pathspec only.
- The 16:00 recheck records `same` or `differs by X`. With no first read, it becomes the record ("at recheck").
- The confirm records `confirmed` within 0.01 or `differs by X`. A NIFTY 50 or NIFTY BANK difference alerts; a VIX
  difference is recorded only.
- The overdue alert is sent once, through a write-once mark.
- Both steps are last, after `lab_close`, on the real tuple.
- No printed line or alert holds a level; criterion 8 tests 7 formats.
- The deviations are stated, and each is reasonable:
  - 502 lines of code, not about 270;
  - the raw file is the canonical JSON of the parsed answer;
  - the official file comes from Drive, else NSE's archive (as every reader of it gets it);
  - the worst case is about 5.5 minutes;
  - hand runs leave their receipts to the caller.

## Gates (exact head 2098a06d)

| Gate | Result |
|---|---|
| pytest `-n auto` (no Slack token, no growwapi) | **9208 passed**, 16 xfailed, 355 s |
| `ruff check`, `ruff format --check` | clean, 1729 files formatted |
| `tools/check_imports.py`, `tools/check_records.py` | clean (1819 files); record scan clean (7446 files) |

## My plants (each reverted)

| # | Plant | Caught |
|---|---|---|
| 1 | the 15:30 stamp time not checked | yes, 1 failed |
| 2 | the tolerance strict (0.01 no longer confirms) | yes, 2 failed |
| 3 | the record's values appended to the read line | yes, 1 failed |
| 4 | the overdue mark ignored (an alert every run) | yes, 1 failed |
| 5 | a VIX difference alerts | yes, 4 failed |
| 6 | a special session read like a regular one | yes, 4 failed |

## Should fix

**SF1. A failure while confirming an earlier day loses today's read, at 15:46 and again at 16:00 [strong: a probe
test].**

`CloseReader.run` calls `self.confirmer.run(day)` first, before the calendar check and before the read
(`reader.py`, line 3 of `run`). `Confirmer._confirm` catches only `BadFile`. Everything else propagates:
- the archive source can raise after its retries (`RawSourceCoolingOff`, network errors; `raw_source.py`
  `_response`);
- the Drive store and cache can raise on `get`;
- a write-once `put` can raise on a conflict.

My probe: day 19 Oct recorded and unconfirmed, the official source raising `requests.ConnectionError`, and a good
NSE answer for 21 Oct at 15:46. Result: **`ConnectionError` raised, nothing printed, and no record for 21 Oct.**
The 16:00 recheck runs the same confirm first and fails the same way. So an outage of NSE's archive, or of Drive
reads, on day d+1 or later costs every later day's provisional close until it clears. That is the evening check's
whole input.

The time limit makes it worse:
- NSE's archive source retries 4 times (`RETRY_WAITS = (5, 15, 45)`, a 60 s timeout each), about 5 minutes per
  unconfirmed day in the worst case, before the read starts;
- the read's own worst case is about 5.5 minutes;
- so one slow confirm can push the step past O1's 600 s `COMMAND_LIMIT_SECONDS`, which kills it.

Fix expected:
- **read first, confirm after.** Today's read must not depend on yesterday's official file;
- catch the confirm's failures per day: one line naming the error class (no message, no level), the day stays
  unconfirmed, and the overdue rule still applies. Decide whether a confirm failure alerts on its own or only
  through the overdue alert, and say which;
- add tests:
  - the official source raising, then today's read still recorded and the exit code still 0;
  - a Drive `get` failure on an earlier record, with the same result;
  - the order: the read's line printed before any confirm line.

## Minor

1. **A hand run's confirm alerts from wherever it runs.** Hand runs leave their receipts to the caller (a stated
   deviation). A hand run that confirms a differing day also sends the alert and writes the `.confirm.json`. That is
   fine, but `CLAUDE.md`'s routine text has no A4h section yet. Say in it, or in the story, that a hand run's receipts
   must be committed (`receipts/data/closes/`), or the next routine run will not see the confirm or overdue files and
   will try to write them again (a write-once conflict).
