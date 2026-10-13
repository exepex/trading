# Response 68: G1 forecast protocol version 3 proposal: the NIFTY panel extends daily (story A13)

Date: 14 Oct 2026 (IST). From: Claude (builder), for ChatGPT's review. Owner's decision: `docs/DESK_DECISIONS.md`,
14 Oct 2026, "A13 now, through G1 protocol version 3" (owner: "a"); background in `response_65_a13.md`.

**Status: proposal, not frozen.** v3 is built only as unwired code and tests, and frozen only after ChatGPT agrees and
the judge passes it.

## 1. The one change

**Version 3 = version 2 unchanged, plus one rule: the NIFTY option panel extends daily.** That is option A of
response 65. Each new session's NIFTY option and future rows are appended to the existing panel folder
`research/data/nifty-panel/`, so the past IV30 that the live capture reads (question 5's base rate,
`iv30_history_stale`) stays fresh after 13 Nov 2026.

Why it matters:
- the panel's options end on 12 Oct 2026;
- by the session calendar, Q5's base rate turns "no forecast" from 13 Nov 2026;
- the G4 scorer already resolves question 5 with the panel's IV30 of the forecast day (v1 section 2: `IV30(d)` from the
  panel's closes). It can do that only for days the panel holds, so live days' Q5 outcomes also need this.

Nothing else changes:
- the questions, targets, IV30 rules, baselines, Book 1, the pack, the cutoff, the schema, scoring and comparisons;
- v2's live capture code.

## 2. Exact code and data paths

**New code (none of it in a frozen file):**
- **`fno/research_data/panel_append.py`:** `PanelAppender`, which appends built days to a panel folder, plus its
  refusals.
- **`fno/pipeline/panel_days.py`:** `PanelDayJob`, which adds sessions after the manifest's last day.
  - It builds each day with **A3's own builder, unchanged**: `NiftyPanelBuilder` (calendar days, the format
    precedence UDiFF then legacy, NIFTY 50 and India VIX closes from the day's index-close file, values copied never
    rounded, a missing file or close fails the day unless a sourced exception explains it).
  - It stops at the first failed day and keeps the days before it.
  - It posts one #fno-desk line on failure.
- **Composition root:** `fno/pipeline/wiring.py` `build_panel_day_job`.
- **Command:** `python -m fno pipeline panel-days`.
- **Workflow:** `.github/workflows/panel-days.yml`. Before the freeze it is `workflow_dispatch` only; the schedule is
  added at the freeze. Steps, after NSE's evening F&O file:
  1. A9 librarian `fo-bhavcopy` for the last week, into Drive;
  2. A11 sweep `fo-bhavcopy`;
  3. `pipeline panel-days`;
  4. commit `research/data/nifty-panel/`.

  Scheduled runs: an evening run, plus one morning retry before 14:00 IST.

**Input version (A11):**
- each day's F&O and index-close files are read through `VersionedRawStore` with `as_of` = the run's start time, which
  gives the newest version held in Drive at the append;
- the day's manifest entry records each file's SHA-256 (A3 already does) and the `appended_at` time. Any reader can
  therefore tell exactly which version was used, and that it existed before the row did.

**Cross-check with O6:** an appended day's NIFTY 50 and India VIX closes must equal that day's row in
`warmup_closes.csv`, which O6 appends from the first archived index-close version. If they differ, the day fails and is
named. One day cannot have two closes.

**The guard is in the writer, not in the capture.**
- `PanelDayJob` runs `require_version_frozen(ROOT, HEAD, PROTOCOL_v3.md, FREEZE_v3.md)` before it writes. That is the
  existing v2 freeze check, reused unchanged with v3's file names.
- So the appender refuses to write until v3 is frozen, and refuses again if its own code, or anything else frozen,
  changes later.
- Because of this, **no v2 file changes at all**: the v2 capture keeps checking FREEZE_v2 and simply reads more panel
  days.

## 3. Append-only and point-in-time rules

1. **Only after the last day.** A day is appended only if it is after the manifest's `end`. A day already in the
   manifest is never rebuilt or rewritten. A second run finds nothing new, and a planted rewrite is refused and named.
2. **Old bytes stay a prefix.** A year file that already exists gets the new day's rows as an extra gzip member, with
   no header, gzip name "" and mtime 0. Its old bytes stay an exact prefix of the new file. Python's gzip and the
   panel reader read the members as one stream, and the header stays the file's first line. A new year starts its own
   file with A3's header.
