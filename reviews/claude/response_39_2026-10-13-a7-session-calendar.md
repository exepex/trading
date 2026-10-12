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
