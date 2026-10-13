# Participant open interest: release-time evidence (story A8)

`release_checks.csv` is the committed log of the release-time recorder (`python -m fno participant-oi watch`,
`fno/research_data/release_times.py`). Each row is one check of NSE's archive for one session's file
`fao_participant_oi_DDMMYYYY.csv`:

| column | meaning |
|---|---|
| `day` | the session the file is for |
| `checked_at` | when it was checked (IST, ISO 8601) |
| `outcome` | `present`, `absent` (HTTP 404) or `unreachable` (no answer after retries: says nothing about the file) |
| `sha256` | SHA-256 of the file when present |

Rows are only ever appended, never edited or deleted.

**How the rule is set from it.** A day counts as measured only when the log shows its file `absent` and later
`present`. The first `present` time is an upper bound on the real release (the safe side for look-ahead). From each
measured day, the lag in sessions is the number of sessions after the file's day until the first decision at or after
that time plus 30 minutes. With 20 or more measured days, the rule is "usable `max lag` sessions after the file's day,
at the decision time" (`MeasuredReleaseRule`). Until then the default applies: usable from the next session's decision
time (`NextSessionRule`). `python -m fno participant-oi rule` prints the rule in force and the count of measured days.

The raw files themselves live in the project's Drive folder under `raw/nse/derivatives/participant-oi/`, never in this
repository; their SHA-256 fingerprints are in `tools/nse_raw_download/manifest_participant_oi.csv`.
