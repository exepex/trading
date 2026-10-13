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
