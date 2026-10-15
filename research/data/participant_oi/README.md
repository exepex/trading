# Participant open interest: release-time evidence (story A8)

`release_checks.csv` is the committed log of the release-time recorder (`fno/research_data/release_times.py`): the
GitHub Actions job `participant-oi-watch` runs `python -m fno participant-oi check-once` every 15 minutes from 16:37 to
23:22 IST, with no AI session (`participant-oi watch` keeps checking in one process). `.gitattributes` merges this file
by union, so two writers' new rows never conflict. `release_rereads.csv` records, per due day, that the daily re-read
of the last 5 seen files (rewrite detection) finished with every file answered.

Each row is one check of NSE's archive for one session's file `fao_participant_oi_DDMMYYYY.csv`:

| column | meaning |
|---|---|
| `day` | the session the file is for |
| `checked_at` | when NSE's answer came (IST, ISO 8601), after any retries: a 503 retried first is not seeing the file (orchestrator's decision 37, story A9b). Rows before A9b's merge: when the single try began (no retries then, so the two are seconds apart at most) |
| `outcome` | `present`, `absent` (HTTP 404), `unreachable` (no answer after the retries of `fno/storage/retry_policy.py`, or refused: says nothing about the file) or `rewritten` (present, with other bytes than first seen) |
| `sha256` | SHA-256 of the file when present |
| `last_modified` | NSE's own Last-Modified time for the bytes seen (ISO 8601; empty in the two rows written before 13 Oct 2026's change) |

Since A9b each check's start time goes to `release_check_starts.csv` beside it (`day, checked_at, started_at`, joined on
`day` and `checked_at`; also merged by union): `checked_at` minus `started_at` is the retry gap (up to 65 s of waits,
or 3 x 120 s when NSE asks to wait). It is a separate file so that a writer that commits only `release_checks.csv`
(the A8 Claude routine commits it by path) loses start times, never a check. A check without a start row reads as
started when it was checked.

Rows are only ever appended, never edited or deleted.

**How the rule is set from it.** A day counts as measured only when the log shows its file `absent` and later
`present`. The first `present` time is an upper bound on the real release (the safe side for look-ahead). From each
measured day, the lag in sessions is the number of sessions after the file's day until the first decision at or after
that time plus 30 minutes. With 20 or more measured days, the rule is "usable `max lag` sessions after the file's day,
at the decision time" (`MeasuredReleaseRule`). Until then the default applies: usable from the next session's decision
time (`NextSessionRule`). `python -m fno participant-oi rule` prints the rule in force and the count of measured days.

The raw files themselves live in the project's Drive folder under `raw/nse/derivatives/participant-oi/`, never in this
repository; their SHA-256 fingerprints are in `tools/nse_raw_download/manifest_participant_oi.csv`.

## Supporting evidence: NSE's Last-Modified times (13 Oct 2026)

`archive_last_modified_2026-10-13.csv` holds the `Last-Modified` header NSE's archive returned on 13 Oct 2026 for
every participant-OI file, 2019-01-01 to 2026-10-12 (1,929 files). It shows when NSE **last wrote** each file, not
when the file first appeared, so it cannot set the rule; it only supports or questions it:

- 0 files were last written before 15:00 IST on their own day;
- 1,824 (94.6%) were last written after that day's close and before the next session's 15:00 (same-day times
  17:00-23:59 IST, most 18:00-20:00);
- 105 were last written later: 95 of them in 2019 in batches (whole months rewritten on 17 Jan 2019 and 6 Mar 2019,
  for example) and 10 since 2020 (one, 15 Jan 2024, rewritten on 15 Jan 2025). NSE therefore rewrites archive
  files after publishing them: a historical study reads today's version, which may differ from what was published
  at the time, and on those 105 days the file may also have first appeared late.

**Used by the rule (judge 15).** NSE's bytes held today are usable no earlier than their own last write: the wired rule
(`fno/composition.py`, `build_participant_oi_rule`) wraps the default or measured rule in `LastWriteBoundRule`, fed by
this table and the recorder's `last_modified` column (the latest time per day wins). This holds back exactly the 105
rewritten days and leaves the other 1,824 unchanged. Each recorder run also re-reads the last 5 seen files and logs
`rewritten` when their bytes change, and the command then exits 1.

## Monthly sweep (judge 16)

`python -m fno participant-oi sweep` reads every recorded file in full from NSE (through the polite session and
`RevisionCapturingSource`, so a rewritten file is kept as a revision; about 35 minutes for 1,929 files) and compares each Last-Modified with the latest one on record. A day whose
write time moved later gets a row in `last_modified_sweeps.csv` (`day, checked_at, last_modified`), is printed as
`MOVED <day> ...`, and is held back by the rule from then on; the command exits 1 on any moved or unanswered file. The
recorder's own recheck covers only the last 5 sessions, so this sweep is what catches a rewrite months later. A moved
day also means the bytes held in Drive are an older version than NSE now serves; re-download and compare before using
that day.
