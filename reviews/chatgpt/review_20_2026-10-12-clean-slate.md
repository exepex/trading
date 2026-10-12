# Review 20 — Clean-slate removal design

- **Reviewer:** ChatGPT (independent design/code review)
- **Date:** 2026-10-12
- **Repository/ref reviewed:** `exepex/trading`, `main` at `c258bfdd9f20e35c1db6ccbe7fd55df5e06a5dae`
- **Sources:** `reviews/claude/response_24_2026-10-12-clean-slate.md`, `docs/CLEAN_SLATE_DESIGN.md`, `docs/DESK_DESIGN.md` v2.1 + §12, `docs/DESK_DECISIONS.md`, `docs/IMPLEMENTATION_PLAN.md`, `docs/stories/{A,B,C,D,E,F}-*.md`, `AGENTS.md`, `CLAUDE.md`; inspected actual Python, tests, requirements and configuration.
- **Verdict:** **AGREED WITH CHANGES** — approve the goal of removing the entire old trading desk, **not the cleanup as currently specified**. Resolve blocking items before the destructive commit. Nothing here authorises deleting the running A4 routine or data.

## Findings (evidence, severity and required correction)

### 1. [BLOCKING; strong evidence] A4 recorder has a real source-provider regression hidden by the proposed config cleanup

**Evidence:** `config.yaml:7` currently says `provider: nse`, while `config.yaml:122-124` says `live.chain_provider: auto`. The A4-specific composition at `fno/live/services.py:336-344` explicitly reads `live.chain_provider`, not the root setting. `fno/live/quote_cli.py:17-27` builds A4 through that composition; `fno/providers/__init__.py:10-22,30-41` chooses Groww via `auto` only when usable credentials are available. Proposed appendix C deletes `live` and switches root `provider` to `auto`, so A4 can start using a different provider than before, and `chain` can also silently switch from NSE to Groww. That is **not** “move only / no behaviour change” as claimed in §§2, 3 and 5. The existing A4 tests (`tests/live/test_quote_recorder.py:26-55,61-182`) instantiate a fake provider directly, so they do not prove composition equivalence.

**Fix:** Give A4 its own **explicit, preserved data-provider choice**, independent of the CLI's chain-provider default, or document and explicitly approve a changed policy. Demonstrate before/after matrix for Groww credentials present / absent, including fallback and failure behaviours, never changing the chosen source silently. Add integration tests for `python -m fno quotes record` composition, exact `research/data/quotes/` output, and canonical bytes/schema with a deterministic provider. A4 must continue using `fno/storage/wiring.py:53-60` for storage and the NSE expiry fallback at `fno/live/expiry_listing.py:32-54`.

### 2. [BLOCKING; strong evidence] Cleanup acceptance criterion 3 is impossible with the retained sample provider; its process result is not a proof of recording

**Evidence:** `fno/providers/sample.py:16-66` implements `expiries` and `chain` but **does not implement `quote_book`**; inherited `fno/providers/base.py:53-56` returns `None` for every leg. `fno/live/quote_recorder.py:115-160` then emits rows that lack live quotes, and its `complete` flag only checks whether collection raised errors and row count matches; it does not require valid books. The sample provider's fixed `as_of` is 2026-10-09 (`sample.py:19-21`), and the CLI `--outside-window` never creates a canonical record (`quote_recorder.py:98-99`). Thus the proposed “`quotes record --outside-window` works with the sample provider” is at best an **offline smoke call**, not evidence of real quote capture or unchanged A4 behavior.

**Fix:** Specify the expected exit/status/attempt contents of this smoke test. Use a deterministic fake `quote_book` provider or sample fixture for an end-to-end A4 test with usable bid/ask, size, same-day trades, the two monthly expiries, immutable retries, canonical marker, NSE expiry fallback, report, and failed/holiday paths. Assert output directory and hashes stay compatible.

### 3. [BLOCKING; strong evidence] Deleting old E4 does **not** delete the need for separate paper-account concurrency protection

