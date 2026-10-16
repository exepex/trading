# O9. All fetched data to Google Drive; GitHub keeps code and SHA-256 receipts only (lane 1)

**Owner decision (16 Oct 2026, in their words):** "I want routines of both to start saving the data into Google Drive
that we fetch from other sources. We have enough space to accommodate data in Google drive. Also, move existing data
from both repository to Google drive. We don't want to add data into github anymore. Whether it's github actions from
both repositories or claude routines to save data fetched from other sources to Google drive instead of github and we
always fetch data from Google drive to prepare or generate reports." Asked what stays in GitHub: "Hash receipt only".

Applies to both repositories: `exepex/trading` (this story) and `contactexepex/agentic-stock-prediction` (market-brief;
its own design file points here and needs that repository's approval rules: both AIs and the owner).

**Why now (strong evidence, 16 Oct 2026):** the A16 recorder lost data because its data path ran through git. Routine
containers start on a `claude/lucid-ptolemy-*` branch GitHub does not have; the committer pulled and pushed the current
branch, so every pull failed and the rows stayed in the container (`NOT committed`); 11:15 and 11:30 were rescued by
hand; two overlapping runs could not see each other's rows and both took 11:00 (an add/add conflict). The immediate
fixes are story A16f (`story/a16f-first-mark-and-main`); this story removes git from the data path altogether.

## Design

1. **One store interface, Drive behind it.** Every writer of fetched or derived data writes through `RawFileStore`
   (already used by A4b, A9, A12, A16, E2c) into the owner's Drive under the existing layout (`raw/...`, `derived/...`),
   never into the repository. New folders follow the repository path they replace: `research/data/<x>/...` becomes
   `data/fno/<x>/...` in Drive; market-brief's `data/<market>/<kind>/...` becomes `data/market-brief/<market>/<kind>/...`.
   Swapping Drive for another store later is one new class plus one line in `fno/storage/wiring.py` (CLAUDE.md, design
   for change).
2. **Write once, never overwrite.** Every record is a new file (the A16 rule: two runs racing for one mark both store,
   each under its own name). Drive has no atomic "first push wins"; the receipt (below) decides which copy counts.
3. **Receipts in GitHub, data never.** After each Drive write, the writer appends one line to a receipts file in the
   repository: `drive_path, sha256, bytes, written_at (UTC), writer, run_id`. No value, no row of data. This keeps an
   off-platform timestamp, so a sealed forecast can still be proven to predate its outcome and the health check (O8)
   still reads GitHub push receipts. The first receipt for a logical record wins; later copies are kept and listed.
4. **Readers read from Drive.** A run that prepares or generates a report first syncs the folders it needs from Drive
   into a local cache (`work/drive-cache/`, git-ignored): it lists the folder, downloads only files whose MD5 is not in
   the cache, and checks every file's SHA-256 against its receipt (a mismatch stops the run and alerts #fno-desk). The
   code then reads local files as today, so DuckDB globs and CSV readers do not change.
5. **Push target (A16f, kept):** the receipts commit still pulls and pushes `origin main` whatever branch the routine
   container is on, and refuses while the checkout carries anything else not on main.

## Inventory (what changes)

| Writer (schedule) | Writes today in git | After O9 |
|---|---|---|
| A16 15-minute recorder routine (hourly :52 IST) | `research/data/intraday/slots, rv, heartbeat.json` | Drive `data/fno/intraday/...`; receipts |
| 3 pm recorder routine (14:33 IST) | `research/data/quotes/` sidecars, `.canonical` | Drive; receipts |
| A8 participant-OI routine (17:11 IST) and monthly sweep | `research/data/participant_oi/` | Drive; receipts |
| forecast-capture.yml (14:00 IST) | `research/forecasts/live_v2/*_pack.json`, books, fire log | Drive; receipts (sealing evidence) |
| forecast-scores.yml (22:41 IST) | `research/forecasts/scores` | Drive; receipts |
| postmortem-weekly.yml (Sat) and its routine | `research/forecasts/v4_scores`, `research/postmortems` | Drive; receipts |
| health-check.yml (17:51 IST) | `research/ops/health_runs.csv` | Drive; receipts |
| index-closes.yml, panel-days.yml, nse-margins.yml, participant-oi-*.yml, quote-recorder-nse.yml | `research/data/{nifty-panel, margins, participant_oi, quotes, global-cues, vix}` | Drive; receipts |
| Librarian manifests (`research/data/manifests`, 14 MB) | manifest rows | Drive; the receipts replace them |
| AI books seal (`fno/ai/transport.py`), desk sync (`fno/desk/git_sync.py`), read-model publisher | forecasts, desk state, publication inputs | Drive; receipts |
| market-brief: 16 dispatcher routines on 16 Oct (daily, post-close, evening, intraday and weekly per market, 4 news), `onboard.yml` | `data/<market>/...` (119 MB), `reports/` (7 MB), `summaries/` | Drive; receipts |

Not data, stays in GitHub: code, tests, config, docs, stories, decisions, judge files, reviews, conversation logs,
`research/data/calendar/nse_sessions.csv` (hand-curated input with circular links, read by every run: proposed to stay;
owner to confirm).

## Existing data

Copy every data file of both repositories to Drive (same layout as above), verify each copy's SHA-256 against the
committed file, write one receipt per file, then remove the files from the repositories' HEAD in one commit per
folder. **Git history is not rewritten**: rewriting a public repository's history needs a force push and breaks every
clone, and the data stays public in history either way until it is rewritten. Whether to rewrite history later is an
owner question (below).

## Order of work (each step its own judge round; nothing switches until its reader works)

1. Drive token: the OAuth refresh token issued in Testing mode likely expires about 20 Oct 2026; after O9 every run
   depends on it. Re-issue it from the published app first (A12 checklist steps 1.4-1.5).
2. Receipts writer and the Drive cache reader (`fno/storage/`), with tests on a local folder store and a fake Drive.
3. A16 recorder (the most time-critical writer), then the 3 pm recorder, then forecast capture and sealing, then
   scores, health, post-mortem, panels and the rest of the workflows.
4. Market-brief, after its own design approval: one cache-sync step at the start of every routine, one upload-and-
   receipt step at the end, replacing each prompt's `git add data ... git push` step.
5. Copy and verify existing data, then remove it from HEAD.

## Risks (stated plainly)

- **Single point of failure:** a Drive outage or expired token stops every run (today a git-only run keeps working).
  Every run alerts #fno-desk on a Drive failure and keeps the files in a local spool until the next run uploads them.
- **Speed:** one Drive stream measured 0.41 MB/s (A14c, 16 Oct). A cold cache of market-brief's 119 MB takes about
  5 minutes; the incremental cache keeps daily runs to the few new files. The cache must persist per environment or
  the first run each day pays the cold cost.
- **Concurrency:** Drive cannot reject a second writer; write-once names plus first-receipt-wins replace git's merge.
- **Privacy:** data leaves the public repositories (a gain: raw values were already moved to Drive for licence
  reasons); the receipts show only paths and hashes.

## Criteria

1. No workflow or routine of either repository adds a data file to git; a check in CI fails a commit that adds a file
   under the old data folders.
2. Every Drive write has exactly one receipt line with a matching SHA-256; a test plants a changed file and the reader
   stops with an alert.
3. Two overlapping A16 runs racing for one mark: both copies in Drive, one receipt wins, the reader uses it.
4. Every report and read model built from the Drive cache equals the one built from the old repository data for the
   same day (byte-identical outputs on a recorded day).
5. Existing data: one receipt per copied file, all hashes equal, then removal from HEAD.

## Open questions for the owner

1. Rewrite git history to remove the old data from the public repositories? (Force push; every clone must re-clone.)
2. Keep the NSE session calendar in the repository (hand-curated input), or move it too?
3. Market-brief is paused (13 Oct decision); move its routines now or when stock work resumes?

**Depends:** A16f (push target), Drive token re-issue · **Size:** L · **Status:** story text for the judge
