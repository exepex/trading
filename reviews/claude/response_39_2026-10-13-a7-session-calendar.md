# Response 39: story A7, every component uses the session calendar (builder claims)

**Status:** built; awaiting judge
**Story:** `docs/stories/A-data-foundation.md#a7-every-component-uses-the-session-calendar`

## What changed

- `fno/quotes/recorder.py`: `QuoteSnapshotRecorder` takes a `SessionCalendar` (line 87). `record()` asks
  `_session_kind(day)` (lines 107-109, 129-133) and records only on `regular` and `special` sessions
  (`RECORDED_SESSION_KINDS`, line 38). A calendar session with no same-day trade is no longer "not a trading day": the
  attempt gets the failure `calendar says session, no same-day trades` (lines 163-166), so it is kept incomplete,
  retried to 15:10 and the day's canonical becomes `none`. `RecordResult.reason` carries why (lines 82, 182-183).
- `fno/quotes/cli.py`: `record_today` (line 44) prints the result line (plus the reason), posts an alert to #fno-desk
  for the cross-check (lines 59-60) and stops loudly on a `CalendarError` (lines 50-56: message, file path, alert,
  exit 1). `exit_code` (line 64) keeps A4's mapping and adds: cross-check failure is always exit 1.
- `fno/research_data/calendar.py`: the out-of-range message (`OUTSIDE_RANGE`, line 26, used at line 100) now says what
  to do: add every row of NSE's `<year>` holiday circular, with source links, to the calendar file.
- Wiring: `build_session_calendar()` in `fno/storage/wiring.py:99` (also used by the coverage check, line 96, DRY);
  `fno/composition.py:29` injects it into the recorder.
- `CLAUDE.md` routine steps 2 and 4: the calendar decides the day; the command posts its two alerts itself.

## Criteria

| # | Criterion | Code | Test |
|---|---|---|---|
| 1 | Special Saturday session with same-day trades is recorded with a canonical snapshot | recorder.py:107-109, 38 | `test_a_special_saturday_session_is_recorded_with_a_canonical_snapshot` |
| 2 | Weekday holiday: nothing recorded, "not a trading day" | recorder.py:107-109 | `test_a_weekday_holiday_records_nothing_and_never_asks_the_provider` (provider fails the test on any call; no files) |
| 3 | Calendar session, no same-day trades: attempt kept with `complete=false` and the stated reason, run exits non-zero, no day silently skipped | recorder.py:163-166, 182-183; cli.py:59-60, 64-68 | `test_a_session_without_same_day_trades_is_kept_incomplete_retried_and_ends_none` (every attempt kept, reason in every meta, canonical `none`); `test_the_command_exits_non_zero_and_alerts_on_the_cross_check` (exit 1, one alert, also for `--outside-window`) |
| 4 | All A4 tests and the four byte-identical baseline scenarios pass unchanged | constructor default `calendar=None` keeps A4's inference (recorder.py:87-91, 131-132, 164-165) | `tests/quotes/test_quote_recorder.py` and `tests/quotes/test_recorder_baseline.py` untouched (`git diff --quiet origin/main -- ...` passes); extra: `test_with_the_real_calendar_the_baseline_bytes_are_unchanged` runs the four baseline scenarios with the real calendar injected and gets the same bytes |
| 5 | A day outside the calendar fails loudly (no guess) | calendar.py:26, 99-100; cli.py:50-56 | `test_a_day_outside_the_calendar_fails_loudly_and_says_what_to_add` (CalendarError, exit 1, message names the 2027 circular and the file, alert sent, no files); `test_an_invalid_calendar_file_also_stops_the_command` |

Also: `test_the_app_builds_the_recorder_with_the_repository_calendar` proves the real command path injects the
repository calendar (1 Feb 2025 Saturday and 1 Feb 2026 Sunday Budget sessions are `special`, 20 Oct 2026 Dussehra is
closed, 13 Oct 2026 is a session); `test_an_ordinary_weekend_day_is_closed_and_a_muhurat_day_says_why`;
`test_other_exit_codes_are_unchanged`.

## Command output (13 Oct 2026, about 04:45 IST)

```
$ python -m pytest -q tests/quotes/test_recorder_calendar.py
15 passed
$ python -m pytest -q tests/quotes/test_recorder_baseline.py tests/quotes/test_quote_recorder.py
16 passed
$ git diff --quiet origin/main -- tests/quotes/test_recorder_baseline.py tests/quotes/test_quote_recorder.py tests/fixtures
(exit 0: unchanged)
$ python -m pytest -q
404 passed
$ ruff check fno tests tools          -> All checks passed!
$ python tools/check_imports.py       -> clean: 98 files, 1 archival skipped
$ python tools/check_records.py       -> record scan: clean
```

