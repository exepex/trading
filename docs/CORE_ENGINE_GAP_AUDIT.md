# Core engine and data capture: gap audit (16 Oct 2026)

Read-only audit of `exepex/trading` at `origin/main` ef517d21 (16 Oct 2026). Sources: docs/WORK_REGISTER.md,
docs/DESK_DECISIONS.md (last rows), docs/BUILD_MAP.md, docs/design_v2/REPLAN*.md and 07_ai_team.md, docs/stories/*,
reviews/judge/README.md, .github/workflows/*.yml, `gh run list` (recent run results), CLAUDE.md, research/data/,
conversations/2026-10-16.md, and the story branches named below.

Labels: **[strong]** = read from files, git history or run logs; **[some]** = inferred from partial evidence;
**[reasoning]** = judgement only.

Owner rule applied (16 Oct, via the coordinator): internal data (recomputed figures, scores, re-evaluations) can be
regenerated, so it ranks low. **External data captured now, in good health, ranks first.**

---

## Part A. External data sources: live capture, health, daily loss

"Lost daily?" means: is point-in-time history lost for every day it is not captured? Yes = it cannot be fetched
later. Partly = the values can be fetched later, but not the time they were first seen, or not the bid/ask.

### A1. Captured live today

| Source | What captures it | Health (recent runs) | Lost daily if it stops? |
|---|---|---|---|
| NIFTY monthly options at 3 pm, Groww (188 contracts, bid/ask/depth) | 3 pm Claude routine (CLAUDE.md steps 1-4; A4/A4b). Raw data in Drive; sidecar and `.canonical` in repo | Complete on 14, 15 and 16 Oct (`research/data/quotes/groww/.../2026/10/`) [strong] | **Yes.** Bid/ask exists nowhere else. NSE bhavcopy has closes only |
| NIFTY monthly options at 3 pm, NSE public chain | The same routine (`quotes record --source nse`) | Complete on 16 Oct (188). The separate `quote-recorder-nse.yml` cron **failed on 14 and 15 Oct** (it is superseded by the routine step) [strong] | Yes |
| BANKNIFTY, FINNIFTY, MIDCPNIFTY at 3 pm (A4c) | Code and CLAUDE.md step 3b are on main | **Not recorded yet.** The code reached main's first-parent at about 15:37 IST on 16 Oct, after that day's run. There is no `banknifty_*` sidecar in the repo. The first run is due 19 Oct and is unproven [strong for the absence, some for the timing] | **Yes.** 14-16 Oct are already lost |
| NIFTY 15-minute marks: spot, near future, weekly and monthly chains within 6% (A16) | A16 Claude routine (owner-created). Raw data in Drive; slots, heartbeat and RV in repo until O9 step 2b | Trial day 1 (16 Oct): **13 good, 10 incomplete, 3 missed** (09:15-09:45). Causes: duplicate runs (fixed by O9 step 2a, 3db04211) and a first-mark bug (fixed by A16f). RV void on day 1 by construction [strong] | **Yes.** The missed 09:15-09:45 quotes on 16 Oct are gone for good |
| F&O bhavcopy (UDiFF) and NIFTY panel (A13) | `panel-days.yml`, 21:41 and 12:11 IST | All scheduled runs succeeded on 14 and 15 Oct [strong] | No. NSE keeps an archive (A1, A11 handle rewrites) |
| Index closes, NIFTY 50 and India VIX close (O6) | `index-closes.yml`, 3 runs a day | All succeeded. Starts run 4-5 h late (19:22 UTC for a 15:41 UTC cron) [strong] | No (NSE archive) |
| NSE SPAN margins (A14) | `nse-margins.yml`, 03:30 and 07:45 IST | **Only one scheduled run ever started** (16 Oct 07:12 UTC = 12:42 IST, about 5 h late). The 03:30 IST cron did not start. 15 Oct was dispatched by hand [strong] | Partly. NSE archives SPAN files (A14c reads them), but the margin as of the morning is not stored |
| Stressed-margin factor (A14c) | `stress-factor.yml`, Sunday 10:00 IST | First full run on 16 Oct (df9bfaff) set k = 2.1. Per-family k was decided the same day, not built yet [strong] | No (derived) |
| Participant-wise OI (A8) | `participant-oi-release.yml` and `participant-oi-watch.yml` | The release runs succeed. Each evening's second slot shows **cancelled** (14 and 15 Oct). The A8 measurement waits for 20 release days [strong for the cancels; cause not checked] | Values: no (NSE archive). Release-time evidence: yes |
| FII/DII cash and FPI daily (P8) | `flows-download.yml`, 21:10 IST | Succeeded on 14 and 15 Oct [strong] | Partly. NSE pages are daily and are not always archived [some] |
| CM bhavcopy, delivery, corporate actions, EQUITY_L, Nifty 500 list, symbol changes (P6) | `market-publish.yml`, 07:10 IST (`market archive`) | Succeeded daily [strong]. Corporate actions, EQUITY_L and Nifty 500 are "one copy per day from 13 Oct" (DATA_SOURCES.md) | **Yes** for corporate actions and list versions: NSE overwrites them in place |
| Company filings, Nifty 500 (A12) | `filings-archive.yml`, every 6 h | Succeeded (6 of 6 recent runs) [strong] | Partly. Filings stay online; first-seen time and revisions do not |
| AI books' v2 forecasts (G5) | `forecast-capture.yml` fires the routines | On time for the first time on 16 Oct (sealed 15:11). 14 Oct had no submission, 15 Oct was about 12 s late [strong] | **Yes** (an AI answer cannot be re-asked without hindsight) |

### A2. Built, but not captured daily (no schedule)

| Source | State | Lost daily? |
|---|---|---|
| Global cues A17: US closes (Drive only), US 10-year, Brent, USD/INR (FBIL/RBI) | Built and back-filled. A17's scope says "Out: a schedule". The last data commit is 15 Oct, and no workflow calls `global-cues` [strong] | Partly. Values can be fetched later, but first-seen time is lost, so the 09:15 and 15:00 cut-offs cannot be proven. The FBIL table needs care [some] |
| India VIX OHLC table (A15) | Back-filled. Daily close comes from index-closes. OHLC "monthly `fill` by hand" [strong] | No (NSE archive) |
| Groww 15-minute candle back-fill (A16b) | Ran once as a back-fill (to 14 Oct). On 16 Oct it was a one-shot scheduled task. No daily schedule [strong] | Partly. Groww served expired Aug/Sep 2026 contracts on 15 Oct; how long it keeps them is unknown [some] |
| Groww broker margin per structure (A14c part 2; STR1b-2's "owner's dated margin check") | Not built [strong] | **Yes.** The broker's margin on a given day cannot be asked later |

### A3. Not captured at all (no story, or a story text only)

Ranked by how much history is lost each day.

| # | Missing external source | Who needs it | Lost daily? | Story |
|---|---|---|---|---|
| 1 | **News and announcements, timestamped** (market, macro, company, NSE/SEBI) | AI team analysts (F2, 07_ai_team 7.2), devil's advocate, LR2 | **Yes.** True first-seen time cannot be rebuilt later | none (BUILD_MAP: "F&O news waits until its source ... named") |
| 2 | **NSE and SEBI circulars** (margin method, lot size, contract changes, F&O rules) | C2/C4, A14, STR1, the factory's "who pays" | Yes (dates can be found later; the notice time is fuzzy) [some] | none ("NSE circular changes: accepted as a known limit", DESK_DECISIONS 15 Oct) |
| 3 | **BANKNIFTY/FINNIFTY/MIDCPNIFTY intraday marks**, and NIFTY strikes beyond 6% intraday | Book 3's wider universe later, LM1 for far legs, BR1 | Yes | none (A16 is NIFTY within 6% only) |
| 4 | **Stock-option quotes, bid/ask** | A18 / R2 | Yes | A18 paragraph only. R2 was screened out by R1b, so it is low now |
| 5 | **Economic calendar beyond RBI/Budget**: India CPI/GDP, US FOMC/CPI/payrolls, election dates, index-heavyweight results dates | Weather drivers, macro analyst, M1 "event in window" | Partly. Dates are recoverable; `announced_on` is only valuable when entered on the day it is announced | A6 is hand-kept: 61 rows, budget and rbi_policy only, last edited 12 Oct [strong] |
| 6 | **F&O ban list, lot-size master (`fo_mktlots`), contract master** daily | C4 (lots), stock-option ideas, STR1 | Partly. NSE overwrites them [some] | none |
| 7 | **91-day T-bill yield** (S6 cash rate) and the repo rate | S6 do-nothing benchmark | No (RBI archive) | one-time step at the S1 freeze |
| 8 | **SEC filings / US company data** | Nothing in the F&O design needs it [strong: no story or design row asks] | n/a | Not needed (US closes only, via A17) |
| 9 | **Market depth beyond top of book; full NIFTY chain at 15:15 and 10:15** (E3/E8 fill snapshots) | E8 fills, RM1 condition 4 | Yes | Covered by A16's 15:15 and 10:15 marks within 6%. Legs outside 6% are not covered [some] |

---

## Part B. Core-engine stories end to end

### B1. Existing stories (owner from WORK_REGISTER, status from the judge index and git)

| Area | Story | Owner session | Status |
|---|---|---|---|
| **Daily run (all books)** | **O1** daily desk routine (`story/o1-daily-run`) | 014zYLf18PgCzR7YoHs1X5Dp | Judge 178 add. 18 **PASS, may merge once main is green**. Main is red: 3 risk tests read the 2.1 `stress_factor.csv` row. After merging, every `daily.live_from` flag (margin_check, weather, forecasts_v4, card) is still null, and the owner must create the routine [strong] |
| Daily run | O2 failure handling | 014zYLf18 | Story text; code after O1 |
| Book 1 | D1-D3, D3b, D6, C2-C5, E2-E7, E2c, E2d, E4c, E4d, E5, E5b, S2, S3, S6, F9a, RM1 | various | Merged. **None of it runs**, because O1 is not live [strong] |
| Book 1 fills | **E8** owner-timing fills (`story/e8-code-part1`) | 01H1CmuWzBtbtjzoQNJUz2Dz | Part 1a and 1b PASS (judge 203 add. 1, 3-4); **not merged** (+74 commits) [strong] |
| Book 1 | E6b missed executions | 0134MoC6f7aAJVcHRBiyATo6 | Text merged; code waits for E8 |
| Book 1 | C5b brake restart (`story/c5b-restart-decision`) | 012eM7Ti (C5/E1b builder) [some] | Open branch, not merged |
| Book 1 | STR1b-2 activate one- and two-leg structures | 01BYjW9auJnoiMQoH2WYVwYJ | Not started; needs the owner's dated margin check |
| Strategies | **R1** factory: R1a merged (judge 261); R1b (`story/r1b-screens`) PASS (judge 266 add. 1), not merged; R1c shadows **paused "for the owner's mockup review"** although it is backend | 01XFXpbkyixX7SuXeQCp5EnX | Some. R1c's pause looks wrong under the 16 Oct "no UI" rule [reasoning] |
| Strategies | **R3** forward shadows (B0) | 0145TfSwzmpk6MBrH92f5h4G | Part A merged; part B code waits for E8 part 1b |
| Book 2 | **D4** envelope code (`story/d4-envelope-code`) | 01SFDjjZx7JYziM3jqJytG2z | Judge 260 add. 1 **FAIL** (an unproven-limit B in `eligible`). Fix 094f7a97 awaits re-judge. The register row still says "text only" (stale) |
| Book 3 | **D5** constitution and registry (`story/d5-constitution-code`, built on D4) | 01SFDjjZ | Judge 263 add. 1 **PASS**, merge only after D4 |
| Book 2 | F5 decider | none | "later" (text from the first plan) |
| Book 3 | F6 decider and pilot; F7 matched shadows | none | "later" |
| Books 2-3 | F1 trading part (isolated decision sessions, receipt and promotion deadlines) | none | Forecast part done; trading part "later" |
| Books 2-3 | F2 role agents and finding cards (REPLAN: cut to the 07_ai_team analysts) | none | "later" |
| Books 2-3 | F4 AI judge (changed: overrides dropped) | none | "later" |
| Books 2-3 | D3 refusal of a non-empty `owner_override` (must land before any Book 2/3 paper decision, D4 table) | none ("builder settled then") | Not built. `owner_override` is still a D3 field on main and on the D5 branch [strong] |
| Books 2-3 | S3 reads the shadow `chosen_action` (D4's shadow-only actions) | 0185gR5DmoDh2zBAvgRU4CEB (S3 builder, "at slice E") | Not started |
| Books 2-3 | F8 part 2 (per-book AI cost in C1 and S2's port) | none | Later |
| Books 2-3 | F9b role-value shadow firing | 01SFDjjZ (F9a builder) [some] | Slice E |
| Evidence | T2 (merged); **T3** devil's advocate on cards | 0145TfSw | T3 waits for T1 trade fields and O1 |
| Forecasting | **G6 v4 freeze** | 01MgTu3L1T3y6R18ATTwbFub | "Waits for the G6 session". This **blocks every live v4 forecast** (G7, M1 live, G11) |
| Forecasting | G7b parts b-d (implied baselines, V5, V4) | 0185gR5D | Part a merged; b-c wait for G10's pack |
| Forecasting | G10 part 2: the 14:30 v4 pack capture | 01VK88LxJvV1Gi7Wbr3D4fzp | After A4c is live |
| Forecasting | **G11** AI books on v4 (v2 prompts with BG1 timing) | 01XFXpbk | Text PASS (judge 206 add. 5); code after the v4 freeze |
| Forecasting | M1 live weather | 013xqaNTCbSBytKgqpfaYFqZ | Code merged; live only through O1's `live_from.weather` (null) |
| Evaluation | S1 freeze; LR3 drift code (01SFDjjZ, after O1); LM1 (012eM7Ti, round 1 PASS, round 2a waits for A16's observer, judge 265 FAIL); M2 (0145TfSw, text) | as listed | in flight |
| Data | A16 mark observer port | 01VK88Lx | Judge 265 FAIL (one should-fix) |
| Data | A14c part 2 (Groww margin check) and per-family k | 01Vm1WnH8i9waM8EJG8zwWqg | Part 2 after part 1 (merged). Per-family k decided 16 Oct; no register row yet [strong] |
| Data | O9 data to Drive (steps 2b and later) | 01WHmxEY7WLVTSbNi1Z2adZw | Step 2a merged; 2b due 18 Oct |

### B2. Stories that do not exist yet and must be written

1. **Books 2 and 3 in the daily run.** O1's `DAILY_RUN_STEPS` has a `book1` step only; there is no step for Book 2 or Book 3 [strong]. A story is needed to fire the AI book decision sessions, collect, validate, run C2/C4 and join E8 fills. This is F1's trading part plus an O1 step. **F1 trading has no owner.**
2. **Rule default in the private pack.** Book 2's private pack must carry D2's precomputed rule default and eligible set (F5's design assumes this; E2's private pack does not do it today) [some].
3. **F5 rewrite under design v2.** It must fit D4's narrow v1 envelope (veto, width, lots, choose_strategy), the "no override" rule and the estimand label. The first-plan text predates D4 [reasoning].
4. **F2 rewrite as analyst roles** (volatility, macro/global cues, positioning, equity research), with the card schema and `agents/roles.yaml`. No prompt exists except the two forecaster prompts (`agents/forecast/*_v1.md`) [strong].
5. **F6 rewrite.** Book 3's portfolio manager and strategy proposer flow on D5's registry: propose on day d, register by code, trade from d+1, pilot label.
6. **F7** matched shadow file: rewrite to D4's action vocabulary.
7. **D3 `owner_override` refusal** for every book (an owner decision of 16 Oct, with no builder).
8. **AI-usage capture for the AI book routines now.** `accounting/ai_usage.csv` has one row (the post-mortem), and none for the G5 sessions of 14-16 Oct. F8 says routine sessions "cannot be read from other sessions", so **that usage is lost for good**. G11 fixes this only after the v4 freeze [strong].
9. **News capture**: source, terms, first-seen time, Drive storage (Part A3 #1).
10. **NSE/SEBI circular capture** (Part A3 #2).
11. **A17 global cues on a schedule**, plus the A16b daily candle catch-up and the VIX OHLC daily append (small; these are Part A2's "built, not scheduled").
12. **Economic calendar automation** (A6 extension: India and US macro dates with `announced_on` captured on the day).
13. **Daily F&O master files**: ban list, lot sizes, contract master.
14. **Price-level forecast and valuation record (optional).** No question forecasts a NIFTY price range or distribution: v2 Q1 is direction only, and v4 is movement size. There is no daily record of fair value or IV surface. Both can be rebuilt from captured quotes, so they rank low [reasoning].
15. **G12 house forecast, LR2 why-wrong reviews, S4 monthly report.** These are REPLAN paragraphs only, with no owner; they are internal and can be done later.

---

## Part C. Book 2 (hybrid) engine: what exists, what is missing

**Exists on main [strong]:**
- Book 2's forecast-only routine (G5): prompt `agents/forecast/book2_hybrid_v1.md`, `fno/ai/` (fire, collect, seal, audit, envelope for forecasts).
- C4 fails every Book 2 trade closed (`fno/checks/wiring.py:78`, `WaitsFor("envelope","D4")`).
- D2/D3/D6, E1 accounts, and E4/E8 fills (E8 not merged).
- F9a role-value scoring and S3 scoring code.

**On a branch:** D4 envelope (`story/d4-envelope-code`: `fno/playbook/envelope.py`, `envelope_files.py`, `fno/checks/validity_envelope.py`, 831 lines added). It is off and fails closed. Judge 260 add. 1 FAIL; fix pending.

**Missing for end-to-end paper decisions:** D4 re-judge and merge → D3 override refusal → rule default in the private pack → F2 analyst cards (or decide Book 2 v1 runs with no cards) → F5 decider prompt and output schema → F1 trading-session runner (receipt and promotion deadlines, C2/C4) → O1 step → E8 fill → S3 shadow-action reading → F8 part 2 cost lines. F3/F4 are optional for v1 (T3 reuses `fno/advocate`). **Nothing past D4 has an owner.**

Note [reasoning]: there is no approved strategy (`playbook/registry.csv` holds only B0, status research). So Book 2 would record "no approved strategy" daily even when built. The owner's 16 Oct row accepts "built and judged now, switched off until a strategy qualifies".

## Part D. Book 3 (AI team) engine

**Exists on main:** the Book 3 forecast routine (G5, `book3_ai_v1.md`); `BOOK3_FOLDER` reserved; C4 closed (`WaitsFor("constitution","D5")`).

**On a branch:** D5 (`fno/book3/constitution.py`, `registry.py`, `spec_rules.py`, `wiring.py`, `fno/checks/validity_constitution.py`). PASS, waiting for D4.

**Missing:** F6 decider and strategy proposer, F7 shadows, F2 cards, F1 trading runner, O1 step, G11 (v4 AI forecasts, after the freeze), F8 part 2, F9b.

**AI team roles: code versus design only** (design_v2 07 section 7.2) [strong]:

| Role | State |
|---|---|
| Forecasters (Hybrid, AI team) | **Code, live** (G5, v2 questions) |
| Devil's advocate | **Code** (`fno/advocate`). Live only on the weekly post-mortem; T3 card objections are not built |
| Post-mortem writer | **Code, live** weekly (LR1, `postmortem-weekly.yml`; one run, week ending 10 Oct) |
| Volatility analyst, macro and global-cues analyst, positioning analyst, equity research analyst | Design only (F2 "later") |
| Portfolio manager (Book 3) | Design only (F6) |
| Idea generator | Design only. R1 has idea cards written by hand, no AI generator |
| Red team (F3, now T3) and AI judge (F4) | Design only |
| Code roles: C1, C2, C3, C4, BG1 stop-rule meter | Code, merged. CUSUM (LR3) is text only |

## Part E. Data inventory (internal and generated data)

Key: (a) live daily; (b) built, not scheduled; (c) back-filled only; (d) not built.

| Data | State | Runs it |
|---|---|---|
| 3 pm NIFTY quotes | a | 3 pm routine |
| 3 pm other indices (A4c) | b (first run 19 Oct) | 3 pm routine step 3b |
| 15-minute marks A16 | a (trial) | A16 routine |
| NSE margins | a (unreliable start) | nse-margins.yml |
| Bhavcopy, panel | a | panel-days.yml |
| India VIX close | a | index-closes.yml |
| India VIX OHLC table | c | hand `fill` |
| Global cues A17 | c | none |
| Participant OI A8 | a | participant-oi-*.yml |
| FII/DII P8 | a | flows-download.yml |
| Filings A12 | a | filings-archive.yml |
| Weather M1 | c (to 14 Oct, `backfill_exploratory`) | none (O1 `live_from.weather` null) |
| Forecasts v2 rules (G3) | a | forecast-capture.yml |
| Forecasts v2 AI (G5) | a | forecast-capture.yml + routines |
| Forecasts v4 rules (G7 V6, V2, V3, V7) | c | none until the v4 freeze |
| Forecasts v4 AI (G11) | d | — |
| Scores G4 | a | forecast-scores.yml |
| Scores G8 v4 | b/c (exploratory, inside the weekly post-mortem) | postmortem-weekly.yml |
| Paper decisions D2/D3 (Book 1) | b | none (O1 not merged) |
| Packs E2 | b | none |
| Fills E4/E8 | b (E8 not merged) | none |
| Trade marks E2d | b | none |
| Scorecards E6 | b | none |
| Scoreboards S2/S3 | b | none |
| Budget / AI usage F8 | b. Only 1 row; book routines not captured | hand `budget record-usage` |
| Role value F9 | b (no roles to score) | none |
| Research ledger, factory gates R1 | a by hand (R1a) | CLI |
| Shadows R3 | b/d (part B not built) | none |
| Evidence: cards T1, objections T3, finding cards F2 | T1 b; T3 d; F2 d | none |
| Price forecasts | d (v2 Q1 direction only) | — |
| Valuation (fair value, IV surface) | d. Only IV30 inside forecasts | — |

## Part F. What is lost forever if not captured now (ranked)

1. **The 3 other indices' 3 pm quotes.** 14-16 Oct are lost; confirm the 19 Oct run works [strong].
2. **A16 15-minute marks.** Every missed mark is gone. Day-1 completeness was 13 of 26 [strong].
3. **AI routine usage minutes.** Not readable afterwards. G5 runs every session [strong].
4. **News, with first-seen time.** Nothing is captured [strong].
5. **Broker (Groww) margins per structure** on given days (A14c part 2) [strong].
6. **NSE corporate actions and list versions.** Captured daily since 13 Oct through market-publish; keep that job healthy [strong].
7. **AI answers on v4 questions and AI decisions.** Lost once the engines exist; today Books 2/3 have no approved strategy, so the loss is small [reasoning].
8. **Global cues' first-seen times** (A17 has no schedule) [some].
9. **Circulars and the economic calendar's `announced_on`** [some].
10. **Forward paper days for B0 and the Book 1 decision records.** Forward days cannot be back-filled honestly. Book 1 has nothing approved, so the cost today is test coverage of the desk path, not results [reasoning].

Internal items (weather, v4 rule forecasts, scores, scorecards) can all be regenerated from captured inputs. They rank low, but they will only be labelled "back-fill" and never "live" [strong: M1 labels].

Health problems to fix (one line each):
- `nse-margins.yml`'s 03:30 cron did not start, and the run came about 5 h late.
- `quote-recorder-nse.yml` fails daily. It is superseded by the routine, so retire it or fix it.
- `participant-oi-release` second slot is cancelled every evening (cause not checked).
- `health-check.yml` has no runs recorded (O8 never ran) [strong from `gh run list`].
- Main is red (3 risk tests), which blocks O1's merge.

## Part G. Recommended next 10-15 backend stories

| # | Story | Reason (one line) | Owner exists? |
|---|---|---|---|
| 1 | Make main green (risk tests vs the 2.1 stress row), then **merge O1** and have the owner create the daily routine | Nothing in Book 1-3's desk produces data until O1 runs | Yes: O1 014zYLf18; test fix: A14c builder 01Vm1WnH |
| 2 | **D4 re-judge and merge, then D5 merge** | Book 2/3 gates exist only on branches | Yes: 01SFDjjZ |
| 3 | **D3 owner_override refusal** | Must precede any Book 2/3 decision (D4 table) | No |
| 4 | **F1 trading runner + O1 Book 2/3 steps** (new) | No daily path for AI decisions | No |
| 5 | **F5 Book 2 decider (rewrite) + rule default in private pack** | Book 2 end to end | No |
| 6 | **F6 + F7 Book 3 proposer, decider and shadows (rewrite)** | Book 3 end to end | No |
| 7 | **F2 analyst finding cards (rewrite to 4 roles)** | The "AI team" is today only forecasters | No |
| 8 | **Merge E8 part 1** (PASS) then R3 part B | Fills for every book and the first forward shadow | Yes: 01H1CmuW; 0145TfSw |
| 9 | **AI usage self-timing on current G5 prompts** (or pull G11's timing record forward) | Usage lost every session | Partly (G11 owner 01XFXpbk) |
| 10 | **v4 freeze (G6)**, then G7/M1 live capture and G10 part 2 pack | Every v4 forecast is back-fill only | Yes: 01MgTu3L; 01VK88Lx; 0185gR5D |
| 11 | **News capture story** (source, terms, first-seen, Drive) | Biggest external source missing; lost daily | No |
| 12 | **Schedule A17 global cues + A16b daily catch-up + VIX OHLC append** | Built but not captured daily | Partly (A17/A16b builder 01MBnbVU) |
| 13 | **A14c part 2: Groww margin check**, and the per-family k | Broker margins lost daily; k decision unbuilt | Yes: 01Vm1WnH |
| 14 | **NSE circulars, economic calendar, F&O master/ban list capture** | Point-in-time rules and dates | No |
| 15 | **Workflow health fixes** (nse-margins start, NSE recorder retire, OI cancels, O8 never ran) | Silent gaps in live capture | Partly (A14 owner 01Vm1WnH; O8 owner 012eM7Ti) |

Also: R1c (shadow records) is paused "for the owner's mockup review", although it is backend. Unpausing it fits the 16 Oct rule [reasoning].
