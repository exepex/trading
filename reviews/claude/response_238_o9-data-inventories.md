# Response 238: O9 data inventories of both repositories (read-only, 16 Oct 2026)

Evidence for docs/stories/O9-data-to-drive.md. Two read-only inventories made by research agents of the owner's session 01WHmxEY7WLVTSbNi1Z2adZw; nothing was edited. Every row cites file:line at the commit named in each part. "Unsure" marks what was not traced end to end.

## Part A: exepex/trading

# exepex/trading: data writers, readers and Drive layer (read at origin/main e7649679, 16 Oct 2026)

I changed nothing in the repository. Every row below cites file:line. "Drive?" means the same run also writes the bytes, or their raw source, to Drive. "Unsure" marks things I did not trace end to end.

## 1. Writers: code that writes data files inside the repository

### 1a. Committers (code that runs `git add/commit/push`)

| Committer | Evidence | Commits what | Used by |
|---|---|---|---|
| `GitManifestRecorder` (add, commit, pull `--no-rebase`, push to main, 3 tries) | fno/storage/manifest_commit.py:37-86 | the folder it is given, default `research/data/manifests/` | fno/storage/wiring.py:169-171; librarian_cli.py:59,67,75,90; revisions_cli.py:57,70; participant_oi_cli.py:89,105; filings/runs_cli.py:44,89,161; market_read_models/cli.py:104,120,179,187; `research/data/publications/` via market_read_models/wiring.py:136 |
| `OwnedPathsCommitter` | fno/storage/owned_paths_commit.py:13-29 | `research/data/intraday/{slots/,rv/,heartbeat.json}` | fno/intraday/wiring.py:55,111; intraday/sync.py:48 |
| `Git` / `GitCommitter` (raw-quote guard) | fno/desk/git_sync.py:33-70,102-135 | the paths passed in (journal files) | desk/daily_wiring.py:48-49; books/book1_wiring.py:48-49; desk/drive_sync.py:30; desk/daily_run.py:133; desk/execution_capture.py:49,58; desk/book_versions.py:51; books/book1.py:140 |
| `GitMainTransport` | fno/ai/transport.py:30-51 | one AI-book submission file under `research/forecasts/ai_v1/` | `python -m fno.ai seal/reveal` (routine, fno/ai/__main__.py:25-27) |
| `PublishedHeartbeat` (git calls) | fno/intraday/heartbeat.py:44-57; intraday/wiring.py:84 | reads the published heartbeat. **Unsure** whether it also commits | intraday |

### 1b. Writers by data area

