# DR1 design: staging, certification and the as-seen record (for the owner's review)

**Builder:** session_01SPR8hz6AY8S99wE6ypFRik. **Status:** approved by the owner (23 Oct 2026, about 22:10 IST, relayed
by the orchestrator); built one dataset at a time, every step judged, the A4h closes first. It replaces sections 2, 3 and 6 of
`DR1-data-reliability.md` (the observation/publication split is withdrawn). The audit (section 1 there), DR1-0 and
the routine line stay as they are.

## 1. The owner's words (23 Oct 2026, relayed by the orchestrator)

> "Our reliability is not just the data, but our reliability is also the quality of the data as well. So our system
> needs to have two things in terms of reliability. One, the data must be available all the time. ... The second is
> data consistency. We do not accept corrupted, stale, or incomplete data."

> "why don't we fetch data on different intervals in a temporary location ... they do not become the record? The record
> happens when they prove their originality and consistency ... an overnight or late evening job that processes those
> files, verifies them which one is a correct one, validates its reliability and data consistency and the quality, and
> then moves it to become a permanent record. We don't have to run the forecasting until we get a proper quality data
> ... during the when the market is open, we fetch using Grow live feed ... We can also fetch from NSE and other data
> sources, but we don't make them as a system of record ... fetch NSE files a little bit late, and then we verifies".

The orchestrator's three additions (accepted by the owner): two certification levels (provisional, certified), the
as-seen pointer, and the source split (Groww live feed intraday, pending Tuesday's probe; NSE's final files at day end).

**The owner's decisions on this design (23 Oct 2026, about 22:10 IST), on section 6's points:**
1. "Yes, provisional for 15:15 (Recommended)": the same-day 15:15 decisions use labelled provisional records and are
   graded on certified outcomes.
2. "Yes, with that label (Recommended)": GIFT Nifty, the pre-open auction and the intraday marks are "certified without
   an official file" after the other checks.
3. "Approve, start building (Recommended)": one dataset at a time, a 5-session shadow run before each switch, the A4h
   closes first, every step judged.

## 2. The model

```
fetch ──> STAGING (every attempt, writer-unique name, never read by a forecaster)
              │  certifier: checks, chooses exactly one version, says why
              ├──> PROVISIONAL record (same day, fast checks)   used by time-critical same-day steps only
              └──> CERTIFIED record (evening/overnight, full checks against NSE's final files)
                        used by pre-market forecasts, scoring, back-tests
every decision keeps AS-SEEN pointers: (dataset, session, level, revision, SHA-256) of exactly what it read
```

**Staging.** Every fetch writes to `staging/<dataset>/<session>/<fetched_at>_<run_id>.<ext>` in Drive, with a staging
receipt in git (SHA-256, size, fetched_at, source, writer, run). The name is unique per writer and attempt, so two
containers, a hand run and a routine can never collide on one name (audit items 2, 3, 5 cannot happen). The git push
time of the staging receipt proves when the bytes existed: the "originality" the owner asks for, and what keeps
back-tests free of look-ahead. A staged file is never overwritten, never deleted by a job, and never read by a
forecaster.

