# O9b. Fetched data out of GitHub into Google Drive, group by group (lane 1)

**Owner:** session_013u1Ac2N9eRQ8XCYPjwpaat (O9 from 22 Oct 2026; the first owner session no longer exists) ·
**Orchestrator:** session_01VG1RqxLFUVdvvPuMRYZtDH · **Judge:** Judge F · **Branch:** `story/o9-data-to-drive`, then
one `story/o9b-<group>` branch per step · **Builds on:** O9 (`docs/stories/O9-data-to-drive.md`, judge 228 add. 4) and
its built store: `DataStore` (write-once Drive, `fno/storage/data_store.py`), receipts (`receipts/<path>.sha256`),
`DriveCache` (verified sync), `PartTable` (judge 242).

**Owner, 22 Oct 2026 (orchestrator; DESK_DECISIONS row of 22 Oct):** reverse the cut-list's "migrate only when
needed": every fetched data file goes to Drive. Decided the same day:
1. **Stay in GitHub:** the manifests and receipts (G7), the evidence logs of write and release times (G6), the
   hand-curated settings (G8: `calendar/`, `events/`, `followed-companies/`, and `global-cues/us_market_closures.csv`,
   a sourced hand list), `research/forecasts/**` and the desk records (`journal/`, `accounting/`, `research/ops/`,
   postmortems, cards). They are metadata, our own reviewed inputs or sealed evidence whose worth is git's push time.
2. **History stays as it is:** no rewrite, no private repository. New fetched data goes only to Drive from now on.

## 1. Inventory (main, 22 Oct 2026; `du` and `git ls-files`)

`research/data` holds 73M in 1,926 tracked files. What moves:

| Group | Size, files | Kind | Writer (trigger) | Readers |
|---|---|---|---|---|
| G3 global cues | 1.9M, 8 | 5 append tables (`brent`, `us10y`, `usdinr_rbi` CSVs; `us_trading_dates.csv` rebuilt), `checks/` rewritten each run | `global-cues.yml` (`fno/global_cues`) | the cue tables (`CueTable`, weather drivers, A17 checks); FL1's report facts read `brent.csv` and `usdinr_rbi.csv` by path (`fno/forecast_lab/page/facts.py:19`) |
| G3 VIX | 852K, 4 | `india_vix_daily.csv` append table, `checks/` rewritten | `vix-history.yml` (`fno/vix_history`) | only its own CLI (`docs/DATA_USE_MAP.md`) |
| G4 margins | 384K, 8 | `margins.csv`, `stress_factor.csv`, `stress/` | `nse-margins.yml`, `stress-factor.yml` | the risk manager, C4's margin check (live desk) |
| G2 intraday | 7.2M, 1,791 | `rv-candle/` (1,684 static files, A16b), `slots/`, `rv/`, `heartbeat.json` (live A16) | A16b back-fill, A16 routine | E8 fills, v4 realised variance, the post-mortem |
| G5 NSE chains | part of 568K | `quotes/nse/` day files with values (Groww's `quotes/groww/` holds sidecars and markers only, already receipt-like, and stays) | `quote-recorder-nse.yml` | the price distribution, v2 capture, health |
| G1 panel and closes | 46M, 19 | `options_YYYY.csv.gz` (closed years static, the current year appended), panel manifest, `warmup_closes.csv` | `panel-days.yml`, `index-closes.yml` | v2 forecasters (frozen; FREEZE_v3 records the manifest and closes), v4 rules, the range forecaster, the research engine, desk packs, risk |
| Studies | about 8M | data and result files of `research/<date>-<study>/` (capacity screen 5.5M, backtest, experiment 1 ...) | hand-run | their own scripts; experiment 1 is read at its RUN_COMMIT by `git show` |

The README files, code, FREEZE texts and study write-ups stay in GitHub.

**Readers whose evidence is git's push time** (judge 475 SF1). They judge a file by when GitHub received the commit
that added it, so they move with their group and must give the same answer afterwards:
- O8's health check: `fno/health/expectations.py` (`INTRADAY_FOLDER` for A16's marks, `warmup_closes.csv` for the
  index closes, the panel's `manifest.json` for the panel day) and `fno/health/quote_checks.py` (`quotes/`, the
  `.canonical` markers; G5 moves only the NSE chains, the markers stay); `fno/health/desk_checks.py` (A16's
  `SlotLedger`).
