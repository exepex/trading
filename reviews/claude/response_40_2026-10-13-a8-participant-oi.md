# Response 40: story A8 claims, positioning data source (participant open interest)

**Status: partly built; waiting on the owner's Drive upload (criterion 1 on Drive) and 20 measured release days (the
measured rule in criterion 3).** Everything that can be done today is built, tested and pushed. Builder: Claude
(builder session, claims number 40). Story: `docs/stories/A-data-foundation.md#a8`.

## Verdict in one line

NSE's archive has a participant-OI file for **every one of the 1,929 sessions from 1 Jan 2019 to 12 Oct 2026** and
none on a closed day; the parser reads all 1,929 exactly; a decision on day D cannot see D's file under the default
rule; Drive holds none of them yet, and the release time is not yet measured.

## Criteria

| # | Criterion | Status | Evidence |
|---|---|---|---|
| 1 | Coverage 2019 to today: every session present or a sourced exception; damaged files fail | **NSE archive: MET. Drive: NOT MET (pending the owner's upload)** | below |
| 2 | Parser equals a hand reading of three real files (2019, 2022, 2026) | MET | below |
| 3 | Look-ahead: day D never sees D's file unless the measured rule allows it | **Default rule: MET. Measured rule: built and tested, NOT MET in force (pending 20 measured days)** | below |
| 4 | Raw files stored unchanged with SHA-256, like A1 | MET for the code and the manifest; the owner's copies are checked when the laptop tool runs (pending) | below |

### 1. Coverage

Code:
- `ParticipantOiSource`, `fno/storage/raw_source.py:119`: dataset `nse/derivatives/participant-oi`, URL
  `https://nsearchives.nseindia.com/content/nsccl/fao_participant_oi_DDMMYYYY.csv`, from 2019-01-01.
- In `COVERAGE_DATASETS`, `fno/storage/wiring.py:114`, validated by `validate_participant_oi` (`wiring.py:106`; parser
  plus the day from the file name) wrapped in `FingerprintCheck` (`fno/storage/coverage.py:59`), which also fails a file
  whose SHA-256 differs from the manifest. A1's `data-coverage` command therefore checks the new dataset with no change
  to `CoverageCheck`.
- Library: `build_participant_oi_library`, `wiring.py:80`.

Tests (`tests/test_participant_oi_coverage.py`): `test_participant_oi_is_one_of_the_coverage_datasets`,
`test_a_complete_week_passes_and_a_missing_day_fails`, `test_a_flipped_byte_or_a_file_for_another_day_is_damaged`,
`test_a_file_that_differs_from_its_fingerprint_is_damaged_even_when_it_parses`, all against a fake store that fails on
any write.

Real run 1, NSE's archive. Every calendar day 2019-01-01 to 2026-10-12 (2,842 days) was downloaded through the raw
library (`build_nse_library(ParticipantOiSource, <local folder>)`, polite session, 1 request/s) into a scratch folder.
The coverage check was then run on that folder with the real calendar:

```
dataset                                    from         to expected present missing damaged
nse/derivatives/participant-oi       2019-01-01 2026-10-12     1929    1929       0       0
result: complete
calendar sha256 6101c8746fe17926498fbfcac895b7aad5218c4653982bba82337b6b5dea3961
```

The independent scan agrees: 2,842 days, 1,929 files, 1,929 sessions, no session without a file, no file on a closed
day. No exception rows are needed, so `research/data/calendar/exceptions.csv` is unchanged. Note: **30 Mar 2021**, the
day NSE lacks the old-format F&O file, does have a participant-OI file.

Real run 2, Drive (read-only, the shared folder), the same command path:

```
nse/derivatives/participant-oi       2019-01-01 2026-10-12     1929       0    1929       0
result: INCOMPLETE: missing or damaged files above
```

Drive has none of them: **NOT MET until the owner uploads** (checklist below). After the upload, run
`python -m fno data-coverage --to 2026-10-12`.

### 2. Parser

Code: `fno/research_data/participant_oi.py`.
- `read_participant_oi(data, filename, day)`, line 142, returns per participant (Client, DII, FII, Pro) a
  `Position(long, short)` for six instrument groups, plus the totals.
- It refuses a file:
  - whose title date is not the file's day (`_check_title`, line 75);
  - whose columns are not NSE's 15 (`_rows`, line 85);
  - whose participants are not exactly the four plus TOTAL;
  - with a value that is not a whole number (`_count`, line 108);
  - where NSE's identities fail beyond `ROUNDING_TOLERANCE` (`_check_identities`, line 123): each participant's groups
    add up to its totals, participants add up to TOTAL, and every TOTAL group has long equal to short.

Tests (`tests/research_data/test_participant_oi.py`):
- `test_the_parser_returns_the_numbers_read_by_hand` checks all 4 participants x 7 positions x long/short (56 numbers
  per file) for `tests/fixtures/nse/fao_participant_oi_03062019.csv`, `..._03012022.csv` and `..._09102026.csv`. The
  expected values were transcribed from the raw CSV text with the column order written out in the test, not with the
  parser's mapping.
- Damage, format and variant tests: 17 cases.

What all 1,929 real files taught (each found by running the parser over the full download; every variant has a test):
- **Rounding.** NSE's sums can be off their parts: 805 files exact, 991 files 1 off, 131 files 2 off, none more. The
  root cause is that each participant's figure is rounded separately (for example, 18 Mar 2019 Future Stock Short:
  participants add up to 1,924,326 against TOTAL 1,924,324). The tolerance is therefore 2 (`participant_oi.py:33`).
