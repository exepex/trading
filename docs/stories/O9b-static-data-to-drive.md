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
   classes (`DrivePartsRowLog`, `DriveSnapshots`) that list Drive instead. Step 1b moves only the public cues. Until
   **step 1c** (the private cues, S&P 500, Nasdaq 100, FBIL and A17e's world indexes and pre-open rows, onto the
   receipt-backed classes, agreed with the A17 owner), two ways stand side by side; step 1c ends that (one way,
   not two).
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
| 1c | G3 global cues, private: the S&P 500, Nasdaq 100, FBIL, A17e's world indexes and pre-open rows, from `DrivePartsRowLog`/`DriveSnapshots` (derived area, Drive listed) to the receipt-backed classes | yes (A17's checks, the weather, FL1) | with the A17 owner; from Mon 26 Oct, outside 14:00-16:15 IST |
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

## Step 1b: global cues (`story/o9b-cues`; merges from Mon 26 Oct, outside 14:00-16:15 IST)

**GC2 closed with nothing built** (A17 owner, 22 Oct; response 321 addendum 1): `fno/global_cues` has no open change,
so this step moves the public cue tables, with the A17 owner reviewing the diff before Judge F.

**Files that move** (`research/data/global-cues/`): the public append tables `brent.csv` (631,009 bytes),
`us10y.csv` (618,938) and `usdinr_rbi.csv` (493,096), the shared `revisions.csv` once written; the reports rewritten
each run `us_trading_dates.csv` (76,002) and `checks/{gaps,overlap_usdinr}.csv`.
**Stay in GitHub:** `README.md`; `us_market_closures.csv` (hand-kept, sourced, owner decision 1); `checks/behind_alerted.txt`
(alert episodes, names only); `research/data/manifests/global-cues/**` and its `attempts/` (G7, G6). **Already in
Drive, unchanged:** the private cues (S&P 500, Nasdaq 100, FBIL's USD/INR, the world indexes, A17e's pre-open rows),
through `DrivePartsRowLog` and `DriveSnapshots`; moving them onto receipts is step 1c (section 3), agreed with the A17 owner.
**Writer:** `global-cues.yml` (`fill`, `check`). **Readers:** `build_tables`/`build_reader` (`fno/global_cues/wiring.py`)
serve the cue tables to A17's checks and `verify.py`, the index reader, the weather (M1, `fno/weather/wiring.py`
`build_cue_reader`, `drivers.py`), and FL1's report (`fno/forecast_lab/page_wiring.py`,
`sections/global_cues.py`); FL1's `fno/forecast_lab/page/facts.py:19` reads `brent.csv` and `usdinr_rbi.csv` by path.
**Push-time readers:** none (`fno/health/` reads no global-cues file).

**Design:** in `fno/global_cues/wiring.py`, each public cue's `CsvRowLog(CUES_FOLDER / "<cue>.csv")` and the shared
revisions log become `ReceiptedRowLog(store, cache, "global-cues/<cue>")` (step 1's class, behind A17's `RowLog`
port); `CueChecks` writes its reports through the `Report` port (`CsvReportFile` in tests, `ReceiptedSnapshots` in
the wiring), as VIX's checks do. FL1's `facts.py` reads the two tables through `build_tables()` instead of by path
(agreed with the FL1 builder; one line in its wiring). `global-cues.yml` commits `receipts/data/global-cues/` and the
manifests instead of `$CUES` in the same change. `python -m fno global-cues move` moves the files as step 1 did, and
the same re-run "already in Drive, equal" gates the merge.

**Gap list (step 1b):**

| Requirement | Where |
|---|---|
| verify.py's chain (`source_sha256` to the archived copy through the snapshot log), `first_seen_at` and provenance kept row for row (A17 owner point 1) | rows move byte for byte (rebuilt equals the file); receipts only add; `verify` run on the moved tables in the claims |
| Only the public tables move; the private cues stay in their Drive classes (point 2) | files list above |
| `behind_alerted.txt` stays (point 3) | stays list |
| `global-cues.yml`'s commit step switches with the move (point 4) | design; a workflow test |
| Every path reader traced from `build_tables`/`build_reader` (point 5) | readers list; FL1's `facts.py` switched with its builder |
| Hand list `us_market_closures.csv` stays and its readers keep reading it | stays list (`us_market_closures()`, `NyseCalendar`) |
| Upload, rebuild byte for byte, writer to Drive only, readers through the cache, removal after one scheduled run | as step 1 (section 2) |
| Live readers (weather, FL1) not broken | merges from Mon 26 Oct outside 14:00-16:15; the weather's and FL1's outputs on a recorded day equal before and after (criterion 3) |
| Data tests | `tests/global_cues/test_committed.py` and `test_us_calendar.py` move to the `data` marker; `data-checks.yml` adds `data/global-cues` |

