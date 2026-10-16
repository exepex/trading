# O9. Every data file in Google Drive, write-once; GitHub keeps code and SHA-256 receipts only (lane 1)

**Owner (16 Oct 2026, in their words):** "we are going to store each and every damn file in Google Drive. We fetch it
from there. That's it." / "We store the SHA in GitHub or in database, and we store all the files in Google Drive. And
these files are read-only files. Once they are created, we never change them." / both repositories, every routine and
GitHub Action; "All routines & reports must fetch data from Google Drive & use it for report generation".

Applies to `exepex/trading` (this text) and `contactexepex/agentic-stock-prediction` (section M; its own approval rules:
both AIs and the owner). Replaces the first O9 text (judge 228: FAIL, one must-fix: frozen and test inputs; one
should-fix: receipts must not collide). Built from two read-only inventories of 16 Oct with file:line evidence
(`reviews/claude/` note to follow with both reports attached); the numbers below come from them.

## 1. Rules

1. **Every data file lives in Drive, never in a repository.** Data = anything fetched from an outside source or
   derived from it: raw files, tables, ledgers, logs, manifests, scores, forecasts, packs, heartbeats, reports built
   from data, study results. The owner's word "each and every file" includes the hand-curated inputs (`calendar/`,
   `events.csv`, `stress_factor.csv`, `followed-companies/`): they move too (rule 2 makes their edits new versions).
2. **Write-once.** A path is written once; the same bytes again are a no-op, different bytes are refused
   (`RawFileConflict`, already the behaviour of `GoogleDriveUploadStore.put`, google_drive_upload.py:32-41).
   `replace_contents` (google_drive_upload.py:77) and `DriveIndexStore.replace` (index_store.py:40-56) are removed.
   A file that today is appended to or rewritten becomes a **series of parts**: each write is a new file
   `<table>/<YYYY>/<MM>/<key>.<run_id>.<ext>`; the logical table is the union of its parts; a correction is a new part
   that supersedes an older row (the rule A11 and market-brief already use for corrections). Mutable state (filings
   progress in `index/`, the paper accounts in `paper/`) becomes versioned snapshots `<name>/<UTC stamp>.<run_id>.json`;
   the reader takes the newest.
3. **One SHA-256 receipt per Drive file, in GitHub.** After a Drive write succeeds, the writer commits one small file
   `receipts/<drive path>.sha256` (`sha256  bytes  written_at_utc  writer  run_id`; no value from the data). One file
   per write, so two runs never touch the same receipt and a merge cannot conflict (judge 228 should-fix). The commit
   goes through the A16f committer: `origin main` whatever branch the container is on, refusing a checkout that
   carries anything else. The receipt's commit and GitHub's push record give the off-platform time that today's
   evidence uses (section 5). The first receipt for a logical record wins; a later copy is kept and listed.