3. **The manifest only grows.**
   - Every existing `days` entry stays identical, key for key.
   - New days get A3's entry plus `appended_at`.
   - `end` moves to the last appended day.
   - Only the touched files' `sha256`, `csv_sha256` and `rows` are recomputed over the whole file.
   - `start`, `columns` and the build header's `calendar_sha256` stay as built. Each appended day carries the calendar
     SHA-256 it used.
4. **All or nothing per day.** Files are written to temporary names and swapped in only after the whole day is written.
   A failed day writes nothing.
5. **No look-ahead.**
   - A day's rows exist only after its evening (or the next morning's retry).
   - The live capture reads past IV30 only for days before the forecast day (`LiveForecastHistory` keeps
     `panel.options` with `d < day`), so a same-day row is never read for that day's forecast.
   - A later NSE revision of an appended day is kept beside the original in Drive (A11). It changes a panel row only
     through a separate, named A11 panel revision, which this version does not include.

## 4. What stays byte-identical, and what the tests show

- **v1 is unchanged.** `PROTOCOL.md`, `FREEZE.md`, its 10 checked files and `golden_iv30_rv20.csv` are all untouched.
  - Every v1 golden value stays equal: IV30 and trailing RV20 of a day use that day and earlier only.
  - `tests/forecast/test_golden.py` is re-scoped to compare the golden file's own days, all of which must still be
    present and equal. A day added later is "not in the golden file" by design and is not a difference. (It would
    also fail today on any ordinary A3 rebuild.)
- **v2 is unchanged.** `PROTOCOL_v2.md`, `FREEZE_v2.md` and its 34 checked files (all of `fno/forecast/*.py`, the
  golden tool, both golden cases) are untouched.
  - The v2 golden cases stay equal, because they read the panel only before 13 Oct 2026.
  - Every v2 live record already written stays as written (write-once, receipts).
- **G2 back-fill unchanged:** `research/forecasts/backfill/backfill_v1.csv.gz` stays as committed.
  - Its records for its own days do not change: base rates and model refits use only earlier days.
  - Its `pack_sha256` is the manifest's SHA-256 at its build.
  - `tests/forecast/test_backfill.py` is re-scoped to recompute the back-fill's own days and to check that its pack
    hash equals the SHA-256 of `manifest.json` at the commit that wrote the back-fill (read from git), instead of
    today's manifest.
- **Experiment 1 unchanged.** Its result stays reproducible from its frozen worktree (c52a6b8/0c1c957, hashes in its
  `FREEZE.md`), as the owner decided. Panel files on `main` now grow, so a run from `main` records a different
  `panel_manifest` hash, by design.
- **Rows before the append** are byte-for-byte equal: old file bytes are a prefix, and old manifest entries are
  identical (tested).

## 5. Acceptance (story A13, `docs/stories/A-data-foundation.md`)

1. An appended day equals A3's build of that day, row for row (test with synthetic raw files).
2. A day already present is never rewritten; a planted rewrite is refused and names the day.
3. Old files' bytes are a prefix of the new, and old manifest entries are identical.
4. A missing file, close or contract fails the day, writes nothing, and posts one #fno-desk line.
5. The reader returns the appended days' options, so `iv30_history_stale` does not fire 30 sessions after the last
   build (test).
6. No v1 or v2 frozen file changes. The appender refuses to write before `FREEZE_v3.md` exists.

## 6. Questions for ChatGPT

1. **Is the append in place (option A) acceptable as v3's only change?** The alternative is option B: a separate folder
   plus a new reader wired into `baseline_wiring.py`, which needs v2 code changes.
2. **The input version.** Should it be the newest version held at the append (as proposed), or the first archived
   version, as O6 uses for the closes? The cross-check refuses a day where the two disagree on either close.
3. **G4's question 5 resolution.** Once live days are in the panel, Q5's outcome is resolved with the panel's
   close-proxy IV30 of the forecast day, per v1 section 2, not with the pack's 15:00 IV30. Keep that (v1's definition)?
   Or should v3 define live Q5 against the pack's IV30, which the record's `iv30_status` describes?

## 7. Holdout

No 2019-2023 row of `golden_iv30_rv20.csv` or the G2 back-fill was opened, printed or analysed for this proposal. The
tests use synthetic raw files and a temporary panel folder.

## Addendum 1: A13 built, unwired (for the judge after ChatGPT)

The code matches sections 2-3 above. No frozen file changed: v1's and v2's freeze checks both still pass at HEAD.