## Step 2: G4 margins (`story/o9b-margins`; merges from Tue 27 Oct, 11:00-13:30 IST)

**The split (orchestrator, 23 Oct, on the owner's 22 Oct rule):**
- **Moves** (`research/data/margins/`):
  - `margins.csv`: 106 rows, 15,502 bytes on 23 Oct, computed from NSE's SPAN files (hand rows naming their
    calculator are allowed);
  - each `stress/stress_evidence_<day>.csv`: A14c's computed result.
- **Stays in GitHub:**
  - `stress_factor.csv`: a risk decision record, holding the owner's 1.45 seed and A14c's `applied`/`held` rows;
  - `stress/stress_files_<day>.csv`: every session's SPAN file name with its SHA-256, so manifest-like (G7);
  - `stress/stress_evidence_<day>.md`: the write-up;
  - `README.md`.
- The never-written `stress_broker_check.csv` that `fno/daily/wiring.py` names is A14c part 2's, paused off main; that
  owner moves it to this port when part 2 resumes.

**Writers:**
- A14's `NseMarginJob` through `build_margin_log` (`fno/nse_margins/wiring.py`), committed by `nse-margins.yml`.
- A14c's `StressFactorRun` through `Evidence.write` (folder `STRESS_EVIDENCE`), committed by `stress-factor.yml`.