| Repository path written | Writer (file:line) | Trigger | Committed by | Drive? (store) |
|---|---|---|---|---|
| `research/data/manifests/<dataset>.csv` (SHA-256 per raw file) | manifest_folder.py:69 (`FingerprintingStore`, :95) | data-librarian, data-snapshot, market archive/daily, pipeline jobs | GitManifestRecorder | yes: the raw file goes to `raw/` through `build_owner_drive_store` (storage/wiring.py:116-123). The manifest is the receipt |
| `research/data/manifests/revisions/<dataset>.csv` | storage/revisions.py:85 | data-revisions sweep, participant-oi sweep | GitManifestRecorder | yes: `revisions/` (wiring.py:138-144) |
| `research/data/manifests/filings/*.csv`, `gaps.csv` | filings/manifest.py:72; filings/gaps.py:40 | `fno filings archive/day-lists` | GitManifestRecorder (runs_cli.py:89) | yes: `raw/` plus `index/` progress (filings/wiring.py:41,122-125) |
| `research/data/manifests/global-cues/<cue>.csv` plus `attempts/` | global_cues/snapshot_log.py:40; attempt_log.py:35 | `fno global-cues ...` (manual or routine: no workflow) | by hand ("Claude" commits) | yes: `raw/` (global_cues/wiring.py:131) |
| `research/data/manifests/groww-candles/` | intraday/candle_archive.py:95 | `fno intraday backfill` (A16b), FT1 study | by hand | yes: `raw/groww/indices/...` (backfill_wiring.py:77-84) |
| `research/data/nifty-panel/{options,futures}_<yr>.csv.gz`, `manifest.json` | research_data/panel_append.py:124-126; panel_store.py:88,145 | `fno pipeline panel-days` (panel-days.yml:71); `fno nifty-panel` | workflow `git add $PANEL` | inputs only (reads `raw/`, pipeline/panel_wiring.py:51); the derived panel is repository only |
| `research/data/nifty-panel/warmup_closes.csv` (append) | research_data/warmup_closes.py:96; IndexCloseAppender pipeline/wiring.py:89 | `fno pipeline index-closes` (index-closes.yml:72) | workflow `git add $CLOSES` | inputs only (`raw/`, pipeline/wiring.py:88) |
| `research/data/margins/margins.csv` | nse_margins/margin_log.py:65; wiring.py:45 (path from config.yaml:118) | `fno margins nse-span` (nse-margins.yml:79) | workflow | SPAN file in `raw/` (nse_margins/wiring.py:55-58) |
| `research/data/participant_oi/{release_checks,release_check_starts,release_rereads,last_modified_sweeps}.csv`, `actions/` | research_data/release_times.py:78; reread_log.py:27; write_sweep.py:71; composition.py:168-200 | participant-oi watch/check-once/sweep (3 workflows) | workflows | no (timing evidence only) |
| `research/data/quotes/**/{.meta.json,.canonical}` (plus NSE chain CSVs) | `LocalFolderStore.put` raw_store.py:82-91 via DriveOnlyQuoteStore drive_only_store.py:46-47 | `fno quotes record` (3 pm routine); `--source nse` (quote-recorder-nse.yml:54) | routine step 3 (CLAUDE.md "3 pm quote recorder"); workflow `git add $SNAPSHOTS` | Groww CSVs go to `raw/` only (quote_wiring.py:17-26). The NSE chain stays in the repository (storage/README "Groww's 3 pm quote files") |
| `research/data/intraday/slots/...csv`, `rv/<yr>/...csv`, `heartbeat.json` | intraday/row_files.py:26; heartbeat.py:38 | `fno intraday run` (A16 routine) | OwnedPathsCommitter | raw JSON snapshots go to `raw/` (intraday/wiring.py:90-93) |
| `research/data/intraday/rv-candle/`, deferrals | row_files.py:26 (CandleRvTable); deferral_log.py:32 | `fno intraday backfill` | by hand | candles in `raw/` |
| `research/data/global-cues/<cue>.csv`, `revisions.csv`, `checks/` | global_cues/row_log.py:67 (CsvRowLog, wiring.py:107-109); check_files.py:77 | `fno global-cues` | by hand | private cues already use Drive `derived/global-cues/` (DrivePartsRowLog, wiring.py:102,123) |
| `research/data/vix/india_vix_daily.csv`, `checks/` | vix_history/table.py:84; check_files.py:70 | `fno vix-history` | by hand (cli.py:8,36 is a reminder only) | month JSON files in `raw/` (vix_history/wiring.py:85) |
| `research/data/publications/publication-inputs.csv` | market_read_models/publication_inputs.py:65 | `fno market publish` (market-publish.yml:78) | GitManifestRecorder (wiring.py:136) | the read models go to Postgres; `--local` writes local_publisher.py:64,73 and run_status.py:106 (local only) |
| `research/forecasts/live_v2/<yr>/<d>_pack.json`, `_forecasts.csv` | forecast/capture.py:130-140 | `fno forecast capture` (forecast-capture.yml:99) | workflow (:103,:126) | run summary to `pipeline/` (baseline_wiring.py:53-57) |
| `research/forecasts/ai_v1/**` (submissions, records, fire logs, audits, draws) | ai/transport.py:42; record_writer.py:38; fire.py:50; transcript_audit.py:65; audit_plan.py:80 | AI routines (seal/reveal); `fno ai fire/collect/audits-due` | GitMainTransport plus forecast-capture.yml:126 | no |
| `research/forecasts/scores/<d>.json` | forecast_scoring/cli.py:57-59 | `fno forecast-scores run` (forecast-scores.yml:49) | workflow :52 | receipts read from `pipeline/` (wiring.py:58-61) |
| `research/forecasts/v4_scores/<d>.{md,json}`, `look_*.json` | forecast_scoring/v4/cli.py:53-55; v4/records.py:74 | `fno forecast-v4-scores report/look` (postmortem-weekly.yml:60) | workflow :62 | no |
| `research/forecasts/v4/<forecaster>/...` | forecast_v4_rules/records.py:93 | `fno forecast-v4 capture/backfill` (no workflow found) | by hand | no |
| `research/forecasts/v4/weather/...` | weather/records.py:40 | `fno weather capture/backfill` | by hand | private copy in `derived/weather/` (weather/wiring.py:102-103; capture.py:22) |
| `research/forecasts/backfill/backfill_v1.csv.gz` | forecast/cli.py:76 | `fno forecast backfill` | by hand | no |
| `research/forecasts/golden_iv30_rv20.csv`; `v2/golden/**` | tools/forecast_golden.py:25; tools/forecast_live_golden.py:87,108 (`--write`) | tools | by hand | no |
| `research/forecasts/v4_*.json/.md` | tools/v4_brier_bands.py:166-174; v4_brier_regimes.py:184; v4_vix_null.py:185; v4_futility_study.py:160; v4_claim_thresholds.py:117; v4_regime_stress.py:287; v4_size_study.py:196; v4_null_calibration.py:102; v4_crash_cut.py:130; v4_moved_after_cutoff.py:69 | tools | by hand | no |
| `research/postmortems/<yr>/<sat>.{json,md}`, `_fired.json`, publish record | learning/report.py:76,86 | `fno postmortem weekly/fire/publish` (postmortem-weekly.yml:61-79) | workflow | no |
| `research/postmortems/..._prose.md`, `_objections.md`; `accounting/ai_usage.csv` | routine writes the prose files; budget/usage_ledger.py:103 | LR1 routine (LR1-owner-checklist.md:40-48) | routine step 6 | no |
| `research/ops/health_runs.csv` | health/run_record.py:36; constants.py:345 | `fno health check` (health-check.yml:44) | workflow :49 | no (the folder does not exist on main yet) |
| `research/cards/deliveries/<yr>/<d>-a<n>.json` | cards/deliveries.py:49-56 | `fno card daily` | **unsure** (T1 test post, "Claude" commit) | card text already Drive-only in `cards/` (cards/wiring.py:82-85) |
| `accounting/ai_session_roster.csv`, `accounting/budget/<m>_signal.json` | budget/session_roster.py:86; signal.py:63 | `fno budget record-roster/...` | by hand or routine | no |
| `journal/runs/<d>.json`, `journal/packs/<d>/common.json(.sha256)`, `journal/<book>/daily_totals.csv`, `journal/execution/<d>/`, `journal/<book>/decisions/...`, `validity_failures.csv`, `journal/versions.csv` | desk/run_log.py:54; pack_store.py:44; books/daily_totals.py:37; desk/execution_capture.py:57; playbook/decision_store.py:83-85; books/book1.py:148; books/version_registry.py:108 | E3 daily run / Book 1 (`fno ... book1/run`, `fno versions register`) | GitCommitter | accounts and private packs are already Drive `paper/` (DriveIndexStore, desk/wiring.py:68-79; .gitignore). Only daily_totals and versions are on main today |
| `research/<study>/results*.json`, `research/ledger.csv`, `research/evaluation/FREEZE_v*.md` | research_engine/results_file.py:81-82; research_cli.py:46,67; ledger.py:107,142; evaluation/freeze.py:160,193 | `fno research run`, `fno evaluation freeze` | by hand | no |
| Study scripts under `research/` (desk-meeting-1, backtest, weekly-weather, fill-timing, r2, capacity-screen, breadth, nifty-panel, legacy-format) | e.g. research/2026-10-12-backtest/replay.py:255-259; 2026-10-16-fill-timing/study.py:38,75; ft1study/archive.py:73,87; capacity-screen/screen.py:150; breadth/studies/brstudy/runner.py:29 | manual | by hand | FT1 and R2 put raw files in Drive (fill-timing FREEZE.md:23; r2 FREEZE.md:65-67) |
| Gitignored, never committed: `research/scoreboards/{A,B}/`, `journal/*/account/`, `.ai_book/`, pending markers | scoreboard/matched_board.py:180; whole_system.py:78; books/files.py:38,45; desk/pending_commit.py:68 | n/a | not committed (.gitignore) | B and accounts in Drive `paper/` |
| `tools/nse_raw_download/manifest*.csv` | tools/nse_raw_download/nse_raw_download.py:82,168,214 | the owner's laptop tool | by hand | the code no longer reads them (storage/README "Manifests") |

Not data writers: `playbook/registry.csv` and `*.yaml` status (playbook/registry.py:116; lifecycle.py:42) are configuration. `research/data/calendar/*.csv`, `events/events.csv`, `margins/stress_factor.csv` and `followed-companies/` have no code writer I could find. They are hand-curated, so the owner must decide whether they count as config or data.

## 2. Schedulers

### 2a. Workflows that commit (`contents: write`)

