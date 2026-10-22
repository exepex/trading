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

Each step's text names its files, writers, readers, the reader owners agreed (most have no live owner; the
orchestrator agrees on their behalf), its tests and its removal list.

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

## Open questions

None for the owner: the 22 Oct decisions above settle scope and history.
