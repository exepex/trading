# Review 22 — Clean-slate cleanup judge

**Date:** 2026-10-12  
**Judge:** ChatGPT  
**Repository:** `exepex/trading`  
**Base:** `184ff7e9acca6fd1b47598f69fbac5bb1b3b5914`  
**Build:** `145a632` (one commit ahead of base)  
**Sources:** `reviews/claude/response_27_2026-10-12-cleanup-built.md`, `docs/CLEAN_SLATE_DESIGN.md` v2.1, `docs/JUDGE.md`, approved stories and source files at build commit.

## Verdict: FAIL

**One should-fix finding remains.** The deleted intraday desk left behind Yahoo-backed market-context code with no approved active consumer. This conflicts with the clean-slate objective and §3's claim that kept provider code is only what the new system uses. No blocking money-safety regression was found in the recorder relocation. There are also two minor documentation/test-gate observations.

**Execution limitation:** I independently fetched the pinned GitHub commit and compared `184ff7e..145a632` through the GitHub connector (214 changed files). The local execution container has no checkout and cannot resolve `github.com`; `/mnt/data` contains no repository. Consequently I **could not independently execute** `python -m pytest -q`, `ruff check fno tests tools`, or `python tools/check_imports.py`. I attempted Git access and local test discovery; there were no tests to run locally. Claude reports 165 tests passing and the import graph reporting 70 files clean, but those are **builder claims, not my command outputs**. This limitation prevents an independent execution PASS; it is not itself a claim that the code fails those commands.

## Findings

### F1 — SHOULD FIX — Old Yahoo market-context stack still survives in the kept providers [strong evidence]

- `fno/providers/base.py:17-22` retains `YAHOO_SYMBOLS` and `:47-48` still requires `Provider.context()`.
- `fno/providers/public.py:64-82` still implements `daily_closes()` and `daily_history()` via `query1.finance.yahoo.com`; `:180-200` implements `NSEProvider.context()` using Yahoo history.
- `fno/providers/groww.py:184-199` still implements `GrowwProvider.context()` through `PublicData.daily_history()`; `fno/providers/sample.py:68-82` also builds synthetic context; `fno/models.py:100-118` retains the dedicated `MarketContext` type.
- In contrast, the retained commands use `get_provider(...).chain()` and `expiries()` (`fno/cli.py:35-64`), and A4 uses `expiries/chain/quote_book` (`fno/composition.py:12-17`, `fno/quotes/recorder.py:119-142`). `tests/test_providers.py:1-58` tests chain parsing, not context. New historical research explicitly uses archived NSE daily files (A1–A3, B1–B3), not Yahoo chart history.
- `docs/CLEAN_SLATE_DESIGN.md:42-59` claims every kept function is used by an approved story, yet does not enumerate the retained `context`/Yahoo functions; §4 removes the old Yahoo intraday backtest.

**Expected fix:** Delete the unused `Provider.context` abstract method, its implementations in NSE/Groww/sample providers, `PublicData.daily_history/daily_closes`, `YAHOO_SYMBOLS`, and `MarketContext` **after confirming the entire surviving import/call graph**. If there is a specific approved A–F story needing any of them, name the story and its exact contract instead of keeping them by inertia. Run import, unit and lint checks after trimming. Do not change A4's `expiries/chain/quote_book` path.

This is **should fix**, not blocking: it leaves unwanted old desk infrastructure, but I found no path from it to real orders or the A4 recorder.

### F2 — MINOR — Backtest README still presents the archival replay as a normal root command [strong evidence]

`research/2026-10-12-backtest/README.md:14-24` correctly explains that `replay.py` only runs in the pinned legacy worktree. However, `:27-32` then labels a code block “Commands (from the repository root)” and lists `python research/2026-10-12-backtest/replay.py` without saying *legacy* root. On new main that command necessarily imports deleted `fno.backtest`/`fno.live` modules (`replay.py:22-28`).

**Expected fix:** Change that heading to “Commands (from the legacy worktree root for replay; current main for cost table)” and annotate the replay line. This is an ambiguity, not an active scheduler or runnable old desk.

### F3 — MINOR — Original A4 story's introductory output schema still describes an older recorder [strong evidence]

`docs/stories/A-data-foundation.md:167-173` describes a single `nifty_<date>_1500.csv` and `quote_age_seconds`, whereas the actual recorder writes timestamped attempts, metadata and a canonical marker (`fno/quotes/recorder.py:81-87,115-160`) and marks quote age unknown (`:46-63,170-181`). The same story later clarifies the true A4 implementation at `A-data-foundation.md:174-220`. This inconsistency predates the cleanup but remains misleading to a future implementer/judge.

**Expected fix:** Align the introductory story text with the later approved A4 clarification; do not change the recorder.

## Independent criterion-by-criterion assessment