- v4 scoring: `fno/forecast_scoring/v4/wiring.py` (`RvTable` on `intraday/rv/`, A16's 15:30 flag per day).
- The owner-timing desk: `fno/desk/owner_timing/wiring.py` (`SlotLedger` on `intraday/slots/`, E8's fills).

**Design line:** push-time evidence moves to the push time of the file's receipt (`receipts/<drive path>.sha256`,
committed by the writer in the same run), the role the data commit has today; each check changes the path it looks at,
never its rule. A receipt pushed after the deadline is late exactly as the data file is today.

**Global cues' own path readers** (judge 475 minor): `fno/global_cues/wiring.py` (`CUES_FOLDER`: the cue tables through
`CsvRowLog`, the shared revisions log, `CHECKS_FOLDER`, `TRADING_DATES_FILE`, `BEHIND_EPISODES`), `check_files.py`
(writes `checks/` and `us_trading_dates.csv`), `cue_calendars.py` and `wiring.py`'s `us_market_closures()` (the hand
list `us_market_closures.csv`, which **stays** in GitHub, read by `NyseCalendar`), and FL1's
`fno/forecast_lab/page/facts.py` and `fno/forecast_lab/sections/global_cues.py`. `checks/behind_alerted.txt` is alert
state (names only, judge 351 add. 2) and stays, like the other alert states in `research/ops/alerts/`.

**Reader index** (every `fno/` module that names a group's paths, `grep` on main, 22 Oct; a few are writers or name a
constant only; each step re-checks and lists its exact readers and writers):
- G1 (34): `ai/paths.py`, `composition.py`, `desk/pack_wiring.py`, `forecast/{wiring,baseline_wiring}.py` (frozen),
  `forecast_lab/page/facts.py`, `forecast_scoring/{wiring,replay,resolution}.py`, `forecast_scoring/v4/{wiring,g7_series}.py`,
  `forecast_v4_rules/{series,wiring}.py`, `health/expectations.py`, `pipeline/{index_closes,panel_days,panel_wiring,wiring}.py`,
  `price_distribution/wiring.py`, `price_ranges/{closes,tables,wiring}.py`, `research_data/{nifty_panel,panel_append,panel_reader,panel_store,warmup_closes}.py`,
  `research_engine/{close_series,cycles,leg_prices}.py`, `storage/wiring.py`, and VIX's own overlap check
  (`vix_history/{check_files,wiring}.py` read `warmup_closes.csv`).
- G2 (26): `intraday/*` (recorder, ledger, rv and candle tables, back-fill, settle, wiring), `desk/owner_timing/{wiring,mark_snapshots}.py`,
  `forecast_scoring/v4/wiring.py`, `forecast_v4_rules/{series,wiring}.py`, `health/{expectations,desk_checks}.py`,
  `learning/{readers,wiring}.py`, `market_read_models/weather_block.py`.
- G4 (15): `nse_margins/{job,margin_log,stress_log,wiring,cli}.py`, `risk/{margins,stress_factor,settings,wiring}.py`,
  `checks/{validity_margin,validity_factor,validity_settings}.py`, `scoreboard/entry_facts.py`, `daily/wiring.py`.