**Evidence:** `docs/DESK_DESIGN.md:310-335` requires **three distinct Rs 5 lakh paper accounts**, including Book 3's matched shadow decisions and separate cost accounting; §12.6 line 325 explicitly says “E4's lock is per account”. Current `docs/stories/E-paper-desk.md:122-149` describes an account-scoped single-writer lock, restart/watchdog coordination and independent outputs. The old-vs-new **desk selector** and legacy-output labels are obsolete, but simultaneous E1 instances, Book 1/2/3, scheduled retries and interruptions still threaten the same new ledger. E1's idempotent run ID and crash recovery (`E-paper-desk.md:30-31,44`) do not by themselves serialize competing writers.

**Fix:** Drop E4 **as a legacy isolation story only**, but explicitly move its account-scoped exclusive-write/lease and crash-recovery requirements into the new E1/D3/multi-book implementation and tests. §12.6 must reference the replacement rather than a dropped E4. Test simultaneous starts of two different books (both proceed in different accounts), two writers to the same account (one cannot double-fill), and restart after interrupted commit. Any E4 watchdog test specific to the old runner may go.

### 4. [BLOCKING; strong evidence] Existing A1 calendar work must be **reused**, not reimplemented as an unrelated E1 calendar

**Evidence:** `docs/stories/A-data-foundation.md:24-33,47-50` already specifies an independent, versioned `research/data/calendar/nse_sessions.csv` backed by NSE annual holiday and **special / weekend / muhurat session** circulars, with validation and provenance. `docs/stories/B-research-engine.md:90-92` uses this same calendar to choose next/last eligible trading sessions. Clean-slate §4b instead says a *new* E1 `TradingCalendar` fetched as an NSE holiday list, “written new” and cached; `fno/live/feeds/nse_feed.py:71-73` has only a holiday endpoint. A weekday-minus-holidays-only calendar cannot infer exceptional weekend sessions. Nor does a missing same-day trade conclusively identify a holiday: `fno/live/quote_recorder.py:143-144` relies on that heuristic.

**Fix:** Keep the `fno/live/feeds/nse_feed.py` implementation removed, **but have E1 and A4 read the A1 independent session calendar behind a small interface**. Make the same versioned calendar canonical for A1, B2, E1 and recorder holiday determination. NSE holiday APIs may update it, not override audited exceptions. Include a special Saturday and holiday tests. Preserve A4's fail-closed/incomplete-attempt handling if the calendar and quote data disagree.

### 5. [SHOULD FIX; some evidence] Kept provider interface contains a dangerous old-desk fill fallback and nonessential live-desk hooks

**Evidence:** `fno/providers/base.py:50-61` has `forget()` (“after a sudden move”) and `live_quote()` whose docstring explicitly invites fallback to **last price +/- slippage** when no book exists. That conflicts with `docs/stories/C-code-roles.md:124-130`, `E-paper-desk.md:23-33,39-45`, and `DESK_DESIGN.md:303-308`: no fictitious stale/last-price fills. `fno/models.py:17-52` still exposes `OptionQuote.fill_price()` with a slippage guess. The clean-slate table marks all providers/models “none”/unchanged, though these are old behaviour, even if no kept caller currently invokes them for paper fills.

**Fix:** Audit these methods during cleanup; remove `live_quote` and `forget` if no approved use remains, or keep them explicitly as *data-only* APIs with no fill fallback. Make E1 require `quote_book`/validated bids and asks (never `OptionQuote.fill_price()`), and add an explicit negative test. Preserve `quote_book` required by A4 and C3.

### 6. [SHOULD FIX; strong evidence] “No old imports in kept code” is only partially checked; a literal dotted-name grep misses relative imports, tests, entrypoints and documentation commands

