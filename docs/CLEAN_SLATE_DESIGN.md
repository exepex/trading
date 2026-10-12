# Clean slate: what the new system keeps, and what of the old system is removed

Status: **proposed, for ChatGPT review** (12 Oct 2026; request: `reviews/claude/response_24_2026-10-12-clean-slate.md`).
Nothing is removed until ChatGPT agrees and the owner approves. After approval: one cleanup commit, then a rewritten
implementation plan, regenerated stories, old issues #3-#21 closed as replaced and a clean issue set created.

Owner decision D3 (`docs/DESK_DECISIONS.md`): remove the old setup entirely; nobody uses it; the new desk starts clean.

## 1. Why remove instead of isolate

- The old system is an intraday **option-buying** desk on ~200 underlyings with chart rules. Its own 30-day backtest:
  219 trades, **-Rs 1.95 lakh**, rule hit rates 49-54% (no edge) (`reports/2026-10-12-backtest-analysis.md`). The
  approved design (v2.1 + section 12) trades protected NIFTY monthly structures decided once a day at about 3 pm.
- Fact check on "we almost lost all trades": the old **paper journal is empty** (`journal/trades.json` and
  `journal/shadow_trades.json` hold 0 trades). The loss evidence is the backtest above, not recorded paper trades.
- Keeping it means story E4 (single-writer lock, legacy labels, watchdog tests) and permanent care so two desks never
  share one paper account. Removing it deletes that risk and that work. Git history keeps every line; the last
  commit before removal is recorded in section 7 so anything can be recovered by hash.

## 2. Target layout after cleanup (no new behaviour, only re-homing)

```
fno/
  composition.py        NEW composition root for app services (replaces fno/live/services.py)
  storage/wiring.py     composition root for raw data stores and sources (unchanged)
  cli.py                commands: drive-check, groww-check, chain, quotes record|report
  providers/            market data only (Groww, NSE public, sample for tests)
  storage/              raw file stores and sources (NSE archives, repository, Google Drive read-only)
  fo_bhavcopy.py        NSE F&O daily file reader (old and UDiFF formats)
  research_data/        expiries, events calendar
  research_engine/      trial ledger and its guard
  accounting/           research ledgers
  quotes/               3 pm quote recorder (moved from fno/live/: recorder, report, cli, expiry_listing)
  analytics.py, costs.py, models.py, config.py, constants.py, http_pacing.py, env_file.py
```
New desk code (stories C-F, the three books) goes into new packages named by the rewritten plan, behind interfaces,
wired only in the two composition roots.

## 3. Kept: every existing function the new system uses

| Existing part | New home | Change | Used by (approved story / design) |
|---|---|---|---|
| `providers/` base, groww, public, sample, `__init__` factory | same | none | A4 recorder, `chain` and `groww-check` commands, tests (sample) |
| `providers/groww_check.py` | same | drop the live-prices check (needs the removed old feed) | owner's Groww credential check |
| `storage/*` | same | none | A1-A3 raw NSE files, Drive archive, quote store |
| `fo_bhavcopy.py` | same | none | A3, B1-B3 (proven identical on 128 overlap days) |
| `research_data/` | same | none | A6 events, expiries |
| `research_engine/` | same | none | B4 ledger guard |
| `accounting/` | same | none | C1 three ledgers |
| `live/quote_recorder.py`, `quote_report.py`, `quote_cli.py`, `expiry_listing.py` | `quotes/recorder.py`, `report.py`, `cli.py`, `expiry_listing.py` | move only; wiring moves to `composition.py` | A4 (judge-passed), 3 pm routine |
| `analytics.py` | same | remove functions left unused after cleanup (found by search, e.g. chart indicators) | B1 (implied volatility), `chain` |
| `costs.py` | same | none | all books' after-cost results, scoreboards A and B |
| `models.py` | same | none (quote, chain types) | providers, recorder |
| `config.py`, `constants.py` | same | remove old-desk constants (news, shock, old event names) | everywhere |
| `http_pacing.py`, `env_file.py` | same | none | NSE downloads, `.env` loading |
| `notify.py` | removed | see section 4; E2 builds a plain-text #fno-desk poster behind an interface | (E2 later) |
| `tools/nse_raw_download/` | same | none | owner's data download |
| `research/` (all studies, ledger, data, experiment 1) | same | backtest replay gets a "re-run at commit X" note (it imports the removed old desk) | evidence, B4, experiment 1 |
| `config.yaml` | same | keep `provider` (set to `auto`), `underlyings`, `lot_sizes`, `charges`, `slack` (fno-desk), `risk_free_rate`; remove the rest | |
| Docs: `DESK_DESIGN.md`, `DESK_DECISIONS.md`, this file | same | link fixes | |
| `IMPLEMENTATION_PLAN.md`, `docs/stories/` | same paths | **rewritten** after this design is approved | |
| `docs/JUDGE.md` | same | rewritten for stories (verdicts per story, no waves) | judge |
| `docs/DATA_SOURCES.md` | same | trimmed to sources the new system uses | |
| `reviews/`, `conversations/`, `research_notes/` | same | none (historical record; old links inside old reviews point to git history) | |
| `reports/`: backtest analysis (+ data json), strategy proposal, "Retail FnO losses and safeguards", `backtest-2026-10-12.md` | same | none | evidence cited by the design |
| Routine: 3 pm quote recorder (`trig_01M5iCBwkfvQhRFpdqBvzxEN`) | same | none (its command is unchanged) | A4 |
| Slack channel #fno-desk | same | quiet until E2 | E2 |