**Certification.** One certifier per dataset (one writer: the day lock and one scheduled job, so no race) reads every
staged version of a session and runs that dataset's checks, in order:
1. integrity: the bytes match the staging receipt (SHA-256, size);
2. layout: the publisher's schema (the existing `content_checks` VALIDATORS for NSE files);
3. session and stamp: the data is for the session it claims (e.g. NSE's "as on" stamp; A4h's stamp after 15:30);
4. completeness: everything expected is there (all 4 indices, both expiries, every strike in the window, no gaps);
5. sanity: no impossible values (negative prices, bid above ask, a close outside the day's high-low, IV out of range);
6. agreement: equal, within a stated tolerance, to an independent source where one exists (Groww against NSE).

It then writes the **record**: a certification receipt `records/<dataset>/<session>.<level>.json` naming the chosen
staged version (path, SHA-256), every check's result, the reason for the choice, and the certifier's version. Writing
it is a push to main: the one atomic step we have (first push wins). Choice by quality only: the version that passes
every check; if several pass and are equal, any (same bytes); if several pass and differ (e.g. two quote attempts), the
dataset's stated rule picks (most complete, then nearest the target time), and the receipt says so. If none passes,
there is no record: the receipt says "not certified: <check, reason>", the catch-up (section 4) fetches again, and
every reader that needs this record stops with that reason (the owner: "We don't have to run the forecasting until we
get a proper quality data").

**Two levels.**
- *Provisional*: same day, minutes after the fetch, checks 1-5 (6 where the second source is already in). Read only by
  steps that cannot wait: the 3 pm capture to the 15:15 seals and the desk, A4h's close for the 20:05 grading, the
  pre-open values for the 08:50 morning edition. Every output made from it carries the label "provisional".
- *Certified*: evening or overnight, all six checks, against NSE's final files (bhavcopy, `ind_close_all`, participant
  OI, ban list). Read by the pre-market forecasts, every score and every back-test. A certified record may choose a
  different version than the provisional one, or correct it; the provisional record is never edited.

**Corrections are revisions.** A later better version (NSE republishes a file, a missed fetch is back-filled) becomes
`<session>.certified.r2.json` with its reason; nothing is overwritten (A11's rule, made general).

**As-seen.** Every decision record (forecast, seal, pack, card, desk decision, grading) lists the records it read as
(dataset, session, level, revision, SHA-256). A later certified correction never rewrites what a decision saw; scoring
uses the certified outcome of the target, and the decision's inputs as seen.

**Readers.** One `RecordReader` per dataset: `read(session, level, as_of)` returns verified bytes and the as-seen
pointer, or refuses with a named reason (no record, not certified, stale: older than the dataset's expected as-of, or
only provisional where certified is required). No reader lists Drive folders or picks among copies: the record names
the file. A stray or duplicated staged file therefore can never make a dataset unreadable (audit item 2b).

## 3. What already does part of it (built on, never a second version)

| Piece | What it already does | What changes |
|---|---|---|
| A4h close read (`fno/close_read/`) | 15:40 read and 16:00 recheck = a provisional close; `confirm.py` checks it against NSE's official `ind_close_all` within 0.01 = certification, with a write-once `.confirm.json` and an alert on a difference | the template: its read becomes staging, confirm becomes its certifier |
| A4 3 pm quotes (`fno/quotes/recorder.py`) | several attempts per day with sidecars; the `.canonical` marker promotes the first complete one | attempts get writer-unique names (today the snapshot ID is the start second: audit item 5); `.canonical` becomes the provisional record |
| O6 quotes compare (`fno/quotes/compare.py`) | Groww's and NSE's canonical snapshots side by side | the agreement check (6) for quotes |
| A11 revisions (`fno/storage/revisions.py`, `versioned_store.py`) | later NSE versions kept beside the first, point-in-time reads by `as_of` | the revision rule for every certified record |
| Content checks and coverage (`fno/storage/content_checks.py`, `coverage.py`) | layout checks per NSE dataset; expected versus present per session | checks 2 and 4 for NSE files; coverage becomes the ledger's NSE part |
| O9 receipts (`fno/storage/receipts.py`, `data_store.py`) | SHA-256 receipt per Drive file, committed to git | staging receipts; certification receipts are a new kind beside them |
| Dashcam seals (`fno/school/dashcam/`) | a seal returned only after the receipt's push; replay conflict; a rerun adopts an unreceipted file | the as-seen pattern for decisions |
| Pack and card SHA lists (`journal/packs/`, the card's "Records used") | each decision lists the SHA-256 of the records it read; late inputs refused at the cutoff | become as-seen pointers with level and revision |
| G13b back-fill labels | back-filled rows are "never live evidence" | the provisional/certified/back-filled label on every output |
| O1 day lock (judge D 537) | one daily run per container | keeps each certifier a single writer |
| DR1-0 `DriveItems` | sees every copy of a name in Drive | the certifier's staging listing; the one-off repair tool |

## 4. Availability: the parts around the record

- **Catch-up.** Per dataset: its source, how long the source still serves a session (NSE archives: years; the ban
  list: its dated archive; live quotes and A16 marks: never), and its fetch command. A missing or not-certified record
  starts a re-fetch into staging on the next run, until certified or past the horizon; then one line "gone: <reason>".
- **Completeness ledger.** Daily, per dataset and session: expected (NSE calendar, live date), staged, provisional,
  certified, readable through its `RecordReader`, fresh. One file under `research/ops/completeness/`, one #fno-desk line
  per gap; a gap starts the catch-up. A reader bug (audit item 1) shows as "certified, not readable" the same day.
- **Real-adapter tests.** Every `RecordReader` and certifier is tested through the real `DriveCache`,
  `ReceiptFolder` and Drive adapters over a fake Drive HTTP remote (`tests/dr1/fake_drive.py`, built for DR1-0).
- **Routine start and setup.** Unchanged from the audit: the first line on latest main, setup importing everything the
  requirements provide, one alert before any step.

## 5. Migration: no live reader ever breaks

Each dataset moves alone, through four phases; a phase moves on only when the ledger shows it clean.

1. **Build, unused.** Staging store, certification receipts, `RecordReader`, ledger: new classes behind the existing
   `RawFileStore`/`DataStore` interfaces, wired in their own composition root. No writer or reader changes.
2. **Shadow.** The dataset's writer also stages each attempt (the existing record path is written exactly as today);
   its certifier runs and writes records; the ledger compares the certifier's choice with today's record every day.
   Readers unchanged. Exit: 5 sessions with no unexplained difference (reasoning only: one trading week).
3. **Readers switch.** Each reader moves to its `RecordReader` at the level it needs, one reader per change, with its
   contract test. No silent fallback to the old path: a refusal is named.
4. **Writers stop.** The old direct record path is no longer written; the staged files and records are the only data.

Order of datasets, most damage first: A4h closes (template, already provisional plus confirm); the daily run logs
(audit item 3); the 3 pm quotes (items 2 and 5; the 15:15 seals read them); A22 pre-open and global cues (items 7, 8);
the NSE archive datasets through the librarian (already manifests plus revisions); A16 intraday after Tuesday's Groww
feed probe (the source decision comes first).

**Frozen code.** Some readers sit inside frozen protocols (e.g. `fno/forecast_scoring/wiring.py` is hashed in
`FREEZE_v3.md`). Switching them needs each freeze's amendment route; they move last, and the design never edits a
frozen file without it.

## 6. Points for the owner (honest limits)

1. **Same-day decisions cannot wait for certified data** (strong evidence, the timetable): the 15:15 seals use the
   15:00 quotes and NSE's final files come out in the evening. They use provisional records, labelled, and are scored
   later against certified outcomes. If you want no decision on provisional data at all, the 15:15 seals must move to
   the next morning: your call.
2. **Some values are only ever provisional** (strong evidence): GIFT Nifty at 08:40, the pre-open auction and the
   intraday marks have no later official file to check against. Their certification can only use integrity, layout,
   stamp, completeness, sanity and a second live source; the record says "certified without an official file".
3. **Storage grows** (reasoning only): every attempt is kept. The 3 pm quotes are the largest daily set; a retention
   rule for staged versions that were never chosen (e.g. 90 days) can come later, never for chosen ones.
4. **A dataset with no certified record stops its readers.** That is the owner's rule, and it means a source outage
   now shows as a named stop instead of a silent gap. The catch-up and the alert make it visible the same day.

## 7. Build step 1 (DR1-1): records for A4h's closes, built and in shadow (branch story/dr1-1-closes-records)

**What it builds (new package `fno/record_store/`, no change to `fno/close_read/` or any reader):** the generic parts
(`StagingArea` and `ReceiptedFiles` version sources, `DatasetRules`, `Certifier`, `RecordFolder` in git under
`receipts/records/`, `RecordReader` with the as-seen pointer) and the first dataset's rules (`closes.py`). In the
shadow phase the closes' versions are A4h's own raw answers (`<day>.first.raw.json`, `<day>.recheck.raw.json`, through
their receipts), so A4h's writer is untouched. Command: `python -m fno records certify closes [--day D] [--level
provisional|certified] [--commit]` and `python -m fno records read closes [--day D] [--level ...]`.

**Closes rules (version 1):** provisional = integrity (bytes equal their receipt; A4h's raw file is its canonical
JSON of the parsed answer, not NSE's byte stream), layout (JSON), A4h's own `read_answer` (NSE stamp that day at or
after 15:30, every index with last and open), sanity (every index positive; NIFTY 50 and NIFTY BANK within 20% of their
open, NSE's widest index band; INDIA VIX is not banded). Certified = the same plus NSE's official index-close file
within A4h's 0.01 tolerance for NIFTY 50 and NIFTY BANK (A4h's `OfficialCloses`); no official file yet means no
certified record, named, and no alert (A4h's overdue rule already alerts that gap).

**Which passing read is the record (settled with the A4h builder and the orchestrator, 23 Oct):**
- *Objection (A4h builder): the 16:00 recheck may differ from the 15:40 read by design; "the reads must agree" would
  leave no provisional close on a correction day.* Accepted. The orchestrator's alternative (block only when two reads
  with the same NSE stamp differ) does not work on this data: both of 23 Oct's reads carry the same stamp
  ("23-Oct-2026 15:30" at 15:40 and at 16:00; strong evidence, the raw files in Drive), so it would block exactly the
  correction days. Rule: a value that changes after the 15:30 close is NSE's correction, so the provisional record is
  the **latest** passing read, the change named ("the later read supersedes the earlier (NIFTY 50 differs by X)"); equal
  values keep the first read, the one A4h's record cites. The A4h builder proposed the first read; DR1 takes the later
  (reasoning only: a post-close change is a correction); the shadow counts the days the recheck differs and which read
  NSE's official file confirms, which settles it with data.
- *Certified:* the passing read closest to the official file (equal: the first read). The A4h builder proposed "both
  agree: no record"; not taken: both within 0.01 of the official file are both correct closes, and refusing would cost
  availability for no consistency gain.
- *Objection: the 20% band must not apply to INDIA VIX.* Accepted (VIX moves more than 20% around shocks; its list
  value is never certified); VIX keeps the positive check.

**After A4h-2 (from Mon 26 Oct):** A4h-2 renames `OfficialCloses.closes(day)` to `values(day)` (`["close"]`); the
A4h builder updates DR1-1's two calls in their merge if DR1-1 merges first. Rules version 2 adds A4h's proposed checks of high, low and previous close (against
the official file and the previous session's close; low <= open, last <= high), VIX fields optional.

**Real Drive, read-only dry run (23 Oct, records kept local, not committed; all four match A4h's record):** `closes
2026-10-22 certified: recorded d98b58cde08f, 1 of 1 version(s) passed; closest to NSE's official file
ind_close_all_22102026.csv, within 0.01; matches A4h's record`; `closes 2026-10-23 provisional: recorded c5c1bb4fdf47, 2 of 2 version(s) passed; 2 passing
version(s) agree on NIFTY 50, NIFTY BANK; matches A4h's record`.

**Shadow running (proposed, not in this branch: it touches routines):** the evening routine certifies the day's
provisional record after `closes read --commit` (`records certify closes --level provisional --commit`), and the
morning routine certifies yesterday's after step 1b archives the official file (`records certify closes --day
<previous session> --level certified --commit`). After 5 sessions with "matches A4h's record" and no unexplained
refusal, phase 3 switches FL1's `A4hTodayCloses` to `RecordReader` (with the A4h and FL1 builders).

### Claims (DR1-1)

1. A record is a pointer (path, SHA-256, size, saved time) plus every version's check results; it never holds a level
   (tested), and the same choice gives the same bytes, so a rerun is a no-op.
2. Choice by quality only: a version failing any check never becomes the record; a later read that differs supersedes
   the earlier with the change named; the certified record names the read closest to NSE's official file, whichever
   read it is (judge 543 SF2: the recheck is named when it is the closer read; the plant "always the first read"
   fails); INDIA VIX may move more than 20% but must be positive; a change of the open alone is named.
3. (Round 2, judge 543 SF1.) A record counts only once origin's main holds it with the same bytes (`publisher.py`
   asks origin itself: a refused push leaves a local commit the committer would never push again). A refused push
   prints "record NOT pushed: ...", alerts #fno-desk and exits 1; the rerun pushes the stuck record ("already
   recorded" only once origin holds it); a record another certifier pushed first is a conflict ("a person decides"),
   alerted, exit 1, never overwritten. Tested on real git with a bare origin, a refusing pre-receive hook and two
   checkouts; the plant "origin always holds it" fails 2 tests.
4. `RecordReader` returns exactly the recorded bytes or refuses by name (no record, missing, other bytes); a certified
   record serves a provisional need, never the reverse; the as-seen pointer names level, path and SHA-256.
5. Two writers staging one session in the same second get two names (`<fetched_at>_<run_id>`).
6. The certifier only reads: its official index-close file comes from the stores, never from NSE (tested). Found in
   the dry run: `build_index_close_files()`'s library archives a file Drive lacks, so a dry run saved 23 Oct's
   official file to Drive (NSE's genuine file; manifest row aa0e2ed30). Every other reader of that function (A4h's
   confirm, the panel) does the same, while `DailyFiles` and `close_read/official.py` say "never writes to Drive":
   reported to the O9 and A4h builders, not changed here.
7. Gates: ruff, `tools/check_imports.py`, full suite 14,647 passed (27 in `tests/record_store/`).

## 8. DR1-1 shadow steps (branch story/dr1-1-shadow-steps, after DR1-1's PASS)

- `records certify <dataset> --since N`: every NSE session from the dataset's `live_from` (closes: 22 Oct) in the last
  N days, one line each; a session already recorded says so; exit 1 while any is not recorded. A session missed one
  morning is therefore caught up the next (the catch-up of section 4, for this dataset). The window ends at the day
  for a provisional record and at the previous session for a certified one (judge 546 SF1: a certified record is due
  only once NSE's official file is out, so including today raised a false "NOT recorded" every trading morning).
  Tested on NSE's real calendar: a trading morning, a Monday (Friday is the last) and the day after the 20 Oct holiday
  (19 Oct is the last), each exit 0 with no line for today; the plant "the window ends today" fails 3 tests.
- CLAUDE.md, morning routine (after `lab open`): `python -m fno records certify closes --since 7 --level certified
  --commit`; evening routine (after `closes read --commit`): `python -m fno records certify closes --level provisional
  --commit`. Each commits only `receipts/records/`. The stored prompts are unchanged ("Run the ... routine in
  CLAUDE.md"), so the owner pastes nothing.
- The command alerts #fno-desk itself for a record not pushed or a conflict (DR1-1 round 2). The routine notes every
  "NOT recorded" line in the day's conversation log and posts it to #fno-desk, except a certified "no official
  index-close file in Drive yet", which A4h's overdue rule already alerts (judge 543's note); it posts the text of any
  "alert NOT sent" line.

## 9. DR1-1b: A4h-2's official values (branch story/dr1-official-values; lane 1, judge B's delta)

A4h-2 (judge 544, 72d769b8) renames `OfficialCloses.closes(day)` to `values(day)` (each index's official open, high,
low and close) and adds high, low and previous close to the list read, refusing a checked index whose open or last is
outside its day range. Built from main with 72d769b8 merged in.

**Design decision: the new fields take part in certification (closes rules version 2).** FL1-1f's evening edition
reads the day range and the previous close from the same record, so a certified record must vouch for them as for the
close (the owner's consistency pillar: no wrong data reaches a reader). For NIFTY 50 and NIFTY BANK: last against the
official close, high and low against the official high and low, previous close against the previous session's
official close (NSE's calendar step back), all within A4h's 0.01. The previous session's file missing means no
certified record, named. INDIA VIX stays recorded, never certified (its list values are not the official ones), and is
out of the 20% band. Provisional checks gain A4h-2's range refusal through `read_answer`, unchanged. The same mapping
as A4h's confirm (`fno/close_read/confirm.py`), applied to every passing read instead of A4h's own record.

**Real Drive dry run (stores only, records local and deleted):** 22 and 23 Oct, provisional and certified, all four
recorded and "matches A4h's record" under version 2.

### Claims (DR1-1b)

1. The certifier calls `values(day)` and takes `["close"]`; the certified choice (the read closest to the official
   close) and every earlier rule are unchanged (all earlier tests pass with A4h-2's field set in the fixtures).
2. A high, a low or a previous close differing from the official value by more than 0.01 means no certified record,
   named by index and field.
3. The previous session's official file missing means no certified record, named.
4. INDIA VIX's range is never certified.
5. Gates: ruff, `tools/check_imports.py`, full suite 14,824 passed (38 in `tests/record_store/`).

### Plants (each reverted)

| Claim | Plant | Caught |
|---|---|---|
| 2 | high and low dropped from the official mapping | 2 tests fail |
| 2 | previous close dropped | 1 fails |
| 3 | a missing previous-session file accepted | 1 fails |
| 4 | INDIA VIX certified like the others | 1 fails |

## 10. DR1-1c: one reader builder, and "cannot read" is never "not out yet" (branch story/dr1-reader-stores)

Judge 558 (note 2) found two reader builders: DR1-1's `stored_index_closes()` read `build_raw_stores()` only (the
service account), which no workflow and no routine sets, so in a routine every certified check would have said "no
official index-close file in Drive yet", a reason the morning routine does not post: silent. Built on O9's
story/o9-readonly-index-close (fb1a4bd7d, with judge F), so it merges after it.

- The certifier takes its official files from O9's one reader builder, `build_stored_index_close_files()` (the stores
  only, the owner's Drive raw area included); `stored_index_closes()` is deleted.
- With no store at all, O9's reader raises `NoReadableStore` (added at DR1's request). Any failure reading the
  official files (no store, a store refusing, a damaged file) is `SourceUnreadable`: the session is "NOT recorded: a
  source could not be read: ...", alerted to #fno-desk, exit 1 (orchestrator, 24 Oct: never a line the morning skips).
  A file simply not archived yet stays the ordinary, unalerted "no official index-close file in Drive yet".
- Judge 554's note: a previous close missing from the previous session's file names that file.

Real Drive (read-only): 22 and 23 Oct certified through O9's reader, both "matches A4h's record"; with the owner's
settings and the service account removed, the reader raises NoReadableStore.

### Claims (DR1-1c)

1. An official source that cannot be read (NoReadableStore, a refusing store) gives an alerted "NOT recorded: a source
   could not be read" and exit 1, never "in Drive yet".
2. A file not archived yet stays an unalerted "no official index-close file in Drive yet".
3. The certifier's official files come from `build_stored_index_close_files()`, never a store list of its own.
4. A previous close missing from the previous file names the previous session's file.

| Claim | Plant (reverted) | Caught |
|---|---|---|
| 1 | a read failure becomes an ordinary failed check | 2 tests fail |
| 3 | the certifier builds the fetching `build_index_close_files()` | 1 fails |
| 4 | the previous file named as today's | 1 fails |

## 11. DR1-1d: judge 561's two notes (branch story/dr1-1d-one-read-one-alert; lane 1, judge B's delta)

- Each official file is read once per run, through one guarded helper (`ClosesRules._official`): the certified
  choice no longer re-reads it outside the guard, so a read failing between the check and the choice can no longer
  end in a traceback.
- A run that alerts (a record not pushed, a conflict, an unreadable source) sends one #fno-desk alert naming every
  session, not one per session (`--since 7` with a store down: one alert, not up to seven).

### Claims (DR1-1d)

1. Two versions of a session read the day's and the previous session's official files once each; a source that
   fails on a second read does not affect the record.
2. A catch-up with a source down sends one alert listing every affected session.

| Claim | Plant (reverted) | Caught |
|---|---|---|
| 1 | no per-run cache | 1 test fails |
| 2 | one alert per session again | 1 fails |