**Evidence:** `fno/cli.py:10-16,29-68,119-139,149-189` uses **relative** imports: `.backtest`, `.deploy`, `.live`, `.brief`, `.journal`, `.notify`. `fno/live/quote_cli.py:20-21` imports `.services` and `.quote_report`, and the old services root imports dozens of old modules at `fno/live/services.py:11-60`. `fno/providers/groww_check.py:34` imports `..live.feeds.live_prices`. `research/2026-10-12-backtest/replay.py:22-28` imports removed modules; it **must fail to execute after cleanup**, regardless of a comment naming an old SHA. `CLAUDE.md:44-74` still calls the old `daily` and `notify` commands, and `README.md:16-30` advertises `daily`/`live` commands. Repo code search for the nine literal strings returned no results even though direct file fetches show many imports, proving that search alone is inadequate here.

**Fix:** Expand acceptance criterion 1 into (a) AST import analysis of every surviving `fno/`, `tests/`, `tools/`, `research/` module, resolving both relative and absolute imports; (b) a static/import smoke test for every retained CLI entrypoint; (c) prohibition on executable references to removed modules/commands in active instructions, scripts and schedules. Historical replay becomes explicitly **non-runnable in the new checkout**, and documents must give an exact isolated checkout/worktree command at the pinned pre-cleanup SHA for replay instead of promising it runs on main.

### 7. [SHOULD FIX; strong evidence] Proposed 4-command CLI contradicts already-approved, not-yet-complete story A1 and the coming scorecard

**Evidence:** `docs/stories/A-data-foundation.md:24-25` explicitly requires `python -m fno data-coverage`. `docs/stories/E-paper-desk.md:98` requires `python -m fno desk scorecard`. Clean-slate §6(3) asserts help lists **exactly** `chain`, `drive-check`, `groww-check`, `quotes`. Four commands are a sensible **immediately-after-cleanup** transitional state, but not the final approved application surface.

**Fix:** Label the 4-command check “at cleanup commit only”, list the command additions owed to approved stories, and avoid an invariant which will falsely fail A1/E3 or force a later deletion of their CLI.

### 8. [SHOULD FIX; strong evidence] Keep-vs-remove inventory needs some precision; common library code is not identical to the rejected desk

**Evidence:** `fno/analytics.py:21-75,110-126,169-176` contains pricing, Greeks, IV and historical volatility essential to B1/C2 and §12 forecasts; `analytics.py:78-108,128-135` has option-chain metrics used by `fno/cli.py:96-100`. By contrast `analytics.py:140-168` has EMA/RSI from the old chart desk; clean-slate §3 allows trimming chart indicators but does not call out an explicit test of remaining consumers. `fno/constants.py:8-67,82-146` intermixes reusable instrument/trade enums and obsolete session/news/shadow/shock constants. `fno/config.py:25-40` still implements `profile`/`profiles` merging, whose keys §C removes; loader behaviour must be intentionally simplified or documented as unused. `fno/providers/sample.py:27-31` generates generic five weekly expiries rather than a realistic A4 two-monthly listing.

**Fix:** Publish an explicit per-symbol/function keep/remove list for shared files, or add direct consumers/tests when retaining a method. Preserve maths and safe data interfaces, remove legacy-only formatting/policies after proving nonuse. Update `config.py` to the intended simple schema and regression-test unknown/removed keys (a permissive YAML loader alone cannot enforce “no code reads removed key”).

### 9. [SHOULD FIX; reasoning only] “No participant OI data lost” overstates evidence; availability is not equivalent to point-in-time preserved inputs

**Evidence:** `fno/live/feeds/participant_oi.py:15,38-47,75-88` uses an NSE daily participant-OI URL and parses FII positioning; it is not a general participant-archive preservation facility. Section 4b proposes removing it and redownloading later. `DESK_DESIGN.md:48-55,118-125,138-143` names positioning and FII/DII signals for edge E6 and expert findings; section 12's books can use them **when permitted and time-stamped**. Current B6 (`docs/stories/B-research-engine.md:249-277`) does not explicitly depend on this old adapter.