- **Titles typed by hand** in 2019-2020: "January 01, 2019", "Aug 05 2019", `Aug 20,"2019"`, "Feb 28 ,2020", stray
  quotes. 8 Jun 2021 has **no year**: then month and day must still match.
- **12 Dec 2019** FII row: `"10,02,064.00"` (Indian grouping, zero fraction) is read; a real fraction or a minus sign
  is refused.
- **22 Feb 2024**: a 16th column with no header name, filled only in the FII row (6,850,707, FII's long plus short).
  Unnamed columns are ignored; a named extra column is refused.
- Result: `parsed 1929 refused 0`.

To re-read one file by hand: open `tests/fixtures/nse/fao_participant_oi_09102026.csv`. The FII row reads
`34943,328931,3542863,2867395,600034,1245164,946852,704672,197429,316370,347630,186717,5936804,5382197`. The test
expects future index (34943, 328931), future stock (3542863, 2867395), index call (600034, 946852), index put
(1245164, 704672), stock call (197429, 347630), stock put (316370, 186717), totals (5936804, 5382197).

### 3. Look-ahead and the release-time rule

Code:
- `fno/research_data/availability.py`:
  - the `AvailabilityRule` interface (line 36);
  - `NextSessionRule` (line 49), the default: usable from the next session's decision time;
  - `MeasuredReleaseRule` (line 62): usable `lag` sessions after the file's day.
  - The lag is counted **in sessions, not hours**: an hours-based rule (my first version) let a weekend hide a file
    published after the next session's decision. The test caught it, and the design was changed.
- `fno/research_data/release_times.py`:
  - the append-only `ReleaseLog`;
  - `first_seen_times` (line 64): a day counts as measured only when the log shows it absent, then present;
  - `choose_availability_rule` (line 75): the default below `MIN_MEASURED_DAYS = 20` (line 26), else the largest lag
    seen, with a 30-minute margin;
  - `ReleaseTimeRecorder` (line 86).
- `fno/research_data/positioning.py:26`: `PointInTimeParticipantOi.as_of(decision_moment)` checks the rule
  **before** asking for a file, so D's file is never even fetched for D's decision.
- Wiring, in `fno/composition.py`:
  - `DESK_DECISION_TIME = 15:00` IST (line 34; E3 freezes the exact timetable);
  - `build_release_time_recorder` (line 74), which asks NSE directly and never Drive;
  - `build_participant_oi_rule` (line 84), set from the committed log;
  - `build_point_in_time_participant_oi` (line 90).
- CLI: `python -m fno participant-oi watch [--day] [--until HH:MM] [--every MIN]` and `python -m fno participant-oi
  rule` (`fno/research_data/participant_oi_cli.py`).

Tests (`tests/research_data/test_participant_oi_availability.py`):
- `test_by_default_a_decision_on_day_d_never_sees_ds_file`: Friday 15:00 and 23:59 see Thursday's file, Monday 14:59
  still Thursday's, Monday 15:00 sees Friday's;
- `test_the_default_skips_holidays_and_weekends`;
- `test_the_default_holds_until_twenty_days_are_measured` (19 days: default; 20: measured);
- `test_only_a_measured_rule_can_let_day_d_see_ds_file`;
- `test_measured_evening_releases_give_the_next_session_and_a_late_one_pushes_further`;
- `test_a_day_counts_as_measured_only_when_seen_absent_before_present`;
- two recorder tests (logs every check, stops at the cutoff, skips closed days, never re-asks a seen day);
- `test_the_wired_rule_follows_the_committed_evidence_file`;
- two CLI tests.

Evidence on file:
- `research/data/participant_oi/release_checks.csv` exists with its first two real rows (13 Oct 2026, 06:06 IST): 12 Oct
  `present` (SHA-256 `8ceb5e8a…`, identical to the manifest), which does not count as measured because it was never
  seen absent; and 13 Oct `absent`.
- `python -m fno participant-oi rule` prints `rule: next session at 15:00 IST (the default until release times are
  measured); measured days: 0 of 20`.

Supporting evidence, not the measurement: `research/data/participant_oi/archive_last_modified_2026-10-13.csv` (NSE's
Last-Modified for all 1,929 files; see the README there):
- 0 files were last written before 15:00 on their own day;
- 1,824 (94.6%) were last written before the next session's 15:00;
- 105 were written later (95 of them in 2019 batch rewrites).

**NOT MET (pending):** the measured rule needs 20 bracketed days from a scheduled run (proposal below).

### 4. Stored unchanged, with SHA-256

- The raw library and stores keep NSE's bytes and names unchanged, and refuse different bytes at an existing path (A1's
  `RawFileStore.put`).
