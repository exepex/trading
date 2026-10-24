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
| `DriveCache` | `sync(prefix, into=, strip=)`: the receipts are the index (Drive is never listed; a file without a receipt is never read); downloads only what the cache lacks or holds with other bytes; checks every byte against the receipt's SHA-256; a missing or changed file is reported, never written. Every caller stops and alerts when `not report.complete`. Files restored with `into=` go to git-ignored paths only | `GoogleDriveStore` reads, `DriveOnlyQuoteStore`'s SHA check |
| `PartTable` | write one CSV part per run and day; read the union of a table's parts in path order. JSONL parts and supersession rules (latest-wins) are not built: each table keeps its own rule, and a step that moves a JSONL or superseding table builds or names its reader first (judge 242) | new; replaces in-place appends |
| `Snapshot` | versioned state files `<name>/<run_id>.json`, newest run_id wins; two runs in the same UTC second are ordered by the run_id's random suffix, so a step whose snapshots can share a second must not rely on their order | replaces `DriveIndexStore.replace` |

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

## O9-child: the Drive store never caches an absence (24 Oct 2026; story text first)

Branch `story/o9-child-no-absent-cache`, from main. Assigned by the orchestrator on 24 Oct to REH1's builder
(session_01GAACYjcfHWkC3hp33iiMXV): O9's owner on the register is the earlier orchestrator session. Lane 1 (Drive,
every reader and writer of the record), one judge. Code starts after the judge.

### The finding (strong evidence: a dry run's own branch)

The G10 builder's 23 Oct rehearsal (run 20261024T152428Z-b3890a) failed `price_ranges` with "BANKNIFTY build failed:
the Drive cache could not verify the close tables: data/price_ranges/v1/closes/banknifty_through_2026-10-22_rows002415_
ea232e876681.csv: in the receipts, not returned by Drive".
- The receipt it names is the step's own. Commit f1cd35fb1 on `rehearsal/2026-10-23-20261024T152428Z-b3890a` ("step
  price_ranges") adds it, written at 15:20:06 IST by writer `pricerange`, run 20261023T094954Z-6417f3. So the step
  wrote the table, then could not read it back in the same process.
- The step writes through `DataStore` (`build_data_store`: its own `GoogleDriveUploadStore`) and reads through
  `DriveCache` (`build_drive_cache`: a second instance). `GoogleDriveStore.get` walks the path with `_child`, which
  caches an absent folder or file as `None` (`fno/storage/google_drive.py:68-81`, `_file_id(fresh=False)` at
  90-99). The cache's instance had looked under the folder before the writer's instance created it, kept "absent",
  and answered the later read from that memory without asking Drive.