Real calendar, simulated 1 Jan 2027 through `record_today` (no Slack token in this session):

```
3 pm quote recorder stopped, nothing recorded: 2027-01-01 is outside the calendar (2019-01-01 to 2026-12-31): add
every row of NSE's 2027 holiday circular (weekday holidays, weekend special sessions, the muhurat session), each with
its https source link, to the calendar file (research/data/calendar/nse_sessions.csv)
alert NOT sent: FNO_SLACK_BOT_TOKEN is not set
exit 1
```

## Other components that decide "is today a session"

Searched `fno/`, `tools/`, `.claude/` for `weekday`, `holiday`, `WEEKEND`, `is_session`, `trading day`:
- `fno/quotes/recorder.py`: converted (this story).
- `fno/storage/coverage.py`: already asks the calendar (A1); now through the shared `build_session_calendar()`.
- `fno/providers/sample.py:29`: computes a sample expiry weekday, not a session decision; not changed.
- `tools/nse_raw_download/`: the laptop download tool learns closed days from NSE's published files and its manifest;
  it is not a scheduled component and does not import `fno`; not changed.
No other scheduled component exists in the code today.

## Doubts and limits (please check)

1. **The routine only fires on weekdays (strong evidence: CLAUDE.md "on weekdays"; the trigger is at 14:48 IST
   weekdays).** The recorder now records a special weekend session, but the trigger never starts it on a Saturday or
   Sunday, so such a session would still be lost. Fix outside this code: run the trigger every day; on closed days the
   command prints "not a trading day" and exits 0. I did not change the trigger (the orchestrator owns it).
2. **No-calendar mode kept for the A4 tests (reasoning only).** Criterion 4 requires the A4 tests unchanged, and one
   of them expects a weekday with no same-day trade to be "not a trading day". That is only possible if a recorder
   built without a calendar keeps A4's inference. The app never builds it that way (test above). The judge may prefer
   the A4 test updated instead; that would break criterion 4 as written.
3. **Behaviour change on a missing Groww login (some evidence: `Provider.quote_book` returns None for the NSE
   provider, `fno/providers/base.py:39-42`).** Under A4, with `quotes.provider: auto` and no Groww credentials, every
   row had no trade time, so every weekday quietly ended "not a trading day", exit 0. Now that is a cross-check failure:
   attempts kept, canonical `none`, alert, exit 1. This is the intended "never silently skipped", but the first real
   run (13 Oct) will alert if the Groww credentials are missing.
4. **Muhurat days are skipped (reasoning only).** The calendar has no session hours; muhurat sessions are one hour
   (18:00-19:15 in most years, 13:45-14:45 in 2025), never covering 14:55-15:10, so the recorder skips them with the
   reason "muhurat session only". Short weekend special sessions (the 2024 DR drills ended 12:30) would still be
   attempted; their quotes would be after the close. Fixing that needs session hours in the calendar file (A1 scope).
5. **Calendar fingerprint not in the meta (reasoning only).** `SessionCalendar.calendar_sha256` says results that rely
   on the calendar record it; adding it to `meta.json` would break the byte-identical baseline (criterion 4), so it is
   not recorded.
6. **Yearly update needed:** the calendar ends 2026-12-31. On 1 Jan 2027 the recorder stops with the message above
   until NSE's 2027 circular rows are added. A yearly task should add them each December once NSE publishes the list.

## A5 judge-7 fix (finding 1: the recorder used a different monthly rule)

**Finding accepted** (reproduced: on NSE's real 2 Apr 2025 list the old recorder rule gives [30 Apr, 29 May]; 30 Apr
was a weekly moved for a holiday, the monthly was 24 Apr).

**Fix:** the recorder now uses A5's single definition, `research_data.expiries.monthly_as_of`.
- `fno/quotes/monthly_contracts.py` (new, `PointInTimeMonthlies`, line 34 calls `monthly_as_of`). An expiry more than
  `MONTHLY_LISTING_DAYS` (50) ahead today is monthly from today's list. For a nearer one it reads NSE's file of the
  latest day on or before `expiry - 51 days`. A contract stays listed from its listing day to its expiry, so a monthly
  is in that file and a weekly (never listed more than 42 days ahead) is not. Same answer as `monthly_as_of` over the
  full history, with one file per near expiry. Files are cached, so later attempts in the window read nothing again.