- G5 (NSE chains; 30 modules name `quotes/`, most for Groww's markers, which stay): `quotes/{recorder,compare,cli}.py`,
  `price_distribution/sources.py`, `forecast/capture.py`, `forecast_scoring/{wiring,replay}.py`, `health/{expectations,quote_checks}.py`,
  `market_read_models/chain_blocks.py`, `scorecard/wiring.py`, `desk/{daily_wiring,git_sync}.py`, `daily/*`.
- G3: the global-cues readers above; VIX: `vix_history/*` only.

## 2. How a group moves (the same five steps each time)

1. **Upload the existing bytes** through `DataStore` under `data/<group path>`, one receipt each, and verify by
   downloading. An append table moves as its first part: today's file, byte for byte.
2. **Writers write to Drive only**, behind the interfaces they already have:
   - an append table (rows only ever added) becomes a `PartTable`-style series: each run that adds rows writes one new
     part (header and the new rows), and the table is the union of its parts in name order;
   - a file rewritten every run (checks, rebuilt lists) becomes a snapshot series: a new file per run, the newest is
     current;
   - a static file (one per session, closed years, study results) is one Drive file.
   O9b adds one receipt-backed append-table adapter and one receipt-backed snapshot series, reading through the
   verified cache (receipts are the index, Drive is never listed: O9 rule 4). A17's `RowLog` port already has Drive
   classes (`DrivePartsRowLog`, `DriveSnapshots`) that list Drive instead; when global cues move (step 1b) they move
   to the receipt-backed classes too (one way, not two).
3. **Readers read through the verified cache.** A reader that goes through a port (the cue tables, the VIX table)
   changes one line in its composition root. A reader that opens a path (FL1's facts, the frozen panel readers) gets
   either the same port (agreed with its owner) or, where the code cannot change (frozen files), the files restored
   byte for byte to their old, now git-ignored paths before it runs (O9 section 4.1: `DriveCache.sync(..., into=)`).
   A missing or changed file stops the reader and alerts, never reads a partial table.
4. **Tests** that read the real files switch to fixtures in `tmp_path`; those whose point is the real data get the
   `data` marker and run after a cache sync (CI gets that step with the Drive settings it already has for the jobs).
5. **Remove the files from HEAD** only after steps 2-4 are merged and one scheduled run has passed on the new path;
   the folder is added to `.gitignore` and to the commit hook's refusal list (O9 rule 5), so nothing writes data
   back into a checkout.

**Equality criterion for every group:** the table rebuilt from Drive equals today's committed file byte for byte
(SHA-256 equal), and each reader's output on a recorded day is the same before and after the switch.

## 3. Steps (each its own judge round; live readers never broken)

| Step | Group | Live reader? | When it may merge |
|---|---|---|---|
| 1 (pilot) | G3 VIX (`research/data/vix/`) | no: only its own CLI reads it | text and code may be judged and merged before Mon 26 Oct (no live reader) |
| 1b | G3 global cues | FL1's report reads two tables (agreed with its builder first) | after or inside GC2 (below); from Mon 26 Oct, outside 14:00-16:15 IST |
| 2 | G4 margins | yes (desk risk, C4) | from Mon 26 Oct, outside 14:00-16:15 IST |
| 3 | G2 intraday: `rv-candle/` first (static), then the live A16 files | yes (E8, v4 RV) | as step 2 |
| 4 | G5 NSE chains | yes (price distribution, capture) | as step 2 |
| 5 | G1 panel and closes, with restore-to-path for the freeze checks | yes (most forecasters) | as step 2, last of the market data |
| 6 | Studies | no | any time after its judge round |

**One builder per function:** GC2 (DESK_DECISIONS 22 Oct, row "Three new stories"; the A17 builder, judge F) reworks
the same global-cues module (FRED where it is on time and equal). So the pilot is VIX alone, and the global-cues
tables move either inside GC2, by its builder through O9b's adapters, or right after GC2 merges, as agreed with that
builder; never two versions of the module at once.

Each step's text names its files, writers, readers (push-time readers first), the reader owners agreed (most have no
live owner; the orchestrator agrees on their behalf), its tests, its removal list and **its own gap list** (judge 475
B1): every requirement of this text and of the step, and where the step meets it.

## 4. Git history (honest constraint; owner decided: leave it)

Removing a file from HEAD does not remove it from git history: the repository is public, so every version committed
before the move stays readable by anyone with a clone or the web interface. The options and their cost, for the
record:
- **Leave history (chosen):** free; past data stays public; data from each group's move date on never enters GitHub.
- **Rewrite history** (`git filter-repo`, force push): every clone and session must re-clone, every open branch
  breaks, and every commit SHA changes, including the SHAs cited in FREEZE records, judge files and claims, so frozen
  evidence would need re-pinning. Large and risky.
- **Private repository:** one owner setting, history kept; GitHub Actions minutes become metered (2,000 a month on
  Free, 3,000 on Pro); about 70 scheduled runs a day plus the checks on every push is an estimated 6,000-15,000
  minutes a month (reasoning only; the owner's billing page has the real figure).

## 5. Risks

- **Drive outage or expired consent** stops every switched reader: each alerts once and reads nothing partial
  (today's behaviour of the Drive-only quote store).
- **Speed:** one Drive stream measured 0.41 MB/s (A14c). A cold cache of G1 (46M) costs about 2 minutes per job;
  every job syncs only its own group, and incremental syncs download only new parts.
- **Many small parts:** one part per run per table. Reasoning only: a few thousand small files a year are fine for
  Drive and git (receipts); a yearly roll-up can be added if not.
- **A writer missed:** the hook and CI refusal (step 5) catch any later write into a moved folder.

## Acceptance criteria (each step, good, bad, boundary and empty cases)

1. Every moved file has one receipt whose SHA-256 equals the committed file's; a planted changed or missing Drive
   file stops the reader with one alert.
2. An append table rebuilt from its parts equals the old file byte for byte; a run that adds no rows writes no part;
   two runs the same second never collide (run ids).
3. Each reader's output on a recorded day is identical before and after its switch (the step names the output).
4. No workflow, routine or CLI writes into a moved folder; the hook refuses a commit adding one.
5. After removal from HEAD: the full suite (both markers) and every freeze check pass.
6. The first scheduled run after each switch is cited in the step's claims.
7. **O8 is unchanged:** on a recorded day, the health check's rows for the moved group are identical before and after
   the switch; a receipt pushed after the deadline is `late` and a missing one `missed`, as the data file was (the
   same for v4 scoring's per-day flags and the owner-timing desk's marks).

## Step 1: the VIX pilot (`story/o9b-vix`)

**Files that move** (`research/data/vix/`): `india_vix_daily.csv` (789,682 bytes, 4,019 days from 19 Jul 2010) and
`checks/{gaps,level_flags,overlap_index_close}.csv`. `README.md` stays.
**Writer:** `vix-history.yml` (`python -m fno vix-history fill`, then `sweep`). **Readers:** only `fno/vix_history`
(its `fill`, `check` and `verify` commands) and its tests (`docs/DATA_USE_MAP.md`; reader index above). No push-time
reader; no live reader; VIX's overlap check reads G1's `warmup_closes.csv`, which stays until step 5.

**Design (one new class behind each existing port, one line per composition root):**
- A17's `RowLog` port moves, unchanged, from `fno/global_cues/row_log.py` to `fno/storage/row_log.py` (shared by
  every append table; global cues' imports follow, nothing else changes).
- `fno/storage/receipted_rows.py`: `ReceiptedRowLog` (an append table as write-once Drive parts named by the run id,
  through `DataStore`, read through the verified `DriveCache`; the rows are the parts' rows in name order) and
  `ReceiptedSnapshots` (a report as one new Drive file per run, the newest current). A file in Drive without a
  receipt is never read; a missing or changed one raises `DriveDataUnavailable`.
- `fno/storage/report_files.py`: the `Report` port (`write(fields, rows)`) with `CsvReportFile` (an atomic file
  rewrite) and `ReceiptedSnapshots`.
- `VixDailyTable` takes a `RowLog` (its rules unchanged: no day twice, no hole filled, a broken log refused as
  `VixTableConflict`); `VixCheckFiles` takes one `Report` per check file. `fno/vix_history/wiring.py` picks the
  receipt-backed classes under Drive's `data/vix/`.
- `fno/storage/moving.py` and `python -m fno vix-history move`: each committed file becomes its series' first file,
  read back equal through the cache; again is a no-op; Drive holding other bytes stops the move, nothing overwritten.
- `vix-history.yml` commits `receipts/data/vix/` and the manifests instead of the data folder.
- `data` tests: `pytest.ini` keeps the `data` marker out of the default run; `python -m fno data-cache sync <prefix>`
  fills the verified cache; `tests/data_cache.py` reads only that cache (a Drive stand-in refuses every call, so a
  missing file fails with the sync command); `tests/vix_history/test_committed.py` runs on it. `data-checks.yml`
  (daily, and on pushes touching receipts, tests or `fno/storage/`) syncs the moved prefixes and runs `pytest -m data`,
  with an alert step, on O10's capture-watch list.

**Order:** judge PASS → `vix-history move` from this container on the judged branch (receipts committed on the
branch) → `data-cache sync data/vix` and `pytest -m data` green → merge (full suite) → the first scheduled run on
the new path → a removal commit: the four files out of HEAD, `research/data/vix/*.csv` and `checks/` in `.gitignore`
and in the commit hook's refusal list.

**Gap list (step 1):**

| Requirement | Where |
|---|---|
| Upload the existing bytes, one receipt each, verified by download | `vix-history move` (`move_into`); `tests/o9b/test_moving.py` |
| Rebuilt table equals today's file byte for byte | `ReceiptedRowLog.rebuilt`; move reads back equal; `test_receipted_rows.py` |
| Writer writes Drive only | `wiring.py` (receipt-backed classes); `vix-history.yml` commits receipts |
| A run adding no rows writes no part; two runs never collide | `test_a_run_that_adds_no_rows_writes_no_part`, `test_two_writes_in_one_run_keep_their_order` (run-id names) |
| A changed or missing Drive copy stops the reader | `test_a_changed_drive_copy_stops_the_reader`, `test_a_missing_drive_copy_stops_the_reader` |
| A Drive file without a receipt is never read | `test_a_file_in_drive_without_a_receipt_is_never_read` |
| The table's rules unchanged | `tests/vix_history/test_table.py` (12, on `CsvRowLog`) |
| Reader outputs identical | `test_committed.py` (`data`): the checks the code writes from the Drive table equal the Drive checks byte for byte |
| Tests on real data | `data` marker, `data-cache sync`, `data-checks.yml` |
| No push-time reader, no live reader | inventory above; nothing outside `fno/vix_history` reads it |
| Removal from HEAD, refusal in the hook | the removal commit after the first scheduled run |
| One builder per function | `RowLog` moved, not copied; A17's owner told; global cues untouched otherwise |

## Gap list

| Requirement | Where |
|---|---|
| Every fetched or read-only data file out of GitHub into Drive (owner, 22 Oct) | sections 1-3; the kept groups named in the owner's decision 1 |
| Write-once Drive, SHA-256 receipts, verified cache (O9 rules 2-4) | section 2 steps 1-3; criteria 1-2 |
| Inventory with sizes, per dataset | section 1 |
| Each reader switched to the verified cache | section 2 step 3; reader index (section 1) |
| Readers whose evidence is git push time | section 1 (push-time readers, design line); criterion 7 |
| Receipts kept in GitHub; files then removed from the tree | section 2 steps 1 and 5; criteria 4-5 |
| Agree each dataset with its reader's owner | section 3 (orchestrator for readers without a live owner; GC2 and FL1 named) |
| Never break a live reader; nothing live before Mon 26 Oct or 14:00-16:15 IST | section 3 table; criterion 3 |
| Story text first, then small steps, one group each | section 3 |
| Frozen readers keep working | section 2 step 3 (restore-to-path, O9 4.1); criterion 5 |
| Tests on real data | section 2 step 4; criterion 5 |
| Git history stays public; the options and their cost | section 4 |
| Kept in GitHub: manifests, receipts, evidence logs, hand-curated settings, sealed records (owner, 22 Oct) | owner's decision 1; `us_market_closures.csv` and `behind_alerted.txt` named |
| Each step's own requirements | each step's gap list (section 3) |
| A new dataset read straight through `DriveCache.sync` (as `circulars` and `flow_history` do) stops before its first receipt: write first, or read through `ReceiptedRowLog`, whose empty series reads empty (judge 536 minor) | each step's design and gap list |

## Open questions

None for the owner: the 22 Oct decisions above settle scope and history.

## Claims

**Judge 475 (FAIL, round 1 of 2), all accepted:**
- B1 accepted: a gap list for this text (above), and the rule that each step's text carries its own.
- SF1 accepted: the push-time readers (O8's `expectations.py`, `quote_checks.py` and `desk_checks.py`, v4 scoring's
  `RvTable`, the owner-timing desk's `SlotLedger`) are in section 1. The design line says that push-time evidence moves
  to the push time of the file's receipt. Criterion 7 says O8 is identical and a late receipt is still late. While
  checking, I found three more readers and added them: VIX's own overlap check reads G1's `warmup_closes.csv` (so it
  moves with G1); FL1's `forecast_lab/sections/global_cues.py` reads the cue tables; and `checks/behind_alerted.txt` is
  alert state, so it stays.
- Minor accepted: global cues' own path readers are named, with the readers of the hand list that stays
  (`us_market_closures()` and `NyseCalendar`).
- A full reader index per group (`grep` on main, 22 Oct) is in section 1. It covers every module, not only the judge's
  examples.

**Step 1, the VIX pilot (code, for Judge F):**
- Built as in step 1's text above. Files: `fno/storage/{row_log (moved), receipted_rows, report_files, moving, cache_cli}.py`;
  `fno/vix_history/{table, check_files, wiring, cli}.py`; `.github/workflows/{vix-history, data-checks, capture-watch}.yml`;
  `pytest.ini` (the `data` marker); `tests/data_cache.py`; `tests/o9b/`; `tests/vix_history/{test_table, test_committed}.py`.
- Tests: 13 in `tests/o9b/` (a moved table rebuilds byte for byte; no rows means no part; same-run order; changed,
  missing and unreceipted copies; snapshots; moves, a second move, refusal, an unequal read-back); VIX's 12 table
  tests on `CsvRowLog`; 4 `data` tests on the verified cache.
- **Mutations: 8 of 8 caught.** Two survived at first and their tests were added: a stray file in the cache folder
  without a receipt, and a read-back unequal after the move.
- Gates: ruff, format, imports and record scan are clean. Full suite: 9,837 passed with 1 failure, and that failure
  is on main too (`tests/forecast_v4_rules/test_v4rules_phase2.py::test_every_committed_g7_record_row_carries_this_trees_method_hash`,
  G7's records, already reported to the orchestrator). The 4 `data` tests run after the move.
- Reader index: cited from section 1 (judge 475 add. 1). Nothing outside `fno/vix_history` reads VIX.
- Not yet: the move, the data tests on the moved data, the first scheduled run, and the removal commit (the order
  above). They follow the PASS, and the claims will record each.
- **After the PASS (judge 477), in order:**
  - The move read back equal, and its re-run just before the merge said "already in Drive, equal" for all four files.
  - Merged at ef9e976b.
  - First data-checks run 39769005484: "4 downloaded and verified", 4 passed.
  - **First scheduled run on the new path:** vix-history.yml run 39911658650, 23 Oct 06:28 UTC (the 07:11 IST cron,
    landed 4 h 47 min late). Every step succeeded and there was no alert. Its commit 6964334 holds only three receipts,
    `receipts/data/vix/checks/{gaps,level_flags,overlap_index_close}/20261023T062835Z-4b0c64.csv.sha256`: no table
    part, because September was already archived, so no rows were added. It added no repository data file.
    [strong: run log]
  - **Removal commit** (`story/o9b-vix-removal`, for Judge F):
    - `research/data/vix/*.csv` and `checks/` are out of HEAD; the README stays and says where the data is.
    - Both paths are in `.gitignore`.
    - The record scan refuses them by path even past `git add -f` (`MOVED_VIX_FILES`, `fno/record_scan/forbidden_files.py`,
      wired in `build_record_scanner`). A test commits a force-added file in a real checkout and sees it refused,
      and sees the README still commit.
    - The `vix-history move` action and its repository paths are deleted, as nothing can move any more.
    - The data tests still pass on the cache.
  - **Judge 477 addendum 1: PASS at 9c2ac0b6; merged to main at d0c22a05 (23 Oct, 16:3x IST).** Gates on the merged
    tree: 14,548 passed and 16 xfailed, with ruff, imports, record scan and check_numbers clean. The post-push rerun
    was the same.
  - Found on the way, for a later step and not built here: every run writes three new check snapshots even when
    they are unchanged (3 receipts a day for VIX). A repository file rewritten with the same bytes used to make no
    commit. Writing a snapshot only when it differs from the latest one would restore that.

**data-checks trigger (story/o9b-data-checks-trigger, for Judge F; assigned by the orchestrator, 23 Oct):**
- **The defect, mine:** data-checks.yml's push filter held `receipts/data/**`, which matches every job's receipts,
  several pushes an hour. GitHub keeps one pending run per concurrency group and cancels the others, even with
  `cancel-in-progress: false`. On 23 Oct, O10's capture-watch recorded 24 "data-checks, before any step, cancelled"
  rows in `research/ops/capture_errors.csv` (16 by 16:24 IST).
- **Root fix:** the push paths are now `tests/**`, `fno/storage/**` and the workflow itself. The daily 09:41 IST run
  checks the moved groups' new receipts. `tests/o9b/test_data_checks_workflow.py` pins this.
- **O10's side:** `fno/health/run_failures.py` now has `REPLACEABLE = ("news-capture", "data-checks")`, with the O10
  builder's condition beside it. That condition holds only while data-checks records nothing per push or per day that
  a cancelled run would have had to write. The O10 builder (013YJ5gj, handed over) agreed as reasoning only; the
  orchestrator assigned the change to me.
  - The test `test_a_replaced_data_checks_run_is_neither_recorded_nor_alerted` checks both cases: cancelled before a
    step means no row and no alert; cancelled after a step means one row and one alert.
  - Mutation: the old one-entry tuple fails it.
- **For O10's criterion 7** (response_254 is O10's file and is left alone): the 23 Oct rows are the first live
  evidence that capture-watch records cancelled runs, each with its run link and "before any step".
- **Judge 477 addendum 2: PASS at 5a423497 (the trigger); addendum 3: PASS at ccfc340a (REPLACEABLE).** Both merged
  together with the orchestrator's go (23 Oct, after 16:15 IST).

**`DriveCache.sync` on a single file (story/o9-sync-file, for Judge F; assigned by the orchestrator, 23 Oct):**
- **The defect:** `ReceiptFolder.under()` treated every prefix as a folder. For one file's path it returned `[]`, so
  `sync(<file>)` answered `SyncReport(present=0, problems=[])`, an empty success. The FL1 builder proved this is
  the root cause of the broken evening check on 23 Oct.
- **The fix, in O9's store (`fno/storage`):**
  - `under(prefix)` returns that one receipt when `prefix` names a receipted file, so a single-file sync now
    brings exactly that file, verified.
  - `sync()` reports "`<prefix>`: no receipts under it (neither a receipted file nor a folder holding one)" when
    nothing matches, so a wrong path is never an empty success.
  - A receipt-backed series with nothing written yet (a new table, say the global cues' revisions log) checks for
    receipts first and reads as empty, not unreadable.
- **The callers, checked on main:**
  - Single-file paths: only FL1's `forecast_lab/a4h_closes.py` and `forecast_lab/sections/gift.py`. They now get
    their file. The FL1 builder is changing them anyway; this fix makes the old call correct, not a second fix.
  - Every other caller passes a folder: `price_ranges`, `price_distribution`, `premium_ranges`, `itm_chance`,
    `circulars`, `flow_history`, `v4_pack/release` (a dirname), `school/dashcam` (a folder), `forecast_lab/wiring`,
    `cache_cli` and the receipted series.
  - The folders those callers sync from their own outputs all hold receipts today (premium_ranges 2,
    itm_chance 1, price_distribution 21), so the new problem line changes no live answer.
- **Tests:** a single file is synced alone; three wrong prefixes each give exactly the new problem, with nothing
  downloaded; an empty row log and an empty snapshot series read as empty. All 3 mutations, one per change, are
  caught.
- **Judge 536: PASS at 494d97df.** It may merge before FL1's branch, on the orchestrator's go. The judge listed all 13
  sync callers: every one that must succeed has receipts today. Their minor is accepted as a row in the umbrella gap
  list: a new dataset read straight through `sync()` must write first, or read through `ReceiptedRowLog`.

**Readers of NSE's index-close files never write to Drive (story/o9-readonly-index-close; DR1 and DRY1 row b4,
assigned by the orchestrator 23-24 Oct; agreed with the A4h, FL1 and G13 builders).**
- **The defect:** `build_index_close_files()` is A9's `RawFileLibrary`. On a file no store holds it fetches the file
  from NSE and archives it to Drive, with a manifest row. So A4h's Confirmer, FL1's editions (`lab preview`
  included) and page, and G13's issuer and `pricerange closes` could all write to Drive. A dry run did on 23 Oct
  (manifest row aa0e2ed30).
- **The fix:**
  - `fno/storage/raw_library.py` gains a `FileLibrary` interface and `StoredFilesLibrary` (the stores only; a
    missing file is `RawFile(None, "not stored yet")`). `RawFileLibrary` stays the writer's.
  - `storage/wiring.py` adds `build_stored_index_close_files()` for readers. Its stores are the service account's
    (where set) plus the owner Drive's raw area, read with the owner's settings, because GitHub's jobs carry only
    those. Without that, a reader there would have found no store at all.
  - `build_index_close_files()` stays the writer's: the panel and the warm-up closes (`cli.py`).
  - **Where reads now come from (the FL1 builder's note, stated plainly):** the old library read only the service
    account's stores and wrote to the owner's Drive. So a file that existed only in the owner's raw area was never
    read from there; it was fetched from NSE again, and the archive's `put` then found the same bytes. Readers now
    also read the owner's raw area, so they find exactly what the librarian archived. The writer's library keeps
    its old read order.
  - `daily_files`' docstring is corrected; it had said "Drive is only read".
- **Switched:** `forecast_lab/wiring.py` (`build_composer`), `forecast_lab/page_wiring.py` (VixSection),
  `price_ranges/wiring.py` (`build_issuer`, `build_table_update`) and `close_read/wiring.py` (the Confirmer).
- **What a missing file now does** (each owner confirmed their path):
  - A4h's Confirmer: its existing "no official index-close file in Drive yet" line and one overdue alert. That line
    is now literally true.
  - FL1: the 3 pm price, labelled; "not archived yet"; VIX "not available".
  - G13: `CloseTables.update` prints its "no index-close file" gap line and retries the day later. If all four
    librarian attempts fail, the 15:20 BANKNIFTY issue builds on a table one session short. G13 accepted that.
- **Tests** (`tests/o9_store/test_readonly_index_close.py`, each with NSE's fetch and the fetching library made to
  fail the test):
  - the library itself;
  - the reader's builder (a stored day read, a missing day None);
  - G13's `build_table_update` (their ask);
  - every reader's composition root naming only the reader's builder (FL1's ask for `build_composer` and the page).
  `build_composer` is not driven end to end (its cache and config stack), which is why the last check is by name.
  The by-name check reads the whole file text, so an import of the fetching builder fails it as well as a call
  (FL1's ask). A mutation back to the fetching library fails 2 tests. FL1 approved their lines (24 Oct).
- **After A4h-2 merged (92eec596):** main is merged in and `close_read/official.py`'s docstring now names the reader's
  builder and drops its old fallback to "NSE's own archive". `research_data/
  nifty_panel.py`'s `DailyFiles` docstring also says "never writes to Drive"; that module sits with the v3 panel,
  so it is left for its owner.
- **For DR1:** `record_store/wiring.py`'s own `stored_index_closes()` does the same read. DR1's owner could call
  `build_stored_index_close_files()` instead, so there is one reader builder, not two.
- **Judge 558 (FAIL, round 1 of 2), both accepted:**
  - **SF1:** `_reader_raw_stores` was untested, though on GitHub it is the reader's only store: no workflow sets the
    service account. The new test `test_on_github_the_readers_only_store_is_the_owner_drives_raw_area` sets the four
    owner settings with no service account and asserts exactly one `AreaStore` over the owner drive at `RAW_AREA`.
    With no settings it asserts `[]`. The owner drive is a local stand-in, because the real one signs in on use. The
    judge's plant (the owner area dropped) now fails it.
  - **Note 1, for FL1:** the 20:05 evening edition can no longer fetch the same day's official index-close file.
    index-closes.yml archives it at 21:11 IST or later, so a later morning edition confirms it. That is by design: the
    evening says "not archived yet" for that day.