| # | Criterion | Judgment and direct evidence |
|---|---|---|
| 1 | Import graph | **STATIC CHECK / EXECUTION UNVERIFIED.** `tools/check_imports.py:16-24,27-61,68-93` resolves relative and absolute `fno` imports, skips exactly the archival replay, and returns nonzero on missing modules. `tests/test_import_graph.py:20-45` tests planted missing imports and imports app modules. I could not run it. |
| 2 | Pytest + Ruff | **EXECUTION UNVERIFIED.** Claude reports 165 passing tests, Ruff clean. I read the new test sources; no independent local run was possible. |
| 3 | Four CLI commands | **STATIC PASS.** `fno/cli.py:67-87` registers only `drive-check`, `groww-check`, `chain`, `quotes`; quote actions are in `fno/quotes/cli.py:8-14`. CLI execution unavailable. |
| 4 | Relative docs links | **PARTIAL / EXECUTION UNVERIFIED.** Reviewed changed docs and the archival README; no removed path in an active command was found, but no independently executed whole-tree Markdown link check. F2 is a misleading command, not a dead link. |
| 5 | App config | **STATIC PASS.** `fno/config.py:14-19,32-50` strictly validates app top-level keys while preserving plain frozen-study config; `tests/test_config.py:7-33` checks 14 removed keys and old frozen settings. |
| 6 | Removed requirements | **STATIC PASS.** `requirements.txt:1-5` no longer lists DuckDB, pytz, Pillow or psutil; changed-file inspection and retained source showed no imports of them. |
| 7 | Recorder command/path | **STATIC PASS.** `fno/quotes/cli.py:17-33` retains `python -m fno quotes record`; `fno/composition.py:12-17` calls the unchanged quote store; `fno/quotes/recorder.py:24-38,81-87` keeps output names. |
| 8 | No data lost | **DIFF PASS for tracked files.** Compare reports no changed `research/data/**`, `research/LEDGER.md`, `research/ledger.csv`, or `accounting/**`. Only retained-study change is `research/2026-10-12-backtest/README.md` (13 added lines); five legacy `reports/*brief*/page/slack/candidates` outputs are removed as approved. No independent SHA-256 manifest run, and untracked external data cannot be audited from git. |
| 9 | Recorder integration | **STATIC PASS / EXECUTION UNVERIFIED.** `tests/quotes/test_recorder_baseline.py:28-81` compares four deterministic output scenarios byte-for-byte against committed golden fixtures; `tests/test_composition.py:34-80` checks root-vs-quotes provider separation and Groww/NSE auto choice. Recorder and expiry-listing files were Git-detected renames with no content changes. |
| 10 | Routine audit | **EXTERNAL STATE UNVERIFIED.** `CLAUDE.md:44-54` preserves the weekday recorder instructions; Claude says routine `trig_01M5iCBwkfvQhRFpdqBvzxEN` remains enabled and unchanged. I cannot independently inspect its scheduler through GitHub. |
| 11 | No old execution | **STATIC PASS with F1 cleanup gap.** The compare deletes old runner, deploy scripts, live desk, news, backtest and brief; `fno/cli.py:67-87` exposes no legacy commands; `docs/DESK_DESIGN.md:325` points to E1's lock and `docs/stories/E-paper-desk.md:53-59` contains the migrated criteria. Archival replay is not an active CLI. F1 is retained unused source, not a runnable old desk. |

## Section 9: each design-to-build difference judged

1. **Remove `parse_groww_book` rather than move its test — ACCEPT [strong evidence].** Its old caller `GrowwProvider.live_quote` was removed; `parse_groww_quote_book` and `quote_book` remain in `fno/providers/groww.py:92-119,175-183` and are tested at `tests/test_groww_provider.py:93-107`. Keeping an unused alternate parser would be unnecessary.
2. **Remove `Direction` — ACCEPT [strong evidence].** The surviving app no longer uses the old direction enum; the archival replay is pinned to its old commit. `fno/constants.py` now has the relevant provider/IO constants without that enum.
3. **Keep `load_config` plain for frozen research, add `load_app_config` strict — ACCEPT [strong evidence].** `fno/config.py:32-50` and `tests/test_config.py:25-33` preserve historical input semantics while rejecting obsolete keys in app settings. This is superior to modifying frozen study inputs.
4. **Remove `tests/research/test_opening_bridges.py` — ACCEPT [strong evidence].** That test imports/executes the archival replay; the worktree instructions at `research/2026-10-12-backtest/README.md:14-24` retain a reproducible route at the base commit.
5. **Protect `research/data` and `journal` in tests — ACCEPT [strong evidence].** `tests/conftest.py:7-27` checks tracked paths' modification timestamps around a test session. This is an appropriate regression guard; it is not a cryptographic data-integrity check.
6. **Commit four recorder golden scenarios — ACCEPT [strong evidence].** `tests/quotes/test_recorder_baseline.py:55-81` checks byte-for-byte output for normal, retry, no-trade and December fallback; compare shows committed fixture CSV/metadata/canonical files.

## Additional hunting and scope

- **Recorder:** the relocated `fno/quotes/recorder.py`, `report.py` and `expiry_listing.py` are Git-detected content-identical renames; CLI and composition changes are narrowly scoped. I found no introduced order path, fabricated fill, or output rewrite.
- **Known pre-existing calendar limitation:** `fno/quotes/recorder.py:93-95` still skips every Saturday, including a special trading session. The approved A1 session-calendar work is not built yet (`docs/stories/A-data-foundation.md:27-33`). This is an acknowledged future-story issue, **not a new cleanup regression**, and should not be misreported as one.
- **Legacy archive:** the replay intentionally cannot run on new main; it is recoverable at the exact base SHA. Do not remove the historical data or pin.
- **Security:** no new order API or committed secret was found in the reviewed changed source. No runtime broker/API network test was made.

**Required before a PASS:** resolve F1, clarify F2/F3 when updating docs, and provide independently executable test/lint/import-check evidence in an environment with the repository checkout. Per `docs/JUDGE.md:6`, any unresolved should-fix means **FAIL**.