- New: `tools/nse_raw_download/manifest_participant_oi.csv`, with all 2,842 days (1,929 files with SHA-256, 913 days
  without a file), in the same format as the F&O manifest.
- The laptop tool now has the dataset (`tools/nse_raw_download/nse_raw_download.py:77`). It checks every download and
  every existing copy against the manifest (`load_manifests`, line 114) and never re-asks the known no-file days. It
  fetches participant OI independently of the F&O file (line 249); otherwise 30 Mar 2021 would be skipped.
- Coverage fails any file whose SHA-256 differs from the manifest (`FingerprintCheck`).
- Tests:
  - `test_participant_oi_is_checked_against_its_own_manifest_and_its_known_gaps_are_not_asked`;
  - `test_the_shipped_participant_oi_manifest_is_read`;
  - `test_the_committed_real_files_match_nses_fingerprints_in_the_manifest`;
  - the existing laptop-tool tests, adjusted for the new dataset (requests counted per dataset).

## Command output (13 Oct 2026, after merging main at 8ff011f)

```
python -m pytest -q                      -> 492 passed
A8 tests + laptop tool tests             -> 43 passed
ruff check fno tests tools               -> All checks passed!
ruff format --check fno tests tools      -> 102 files already formatted
python tools/check_imports.py            -> clean: 109 files, 1 archival skipped
python tools/check_records.py            -> record scan: clean (305 files)
tests/test_code_size.py                  -> 110 passed (largest new file 152 lines)
```

## Owner's step (checklist)

1. On the laptop, get the latest repository and run `tools/nse_raw_download/nse_raw_download.py` (double-click). Give
   it the same folder as before.
2. It downloads only what is new: participant OI, 1,929 small files (under 1 KB each), about 35 minutes at one request
   a second. It prints `MISMATCH` if any file differs from the fingerprints; tell Claude if it does.
3. Drag the `raw` folder into `fno-research` on Drive and choose "skip" for files that already exist.
4. Tell the orchestrator. A session then runs `python -m fno data-coverage --to 2026-10-12` and records the output for
   criterion 1.