**Readers of `margins.csv`** (the A14/C2/C4 owner's check, 23 Oct):
- C2's `MarginTable` (`fno/risk/margins.py`, wired in `fno/risk/wiring.py` from `RiskSettings.margins_file`);
- C4's `MarginFile` (`fno/checks/validity_margin.py`, wired in `fno/checks/wiring.py` from C4's `MarginSettings`; C4
  counts a row's age in sessions, which stays);
- A14's own `MarginLog`, which reads its rows back to refuse a second figure for a structure, width and day.

The school's road margin and practice wiring read only the factor file, which stays. No desk-pack reader was found.
**Push-time readers:** none.

**Design** (the pilot's classes; one owner for all of G4, who agreed on 23 Oct):
- `margins.csv` becomes `ReceiptedRowLog(store, cache, "margins/margins")`: one write-once part per run, with its
  receipt under `receipts/data/margins/`. A14's `MarginLog` keeps its refusals and appends through the `RowLog` port.
  C2's `MarginTable` and C4's `MarginFile` take their rows from that port, not from a path. C4 keeps its column check.
- `config.yaml` keeps one key that both settings read: `risk.margins.table: margins/margins`, the Drive table, in place
  of `file`. That way C2 and C4 read one source, and their settings tests stay meaningful (the owner's preference).
- Each `stress_evidence_<day>.csv` is a `ReceiptedSnapshots` file in `margins/stress-evidence/<day>`. Each factor row's
  `evidence_sha256` is the SHA-256 of that day's evidence text, and the Drive receipt holds the same bytes, so a reader
  still checks factor row to evidence through the receipt (a test).
- **Fail-closed, no fallback** (owner, 23 Oct: "we are going to have Google Drive for now ... let's not worry about
  that"): when Drive cannot give the table (settings missing, a copy unverified, a network error), C2 and C4 raise their
  existing "no margin row" refusals, so there is no trade. There is one test per reader and no other outage handling.
  Book 1's desk is frozen from Mon 26 Oct (owner, 23 Oct), so the live cost is small.
- `nse-margins.yml` commits `receipts/data/margins/` and the manifests instead of `margins.csv`. `stress-factor.yml`
  commits the evidence receipts and keeps committing `stress_factor.csv` and the file lists. The one-off
  `margins move` command moves the file and the evidence CSVs, with the same read-back and catch-up as step 1b.

**Gap list (step 2):**

| Requirement | Where |
|---|---|
| Only fetched or derived data moves; decision records, manifests and write-ups stay (orchestrator's split) | split above |
| Every reader and writer of the moved files switched (owner's list) | readers and writers above; tests that read the real file get fixtures or the port |
| Factor row to evidence still checked by SHA-256 | design; a test |
| C2 and C4 read one configured source | `risk.margins.table`; settings tests |
| Fail closed, no fallback, one test per reader (owner, 23 Oct) | design |
| Upload, rebuild byte for byte, writer to Drive only, readers through the cache, removal after one scheduled run | as steps 1 and 1b |
| Merge window outside 14:00-16:15, the Groww probe (10:15-10:45 and 14:00-16:20 on 27 Oct) and the nse-margins slots (03:30, 05:00, 06:30, 07:45, 08:30 IST, plus GitHub's lateness); never Sunday 10:00-13:00 (stress-factor.yml) | header: Tue 27 Oct, 11:00-13:30 IST |
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

**Step 1b, global cues (code, for the A17 owner, the FL1 builder and Judge F):**
- Built as in step 1b's text above. Files:
  - `fno/global_cues/{drive_wiring (new), wiring, check_files, cli}.py`
  - `fno/storage/{receipted_rows, moving, report_files, row_log}.py`
  - FL1's `fno/forecast_lab/page/facts.py` and `page_wiring.py`
  - `.github/workflows/{global-cues, data-checks}.yml`
  - `research/data/global-cues/README.md`
  - tests: `tests/o9b/test_global_cues_drive.py` (new), `tests/o9b/{test_moving, test_receipted_rows}.py`, the
    `tests/global_cues` files that call `CueChecks`, `tests/forecast_lab/test_page_facts.py` and
    `tests/test_capture_schedules.py`
- `CueChecks` now writes its two public reports and `us_trading_dates` through the `Report` port. `DriveSnapshots` is
  a `Report` too. The wiring writes them as `ReceiptedSnapshots`; tests write them with `csv_reports`.
- **Two design changes found while building, both in step 1's shared classes:**
  1. **A move catches up.** `global-cues.yml` on main keeps appending to the repository files until the merge, so the
     merge-day re-run would have refused ("Drive already holds other bytes"). `move_into` now asks the series:
     - a table whose Drive copy is a whole-line start of the file gets the later rows as one new part, under the
       header;
     - a report gets a new snapshot;
     - anything else is still refused, and the bytes must read back equal.
  2. **Parts must sort in order.** Part names are a run id (time to the second plus a random suffix). Two runs in the
     same second could therefore read back out of order. My own test caught this as an unequal read-back. A new part
     that would not sort after every receipted part of its series is now refused (`PartOutOfOrder`); nothing is
     written.
- FL1, agreed with its builder (22 Oct):
  - `RepositoryFacts(root, flows, cue_rows)` keeps its contract: brent and USD/INR are `{value_date: value}` up to
    the report's day.
  - The new `CueRows` (`page/facts.py`, wired by `page_wiring.cue_rows()`) reads each table once per process. A table
    Drive cannot give (settings missing, a copy unverified, sign-in refused: all `RuntimeError`) gives no rows. It is
    named, never skipped silently (the FL1 builder's request, 22 Oct): `FactsSource.problems()` names it, and
    `PageBuilder._cues` adds one failed "Reasons' facts" view per problem. That view lands in the page's system
    line, and `maker.py` alerts it once with the report. The text gives the error type only, because a message can
    hold paths. The VIX and flows reasons stay. Three mutations on these lines were caught.
  - No `live_only` filter was added.
- The real move (22 Oct, from this session) read back equal for all six files:

  | File | Bytes | SHA-256 starts |
  |---|---|---|
  | us10y | 618,938 | 0053dbe0 |
  | brent | 631,009 | ce69a512 |
  | usdinr_rbi | 493,096 | 83508820 |
  | us_trading_dates | 76,002 | 1969b82e |
  | gaps | 90,770 | c5a89239 |
  | overlap | 10 | 62132041 |

  `revisions.csv` does not exist yet, so it was not moved.
- Evidence on the moved data:
  - From a cold cache: "6 downloaded and verified", and 7 `data` tests passed.
  - Each table rebuilt through the real wiring equals its repository file byte for byte.
  - `global-cues verify --cue us10y --cue brent --cue usdinr_rbi` on the moved tables printed "every cue row equals
    the archived copy it names" (exit 0).
  - Criterion 3 for FL1: the facts' brent and USD/INR series, old path against new, over the 30 sessions from
    8 Sep to 22 Oct 2026 showed 0 differences.
  - The weather reads the same `rows()` and needed the Drive settings already (`build_reader(include_private=True)`).
- **A17 owner's review (22 Oct): OK, no blocker.** 2,323 tests passed on their checkout, all 5 points met, and the
  reader grep found GR1's `inputs.py` too (it reads through `build_tables`, so it follows the move). Merge-day item 1
  (the race) is accepted, above. Item 2 is accepted: the README says the repository copies stop updating at the
  merge. Their note is accepted as a later step, for VIX as well. Every run's fresh runner downloads every part once,
  about 1,000 small files per run after a year, so the step is an `actions/cache` of `work/drive-cache` keyed on the
  receipts. This step does not build it.
- **Mutations: 9 of 9 caught.** Three survived at first and their tests were added:
  - the revisions log left out of the move;
  - the overlap check not written;
  - the order check's `>=` weakened to `>`. The second series of one run reusing a held part name is now refused
    by name, not by Drive's write-once conflict.
- Changed behaviour, stated plainly: `global-cues check` (and `verify`) now need the Drive settings, because every
  table is in Drive. No schedule calls `check`.
- Not yet:
  - the A17 owner's and FL1's reviews of this diff, then Judge F;
  - the merge from Mon 26 Oct, outside 14:00-16:15 IST, and only while global-cues.yml has no queued or running
    run. GitHub starts its crons late: the morning ones land around 05:30-06:40 IST, and the 14:11 one lands 17:50-21:00
    or later (A17 owner's measurement). `global-cues move` runs just before the merge, and **once more right after it,
    before the next scheduled run**. Otherwise a run that lands between the last catch-up and the merge adds rows to
    the repository files only, and the next run on Drive would re-add them with a later `first_seen_at` (the A17
    owner's merge-day item 1, accepted: I traced it in `CueTable.merge`). Each move says "already in Drive, equal" or
    "caught up and read back equal";
  - the first scheduled run on the new path;
  - the removal commit.

**Judge 478 (FAIL, round 1 of 2), both accepted:**
- SF1 accepted. I checked it: `requests.ConnectionError` and `HTTPError` are `OSError` subclasses
  (`issubclass(..., OSError)` is True). `CueRows` caught only `RuntimeError`, so a Drive network failure would have
  escaped through the unguarded `facts.facts(day)` and lost the edition. `CueRows` now catches
  `(RuntimeError, OSError)`, naming the class only. The test is parametrized over `RuntimeError`,
  `requests.ConnectionError` and `requests.HTTPError`. Each gives one failed "Reasons' facts" view, the line in the
  system line, one alert, and the other facts kept. A mutation back to `RuntimeError` alone fails 2 of the 3 cases.
- Minor accepted: the umbrella's "one way, not two" line (section 2) now says step 1b moves only the public cues,
  and that the two ways stand side by side until **step 1c**. Step 1c, the private cues onto the receipt-backed
  classes with the A17 owner, is a named row in section 3's table and is cited in step 1b's files paragraph.
- **Judge 478 addendum 1: round 2 PASS at a2f96e5f.** It may merge from Mon 26 Oct, outside 14:00-16:15 IST, with no
  global-cues run queued or running and `global-cues move` run just before and just after the merge.
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

**Step 2, G4 margins (code, for the A14/C2/C4 owner and Judge F):**
- Built as in step 2's text above.
- **New port:** `fno/storage/table_source.py` (`TableSource`, with `FileTable` and `ReceiptedTable`; any read failure
  is `TableUnavailable`, naming the error type only). `data_wiring.build_data_table(folder)` builds the Drive table on
  first read, so missing settings refuse the read, never the wiring.
- **Readers:**
  - C2's `MarginTable` and C4's `MarginFile` take a `TableSource`, keep their column checks, and turn
    `TableUnavailable` into `RiskInputError` and `MarginProblem` (no trade).
  - `config.yaml` `risk.margins.table: margins/margins` replaces `file`, read by both settings (`RiskSettings.margins_table`,
    `MarginSettings.table`).
  - `build_risk_manager(..., tables=)` defaults to Drive. Tests pass `tests/margin_tables.local_tables(path)`.
  - C4's `build_validity_checker` reads the same name.
- **Writers:**
  - A14's `MarginLog(table, log)` reads through the port and appends through `RowLog`. The wiring gives both the
    same `ReceiptedRowLog("margins/margins")`.
  - A14c's evidence CSV goes through `build_evidence_saver` to `ReceiptedSnapshots("margins/stress-evidence/<day>")`
    before its factor row. The same bytes again write nothing. The file list and the `.md` stay in the repository.
  - `nse-margins.yml` and `stress-factor.yml` commit the receipts; `data-checks.yml` adds `data/margins`.
- **One behaviour change, stated plainly:** A14's log used to add a missing final newline to a hand-edited file
  before appending. The `RowLog` port refuses that by name instead, and nothing is written (`MarginLogConflict`).
  Drive parts cannot have that state.
- **The real move (23 Oct, this session) read back equal:**

  | File | Bytes | SHA-256 starts |
  |---|---|---|
  | `margins.csv` | 15,502 | f78e872c |
  | `stress_evidence_2026-10-16.csv` | 3,277 | 54d0ab13 |
  | `stress_evidence_2026-10-18.csv` | 94 | 3ea716e8 |

- **Evidence:**
  - Cold cache: "3 downloaded and verified", and 2 data tests (`tests/nse_margins/test_committed_margins.py`)
    passed.
  - The rebuilt table equals the file byte for byte.
  - Criterion 3: C2's margin parts for every structure and width on 16 and 23 Oct, file against Drive, gave 30
    compared and 0 different. C4's rows are equal.
  - Both factor rows with evidence (16 and 18 Oct) match their receipts' SHA-256
    (`tests/nse_margins/test_committed_evidence.py`; the owner's link check).
- **Tests:**
  - `tests/o9b/test_margins_drive.py` (4): the move and the reads through the real wiring; C2, C4 and the log
    refusing by name on a Drive network error; an empty Drive table counted as missing; the evidence saved once with
    the factor row's SHA-256.
  - 15 existing test files moved to the ports. Their fixtures stay test fixtures. `tests/e2e_acceptance` reads a
    frozen `fixtures/margins_to_2026-10-16.csv` (45 rows) through the patched `build_data_table`, the same precedent as
    `tests/risk/fixtures/margins_2026-10-14.csv`.
- **The A14/C2/C4 owner's review of 66a9b97d (23 Oct): two blocking points, both accepted after reproducing them.**
  1. **The merge-day re-run of `margins move` would have refused.** The catch-up is step 1b's change (on
     `story/o9b-cues`, not yet on main), so this branch now carries step 1b's exact `moving.py` and
     `receipted_rows.py`, with their tests. They are identical changes, so Monday's merge of step 1b meets no
     conflict here. A new test: the file grows by one row and is caught up (C2 then reads the new row), and a table
     that is not a start of Drive's is refused, with nothing written.
  2. **No final-newline guard on the Drive side.** A first part without its last new line would have joined the
     next part's first row to its last row silently. `ReceiptedRowLog` now refuses such a part by name
     (`TableFileBroken`) when writing it, and `rebuilt()` refuses one put there by hand when reading. New tests cover
     the move of such a file (refused, nothing written) and a hand-put part (refused at read). One step 1b test
     changed to match: a mid-line Drive copy is now refused at read, by name, not as "other bytes".
  - **The old mend on hand-edited files:** the owner's answer is to keep the refusal ("a margin row is evidence").
  - **Docstrings:** the four that still said "margins file" are fixed (`validity.py`, `validity_limits.py`,
    `validity_margin.py`, `job.py`).
  - **The owner's minor, for the record:** if nse-margins' push fails after its Drive part is written, the part has
    no committed receipt, so the next run does not see those rows and writes them again as a new part. That is safe:
    the receipts are the index, so no key is duplicated. Meanwhile C2 reads the older row, and the age rule fails
    closed.
- **The owner's re-check of 9f22ba3c: no objection to Judge F** (their repros: the grown file caught up, the
  file without its last new line refused; 1,088 passed). Their three notes:
  1. **Accepted and built:** an evidence CSV differing from Drive's copy would have been caught up as a newer
     snapshot. `move_into(..., exact=True)` now refuses it, and `margins move` uses that for the evidence, since its
     factor row names the SHA-256. Tests: the evidence refused with nothing written, and an exact move never catching
     up a report. A real re-run says "already in Drive, equal" for all three files.
  2. **Correct:** `receipted_rows.py` and `moving.py` differ from `story/o9b-cues` by this step's guards. Monday's
     merge of step 1b meets separate hunks here, which I check when the second branch lands.
  3. **Noted:** `write_bytes` lists the series' receipts on every write (the part-order check), which is cheap at
     these sizes.
- Gates at 9f22ba3c: full suite 14,583 passed and 16 xfailed, clean.
- **Judge 534: PASS at 162df9c8.** It may merge Tue 27 Oct 11:00-13:30 IST, after step 1b and a merge of main, with
  `margins move` before and after, on the orchestrator's go. The judge's 4 plants were caught. The judge's note for
  the owner: from the merge, a Drive outage or an expired sign-in refuses every trade that needs a margin (the owner's
  no-fallback choice). After the merge, the claims will cite the first nse-margins and stress-factor runs and the
  first desk day's margin reads.
- **Not yet:** Judge F, the merge on Tue 27 Oct 11:00-13:30 IST with `margins move` re-run before
  and after, the first scheduled runs, and the removal commit.
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

**DRY1's findings on step 1b (orchestrator, 24 Oct; `docs/dryruns/DRY1_2026-10-23.md` rows g1 and g7):**
- **g1, conflicts with main:** main is merged into `story/o9b-cues`, keeping both sides. Judge 536's empty-series
  guard in `receipted_rows.py` merged in by itself, beside step 1b's catch-up and part-order code. The tests of both
  stay: tests/o9b, o9_store, global_cues and forecast_lab gave 409 passed on the merged tree.
- **g7 (P-g2), Drive lags main and nothing alerts:** confirmed. Main's job kept appending to the repository CSVs
  after the 22 Oct move, so the lab read 21 Oct's USD/INR.
  - **The root fix stays the merge step:** `global-cues move` runs just before the merge and just after it (above).
  - **New check so a lag cannot stay silent:** `test_no_drive_table_lags_its_repository_copy_while_the_copy_exists`
    (a `data` test, run daily by data-checks, which alerts on failure). While a moved file is still in the
    repository, it must be a whole-line start of its Drive table.
  - **Proof:** the test failed on 24 Oct (Drive behind). `global-cues move` then caught up us10y, usdinr_rbi and
    us_trading_dates, each read back equal. The test then passed (8 data tests). The new receipts are on this branch.
- **Who merges:** the orchestrator, not me (24 Oct). The steps above stand for whoever merges: no global-cues run
  queued or running, `global-cues move` just before and just after, then the full gates.

**DRY1's finding g2 on step 2 (orchestrator, 24 Oct): rebuilt on the merged step 1b.**
- `story/o9b-margins` now has `story/o9b-cues` merged in (61a0eee5: step 1b with main and judge 536's guard), in place
  of its own copy of step 1b's files. The conflicts and how each was resolved:
  - `moving.py`: this step's `exact` line kept.
  - `receipted_rows.py`: this step's newline-guard constant kept.
  - `data-checks.yml`: `MOVED: data/vix data/global-cues data/margins`.
  - `tests/o9b/test_moving.py`: this step's stricter mid-line test kept, replacing step 1b's "other bytes" version.
  - `tests/o9b/test_receipted_rows.py`: both sides' tests kept.
  - The story and the register: both sides kept, and the sections reordered (1b before 2).
- **`fno/storage/receipted_rows.py` against main** (`git diff origin/main -- fno/storage/receipted_rows.py`): only
  additions, and judge 536's two-line empty-series guard in `files()` is untouched. The only removed line is the
  `RowLog` import, extended with `TableFileBroken`. The additions:
  - step 1b's: `OUT_OF_ORDER` and `PartOutOfOrder`, the part-order check in `write_bytes`, and `catch_up` on both
    series;
  - this step's: `NO_LAST_NEWLINE`, `ReceiptedRowLog.write_bytes` refusing a part without its last new line, and
    `rebuilt()` refusing one at read.
- Affected areas on the rebuilt tree: tests/o9b, o9_store, global_cues, nse_margins, risk and checks gave 1,226
  passed. This goes back to Judge F as a delta.