- Two things hide it, so it fails only when both are absent. A warm local cache (a file already on disk with the
  receipt's SHA-256 is never asked of Drive). And the replay clock: from the real file's receipt `written_at` (15:20:20.479
  IST for this table; the receipt reached main at 15:20:35) REH1a's visibility lets `DryrunDrive` fall back to the
  real record's copy, whose bytes are the same, so a read after that time passes despite the stale absence. The
  failing run's step ended at 15:20:20.40, before it; REH1j's two samples ended at about 15:20:26, after it, and
  passed on the same code. A cold cache read before the real `written_at` fails. (Corrected in the code
  round: the text first said the start times were not the cause; they are one of the two masks.)
- It is not a rehearsal-only bug. In a real run the same happens whenever one instance reads a path before another
  creates it in the same process (the first file of a new folder: a new year, a new dataset). A rehearsal makes it
  systematic, since every `dryrun/<run_id>/` folder starts absent and `DryrunDrive.get` looks there first.

### The rule (the design fix, not a rehearsal patch)

- `_child` caches only what it found (an ID), never an absence: a later lookup of an absent name asks Drive again.
  That is the rule `GoogleDriveUploadStore._fresh_child` already states for writes ("Looks again instead of
  trusting a cached absent"); reads now keep it too. `_fresh_child` keeps its own re-check of a found ID.
  `file_id(fresh=True)` only drops the file's own key, so today a cached absent folder above it fails it too (judge
  612 reproduced it); with the rule it finds the file like every other walker of `_child` (`get`, `metadata`,
  `checksums`, `folders`).
- A cached ID is still trusted: the record is write-once (never deleted or moved by a reader), so a found item
  stays found.
- **Cost (reasoning only):** one more Drive list call per repeated lookup of an absent name within one process. A
  real run asks for absent names rarely and seldom twice. A rehearsal asks first for its own `dryrun/<run_id>/` copy
  of every read, so each cold read costs one to two more list calls (the walk stops at the first absent folder).
  Calls go through `DriveSession`'s existing pacing and retries.
- Not chosen: a fresh lookup only inside `DryrunDrive` (it would fix rehearsals and leave the real-run case open).

### Criteria (each with good, bad, boundary and empty cases, a test and a plant)

- **D1. Two instances.** Over one in-memory Drive at the HTTP level (`tests/dr1/fake_drive.py`): instance A looks
  up a path and finds it absent; instance B creates it (folders and file); A's next `get` returns the bytes. The same
  for a missing folder at each depth (boundary: the top folder, the last folder, the file itself). Plant: `_child`
  caching `None` again.
- **D2. Found IDs still cached.** A second `get` of a found file makes no second list call for its folders (a
  counting fake); an absent name is asked again each time. Plant: never caching anything (the found case fails).
- **D3. Real and rehearsal paths.** A real-root `DataStore` write then `DriveCache.sync` read in one process with two
  instances, cold cache: the file is verified and present. The same through `DryrunDrive` under the mode (the write
  lands under `dryrun/<run_id>/`, the read finds it there).
- **D4. Cold and warm cache, `price_ranges`' close tables.** `CloseTables.update` then `latest_text` over the fake
  Drive with two instances: with the local cache empty (cold) and with the previous table already on disk (warm),
  both return the new table; on main today the cold case fails with "in the receipts, not returned by Drive" (the
  test is shown failing before the fix).
- **D5. Empty.** An absent path stays absent (`get` is None, no exception, nothing created).
- **Real sample (rule 6):** the 23 Oct daily rehearsal rerun with a cold Drive cache (the cache folder emptied
  first), `price_ranges` ends ok; its run log line in the Claims.

### Gap list

| Requirement | Covered by | Or out of scope, with reason |
|---|---|---|
| The orchestrator (24 Oct): "the two-instance plant (one instance caches absent, the other creates, the first must then find it)" | D1 | |
| "real and rehearsal paths" | D3 | |
| "cold-cache vs warm-cache rehearsal of price_ranges" | D4, the real sample | |
| "a real sample: rerun the cold-cache 23 Oct rehearsal and show price_ranges ok" | the real sample | |
| A found item deleted or moved in Drive | | The record is write-once; no reader deletes or moves, so a cached ID is never stale by design |
| The service-account reader (`GoogleDriveStore`) and the owner's store (`GoogleDriveUploadStore`) | D1-D5 | One `_child` serves both |

### Claims, code round 1 (for judge F)

Built by session_01GAACYjcfHWkC3hp33iiMXV on `story/o9-child-no-absent-cache` (main merged in). Code: one change in
`GoogleDriveStore._child` (`fno/storage/google_drive.py`): an absent name returns None without being cached; a found
ID is cached as before; `_ids` holds found IDs only. No other file under `fno/` changes.

| Criterion | Test (`tests/test_drive_absent_cache.py`) | On main's code | Plant |
|---|---|---|---|
| D1 | two instances over one HTTP-level fake Drive, at three depths (`x.json`, `a/x.json`, `a/b/c/x.json`): A finds nothing with `get`, `file_id`, `metadata`, `checksums`, `folders`; B writes; A's `get`, `file_id` (fresh), `metadata`, `checksums` and `folders` all see it (judge 612's condition); and a missing last folder under a found one | all 4 fail | the absence cached again: 7 of 10 fail |
| D2 | a found file's folders are not asked twice; an absent name is asked again, its found folders not (a call-counting fake) | fails (the absent name is not asked again) | nothing cached: D2 fails |
| D3 | one step's `DataStore` write then `DriveCache.sync` read on two instances, cold cache: real root and under `dryrun/` | the `dryrun/` case fails; the real-root case passes (no stale lookup of the new name there) | as D1 |
| D4 | `CloseTables.latest_text` before and after the step's own write under `dryrun/`, cold and warm local cache | cold fails with "in the receipts, not returned by Drive", warm passes: the dry run's exact split | as D1 |
| D5 | an absent path stays absent twice, nothing created | passes | |

**Real Drive probe** (the owner's Drive, writes only under `dryrun/o9child-probe-<time>/`): two
`GoogleDriveUploadStore` instances; A reads the path, B writes it, A reads again at once.

```
main's code:  A before: None | A after B's write: None | A file_id(fresh) after: False | a fresh instance C: b'probe\n'
fixed code:   A before: None | A after B's write: b'probe\n' | A file_id(fresh) after: True | a fresh instance C: b'probe\n'
```

It also shows no Drive search lag: a fresh instance finds the file at once, so the stale cache was the only cause.

**Cost** (judge 612 m3; the fake, 20 files read through `DryrunDrive` as a rehearsal reads them): 20 cold reads take
44 list calls (main's code: 25); the same 20 again take 20 (main's code: 0). That is about one extra call per read,
for the absent `dryrun/<run_id>/...` folder. A real run reading existing paths pays nothing extra.

**Gates** (main merged in): 16294 passed, 14 xfailed, 0 failed; ruff, format, imports, record scan, numbers clean.