| Workflow | Command(s) | Paths it git-adds |
|---|---|---|
| filings-archive.yml (every 6 h) | `fno filings probe/archive/day-lists` :48-62 | none in YAML; code commits `research/data/manifests/` (:23) |
| flows-download.yml (21:10 IST) | `fno data-snapshot fii-dii-cash-by-session`, `fpi-daily-by-session` :45-46 | code: manifests (:14) |
| forecast-capture.yml | `forecast capture` :99; `ai fire/collect/audits-due` :107-122; `tools/forecast_live_golden.py` :85 | `research/forecasts/live_v2/*/*_pack.json` :103; then all of `research/forecasts` :126 |
| forecast-scores.yml | `fno forecast-scores run` :49 | `research/forecasts/scores` :52 |
| health-check.yml | `fno health check` :44 | `research/ops/health_runs.csv` :49 |
| index-closes.yml | `data-librarian index-close` :61; `data-revisions sweep` :67; `pipeline index-closes` :72 | `research/data/nifty-panel/warmup_closes.csv` :38,75 (manifests through code) |
| market-publish.yml | `market archive` :65; `db-check` :71; `publish` :78 | code: manifests, revisions, `publications/` (:28) |
| nse-margins.yml | `data-librarian span-bod` :69; `data-revisions sweep` :75; `margins nse-span` :79 | `research/data/manifests`, `research/data/margins/margins.csv` :47-48,82 |
| panel-days.yml | `data-librarian fo-bhavcopy` :60; `data-revisions sweep` :66; `pipeline panel-days` :71 | manifests, `research/data/nifty-panel` :39-40,74-75 |
| participant-oi-release.yml | `participant-oi watch --evidence-folder` :56; `data-librarian participant-oi` :68; `pipeline fire` :76 | `research/data/participant_oi/actions` :35,59 |
| participant-oi-sweep.yml (monthly) | `participant-oi sweep` :53; `pipeline fire` :63 | `.../participant_oi/actions` :56 (revision rows through code) |
| participant-oi-watch.yml | `participant-oi check-once` :51 | `release_checks.csv`, `release_check_starts.csv`, `release_rereads.csv` :30-32,55 |
| postmortem-weekly.yml (Sat) | `forecast-v4-scores report` :60; `postmortem weekly/fire/publish` :61-76 | `research/forecasts/v4_scores`, `research/postmortems` :62,69,77 |
| quote-recorder-nse.yml | `quotes record --source nse` :54 | `research/data/quotes/nse` :31,57 |

Every committing workflow runs `git pull --no-rebase && git push origin HEAD:main`. `checks.yml` does not commit.

### 2b. Routine prompts (they live outside the repository; these are the repository's copies)

| Routine | Data it commits | Source |
|---|---|---|
| 3 pm quote recorder (14:33 IST) | `research/data/quotes/` | CLAUDE.md, "3 pm quote recorder" step 3 |
| A16 15-minute recorder | `research/data/intraday/{slots,rv,heartbeat.json}` (code, plus a manual fallback) | docs/stories/A16-owner-checklist.md:46-58 |
| Book 2 / Book 3 AI routines (fired) | `research/forecasts/ai_v1/` via `fno.ai seal/reveal` | F1-G5-owner-checklist.md:32-46 |
| LR1 weekly post-mortem writer | `research/postmortems/<yr>/<w>_{prose,objections}.md`, `accounting/ai_usage.csv` | LR1-owner-checklist.md:40-48 |
| O6 dry-run routine | "Commit nothing" | O6-owner-checklist.md:37 |
| Every session | `conversations/<date>.md` (docs, not data) | CLAUDE.md "Keep a conversation log" |

Several "Claude" commits of data had no scheduler: v4 forecasts and weather back-fill, global cues, VIX, candle back-fill, card deliveries (`git log -1` per path). These are ad-hoc session runs and need a rule too.

## 3. Readers of repository data

### 3a. Frozen-protocol and git-history checks (they verify bytes at a commit)