**Fix:** Removing the old parser/downloader is acceptable **if** new sourcing has a named owner story and a point-in-time provenance/availability rule before any E6/F1/AI book uses participant positions. Do not claim archived historical files have already been verified or that “nothing is lost”: check access/coverage, release timestamps and archive stability in the corresponding future story. No need to keep old intraday code just in case.

### 10. [SHOULD FIX; some evidence] IV history removal is sound, but the replacement must distinguish historical implied-vol estimates from observed quote history

**Evidence:** `fno/live/learning/iv_history.py:36-54,70-76` computes and writes ATM IV **only when observed and flushed**; no persisted IV data was evidenced here (a code inspection cannot prove absence of untracked runtime storage). `docs/stories/B-research-engine.md:15-30` calculates historical IV from the daily files; `DESK_DESIGN.md:337-352` needs a separate **30-day ATM IV** point-in-time forecast baseline. `fno/analytics.py:110-126` computes current chain ATM IV and calls `years_to_expiry()`, so that method is not directly a historical point-in-time computation.

**Fix:** Remove old `IvHistory` **only after** setting the separate B1/§12 historical feature contract: expiry selection, past-only market price, rate, session calendar and missing-data rules, plus forward A4 quote provenance. Do not quietly equate today's chain-based IV with historical calibrated 30-day implied volatility.

### 11. [SHOULD FIX; strong evidence] E2 poster can replace the brief poster, but safe-channel tests must reject hostile overrides as well as wrong prefixes

**Evidence:** `fno/notify.py:17,51-80` isolates the `FNO_SLACK_*` names, but accepts `FNO_SLACK_CHANNEL_ID` override from the environment and a potentially unscoped webhook; using `FNO_*` alone does **not** guarantee delivery only to `#fno-desk`. `docs/stories/E-paper-desk.md:62-80` expressly requires the fixed desk channel and forbids `SLACK_*` use.

**Fix:** Delete the old image uploader and reports. E2's new text-only `DeskReportPoster` must enforce an allowed channel identity (including for configured overrides and webhooks), isolate secrets, redact credentials in error logs, and test that a wrong channel or an unverified webhook is refused. Reusing a small safe `chat.postMessage` helper is permissible; keeping `fno/notify.py` as a legacy brief interface is not.

### 12. [SHOULD FIX; strong evidence] Seven acceptance criteria omit a data/no-loss and scheduler proof

**Evidence:** `fno/storage/wiring.py:53-60` fixes A4's repository quote folder. `fno/live/quote_recorder.py:82-87,98-113,146-159` creates immutable attempts and canonical markers; loss or rewrite of these changes the historical price evidence. `CLAUDE.md:35-42` describes an **external scheduled session** that installs both requirements files, runs `python -m fno quotes record`, commits `research/data/quotes/` and pushes main. The scheduler is not represented by `fno/deploy/*` or root `deploy/*`; removing the latter must **not** be confused with deleting the independently running 3 pm routine. Clean-slate criterion 7 checks command/output paths only, not execution environment, executable output schema, jobs, or calendar behavior.

**Fix:** Add acceptance criteria 8–11:
8. **Data immutability:** compare a pre-cleanup manifest of all existing `research/data/quotes/**`, `research/data/calendar/**`, `research/data/events/**`, `research/data/nifty-panel/**` if present, `research/LEDGER.md`, approved studies and `accounting/**`; no tracked bytes/hashes lost or rewritten (explicit, approved exception list only).
9. **Recorder integration:** in a clean environment install `requirements.txt` and `requirements-groww.txt`; offline fake Groww + NSE expiry fixture tests for normal, duplicate, incomplete, holiday, unusual sessions, fallback, and no order calls; assert stable artifacts and real command status. Treat external live-provider execution as separately verified, not proof by sample.
10. **Scheduled-session audit:** independently inspect the active 3 pm scheduler's actual prompt, repo/ref, working directory, command, credential availability, requirements and commit/push targets; confirm it still exists and targets `main`; if it relies on any old deploy code update safely first. An unchanged command string alone is insufficient. Do not pause/delete it for cleanup.
11. **Legacy isolation:** no active scheduled, deploy, GitHub Actions, docs-driven or CLI path can run, publish or write old desk or old journal results; keep archival replay pinned to old SHA only. Check exact files and command inventory. Reconcile any remaining `docs/DESK_DESIGN.md:325` E4 references before judge pass.