## Proposed routine (not created; the orchestrator decides)

Name "A8 participant-OI release times". **Every day** (weekend special sessions such as Budget days and muhurat
trading need a run too; on a closed day `watch` records nothing and ends at once), starting about 17:11 IST
(`CRON_TZ=Asia/Kolkata 11 17 * * *`), a fresh session. Text:

> Story A8 release-time recorder. Research data only; never places orders. 1. `pip install -q -r requirements.txt` and
> `git config core.hooksPath .githooks`. 2. `python -m fno participant-oi watch --until 23:30 --every 5` (checks NSE's
> archive every 5 minutes until today's participant-OI file appears; on a non-session day it records nothing). 3.
> Commit `research/data/participant_oi/release_checks.csv` and push to `main` (`git pull --no-rebase` first). Never
> edit or delete a row; never use `--no-verify`. 4. If the result is `absent` at 23:30 or `unreachable`, post one line
> to #fno-desk (`C0C89E8QCCD`) and note it in `conversations/<date>.md`. 5. Print `python -m fno participant-oi rule`.

Why 17:11 to 23:30: of the 1,751 files last written on their own day, the earliest was at 17:22 IST (21 Oct 2025, a
muhurat day with an afternoon session), 11 before 17:45, and 9 at or after 22:30. A release before the first check
leaves that day unmeasured, never wrongly measured: a day counts only when it is seen absent first. A run can last up
to about 6 hours and makes at most about 75 requests. A file not seen by 23:30 is a finding in itself. Twenty
measured sessions take about four weeks.

## Doubts and limits (with confidence)

1. **NSE rewrites archive files after publishing (strong evidence: 105 Last-Modified times after the next session,
   including 15 Jan 2024 rewritten on 15 Jan 2025).**
   - A historical study reads today's version, which may differ from what was public then, and on those days the file
     may have appeared late.
   - The next-session rule cannot fix this.
   - Proposal for the owner and the judge: mark those 105 days as "late or rewritten" in any E6 study, or treat
     Last-Modified as a conservative per-day upper bound for history. That is not built here: the story fixes the rule
     at "20 measured days".
2. **The measured rule applies one lag to all of history (reasoning only).** It is measured on 2026 days only. For
   2019 the batch rewrites make the real 2019 release times unknowable.
3. **The tolerance of 2 lets a small corruption pass the identity checks (reasoning only).**
   - For every manifest file, the SHA-256 check catches it.
   - For a file newer than the manifest, only the identities guard it, until the laptop tool's next run records it.
4. **Decision time 15:00 is an assumption until E3 freezes the timetable.** It is one constant
   (`fno/composition.py:34`). With the default rule it matters only for which minute the next session's decision may
   use the file.
5. **The recorder's 5-minute steps give an upper bound only.** The first `present` time can be up to 5 minutes after
   the real release. That is the safe side.
6. Out of scope, as the story says: no signal, dashboard or API use.

## Addendum (13 Oct 2026): orchestrator's scope notes

- **Raw files stay out of GitHub (owner's ruling, relayed by the orchestrator).** The full participant-OI set is
  1,929 files, 1,805,141 bytes. It was measured, not committed, and no repository store was added. Drive coverage
  (criterion 1 on Drive) stays **pending** the upload route the orchestrator is settling with the owner.
- **Laptop-tool fix: index closes on trading days without an F&O file.**
  - Root cause: the tool treated "an F&O file exists" as "trading day". On 30 Mar 2021 NSE has no old-format F&O file
    but publishes `ind_close_all_30032021.csv` (HTTP 200, 8,474 bytes, checked 13 Oct 2026), so the owner's archive
    lacks that file.
  - Fix: a trading day is now any day NSE published a derivatives file, F&O or participant OI (participant OI is
    fetched first, independently).
  - Tests: `test_index_closes_are_fetched_on_a_trading_day_without_an_fo_file` (that exact day) and
    `test_index_closes_are_not_asked_on_a_day_without_any_derivatives_file`.
  - Owner effect: the next laptop run also fetches that one missing index-close file.