- `fno/quotes/expiry_listing.py:32-34`: new interface `ExpiryHistory.listed_on(underlying, day)`.
  `NseDailyFileExpiries` implements it (lines 46-47) through one shared `_latest` reader (line 49). `listed()` still
  looks only at the 7 days before today.
- `fno/quotes/recorder.py:90, 96, 140-151, 158, 162, 197`: with `history` the recorder picks the nearest two monthlies
  by that rule, and meta.json gets `monthly_check` = `{"status": "verified", "rule": ..., "files": [...]}` (the NSE
  files that proved it: source, file, date, SHA-256). Without `history` (the A4 tests and baseline) the old
  last-of-month rule stays, as for the calendar.
- Unreadable history (orchestrator's decision, accepted: a lost day of quotes can never be recorded later, a flagged
  contract choice can be checked later): the recorder falls back to the last-listed-expiry rule, keeps `complete` as
  the quotes themselves warrant, writes `monthly_check` = `{"status": "unverified", "rule": "last listed expiry of
  month", "reason": "..."}` and the command alerts #fno-desk (`fno/quotes/cli.py`, `MONTHLY_UNVERIFIED_ALERT`).
  A later verification finds every fallback day by `monthly_check.status == "unverified"`.
- `fno/composition.py:31`: the app passes the same `NseDailyFileExpiries` as `history`.

**Tests** (`tests/quotes/test_monthly_contracts.py`, 9 tests, all pass):
- `test_the_holiday_moved_weekly_of_30_april_2025_is_not_taken_for_the_monthly`: gives [24 Apr, 29 May].
- `test_the_recorder_records_the_24_april_monthly_and_the_files_that_proved_it`: the full recorder on 2 Apr 2025.
- `test_an_unreadable_history_keeps_the_quotes_flags_the_choice_and_alerts`: complete quotes, exit 0, fallback
  contracts [30 Apr, 29 May] recorded with `monthly_check.status = "unverified"` and its reason, one alert.
- `test_earlier_files_are_read_once_across_retries`.
- `test_nse_files_answer_on_or_before_the_day_and_listed_keeps_looking_only_before_today`.
- `test_with_a_consistent_history_the_baseline_records_the_same_contracts` (4 scenarios): with a history consistent
  with the baseline lists, the CSVs are byte-identical and meta.json is identical except for the added
  `monthly_check`.
- Mutation check: forcing the old rule back makes 2 of these tests fail.

**Baseline:** none of the four scenarios changed. They build the recorder without `history`, and
`tests/quotes/test_recorder_baseline.py`, `tests/quotes/test_quote_recorder.py` and `tests/fixtures` are unchanged
against origin/main.

**Real NSE data** (files from the shared Drive, which mirrors NSE; NSE's archive also answered directly):

```
2025-04-02  A4 last-of-month: [2025-04-30, 2025-05-29]   A5 point-in-time: [2025-04-24, 2025-05-29]  (5 files, 9.0s)
2025-08-18  A4 last-of-month: [2025-08-28, 2025-09-30]   A5 point-in-time: [2025-08-28, 2025-09-30]  (6 files)
2026-10-09  A4 last-of-month: [2026-10-27, 2026-11-23]   A5 point-in-time: [2026-10-27, 2026-11-23]  (6 files, 14.2s)
```

Dry run of 13 Oct 2026 at 14:55, built from the real parts (real calendar, real NSE history, fake provider listing
the 9 Oct expiries, temporary store): `recorded, complete=True`, expiries [2026-10-27, 2026-11-23], no failures,
`monthly_check.files` = the 21 Aug, 28 Aug, 4 Sep, 11 Sep, 18 Sep and 1 Oct 2026 files. The first attempt took 15.8 s.

**Doubts:**
- The first attempt of each day reads about 6 NSE files (about 15 s, from Drive or NSE). The live run of 13 Oct picks
  the same contracts as before (27 Oct, 23 Nov). If Drive and NSE are both unreachable, the quotes are still recorded
  with the fallback rule's contracts, flagged "unverified" and alerted (see above).
- Left as minor, by the orchestrator's decision: judge-7 minor finding 3 (two functions named `monthly_expiries`) is not renamed: the unchanged A4 test imports
  `fno.quotes.recorder.monthly_expiries`. Minor finding 2 (a data check on the 42-day weekly horizon) is not in scope here.