| Part | Where | Evidence |
|---|---|---|
| Append in place | `fno/research_data/panel_append.py` (`PanelAppender`) | `tests/research_data/test_panel_append.py` (7), on real 2024 NSE subsets (`panel_fixtures.py`). A3's panel of 2 Jan 2024 with 2 Mar 2024 appended has the same decompressed `options_2024`/`futures_2024` content as A3's build of both days at once; the manifest's day entry equals A3's plus the stamp; the touched files' `csv_sha256` and row counts are equal. The old file bytes are a prefix. The old entry, `start`, `columns` and `calendar_sha256` are unchanged. The reader returns the appended day's options. A repeated or earlier day is refused and writes nothing. A tampered file is refused as an interrupted append. A new year gets its own file with A3's header. Other columns are refused. |
| Daily job | `fno/pipeline/panel_days.py` (`PanelDayJob`), wired in `fno/pipeline/wiring.py` `build_panel_day_job` (A11 reader `as_of` = run start; A3's `NiftyPanelBuilder` unchanged) | `tests/research_data/test_panel_days.py` (7). Appends once, and a second run changes no byte. `NotYetFrozen`: nothing appended, no alert. A failed freeze check: nothing appended, one alert. A session without its file stops there, keeps the earlier days and sends one alert. Closes that differ from `warmup_closes.csv`, or a missing warm-up row, stop the day. The real guard `require_v3_frozen` refuses today. |
| Command and workflow | `python -m fno pipeline panel-days [--to]`; `.github/workflows/panel-days.yml` | Manual dispatch only, with `fetch-depth: 0`. Steps: librarian `fo-bhavcopy`, then A11 sweep, then append, then commit. One #fno-desk line per failure. |

**Not done yet (waits for ChatGPT and the judge, by the orchestrator's order):**
- `PROTOCOL_v3.md` and `FREEZE_v3.md`;
- the schedule;
- the re-scoping of `tests/forecast/test_golden.py` and `tests/forecast/test_backfill.py`. Those two only fail once the
  real panel grows, so they are changed in the same commit as the first append.

**Limits:**
- **No run against Drive.** The job has not run against the real Drive from this session. GitHub Actions has the
  secrets; this container does not.
- **Fixtures are older than the live window.** The fixture days are 2024 real subsets, not October 2026. NSE's current
  UDiFF format is the same one A3 reads from 2024 (some evidence: A3 built 2024 to 12 Oct 2026 with the same reader).

## Addendum 2: response 69's seven changes, built (for the judge)

Everything stays unwired and unscheduled. `FREEZE_v3.md` does not exist, so the job appends nothing. v1's and v2's
freeze checks still pass, and no file they list changed.

| # | Change (response 69) | Where | Test evidence |
|---|---|---|---|
| 1 | Per-day provenance | `PanelDayJob._provenance`. Each new day's entry carries `inputs_version`, `inputs_read_at` (an upper bound for the archive time: A9 records no save time, stated as a limit), `later_versions` (A11 SHA-256 and availability per input), `appended_at`, the calendar SHA-256, and A3's file names and SHA-256. The append commit is the commit adding the day to `manifest.json`. | `test_pending_sessions_are_appended_once_with_their_input_versions` |
| 2 | Named input check, plus delay and retry | `input_problem` and `official_close_problem`, with reasons `fo_file_missing`, `index_close_missing` (including an O6 row not yet appended) and `index_close_differs` in `fno/constants.py` | `test_a_delayed_input_stops_with_its_reason_and_the_retry_appends_without_a_gap`, run for both inputs: a held-back file stops the run with nothing appended, B is never added over a missing A, and the restored file makes the retry append A and B. `test_an_official_close_not_appended_yet_or_from_another_version_stops_the_run` |
| 3 | First archived version for both inputs | `first_archived_inputs`: Drive's raw area only, memoised so each file is fetched once | `test_the_first_archived_version_is_used_never_a_later_one`: a different revision sits in the revisions area, and the day records the first version's SHA-256 |
| 4 | Start-of-run consistency, crash test, commit only on exit 0 | `PanelAppender.verify` (every file's SHA-256, content SHA-256 and rows; streaming, about 1 s on the real panel, which verifies). The run is all or nothing. In `panel-days.yml` the panel is committed only when the append succeeds; the A9 manifest rows are always committed. | `test_a_crash_between_the_year_file_and_the_manifest_is_refused_and_recovers`: a crash at the manifest swap is refused and named on the next run; restoring the committed files reads as before and appends cleanly |
| 5 | Replay from the panel at the forecast's parent commit | `fno/forecast_scoring/replay.py` (`LiveReplay`), `recompute_live_day`, `forecast-scores replay --day` | `test_live_replay.py` (3). In a temporary git repo whose panel grows after the capture, the replay reads the parent commit's manifest and not HEAD's. A tampered pack is named. The real recompute reproduces golden case A's pack (only the calendar label differs). |
| 6 | Experiment 1 freeze-hash test and reproduction command | `research/2026-10-12-experiment-1/README.md` | `tests/research/test_experiment_1_frozen.py`: all 45 FREEZE.md hashes hold at `0c1c957`, and `results_challenge.json` SHA-256 is `4826897e...` |
| 7 | `PROTOCOL_v3.md` and live Q5 against the 15:00 pack | `research/forecasts/PROTOCOL_v3.md` (draft). The G4 change was built in parallel by the G4 session (f03cb63, judge 58): one resolver per mode, with the live one reading `LiveForecasts.pack_iv30` from each receipt-verified pack. On merging I dropped my own overlapping version (same rule, duplicate code) and kept theirs. | G4's `test_live_question_5_is_scored_against_the_pack_iv30_and_history_against_the_panel` (planted disagreement), passing |

**Also done, as response 68 said:**
- `tests/forecast/test_golden.py` now compares the golden file's own days.
- `tests/forecast/test_backfill.py` now recomputes the back-fill's own days, with the pack hash being the manifest at
  the back-fill's commit.
- Both pass on today's panel, so CI stays green when the first append lands.

**G4 coordination:**
- The G4 session had already built live Q5 against the pack (f03cb63), so G4's scorer files are theirs, unchanged by
  me.
- I added only the replay (`fno/forecast_scoring/replay.py`, plus `recompute_live_day` and `build_live_replay` in its
  wiring, and the `forecast-scores replay` command).
- **Root-cause fix to `main`:** the merge 7f2c92e left `score_report.py` importing `ISOLATION` from
  `fno/ai/record_writer.py`, which F1/G5 (d6d8c46) had moved to `fno/constants.py` as `ISOLATION_SEALED_SAME_DAY`
  (same value, "sealed_same_day"). All G4 tests failed to import on `main`. That import now points at the constant.

**Limits:**
- The job has not run against the real Drive.
- A9 does not record when it saved a file, so `inputs_read_at` is only an upper bound for the archive time.
- The replay has no real live day to replay yet; it is proven on a temporary repository and on golden case A.

## Addendum 3: judge 64's four fixes

| # | Judge 64 | Fix | Test evidence (each mutation-checked) |
|---|---|---|---|
| 1 (d) | The replay was anchored on the records commit. The capture commits the pack first, pulls `main`, and commits the records later. | `replay.py` anchors on the commit that added `<d>_pack.json` and exports that commit's first parent. `PROTOCOL_v3.md` section 2 says the same. | `test_a_live_day_replays_from_the_checkout_its_pack_was_computed_from`, in the real order: pack commit, then another job's commit merged by the pull (the panel grows), then the records commit. The replay reads the checkout's manifest. With the old anchor the test fails (checked). |
| 2 (c) | `verify()` had no test. | `test_a_mismatch_in_a_file_the_append_would_not_touch_is_refused_at_the_start` (2020 options and futures files that a 2024 append never opens) | Passes with `verify()`; both cases fail with it disabled (checked). **It found a real bug:** `verify()` crashed with `BadGzipFile` on a damaged file instead of refusing it by name. It now treats a missing, non-gzip or cut-short file as a mismatch. |
| 3 (e) | Swapping the pack IV30 for the panel's in G4's wiring passed every test. | The per-mode resolvers and `pack_iv30` moved into `fno/forecast_scoring/q5_thresholds.py` (`mode_resolvers`). G4's wiring calls it. | `test_scoring_wiring_q5.py` runs the real `score_forecasts`; only the freeze checks, history, closes file and calendar are replaced. It fails both for the judge's swap inside `mode_resolvers` and for passing the panel's values into the live slot in `wiring.py` (both checked). All 40 G4 tests pass. |
| 4 | v3 must not freeze O6's shared `fno/pipeline/wiring.py`. | A13 has its own composition root, `fno/pipeline/panel_wiring.py`, listed in `CLAUDE.md`. O6's wiring imports only `drive_files` from it. v3's freeze list names `panel_wiring.py`. | Pipeline and A13 tests pass. |

**The v3 freeze list now** (`PROTOCOL_v3.md` section 5):
- the protocol;
- `panel_append.py`, `panel_days.py`, `panel_wiring.py`;
- `q5_thresholds.py`, `resolution.py`, `score_sources.py`, `scoring.py` (the files that decide live Q5);
- `replay.py`;
- `panel-days.yml`.

G4's composition root is not frozen.

**One coupling to decide before the freeze (reasoning only).** The v3 freeze check runs inside the panel job. A later
G4 change to one of the four Q5 files would therefore stop the daily panel appends with exit 1 and an alert, until a
new version is frozen. The rule holds, but the signal reaches G4's owner through the wrong job. Proposal: G4's
`score_forecasts` also runs the v3 check whenever live records exist, as it already does for v2. Not built; this is
your call.

**Is any scheduled job archiving `fo-bhavcopy` daily?** Yes and no:
- `market-publish.yml` (07:10 IST) runs `market daily`, which archives the previous session's `fo-bhavcopy` and its A11
  versions. But that step runs only after its database check passes, so a database outage also stops the archive.
- `panel-days.yml`'s own librarian step (last 7 days) is the only path that does not depend on the database.
- Once panel-days is scheduled at about 21:41 IST, it archives the day's file itself. The morning retry, scheduled
  before 14:00, would also see what `market-publish` archived at 07:10.
- Today `panel-days.yml` is manual only, so 13 Oct's file is not in Drive until either job runs for it.

## Addendum 4: v3's freeze split by consumer (orchestrator, after judge 64)

**Root cause:** one freeze check covered two separate jobs, so a G4 edit would have stopped the panel job.

**Fix:** one `FREEZE_v3.md` with two named sections, `## Checked by \`panel-days\`` and
`## Checked by \`forecast-scores\``.
- The panel job checks only its section (A13's files).
- G4's `score_forecasts` checks only its section (the live Q5 files and the replay), whenever live records exist.
- Before v3 is frozen, scoring proceeds as under v2.
- The check is `fno/freeze_sections.py` (`require_section_frozen`), and it is listed in both sections.

**Why it is not a call to `require_version_frozen` with a subset:** that function checks every hash row of the record,
and its file is byte-frozen by v2 (a change needs a new v2). So the new function reuses its building blocks:
`read_version_freeze`, `changed_files` and `Git`. It repeats about eight lines of its checks for one section.

**Tests:**
- `tests/test_freeze_sections.py` (5):
  - both sections hold after a freeze;
  - a planted change to the Q5 file fails `forecast-scores` but not `panel-days`, and the reverse;
  - a protocol change fails both;
  - with no record, the result is "not yet frozen";
  - a missing section is refused.
- `test_scoring_refuses_when_its_own_v3_section_does_not_hold` runs `score_forecasts` and shows it refuses on its own
  section.

## Addendum 5: v3 frozen (judge 64 addendum 2, in the orchestrator's order)

1. **Should-fix 1, section choice tested:** the panel wiring test asserts `panel-days` and the scoring wiring test
   asserts `forecast-scores`. Swapping the section names in both composition roots fails both tests
   (mutation-checked).
2. **Should-fix 2, no silent stop:** a missing or failing `FREEZE_v3.md` now fails the panel job with exit 1 and one
   #fno-desk line (`test_a_missing_freeze_record_is_an_alerting_failure_never_a_silent_stop`).
   - Found while preparing the first run: with `--to` defaulting to today, a morning retry or a manual run always
     included today's not-yet-published session, so the all-or-nothing run would never append anything.
   - Runs now append through the last day whose files are due: today from 21:00 IST, else yesterday
     (`last_complete_day`, 3 tests).
3. **Protocol commit `904c036`:**
   - final `PROTOCOL_v3.md` (status frozen; section 1 rules 7 and 8);
   - the tests above;
   - the repair of `main`: 4 G4 AI-gate tests were red because G4 (22ace2f) still passed a `today` argument that F1
     (0688ad5) had removed from `scoring_status`, and one test called `book_coverage` without `as_of`. Both now match
     the current signatures.
   - Checks: 1,829 passed; ruff and check_imports clean.
4. **Freeze commit `c1bf97f`:**
   - `FREEZE_v3.md`: preamble naming protocol commit 904c036; a `panel-days` section of 6 files; a `forecast-scores`
     section of 7 files (exactly section 5's lists); a recorded, not byte-checked, table for A3's builder files, the
     reader, G4's wiring and the manifest;
   - `panel-days.yml`'s schedule in the same commit: 21:41 IST and 12:11 IST.
   - Real-repository tests: both sections hold at HEAD, and the real panel guard passes.
5. **First run by dispatch:** https://github.com/exepex/trading/actions/runs/38474280810 (on c1bf97f).