## Direct answers to the seven questions

1. **Marked remove but required by an approved story or §12?** No entire rejected live/backtest/news module needs to remain operational. However, **E4's per-account lock and restart requirements** survive via §12.6 / E1-D3; **A1's existing trading-session calendar specification** must underpin E1 and A4; historical positioning availability and 30-day IV provenance must be assigned to B6/F1/B1/§12. The legacy `research/2026-10-12-backtest/replay.py` is intentionally not runnable on new main: document pinned-checkout reproduction.
2. **Marked keep but actually old?** `fno/providers/base.py:50-61` (`forget`, `live_quote`/last-price fallback), `fno/models.py:45-52` (`fill_price`), chart-only `fno/analytics.py:140-168`, obsolete `fno/constants.py` enums/flags, profile merge `fno/config.py:25-40`, and some Yahoo/context/weekly-sample paths deserve function-level cleanup. Preserve reusable pricing/IV, source methods, `quote_book`, storage and tests.
3. **§4a dependencies accurate?** Broad **production** picture is credible: old `fno/cli.py`, `fno/providers/groww_check.py`, old `fno/live/quote_cli.py` through old `services.py`, and the replay script are concrete couplings. But literal dotted `grep` is **not adequate** for relative imports; must test via AST/import closure. The nine GitHub code-search strings produced empty results; therefore this review **does not certify** a repository-wide clean negative grep.
4. **§4b logic?** Trading-day calendar: **change** to reuse A1 authoritative source and special sessions. Slack: replacement acceptable with hard channel/credential controls. Participant OI: removal acceptable conditional on a documented later source and availability checks, not “no data lost” as fact. IV history: removal acceptable conditional on historical-vs-forward IV and forecast expiry methodology. Old kill switch, feeds and market clock otherwise not needed for new 3 pm book.
5. **Drop E4?** **Yes as an old/new desk coexistence story; no as deletion of its multi-writer guarantees.** §12.6 must stop citing a nonexistent E4.
6. **Seven criteria sufficient?** **No.** Add the four judge-proof criteria in finding 12, strengthen static imports/CLI with relative-import parsing, and provider choice/integration checks in findings 1–2.
7. **A4/schedule risk?** **Material.** Provider-selection regression is presently explicit in config/code. The 3 pm routine invokes the unchanged command but relies on imported composition, dependency install and preserving existing quote paths; audit it separately. The proposed cleanup should **not delete or suspend** the A4 scheduler.

## Agreements and limits

**Agreed (strong evidence):** Remove old options-buying engine, kill/exit policies, Yahoo simulated backtest, legacy brief/HTML/Slack-image publishing, old shadow journal, desk PC watchdog and obsolete tests; keep data-source abstractions, Groww quote books, real NSE daily readers, analytical pricing, the A4 quote recorder, immutable recordings and judge records. Do **not** delete untracked/remote account state as an inference from git alone. Historic `research/2026-10-12-backtest/` and reports should remain as labelled evidence.

**Verification limit:** Examined GitHub's complete 381-entry `main` tree and directly fetched relevant source/test/story files. This was a static review via the GitHub connector, **not an executed pytest/ruff run or a locally executed import scan**. The external 3 pm scheduled-session definition was not accessible through GitHub; its active configuration is **not verified**. No claim of an actual passing cleanup build or current external job health is made.

**Confidence:** findings labelled above: **strong evidence** when source lines directly show the problem; **some evidence** where implementation consequences depend on untested runtime conditions; **reasoning only** for unverified future archive availability.

**Final verdict: AGREED WITH CHANGES** (blocking 1–4; should-fix 5–12). Owner D3 is sound; update the design and judge gates before deleting anything.