| Check | What it verifies | Evidence |
|---|---|---|
| Forecast v1 freeze | `research/forecasts/golden_iv30_rv20.csv` is a checked file. `nse_sessions.csv` and `nifty-panel/manifest.json` are recorded but not checked | research/forecasts/FREEZE.md:23-24,48-49; checker fno/forecast/freeze.py:43-60 (`changed_files` hashes the working-tree file) |
| Forecast v2 freeze | checked files include `research/forecasts/v2/golden/case_{a,b}/**`, which holds a Groww quote CSV in the repository. `warmup_closes.csv`, the panel manifest and the calendar are "recorded, not checked" (3-column rows that HASH_ROW freeze.py:18 skips) | FREEZE_v2.md:55-64,81-83; freeze_v2.py:27-44 |
| Forecast v3 sections | `nifty-panel/manifest.json` recorded | FREEZE_v3.md:35; freeze_sections.py:41-58 |
| Experiment 1 | `warmup_closes.csv` (hash 9ecff05…, not today's file), panel manifest, events, calendar, exceptions, at RUN_COMMIT via `git show` | research/2026-10-12-experiment-1/FREEZE.md:33-37; tests/research/test_experiment_1_frozen.py:19-27 |
| Fill-timing, R2, weekly-weather freezes | code files only; data named by Drive path plus SHA-256 (`probe.csv` named) | 2026-10-16-fill-timing/FREEZE.md:4,10,23; r2 FREEZE.md:65-67; weekly-weather FREEZE.md:9-11 |
| Freeze tests on the real tree | | tests/forecast/test_freeze.py:87-89; test_freeze_v2.py:60-72; test_freeze_sections.py:76-83 |
| Scoring requires the v1 freeze before the **commit of the back-fill data file** | `git log -1 -- backfill_v1.csv.gz` | forecast_scoring/wiring.py:64-67,82-85 |
| Replay of live days exports `research/data/{nifty-panel,quotes,calendar}` at the pack's commit | `git archive`, `git log --diff-filter=A` | forecast_scoring/replay.py:27,63-75; tests/forecast_scoring/test_live_replay.py:95-99 |

### 3b. Ordinary readers in fno/ and tools/

| Data | Readers |
|---|---|
| `nifty-panel/*.gz`, `manifest.json` | forecast/wiring.py:8; baseline_wiring.py:20; forecast_v4_rules/wiring.py:16; forecast_scoring/wiring.py:34; desk/pack_wiring.py:27; panel_append (reads to append); research_data/panel_reader.py:132; health/expectations.py:35 |
| `warmup_closes.csv` | baseline_wiring.py:61; forecast_v4_rules/wiring.py:21; forecast_scoring/v4/wiring.py:24; ai/paths.py:12 (ai/export.py:17); vix_history/wiring.py:29; learning/wiring.py:21; market_read_models/wiring.py:17; health/expectations.py:34; **tools** v4_brier_regimes.py:48, v4_vix_null.py:45, v4_futility_study.py:46, v4_regime_stress.py:46, v4_size_study.py:47,66 |
| calendar `nse_sessions.csv` | storage/wiring.py:64-65,341-343 (everything); cards/session.py:16; quotes/cli.py:50; intraday/cli.py:100 |
| `events.csv` | storage/wiring.py:308; weather/wiring.py:26; desk/pack_wiring.py:27 |
| manifests | manifest_folder.py (coverage, FingerprintingStore refusals); vix_history/wiring.py:63-80; filings/wiring.py:109; health/expectations.py:33,36; tools/v4_moved_after_cutoff.py:28 |
| intraday rv/slots | forecast_scoring/v4/wiring.py:25,45,58; forecast_v4_rules/wiring.py:37; learning/wiring.py:57; health/desk_checks.py:52; health/expectations.py:37 |
| quotes sidecars and canonical | forecast capture (snapshot-ready); learning/wiring.py:38,56; health/quote_checks.py:14; scorecard/wiring.py:16; desk/daily_wiring.py:30 |
| margins, stress factor | risk via config.yaml:118,136 |
| participant-OI logs | composition.py:184-191; participant_oi_cli.py:39,53,113 |
| `research/forecasts/**` | cards/forecasts.py:25-26; forecast_scoring (live_v2, backfill); v4 scoring (v4/, FREEZE_v4); learning/wiring.py:53; market_read_models/wiring.py:15,71; health forecast_checks; tools/v4_vix_null.py:151 |
| publications, followed-companies, experiment-1 results | market_read_models/wiring.py:67-71 |
| accounting | budget/wiring.py:29; usage_ledger.py:24; session_roster.py:23 |
| journal | books/versions.py:20; desk readers; playbook evaluation (tests/playbook/test_evaluation_wiring.py:26) |
| `research/ledger.csv` | research_engine/ledger.py:21,50 (git pickaxe) |

Workflow readers: forecast-capture pulls `research/data/quotes/**/*.canonical` as its push trigger (forecast-capture.yml:22-25). index-closes and panel-days read the files they append to.

### 3c. Tests that read real repository data (not tmp_path)

tests/risk/test_settings.py:15,44; tests/risk/test_stress_real.py:16,26; tests/risk/test_stress_factor.py:92,110; tests/risk/test_margin_age.py:14; tests/scoreboard/test_do_nothing.py:42; tests/forecast_v4/test_units_settlement_sessions.py:26,104; tests/forecast_v4/test_{brier_bands:18,42, claim_rule:57-67, confirmatory:71-76, vix_null:21-55, brier_regimes:19-48, futility_rule:62-66, cutoff_move:14, regime:21, protocol_text:13-64}; tests/forecast_scoring_v4/helpers.py:15; tests/weather/test_checklist_v0.py:19-20; tests/forecast_v4_rules/test_v4rules_capture_records.py:23; test_v4rules_series_and_rules.py:25; tests/test_warmup_closes.py:90; tests/forecast/test_live_pack.py:19; tests/packs/builders.py:29; tests/ai/fakes.py:22,37; tests/ai/test_inputs.py:36; tests/forecast_scoring/test_replay_quote_store.py:19,35; test_live_replay.py:95-99; tests/cards/fakes.py:25; tests/global_cues/test_committed.py:32,71-75; tests/global_cues/test_failures.py:172; tests/test_participant_oi_coverage.py:81; tests/research_data/test_events.py:62,78; tests/market_read_models/test_p1_data_catalog.py:63,73,191; tests/budget/test_items_and_cap.py:134; tests/accounting/test_ledgers.py:84-85; tests/books/test_paper_account.py:45; tests/versions/test_version_registry.py:59; tests/research/test_experiment_1_frozen.py:13-27; tests/research_engine/test_cycles_real.py:25; test_four_leg_regression.py:19; tests/research/{r2_synthetic.py:12, conftest.py:6, test_capacity_*}; tests/research_ft1/*:6,26; tests/quotes/test_recorder_calendar.py:137; plus the freeze tests in 3a. tests/conftest.py:16 forbids tests from writing `research/data` and `journal/`.

That comes to about 45 test files, well over the judge's 22. Many read only study results, protocols or calendars. Which of these count as data is the owner's call.

## 4. The Drive layer today

- **Interfaces:** `RawFileStore` (get, put, checksums, folders; raw_store.py:35-53). `LocalFolderStore` puts once and raises `RawFileConflict` on different bytes (:56-91). `AreaStore` adds an area prefix (:94-113). `GoogleDriveStore` reads with the service account (google_drive.py:51). `GoogleDriveUploadStore` writes as the owner (google_drive_upload.py:25), and it also has `replace_contents` (:77-86).
- **Not write-once:** `IndexFileStore`/`DriveIndexStore.replace` overwrites files in place (index_store.py:40-56). It is used for `index/` (filings/wiring.py:41,122-125) and `paper/` (desk/wiring.py:68-79). Both conflict with the new write-once rule.
- **Factories** (storage/wiring.py): `build_raw_stores` :92; `build_owner_drive_store`, which is raw plus FingerprintingStore and writes manifest rows into the repository (:116-123); `build_owner_drive` :126; `build_revision_archive` :138; `build_versioned_reader` (point-in-time `VersionedRawStore`) :154; `build_drive_reader` :294; the librarian :283.
- **Drive layout:** `fno-research/{raw, revisions, pipeline, derived, cards, index, paper}`. Sources: storage/README.md tree; constants.py:219,326-327; filings/wiring.py:41.
  - `derived/` today holds `global-cues/<cue>/{rows,revisions,checks}` (global_cues/wiring.py:41,102,123), `weather/<yr>/<d>.json` (weather/capture.py:22) and `<routine>/<dataset>/<batch>/<version>.json` (pipeline/wiring.py:82).
  - `pipeline/` holds run summaries, which are capture receipts (forecast_scoring/wiring.py:58-61).
- **Read-from-Drive helpers:** `VersionedRawStore`; `DriveOnlyQuoteStore.get` checks Drive bytes against the committed sidecar SHA-256 (drive_only_store.py:49-63); `PrivateFiles` mirrors `paper/` into git-ignored local folders and pulls before it reads (desk/private_files.py:1-4); `RawFileLibrary` is "stores first, then NSE" (wiring.py:174-188).
- **No general on-disk Drive cache exists.** The only caches are in-process (pipeline/panel_wiring.py:30).

## 5. Sizes (`du -sh`)

| Folder | Size | Largest parts |
|---|---|---|
| research/data | 69M | nifty-panel 45M (options gz 3.9-7.6M a year; warmup_closes 300K), manifests 14M (filings 9.4M, groww-candles 1.2M, board-meetings 1.5M), intraday 6.8M (1,697 files), global-cues 1.9M, vix 852K, participant_oi 140K, quotes 68K, events 40K, calendar 40K, margins 24K |
| research/forecasts | 15M | v4 14M, backfill 308K, scores 256K, golden_iv30_rv20.csv 140K, v2 112K, ai_v1 80K |
| research studies | about 8M | capacity-screen 5.5M (5.4M data), fill-timing 592K, r2 484K, backtest 464K, weekly-weather 360K |
| research/postmortems, cards | 28K, 16K | |
| journal / accounting | 32K / 16K | |
| reviews (docs) | 5.9M | no data files |
| contracts / tools/nse_raw_download | 1.3M / 592K | |

## 6. Evidence that relies on git history or GitHub push times

| Mechanism | Evidence |
|---|---|
| AI-book seal: GitHub activity-log push time is the receipt | ai/receipts.py:1-78; ai/submissions.py:40-49; ai/history.py:15; forecast-capture.yml:12-15,68 |
| Health check: data on time, judged by the push receipt of the commit that added the row (git pickaxe) | health/evidence.py:1-3,16-21,56; health/wiring.py:26-31; health-check.yml:43; window.py:3 (the 7-day activity window) |
| Card witness: reads committed records at HEAD; push receipts | cards/committed.py:1-2; cards/witness.py:3; cards/wiring.py:99-100 |
| Desk decisions: "committed before the deadline" | desk/committed_decisions.py:46-57; books/decided_runs.py:61; scoreboard/committed_runs.py:49 |
| Freeze ordering (protocol commit is an ancestor; first commit containing the FREEZE file) | forecast/freeze.py:48-60; freeze_v2.py:33-35; freeze_sections.py:48-50; panel-days gate pipeline/panel_wiring.py:46 |
| Scoring keyed to the back-fill file's last commit | forecast_scoring/wiring.py:64-67,84-85 |
| Replay from the commit that added a pack | forecast_scoring/replay.py:59-75 |
| Ledger trials found by git pickaxe | research_engine/ledger.py:50; playbook EvidenceCommitted playbook/wiring.py:47; playbook/history.py:33 |
| Manifest rows are "evidence only once committed" | storage/README "Manifests"; vix_history/cli.py:8; cli.py:73 |
| Experiment-1 freeze read at RUN_COMMIT | tests/research/test_experiment_1_frozen.py:19-27 |
| A16 run timing reported from heartbeat commits | A16-owner-checklist.md:73-81 |
| tools/v4_moved_after_cutoff uses the last commit of a path | tools/v4_moved_after_cutoff.py:52 |

**Unsure:** whether `PublishedHeartbeat` commits; who writes `research/data/v4_days/`, since forecast_scoring/v4/wiring.py:26 names it and I found no writer; how often `card daily`, `global-cues` and `vix-history` run in practice.


## Part B: contactexepex/agentic-stock-prediction

# Data storage inventory: agentic-stock-prediction ("market-brief")

Checkout: `/home/user/agentic-stock-prediction`, shallow clone, HEAD 6840f0a (2026-10-16). Paths are relative to the repo; `S/` = `scripts/`, `MB/` = `scripts/marketbrief/`.

**Short answer.** All data lives under `data/<market>/<kind>/YYYY/MM/YYYY-MM-DD.<jsonl|csv>`. Everything is written by **appending to day files** (one helper does it), and the same day file is appended by several runs and sometimes by back-dated writes. So "write-once, never modified" **does not fit the current file unit**. Each append would need to become its own new Drive object (one file per run per kind), or day files would have to be sealed. Every reader goes through one DuckDB function that globs **all history of all 74 kinds**. There is no Google Drive code in the repo. Two mechanisms rely on git history as evidence: the F1.8 paper-trade lock (commit time) and the judgments log test.

---

## 1. Writers

### 1.1 Storage helpers

| Helper | What it does | Evidence |
|---|---|---|
| `paths.ROOT` / `data_dir(market)` | Root is `MB_ROOT` or the code dir; data = `<root>/data/<market>` | `MB/core/paths.py:16,20-22` |
| `storage.day_file(market, kind, day, ext)` | `data/<m>/<kind>/YYYY/MM/YYYY-MM-DD.<ext>`, makes the folder | `MB/core/storage.py:15-20` |
| `storage.append_jsonl(path, rows)` | `open("a")`, one JSON line per row, never rewrites | `MB/core/storage.py:23-30` |
| `storage.recent_ids(market, kind, days)` | Reads the ids in the last N day files, for dedup | `MB/core/storage.py:33-41` |
| `collector_store.stored_rows` | Latest row per id across the newest 400 day files | `MB/collectors/collector_store.py:56-64` |
| `collector_store.store_changed` | Appends only rows that are new or have changed values (a revision is a new row) | `MB/collectors/collector_store.py:97-109` |
| Temp-file pattern (`lifecycle.store.store_rows`, `portfolio.trades.store`) | Writes `work/.../<kind>-<id>.jsonl`, appends it into the day file, then unlinks the temp | `MB/lifecycle/store.py:38-48`, `MB/portfolio/trades.py:152-161` |
| `nse_runner` / `lab.run.append_new` / `intraday.store.write_rows` | Append-new-ids variants | `MB/collectors/nse_runner.py:69`, `MB/lab/run.py:24-31`, `MB/intraday/store.py:13-24` |
| Price CSV `write_bar` | `open("a")` CSV and writes the header on a new file | `MB/collectors/price_frames.py:61-73` |
| Agent `cat >>` (no Python) | `predictions`, `news_enriched`, `data/<m>/judgments` | `routine/PROMPT.md:230,245-247,441-442`; `routine/NEWS_PROMPT.md:79` |

**Write-once conflicts (important):**
- The same day file is appended by several sessions. The news light runs and the pre-open run append to the same news day file (`routine/NEWS_PROMPT.md:49-50`, `routine/PROMPT.md:377-383`). The post-close and evening runs both append to the same price CSV (`routine/EVENING_PROMPT.md:59-60`).
- Some writes are back-dated: the target file is chosen from the row's date, not from today. Examples: `lab.run.append_new` uses the row's `made_at`/`computed_at` date (`MB/lab/run.py:31`), ranges and calibration use `as_of_date` (`MB/analytics/range_publication.py:72`, `MB/analytics/calibration.py:158`), features and regime use `as_of` (`MB/analytics/features.py:200-201`), adjustments use `ex_date` (`MB/collectors/prices.py:204`), and price bars and `price_sources` use the bar day (`MB/collectors/price_frames.py:73`, `MB/collectors/price_nse_fallback.py:240-241`).
- Some files outside `data/` are rewritten in place. `reports/<m>/<session>.md` is rebuilt when stale (`MB/presentation/report/cli.py:41-67`). `reports/<m>/index.html` is rewritten every run (`S/html_report.py:199-200`).

### 1.2 Kinds (74 in `SCHEMAS`; 59 on disk for India, 56 for US)

The schema registry is `MB/core/schemas.py:26-52`. All kinds are JSONL except `prices`, which is CSV.

| Kind(s) | Writer (module:line) | Entry script / routine |
|---|---|---|
| prices (csv), adjustments, price_sources | `collectors/price_frames.py:61-73`, `prices.py:204`, `price_nse_fallback.py:240` | `collect_prices.py` (pre-open, post-close, evening) |
| quotes | `collectors/quotes.py:100` | `collect_quotes.py` |
| events, earnings_estimates | `collectors/events.py:324-325` | `collect_events.py` |
| news, news_updates, news_runs | `collectors/news.py:315-319`; `lifecycle/backfill.py:94` | `collect_news.py`, NEWS and pre-open runs |
| news_articles | `collectors/articles.py:106-136` | `collect_articles.py` |
| news_clusters | `analytics/news_clusters.py:268` | `news_clusters.py` |
| news_verified | `pipeline/news_status.py:164` | `news_status.py` |
| news_claims, primary_texts | `pipeline/claims.py:83,190`; `results/cli.py:104` | `claims.py`, `results_digest.py` |
| results_digests | `results/cli.py:198-199` | `results_digest.py` (RESULTS_PROMPT) |
| news_enriched | agent `cat >>` | `PROMPT.md:230`, `NEWS_PROMPT.md:79` |
| filings | `collectors/filings.py:133`; `lifecycle/backfill.py:119` | `collect_filings.py` |
| sec_times | `collectors/sec_times.py:141` | `check_sec_times.py` |
| fundamentals, holdings, insiders, options, stakes | `collectors/fundamentals.py:152`, `holdings.py:205`, `insiders.py:195`, `options.py:185`, `stakes.py:171` | `collect_*.py` |
| macro, shorts, short_interest, fpi, indices | `store_changed`: `macro.py:156`, `shorts.py:150-155`, `flows_india.py:134-137` | `collect_macro/shorts/flows_india.py` |
| deals, announcements, financials, flows, delivery (NSE) | `collectors/nse_india.py:81` → `nse_runner.py:69`; `relations_india.py:87` | `collect_nse_india.py`, `collect_relations_india.py` |
| features, regime | `analytics/features.py:200-201` | `features.py` |
| ranges, ranges_evening | `analytics/range_publication.py:72` | `ranges.py` |
| calibration | `analytics/calibration.py:158` | `calibrate.py` |
| predictions | agent `cat >>` (gated by `validate.py --stage forecast`) | `PROMPT.md:245-247` |
| agent_reasoning | `model/reasoning.py:211` | `agent_reasoning.py` |
| model_scores, model_versions, model_variant_* | `model/daily_scores.py:180-184` | `model_scores.py` |
| outcomes, range_outcomes | `pipeline/score_predictions.py:197-200` | `score_predictions.py` |
| reviews | `pipeline/review/cli.py:241-242` | `review.py` |
| lessons | `pipeline/lessons/cli.py:112-113` | `lessons.py` |
| replays | `replay/rule_replay/cli.py:203` | `replay.py` |
| graph, graph_runs | `graph/connection_map.py:153,216` | `graph.py` |
| judgments (data/<m>) | agent `cat >>` | `PROMPT.md:441-442` |
| strategy_predictions(+_evening), strategy_abstentions, head_to_head_picks, cost_views | `lab/run.py:67-116` | `lab.py predict/pick` |
| paper_trades_settled | `lab/settle_run.py:138-142` | `lab.py settle` (POSTCLOSE) |
| news_impact, lab_backtests | `lab/reports.py:52`, `lab/backtest_store.py:53` | `lab.py` |
| trade_reasons_ai, eod_analyses, research_reviews | `traders/eod.py:47-52`, `traders/director_report.py:67-68`; strategy rows `traders/outcome.py:79-84` | POSTCLOSE, WEEKLY |
| intraday_checks/runs/alerts, trade_checks, intraday_explanations | `intraday/check.py:152-176`, `intraday/explain.py:125` | `intraday_check.py` |
| slack_posts | `alerts/ledger.py:48`, `alerts/client.py:96` (Ledger `alerts/publish.py:107`) | `alerts.py`, `notify_slack.py` |
| portfolio_trades, watchlist_requests | `portfolio/service.py:50-99` → `trades.py:152` | `portfolio.py` |
| watchlist_events, command_log | `lifecycle/commands.py:81`, `seed.py:79`, `store.py:87` | `company.py` |
| trade_check_details | **No writer found.** Schema `core/schema_intraday.py:72`, read by `warehouse/company_sources.py:138`; not on disk | (unsure) |

### 1.3 Other repo-tracked outputs

| Path | Writer | Mode |
|---|---|---|
| `reports/<m>/<session>.md` | `MB/presentation/report/cli.py:41,67`, then filled by the agent | rewritten when stale |
| `reports/<m>/<session>.html`, `index.html` | `S/html_report.py:197-200` | index is overwritten every run |
| `reports/<m>/charts/<session>/*.png` | `S/charts.py:162` | new per session |
| `reports/<m>/review-<week>.md` | `MB/pipeline/review/cli.py:240` | new |
| `reports/<m>/research-<week>.md` | `MB/traders/director_report.py:56-59` | new |
| `reports/<m>/backtest…`, replay HTML/JSON | `MB/replay/backtest/cli.py:43-46`, `rule_replay/cli.py:194-198` | new |
| `summaries/<m>/{daily,weekly,monthly}/*.md` | **agent-written** (`routine/PROMPT.md:309-317`) | new |
| `judgments/log.jsonl` (build verdicts, union merge) | humans/agents; `.gitattributes` `merge=union` | append |

Not tracked (`.gitignore`: `work/`): `work/model_history` (`MB/constants/model.py:81`), `work/sec_acceptance.json` (`MB/constants/files.py:9`), the warehouse summary and all `work/steps`.

---

## 2. Schedulers that commit

### 2.1 Routine prompts (scheduled outside the repo; crons in `docs/DESIGN.md:19-62`)

| Prompt | Schedule (exchange time) | git step and paths |
|---|---|---|
| `PROMPT.md` (pre-open) | IN 07:40 IST, US 07:45 ET, Mon-Fri | 9e: `git add` strategy_predictions, strategy_abstentions, head_to_head_picks, cost_views + commit + push (`:300-304`). 12: `git add data summaries reports` + commit + push, rebase/conflict rules (`:374-385`). 13a and 13: `git add data/<m>/slack_posts` (`:402,415`). 14: `git add data/<m>/graph_runs data/<m>/judgments [data/<m>/graph]` (`:427-428`). 14a: `git add data/<m>/judgments` (`:450-451`) |
| `NEWS_PROMPT.md` | 31 sessions a week (`DESIGN.md:27-32`) | 3: `git add` the folders in `commit_paths` (news, news_runs, news_updates, news_articles, news_clusters, india announcements) (`:44-52`; list from `MB/pipeline/news_light_run.py:84`). 3f: `git add data/<m>/news_enriched` (`:82-85`) |
| `INTRADAY_PROMPT.md` | IN 11:13/14:13 IST, US 12:27/14:57 ET (`DESIGN.md:40-41`) | 5: `git add` intraday_checks, intraday_runs, intraday_explanations, trade_checks, intraday_alerts, slack_posts (`:58-66`) |
| `POSTCLOSE_PROMPT.md` | IN 17:45 IST, US 18:15 ET | 4: `git fetch --shallow-since=21 days` for the lock (`:36`). 9: `git add data` (`:71-76`) |
| `EVENING_PROMPT.md` | IN 21:30 UTC, US 18:30 ET (`:2`) | 7: `git add data` (`:55-61`) |
| `WEEKLY_PROMPT.md` | Fri 19:30 ET | 7: `git add data reports` (`:59-63`) |
| `RESULTS_PROMPT.md` | (part of the daily run) | digests saved by step 12's `git add data` (`:30`) |

Every save step does `git push origin HEAD:main`, with pull/rebase and conflict rules that rely on append-only lines and `id` dedup (`PROMPT.md:376-384`).

### 2.2 GitHub Actions

| Workflow | Trigger | Commits? |
|---|---|---|
| `onboard.yml` | `workflow_dispatch` only (web tier) | **Yes**: `git add data/`, commit, pull --rebase, push, 5 retries (`:66-80`). Secrets `MOTHERDUCK_INBOX_TOKEN`, `SEC_USER_AGENT`, `SLACK_BOT_TOKEN` (`:37-39`) |
| `tests.yml` | push/PR | No (read-only, `contents: read`). Deselects `test_every_logged_commit_exists` (`:45`) |
| `web-tests.yml` | push/PR | No |

No workflow has a cron schedule. All scheduling is in the Claude Code routines.

---

## 3. Readers

### 3.1 Central reader: `core/database.connect(market)` (`MB/core/database.py:152-178`)
- It creates one DuckDB view per kind for all 74 kinds. The views use `read_json`/`read_csv` over `data/<m>/<kind>/**/*.<ext>` (`:38-43`, `:164-171`), so **the full history is needed locally**.
- SEC kinds join on all `sec_times` files (`:46-58`).
- It builds `own_closed_days` from every distinct price date (`:132-149`).
- It builds `news_id_map` from **all stored news, in first-seen order** (`:98-122`). This is order-dependent dedup across the entire history.
- It then runs `sql/views.sql` (`:177`). `views.sql` itself has no file globs. It only builds views on the kind views (the only `data/` mention is a comment at `:180`).
- **47 modules** call `connect` (grep count). They include the context pack (`MB/pipeline/context.py:261`), the report (`presentation/report/cli.py:37`), `html_report.py`, the warehouse (`warehouse/sync.py:250`), Neo4j (`graph/neo4j/cli.py:106`), the replays (`replay/ai_replay/{evidence,prepare,record,score}.py`, `rule_replay/cli.py:180`, `backtest/report.py:16`) and the dashboard.

### 3.2 Direct file readers (bypass DuckDB)

| Module | Reads | Scope |
|---|---|---|
| `core/storage.py:36` recent_ids | last N day files | recent |
| `collectors/collector_store.py:59` | newest 400 files per kind | ~recent (400 days) |
| `collectors/news_window.py:121` | news/news_runs files ≤ today | recent window |
| `collectors/price_frames.py:108,136` | price CSVs in a lookback | recent |
| `collectors/events.py:97`, `earnings_estimates.py:22`, `fundamentals.py:58`, `holdings.py:68`, `sec_times.py:72` | all files of the kind | full |
| `analytics/price_adjustments.py:51` | all adjustments | full |
| `lifecycle/store.py:54`, `lifecycle/events.py:48` | all watchlist_events / command_log | full |
| `alerts/ledger.py:27` | all slack_posts (idempotency) | full |
| `intraday/store.py:31`, `intraday/alerts.py:38` | intraday kinds | full |
| `pipeline/validate/row_checks.py:29-46` | **every file of every kind** (duplicates, file-day vs row checks, CRLF) | full |
| `lab/settle_run.py:33-46` | all files + `git log -p` | full + git history |
| `replay/ai_replay/copy_asof.py:41,130,154`, `backfill.py:74,105` | copies `data/<m>` as of a date into a scratch root | full |
| `pipeline/news_light_run.py:84` | which kind folders have files (`commit_paths`) | recent |

Readers of `reports/` and `summaries/`:
- `warehouse/rm_brief.py:25-27`: globs `reports/<m>/*.html` into the app.
- `presentation/report/gather.py:94-101`: chart PNGs.
- `pipeline/spotcheck.py:150-152`: past `reports/<m>/<day>.md`.
- `pipeline/validate/report_checks.py:225,308`: the report and `summaries/<m>/daily/<today>.md`.
- `presentation/report/cli.py:47`: reads the previous report.

### 3.3 Warehouse sync (MotherDuck)
`S/warehouse_sync.py` calls `MB/warehouse/sync.py`. It runs `database.connect` (`:250`) and does a **full replace** of every mirrored table each run (`:1-9` docstring). It records `source_commit` = `git rev-parse HEAD` (`MB/warehouse/sync_records.py:50-56`, `sync.py:127,252`). It needs the full history. Secrets: `MOTHERDUCK_TOKEN`, `REVALIDATE_SECRET`, `VERCEL_AUTOMATION_BYPASS_SECRET`, `BRIEF_LINK_SECRET`.

### 3.4 Tests and golden harness reading the repo's data
- They copy or read the real `data/`:
  - `tests/test_warehouse_sync.py:121` and `test_rm_entities.py:85` copy `data/<m>`.
  - `test_api_contract.py:332` copies it too.
  - `test_lifecycle_company_meta.py:67,123` copies or reads `watchlist_events`.
  - `test_intraday_trades.py:113` reads `data/us/prices/2026`.
  - `test_dashboard.py:355,372` reads `data/us` and runs `git status data/us`.
  - `test_relations.py:208` and `test_b12_company_pages.py:151` read `data/<m>/...`.
  - `test_csv_line_endings.py:46` runs `git check-attr` on a data CSV.
- They read `reports/` and `summaries/`: `test_presentation.py`, `test_pipeline.py`, `test_validate.py`, `test_review.py` and `test_dashboard.py` (grep hits; I did not inspect whether they use real files or fixtures).
- The golden harness extracts `data`, `config` and `reports` from git commit `24749bdc…` with `git archive` (`tests/golden/overlay.py:19-39`, `golden.py:13`). **It needs that commit's data in git history.**
- `tests/conftest.py` blocks the network (`tests.yml:3-5`). Drive-backed fixtures would need a local cache.

---

## 4. Existing Google Drive code and storage secrets

- **No Drive code.** A grep for `drive|gdrive|googleapiclient|google.oauth2|pydrive|rclone` across the repo finds nothing. `requirements.txt` has no Google client.
- Env and secrets in use: `MB_ROOT`, `MB_CONFIG`, `MB_NOW`, `MB_MARKET` (`MB/constants/environment.py`), `MOTHERDUCK_TOKEN`, `MOTHERDUCK_INBOX_TOKEN`, `MOTHERDUCK_EXT_VERSION`, `REVALIDATE_SECRET`, `VERCEL_AUTOMATION_BYPASS_SECRET`, `BRIEF_LINK_SECRET`, `SLACK_BOT_TOKEN`, `SLACK_WEBHOOK_URL`, `SEC_USER_AGENT`, `NEO4J_URI/USER/PASSWORD/DATABASE/QUERY_URL`.
- `MB_ROOT` already redirects the whole data root (`MB/core/paths.py:16`). It is the natural seam for a local Drive mirror or cache.

---

## 5. Sizes (this checkout)

| Path | Size | Files |
|---|---|---|
| `data/` | 119M | 1,666 (1,044 csv, 621 jsonl, 1 .gitkeep) |
| `data/india` | 56M | 59 kinds |
| `data/us` | 63M | 56 kinds |
| `reports/` | 7.2M (india 4.0M, us 3.2M) | 109 (24 md, 20 html, 62 png, 1 json, 2 other) |
| `summaries/` | 108K | 24 (18 md) |
| `judgments/` | 280K | 1 (`log.jsonl`) |

Top 15 kinds per market (size, files):

| India | | US | |
|---|---|---|---|
| news | 14M, 11 | news | 17M, 11 |
| strategy_predictions | 6.9M, 7 | news_enriched | 6.9M, 7 |
| trade_checks | 5.9M, 5 | strategy_predictions | 5.3M, 6 |
| news_enriched | 5.6M, 9 | trade_checks | 4.4M, 4 |
| strategy_predictions_evening | 4.2M, 4 | strategy_predictions_evening | 4.0M, 4 |
| model_variant_scores | 3.3M, 7 | model_scores | 3.3M, 7 |
| model_scores | 2.4M, 8 | news_clusters | 3.0M, 10 |
| prices | 2.3M, **531** | news_articles | 2.6M, 10 |
| intraday_checks | 1.7M, 6 | model_variant_scores | 2.4M, 6 |
| news_clusters | 1.6M, 10 | prices | 2.2M, **513** |
| cost_views | 1.5M, 6 | fundamentals | 2.2M, 2 |
| news_articles | 1.3M, 10 | news_verified | 1.7M, 7 |
| news_verified | 912K, 8 | intraday_checks | 1.6M, 5 |
| head_to_head_picks | 564K, 5 | cost_views | 1.1M, 5 |
| ranges | 540K, 9 | holdings | 532K, 1 |

**Projected growth (reasoning only).** Prices are backfilled from 2024-10, but most kinds start around 2026-10-05. About 119 MB came in roughly 10 days, so growth is on the order of 3-4 GB a year for the two markets. The file count also grows fast: one file per kind per day, plus one file per append if every append becomes its own Drive object.

---

## 6. Things relying on git history or commit times

| Mechanism | Evidence | Impact |
|---|---|---|
| **F1.8 paper-trade lock**: a prediction or pick counts only if its row's **first commit time** is before D's open; found with `git log -p` per data file | `MB/lab/timing.py:31-82`; `MB/lab/settle_run.py:33-56` (no git repo means a `made_at`-only check; a row never committed is not locked); `MB/contracts/protocol.py:76`; routine step 9e (`PROMPT.md:298-304`) and the shallow-fetch deepening (`POSTCLOSE_PROMPT.md:35-40`) | Core evidence of no look-ahead. Moving off git needs a replacement timestamp, for example Drive `createdTime` or the receipt commit time. |
| Rebase keeps the step-9e commit time | `PROMPT.md:376-377` (`--committer-date-is-author-date`) | same |
| `made_at` check | `timing.is_locked` (`timing.py:80`); forecast gate "evidence public before `made_at`" (`PROMPT.md:240-243`, uses stored `first_seen_at`, not git) | uses data, not git |
| `judgments/log.jsonl` test: every logged commit exists | `tests/test_judgments.py:73-79`; deselected in CI (`tests.yml:42-45`) | code-review log, not market data |
| Golden harness inputs from commit `24749bd…` | `tests/golden/overlay.py:19-39` | needs data in git history |
| Warehouse `source_commit` recorded as the data version | `MB/warehouse/sync_records.py:50-56` | would need a data-manifest version instead |
| Merge or conflict rules that assume git merges of append-only files | `PROMPT.md:378-384`, `.gitattributes` (`judgments/log.jsonl merge=union`, `data/**/*.csv -text`) | obsolete with Drive |
| Code-structure test reads an old commit (code only) | `tests/test_code_structure.py:71-78` | unaffected |
| Lock test builds its own git repo | `tests/test_lab_db.py:173-204` | must be redesigned with the lock |

## Uncertainties
- `trade_check_details` has a schema and a reader but I found no writer.
- I did not open every test to tell real-data reads from fixtures; the test list in §3.4 comes from grep hits.
- The routine crons come from `docs/DESIGN.md`. The actual schedules live in the claude.ai routine settings, which I cannot see.
- The shallow clone means I could not measure git-history size or per-file commit counts.
