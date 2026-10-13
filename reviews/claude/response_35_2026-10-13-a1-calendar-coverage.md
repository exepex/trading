# Response 35: A1 raw NSE archive complete and checked, builder's claims for the judge

Builder: the orchestrator session. Story: `docs/stories/A-data-foundation.md` A1.

**Real run (criterion 4)**, 13 Oct 2026 about 01:05 UTC: `python -m fno data-coverage --from 2019-01-01 --to 2026-10-12`
against the owner's Drive (read-only service account), on main at 769878d. The participant-OI rows belong to A8 and A9
(not in Drive yet) and are left out here:

```
dataset                                    from         to expected present missing damaged
nse/derivatives/fo-bhavcopy-legacy   2019-01-01 2024-07-05     1367    1366       0       0
nse/derivatives/fo-bhavcopy          2024-01-01 2026-10-12      690     690       0       0
nse/indices/index-close              2019-01-01 2026-10-12     1929    1929       0       0
excepted nse/derivatives/fo-bhavcopy-legacy 2021-03-30: Normal trading day (...), but NSE's archive has no old-format F&O bhavcopy for it: 404 from both archive hosts, checked 12 Oct 2026
calendar sha256 6101c8746fe17926498fbfcac895b7aad5218c4653982bba82337b6b5dea3961
```

No "unexpected file" line: no file on any day the calendar calls closed. The exit code was 1 only because of A8's
participant-OI rows (0 of 1,929 in Drive).

| # | Criterion | Claim and evidence |
|---|---|---|
| 1 | The laptop tool saves old-format F&O and index files under `raw/nse/...` with original names and bytes, asking only for the folder | `tools/nse_raw_download/nse_raw_download.py`. Tests: `tests/test_nse_raw_download.py::test_old_years_get_old_format_and_index_files_and_days_without_files_are_asked_once`, `::test_the_tool_uses_exactly_the_archive_layout_and_addresses_of_fno_storage`, `::test_the_folder_comes_from_the_command_line_or_one_question`. |
| 2 | A second run downloads and changes nothing; days known to have no file are not asked again | Same test (second run: `asked == []`), and `::test_verified_files_are_saved_holidays_are_not_asked_and_a_mismatch_is_never_saved`. |
| 3 | One missing old-format day and one flipped-byte zip: `data-coverage` lists exactly those and exits 1 | `fno/storage/coverage.py` (`CoverageCheck.run`, `_check_day`, `report_lines`). Test: `tests/test_coverage.py::test_lists_exactly_the_missing_day_and_the_damaged_file` (a flipped byte in a real deflated zip; validation through A2's `read_fo_file`, zip checksums included). CLI exit code: `fno/cli.py` `cmd_data_coverage`. |
| 4 | The owner's complete upload: every expected session present, checksum- and schema-valid, or a sourced exception | The real run above: 0 missing, 0 damaged in all three datasets. The one gap is a sourced exception (`research/data/calendar/exceptions.csv`, 2021-03-30). The owner uploaded the one file the laptop tool had skipped (index close of 2021-03-30); the tool bug that skipped it is fixed in A8's d59b4b0. |
| 5 | A file on a calendar holiday is reported as "unexpected file" | `_check_day` (non-session day with data). Test: `tests/test_coverage.py::test_file_on_a_closed_day_is_reported_for_review`. The real run found none. |
| 6 | Calendar validated: every holiday and special session has a source link; its commit precedes any coverage result that relies on it | `CsvSessionCalendar._add` refuses a row without an https source, an unknown kind, a weekend "holiday", a weekday "special", or a duplicate. Years without rows refuse the file. Tests: `tests/research_data/test_calendar.py::test_invalid_calendar_files_are_refused` (7 cases) and `::test_committed_calendar_is_valid_and_sourced`. Calendar commit 88e1671 (12 Oct 2026 22:56 UTC) precedes this run, which prints the calendar's SHA-256. Sources: 28 NSE circular URLs, every date read from the PDF text (`research/data/calendar/README.md`). Cross-check: every one of 2,842 days matched NSE's file existence, except 2021-03-30 (the exception). |
| 7 | Only read requests to Drive (a fake Drive that fails on any write) | Test: `tests/test_coverage.py` `ReadOnlyFakeDrive.put` raises; every coverage test uses it. The real store's `GoogleDriveStore.put` raises `ReadOnlyStoreError` (`fno/storage/google_drive.py`). |
| 8 | `SessionCalendar` answers a weekday holiday, a special Saturday and a muhurat session from the file; a day outside the range raises | `fno/research_data/calendar.py`. Tests: `test_weekday_holiday_is_not_a_session`, `test_special_saturday_and_muhurat_sessions`, `test_neighbouring_sessions_skip_closed_days`, `test_day_outside_the_covered_years_raises_instead_of_guessing`. |

**Root causes found and fixed on the way:**
- **Drive token never renewed.** Drive access tokens last about 1 hour and the store never renewed them, so the first
  real run died with HTTP 401 after an hour. Fixed in 8ff011f (token function, one fresh sign-in on a 401; tests).
- **One HTTP 500 killed a whole run.** Fixed in 769878d (retries with growing waits on 429, 5xx and dropped
  connections; tests).
- **Slow serial reads.** Coverage reads 8 files at a time and prints progress per dataset (8ff011f).

**Doubts:**
1. Session hours are not in the calendar. A short special session (e.g. the 2024 DR drills that ended 12:30) is
   known as a session but not its hours (A7's judge noted it; minor).
2. The calendar ends 2026-12-31. A one-shot routine on 15 Dec 2026 adds 2027 from NSE's circular.
3. Rows dated after 12 Oct 2026 cannot yet be checked against files (medium confidence), especially the 8 Nov 2026
   muhurat timing.

Checks on main: `python -m pytest -q` passes (534 on the last run), ruff and the import check are clean, and the record
scan is clean.