## 4. Removed (and what, if anything, replaces it)

| Old part | Size | Why remove | Replacement in the new system |
|---|---|---|---|
| `fno/live/` except the quote files: runner, scanner, universe, shortlist, signals (12 rule files), exit policy, kill switch, risk gate, contract picker, paper desk, market view/backdrop/clock, move check, price watch, shock detector, alerts, results stores (incl. DuckDB), `services.py` | ~6,300 lines | rejected strategy (intraday option buying); its kill switch closes all trades, contrary to the approved entry-only brake | C2 risk manager per book (brake blocks entries only), C4 validity, E1 daily loop, E2 report |
| `fno/live/news/` (fast news watcher, classifier, impact) | | drives old automatic news exits (design forbids automatic AI/news exits) | news only as a dated input to F1 finding cards, built under F1 if needed |
| `fno/live/feeds/` (live prices, NSE feed, participant OI) | | intraday feeds for the old desk | A4 snapshot + NSE daily files. **Change from response 19:** FII/DII participant OI was "keep as data"; under a clean slate the code goes, and a new `RawFileSource` downloads NSE's participant-OI daily files only if a B6 or F1 story needs them (history is on NSE's archive, so nothing is lost) |
| `fno/live/learning/` (IV history, trade stats, signal report, performance, news speed, view outcomes) | | grades the old desk; IV history never stored any data (checked) | implied volatility from NSE daily files (A3/B1); E3 scorecard; scoreboards A and B |
| `fno/live/research/` (reads the stock tool's research from its repo or MotherDuck) | | old desk input | F1 may re-add a read-only source with point-in-time rules; never writes to the stock tool |
| `fno/backtest/` (Yahoo 5-minute bars, modelled option prices) | 434 | modelled prices, rejected strategy | research engine B1-B3 on real NSE option prices |
| `fno/deploy/`, root `deploy/` (PC watchdog, Windows/Linux schedulers, git sync) | 423 | runs the old desk on the owner's PC | where AI books run is decision D4, decided before books 2 and 3 |
| `fno/brief.py`, `html_report.py`, `snapshot.py`, `strategies.py`, `signals.py`, `journal.py`, `naming.py`, `notify.py`, `providers/cached.py` | ~2,090 | 9:25 brief, old candidates and old paper journal; `naming`, `cached` unused | E2 daily report (plain text to #fno-desk); D3 decision records |
| `cli.py` commands brief, daily, notify, paper, live, backtest, calibrate, deploy | | old desk | `chain`, `drive-check`, `groww-check`, `quotes` stay |
| Old tests (`tests/live/*` except the recorder test, `test_backtest`, `test_deploy`, `test_journal`, `test_notify`, `test_strategies`, and any others that only test removed code) | | test removed code | recorder test moves to `tests/quotes/` |
| `journal/trades.json`, `shadow_trades.json` (both empty) | | old journal | new decision records (D3) |
| `data/live/` (empty) and its `.gitignore` lines; `.gitignore` lines for desk logs | | old desk state | none |
| `judgments/wave-*` (27 files) | | verdicts on old waves | new verdicts per story (rewritten `JUDGE.md`) |
| Old brief outputs in `reports/` (`*-brief*`, `*-page.html`, `*-slack.md`, `*-candidates.json`) | | old desk output | E2 report |
| Docs `WAVES.md`, `SAFEGUARDS.md`, `NEWS_FEED_PLAN.md`, `AI_DESK_PLAN.md`, `AI_PLAN_REEVALUATION.md` | | plans for the old desk; the re-evaluation's conclusions already live in `DESK_DECISIONS.md` and design section 12 | |
| Story E4 ("retire or separate the old live desk") | | nothing left to separate | dropped from the rewritten plan |
| Requirements `duckdb`, `pytz`, `Pillow`, `psutil` | | used only by removed code (each re-checked by search before removal) | |
| Paused 9:25 brief routine `trig_01FVkQVHf8p4Vrae4ZTyuXkc` | | old brief | deleted |
| Old web brief Artifact | | old brief | **deleted only with the owner's explicit yes** (deletion breaks the link for everyone) |
| `CLAUDE.md` "Daily market brief" section; interface list `SignalRule`, `GuardRule`, `IntradayPriceFeed`; composition root `fno/live/services.py` | | old desk | composition roots `fno/composition.py` and `fno/storage/wiring.py`; interfaces `Provider`, `RawFileStore`, `RawFileSource`, `FoFileFormat` plus those the plan adds |
| `README.md` old sections (live desk, profiles, shadow book, paper loop, how a setup is chosen) | | old desk | short README: purpose, commands, layout, routines |

Old safety ideas are not lost: each is either already an approved rule of the new design (entry-blocking Rs 30,000
brake, Rs 10,000 per trade, 3 open trades, C2 stress, C4 liquidity and quote validity) or written down in the
retail-losses report for the plan to reuse.

## 4a. Dependency check (done 12 Oct 2026, by search of the code)

- Kept code that imports removed code: only `fno/cli.py` (old commands) and `fno/providers/groww_check.py` (its
  live-prices check imports `fno/live/feeds/live_prices.py`). Both are trimmed as described in section 3.
  `fno/storage`, `research_data`, `research_engine`, `accounting`, `fo_bhavcopy`, `costs`, `analytics`, `models`
  import nothing from the old desk.
- Research scripts: only `research/2026-10-12-backtest/replay.py` imports the old desk (`fno.live.services`,
  `fno.backtest`). `cost_table.py` and all other studies use only kept modules.
- The 3 pm recorder today is wired through the old desk's composition root (`fno/live/services.py`), so it depends on
  the whole old desk. The cleanup fixes this: `fno/composition.py` wires provider, quote store and NSE expiry
  fallback, nothing else.
- A trial version of the cleanup was drafted, then **undone before commit** on the owner's instruction to get this
  design approved first. Nothing has been removed.

## 4b. Old code with logic the new desk may need (checked one by one)

| Old module | Logic worth keeping | Proposal |
|---|---|---|
| `live/feeds/nse_feed.py` | NSE holiday list, lot sizes, F&O ban list from NSE's website | E1 needs a trading-day calendar. Today the recorder detects holidays from the absence of same-day trades. The plan adds a small `TradingCalendar` (NSE holiday list, cached as a raw file with date and hash) behind an interface, written new, test-first. Ban list is for single stocks: not needed for NIFTY |
| `live/market_clock.py` | session phases in IST | Not needed: the new desk acts once at about 3 pm; the recorder already has its own 14:55-15:10 window |
| `live/contract_picker.py` | spread and open-interest filters per leg | The approved C4 validity check replaces it with stricter, tested rules (same-day trade, quote size, spread) |
| `live/results_store.py` | append-only JSONL records | D3 decision records are specified separately (one JSON file per decision, hashed); written new to that spec |
| `live/kill_switch.py`, `risk_gate.py`, `learning/performance.py` | stop rules | Replaced by approved C2 (entry-only Rs 30,000 brake, Rs 10,000 per trade, 3 open trades, stress). The old switch closes all trades, which the design forbids |
| `live/feeds/participant_oi.py` | FII/DII daily positioning | Rebuilt as a `RawFileSource` only if a story needs it (section 4) |
| `live/learning/iv_history.py` | ATM implied volatility per day | Stored nothing; B1 computes it from NSE daily files for all history |
| `naming.py` | Groww contract display names | E2 report can re-add a one-function formatter if wanted; 16 lines |
| `notify.py` | Slack posting with the F&O bot token (`FNO_SLACK_*`) | Its image upload exists only for the old brief. E2 writes a plain-text `DeskReportPoster` behind an interface; the safe channel rule (only #fno-desk, never `SLACK_*`) moves into E2's tests |

## 5. Changes this forces in approved stories (applied when the plan is rewritten)

- A4: paths `fno/live/quote_*.py` -> `fno/quotes/*`; wiring in `fno/composition.py`. No behaviour change, so the
  judge's pass stands (to be re-confirmed by running its tests after the move).
- All stories: "wired in `fno/live/services.py`" -> `fno/composition.py`.
- E4 dropped. Response 19's G4 (legacy outputs) is moot.
- Decision records stay under `journal/` (new subfolders only, e.g. `journal/decisions/`), so C2, C4 and D3 paths do
  not change.

## 6. Acceptance criteria for the cleanup commit (judge-checkable)

1. No file imports a removed module: `grep` for `fno.live`, `fno.backtest`, `fno.deploy`, `fno.brief`, `fno.journal`,
   `fno.strategies`, `fno.signals`, `fno.snapshot`, `fno.notify` finds nothing outside `reviews/`, `conversations/`
   and the backtest replay (which carries the pinned-commit note).
2. `python -m pytest -q` and `ruff check fno tests` pass; the A4 recorder tests pass unchanged except imports.
3. `python -m fno --help` lists exactly `chain`, `drive-check`, `groww-check`, `quotes`; `python -m fno quotes
   record --outside-window` works with the sample provider.
4. No dead links: every relative Markdown link in `README.md`, `CLAUDE.md`, `AGENTS.md` and `docs/` resolves
   (checked by a small link-check script run once).
5. `config.yaml` loads and contains only the kept keys; no code reads a removed key.
6. Every removed requirement has no remaining import.
7. The 3 pm routine's command and output paths are unchanged.

## 7. Recovery

The commit hash before the cleanup is written into the README "History" line and the backtest replay note
(`git checkout <hash> -- fno/live` restores any part). Nothing in `research/data/` or recorded quotes is touched.

## 8. Questions for ChatGPT

1. Is anything in section 4 still needed by an approved story or section 12 (three books, two scoreboards)?
2. Is dropping E4 safe, given nothing old can run after the cleanup?
3. Are the acceptance criteria in section 6 enough for the judge?

## Appendix A. Every old code file and its verdict

Lines and descriptions are taken from each file's own header (12 Oct 2026). R = remove, K = keep, M = move.

| File | Lines | What it does | Verdict |
|---|---|---|---|
| `fno/live/runner.py` | 311 | market-hours loop: refresh, scan, exits, report | R |
| `fno/live/scanner.py` | 177 | one scan: universe, backdrop, shortlist, signals, contract, risk gate, paper trade | R |
| `fno/live/services.py` | 344 | old composition root | R (replaced by `fno/composition.py`) |
| `fno/live/universe.py`, `shortlist.py` | 74, 45 | ~200 F&O underlyings narrowed each scan | R |
| `fno/live/market_view.py`, `market_backdrop.py`, `models.py`, `indicators.py` | 87, 73, 196, 46 | votes into one view; sector, global, VIX context; 5-minute candle maths | R |
| `fno/live/market_clock.py` | 82 | trading session phases | R (see 4b) |
| `fno/live/contract_picker.py`, `move_check.py` | 183, 59 | one option to buy, stop and target; move needed vs likely | R |
| `fno/live/exit_policy.py`, `news_exit.py` | 72, 44 | stop/target/trailing exits; automatic news exits | R |
| `fno/live/kill_switch.py`, `risk_gate.py` | 45, 129 | close-all switch; old portfolio rules | R (C2 replaces) |
| `fno/live/paper_desk.py`, `results_store.py`, `duckdb_results_store.py` | 167, 108, 81 | old paper fills and JSONL/DuckDB results | R |
| `fno/live/price_watch.py`, `shock_detector.py` | 59, 60 | 20-second prices, sudden-move shocks | R |
| `fno/live/alerts.py`, `cli.py` | 100, 156 | old Slack alerts; `fno live` commands | R |
| `fno/live/signals/*` (12 files) | 719 | chart, news, research, positioning votes and guards (`SignalRule`, `GuardRule`) | R |
| `fno/live/feeds/*` (4 files) | 387 | Yahoo/Groww intraday prices, NSE reference data, participant OI | R (see 4b) |
| `fno/live/news/*` (12 files) | ~1,600 | fast news watcher, classifier, impact score | R |
| `fno/live/learning/*` (6 files) | 475 | IV history, signal hit rates, trade stats, go-live test, news speed | R |
| `fno/live/research/*` (5 files) | 478 | reads the stock tool's research (repo or MotherDuck) | R |
| `fno/live/quote_recorder.py`, `quote_report.py`, `quote_cli.py`, `expiry_listing.py` | 194, 48, 33, 54 | 3 pm quote recorder (A4) | M to `fno/quotes/` |
| `fno/backtest/*` (5 files) | 434 | Yahoo 5-minute replay with modelled option prices; calibration | R |
| `fno/deploy/*` (5 files), `deploy/desk.py`, `deploy/setup.py`, `deploy/README.md` | 423 | PC watchdog, OS schedulers, git sync, setup | R |
| `fno/brief.py`, `html_report.py`, `snapshot.py` | 302, 722, 114 | 9:25 brief: Markdown, HTML, PNG | R |
| `fno/strategies.py`, `signals.py` | 321, 141 | old candidate builder and directional bias | R |
| `fno/journal.py` | 320 | old paper journal (JSON) | R |
| `fno/notify.py`, `naming.py`, `providers/cached.py` | 98, 16, 51 | brief to Slack; contract names; chain cache (unused) | R (see 4b) |
| `fno/cli.py` | 194 | all commands | K, trimmed to 4 commands |
| `fno/providers/groww_check.py` | 50 | Groww credential and data check | K, live-prices part removed |
| everything else under `fno/` (excluding `cli.py`, `groww_check.py`) | ~2,300 | providers, storage, data readers, ledgers, maths, costs | K unchanged |

## Appendix B. Tests

| Test file | Verdict |
|---|---|
| `tests/live/test_quote_recorder.py` | M to `tests/quotes/`, imports updated, assertions unchanged |
| `tests/live/test_fills.py` | R, except its `parse_groww_book` case, which moves into `tests/test_groww_provider.py` (that parser stays) |
| `tests/live/*` (the other 18 files incl. `fakes.py`), `tests/test_backtest.py`, `test_deploy.py`, `test_journal.py`, `test_notify.py`, `test_strategies.py` | R (test only removed code) |
| `tests/test_analytics.py`, `test_providers.py`, `test_groww_provider.py`, `test_storage.py`, `test_drive_check.py`, `test_fo_bhavcopy.py`, `test_http_pacing.py`, `test_env_file.py`, `test_nse_raw_download.py`, `tests/research/*`, `tests/research_data/*`, `tests/accounting/*` | K unchanged |
| `tests/conftest.py` | K: the fixture that removes `GROWW_*` variables stays; the protected-path list drops `data/live` and keeps `journal` |

## Appendix C. `config.yaml`

| Key | Verdict |
|---|---|
| `provider` | K, value `auto` (Groww when its credentials are set, else NSE) |
| `underlyings`, `lot_sizes`, `charges`, `slack` (`fno-desk`, `C0C89E8QCCD`), `risk_free_rate` | K |
| `profile`, `account`, `position_rules`, `holding`, `go_live_criteria`, `performance_kill`, `daily_limits`, `expiry`, `strategies`, `signals`, `liquidity`, `exits`, `live`, `profiles` | R: old desk limits and rules. The approved money rules (Rs 5 lakh, Rs 10,000 per trade, 3 open, Rs 30,000 brake, 31.2% tax) enter config only through C2 and the playbook, with tests |