4. **Every reader reads through a verified Drive cache.** A run first syncs the folders it needs from Drive into a
   local cache (git-ignored), downloading only files the cache lacks, and checks each file's SHA-256 against its
   receipt; a missing or mismatching file stops the run and alerts (#fno-desk; #market-brief for section M). The code
   then reads local files exactly as today: only the root path changes (fno: one `DATA_ROOT` in `fno/constants.py`
   instead of `REPOSITORY / "research" / ...`; market-brief: `MB_ROOT`, core/paths, which already redirects the data
   root).
5. **Nothing writes data into a checkout.** A check in CI and in the commit hook refuses a commit that adds a file
   under the old data folders, and a test refuses code that opens a data path for writing outside the store. This
   also covers the writers no scheduler runs (v4 forecasts, weather back-fill, global cues, VIX, candle back-fill,
   card deliveries, `tools/v4_*`, study scripts): they write through the same store or not at all.

## 2. The parts that make the store

| Part | What | Builds on |
|---|---|---|
| `DataStore` | `put(path, bytes)` write-once into Drive area `data/`; returns the SHA-256 | `GoogleDriveUploadStore`, `AreaStore` |
| `ReceiptWriter` | writes and commits `receipts/<path>.sha256` after a successful `put` | A16f `GitManifestRecorder` (origin main, refusal) |
| `DriveCache` | `sync(prefixes)`: list Drive, download what is new, verify against receipts, keep a local index | `GoogleDriveStore` (service-account reads), `DriveOnlyQuoteStore`'s SHA check |
| `PartTable` | write a part; read the union (CSV and JSONL), latest-wins for supersessions | new; replaces in-place appends |
| `Snapshot` | versioned state files, newest wins | replaces `DriveIndexStore.replace` |

Market-brief gets the same five parts (no Drive code exists there today); the Drive settings are the same four
`FNO_GDRIVE_*` names or a second set chosen by the owner.

## 3. What moves (exepex/trading)

| Area today (size) | Writer and trigger | After O9 |
|---|---|---|
| `research/data/intraday` slots, rv, heartbeat (6.8M) | A16 routine (`OwnedPathsCommitter`) | Drive parts; receipts; claims (section 6) |
| `research/data/quotes` sidecars, `.canonical`, NSE chains (68K) | 3 pm routine; quote-recorder-nse.yml | Drive; receipts (the sidecar becomes the receipt) |
| `research/data/nifty-panel` (45M), `warmup_closes.csv` | panel-days.yml, index-closes.yml | Drive parts; receipts |
| `research/data/manifests` (14M) | librarian, revisions, filings, global cues, candle back-fill | replaced by receipts |
| `research/data/{margins, participant_oi, global-cues, vix, publications}` | nse-margins, participant-oi-*.yml, market-publish.yml, manual CLIs | Drive parts; receipts |
| `research/forecasts/**` (15M: live_v2, ai_v1, scores, v4, v4_scores, backfill, golden) | forecast-capture.yml, forecast-scores.yml, AI routines, postmortem-weekly.yml, tools | Drive; receipts (sealing: section 5) |
| `research/postmortems`, `research/ops/health_runs.csv`, `research/cards/deliveries`, `accounting/*` | postmortem workflow and LR1 routine, health-check.yml, card daily, budget | Drive; receipts |
| `journal/**` (runs, packs, totals, decisions, versions) | desk `GitCommitter`, Book 1 | Drive parts and snapshots; receipts |
| study folders `research/<study>/` data and results, `research/ledger.csv` | manual | Drive; receipts; code and FREEZE text stay |
| Drive `index/`, `paper/` (overwritten today) | filings, desk | `Snapshot` (rule 2) |

14 workflows commit today (filings-archive, flows-download, forecast-capture, forecast-scores, health-check,
index-closes, market-publish, nse-margins, panel-days, participant-oi-release, -sweep, -watch, postmortem-weekly,
quote-recorder-nse); after O9 each commits receipts only. Routines that commit data today: the 3 pm recorder, A16,
Books 2 and 3 (seal/reveal), the LR1 post-mortem writer; their prompts lose every data `git add`.

## 4. Frozen inputs and tests (judge 228 must-fix)

Three classes, each staying valid:
1. **Freeze-checked files** (`golden_iv30_rv20.csv` and `v2/golden/**` hashed by `fno/forecast/freeze.py:43-60`,
   `freeze_v2.py`): the frozen code is not touched (`freeze.py` and `freeze_v2.py` are themselves pinned by SHA-256 in
   `FREEZE.md` line 27 and `FREEZE_v2.md` lines 41-42; judge 228 add. 3). Before a freeze check, the cache sync writes
   each freeze-checked file back to its original repository path, git-ignored, with the same bytes, verified against
   its receipt; `changed_files(root, freeze)` then compares the same hashes, unchanged. Rule 5 holds: ignored files are
   never committed. A frozen file's receipt is written at migration with the hash already in the FREEZE file; a
   mismatch fails exactly as today.
2. **Recorded, not checked** (warmup_closes, panel manifest, calendar in FREEZE/FREEZE_v2/FREEZE_v3; experiment 1's
   files read at RUN_COMMIT by `git show`): git history is not rewritten (section 7), so `git show <commit>:<path>`
   keeps returning those versions and experiment 1's test does not change. Each recorded version is also uploaded
   byte-exact under its own receipt, so it stays fetchable by SHA if history is ever rewritten (open question 1).
3. **Tests that read real repository data** (about 45 files, list in the inventory, beyond the judge's 22): unit
   tests switch to small fixtures built in `tmp_path` (the existing pattern, tests/conftest.py:16); tests whose point
   is the real data (G6 v4 tools on `warmup_closes.csv`, freeze tests, replay) become a "data" marker run after a cache
   sync; the offline guard stays for every other test. CI gets a cache step before the data-marked tests.
4. **Criterion:** after removal from HEAD, every freeze check and the full suite (both markers) pass.

## 5. Evidence that today uses git history (inventory section 6)

The receipt commit takes the role the data commit had; each mechanism changes the path it looks at, not its logic:

| Mechanism | Today | After O9 |
|---|---|---|
| AI-book seal (ai/receipts.py, submissions.py) | GitHub push time of the submission file | push time of its receipt |
| Health check (health/evidence.py) | push receipt of the commit that added the row | push receipt of the part's receipt |
| Card witness, desk "committed before the deadline" | commit of the record | commit of its receipt |
| Scoring keyed to back-fill's last commit (forecast_scoring/wiring.py:64-67) | `git log -1 -- backfill_v1.csv.gz` | `git log -1 -- receipts/<that path>.sha256` |
| Replay of a live day (replay.py:59-75, `git archive`) | repository data at the pack's commit | receipts present at that commit, bytes from the cache |
| Ledger trials, playbook evidence (git pickaxe) | the data row's commit | the receipt's commit |
| market-brief paper-trade lock (lab/timing.py:31-82) | first commit of the row | first commit of the part's receipt |

## 6. The A16 recorder (first writer to move, with the confirmed rate-limit cause)

Evidence (16 Oct): one recorder per mark gave 0 failed quotes (10:45, 11:30, 11:45, 12:45); two at once gave 74-87
(11:00, 12:00, 12:15, 12:30, 13:00); a read-only probe at 12:36 gave one stream 224/224 and two streams 66-67 failures
each, Groww code `429` in a `status: FAILURE` body, which the SDK raises as plain `GrowwAPIException` (so the ledger
showed only the class name). Design:
1. **One taker per mark.** Before a mark, a run commits a claim receipt `receipts/intraday/claims/<day>/<mark>.json`;
   git's push decides atomically (a rejected push is pulled; a claim already there means the mark is taken). A run
   whose claim lost waits for the next mark; the overlap still covers a dead run, because a dead run claims nothing.
2. **Failed quotes are retried once**, after the pass, at the same pace, and the failure keeps Groww's code
   (`GrowwAPIException:429`), never the message text.
3. Slots, rv and heartbeat become Drive parts with receipts; the realised variance reads the parts from the cache.
4. The alert text says the realised variance is void only when an index level is unusable (an `incomplete` mark has
   a usable index; status.py, realised_vol.py).
5. A restarted routine agent never recomputes `--until` from the new hour (16 Oct: the 10:52 run's restart at 11:50
   extended it to 13:05 and duplicated the 11:52 run); the claim rule makes a duplicate harmless anyway.

## M. market-brief (contactexepex/agentic-stock-prediction)

Inventory: 74 data kinds, 119M, 1,666 files; `reports/` 7.2M; no Drive code. Every kind is a day file
`data/<m>/<kind>/YYYY/MM/YYYY-MM-DD.<ext>` appended by several runs (news, pre-open, post-close, evening), sometimes
for an earlier day; agents append with `cat >>`; reports and `index.html` are rewritten. Every reader opens all files
of a kind through `core/database.py connect()` (`**/*.<ext>` per kind, database.py:166).
1. `core/storage.day_file` becomes a part per run (`YYYY-MM-DD.<run_id>.<ext>`); `connect()` already globs every file
   of a kind, so readers see the union unchanged. `cat >>` steps become one `scripts/store.py add <kind> <file>`.
2. Each routine starts with a cache sync of `data/<market>/` (incremental) and points `MB_ROOT` at the cache; it ends
   with upload and receipts instead of `git add data ...` (PROMPT.md 9e, 12, 13, 14; NEWS 3, 3f; INTRADAY 5;
   POSTCLOSE 9; EVENING 7; WEEKLY 7); `onboard.yml` likewise.
3. Reports: each run's report is a new file; `index.html` becomes a page built per run, never an overwrite.
4. The paper-trade lock uses the receipt's first commit (section 5); the golden harness reads its inputs by SHA.

## 7. Existing data

Upload every data file of both repositories to Drive under the new layout, write its receipt with the SHA-256 of the
committed bytes, verify by download, and only then remove the files from HEAD, folder by folder, after that folder's
readers read from the cache (so nothing breaks in between). Git history is not rewritten (open question 1).

## 8. Order (each step its own judge round; a step switches only when its readers work)

1. The five parts (section 2) with tests on a local store and a fake Drive.
2. A16 (section 6) — the most time-critical writer.
3. The 3 pm recorder and quote-recorder-nse; then the panel, closes, margins, participant-OI workflows.
4. Forecasts, AI books, scores, post-mortem, health, cards, desk and Book 1 (section 5 evidence moves with them).
5. The hand-run writers and tools; then frozen inputs and tests (section 4); then removal from HEAD (section 7).
6. market-brief (section M) after its approval.

## Risks (plain)

- A Drive outage or a revoked token stops every run: each run alerts and keeps the bytes in a local spool, uploaded
  by the next run before anything new.
- Speed: one Drive stream measured 0.41 MB/s (A14c, 16 Oct). A cold cache of market-brief's 119M is minutes; the
  incremental cache keeps a daily run to the new files. The cache must persist per environment, or every run pays
  the cold cost.
- Many small files: one receipt per Drive file grows the receipts tree (market-brief writes tens of parts a run).
  Reasoning only: thousands of tiny files a month are fine for git; a yearly roll-up receipt can be added if not.

## Criteria

1. No workflow, routine or CLI adds a data file to either repository; CI and the hook refuse one.
2. Every Drive file has one receipt with a matching SHA-256; a planted changed file stops the reader with an alert.
3. Two A16 runs racing for one mark, tested exactly with two clones of one bare origin: both commit a claim, one push
   lands, the loser's pull meets the add/add conflict on the claim file, keeps the winner's copy (`-X theirs`, the
   committer's existing first-push-wins rule), takes no snapshot and waits for the next mark; one snapshot is taken,
   zero rate-limit failures from overlap.
4. Every report, read model and score built from the cache equals the one built from repository data for a recorded
   day (byte-identical).
5. Freeze checks and the full suite pass after removal from HEAD.
6. Existing data: one receipt per copied file, all hashes equal, then removal.

## Open questions for the owner

1. Rewrite git history to remove old data from the public repositories (force push; every clone re-clones)?
2. A short Slack line on a good recorder run, or silence (today: alerts only, by design)?

**Depends:** A16f (merged 209ac0f6) · **Size:** XL, built in the steps above · **Status:** story text for the judge
