# G6 freeze. Protocol v4 frozen: `FREEZE_v4.md`, the slot rows, the ledger rows

**Repository:** trading · **Lane:** 1 (frozen files, forecast and score records) · **Builder:** session
`session_019rZrcu1GSqUC7PScqwQgo2` (orchestrator's assignment, 24 Oct 2026; the earlier owner, the R2/G7 builder
0185gR5D, is out of reach) · **Judge:** named by the orchestrator · **Branch:** `story/v4-freeze`

**Description:** As the statistician, I want protocol v4 frozen, with every file that decides a v4 baseline, outcome
or score byte-checked and every family slot registered before its first counted day, so that from Mon 26 Oct 2026 no
v4 result can shape its own rules.

**Why:** owner, 24 Oct 2026 (`docs/DESK_DECISIONS.md`, "The owner signs off protocol v4"): "Consider v4 sign off. So
activate all the features which were waiting for v4 sign off." The same row keeps section 10's rule: the freeze
hashes every file that decides a v4 baseline, outcome or score, so it lands once G7b's live V2 baseline code is on
`main` (target Sun 25 Oct, `Frozen on:` 25 Oct, counted from Mon 26 Oct). G11's AI books are switched on only after it.

**Does this change a trade or stop decision?** It fixes the stop rule's Test A (protocol section 6): the members,
their starts and the files that judge them. It places no trade. Said plainly: the freeze makes the record countable;
it makes no forecaster good (protocol 11 D: no v4 member is provable in useful time).

**Source plan:** response 287 (`reviews/claude/response_287_v4-freeze-plan.md` on `story/g6-v4-freeze` at 5ce466d58,
never merged; response 157 and 250 folded into it). Pieces 1 (protocol text), 1b-1d and 3 (slot file, freeze check,
no-implied-vol proof, M1's hash gate) are merged (judges 414, 430, 436). This story is piece 4, rebuilt on today's
`main`, plus what changed since: G10 completion merged, G7b completion and G11 in progress, the owner's 24 Oct rows.

## 1. What `research/forecasts/FREEZE_v4.md` will contain (modelled on `FREEZE_v3.md`)

1. **Title and protocol commit:** `Protocol commit: <sha>`, the commit that gives `PROTOCOL_v4.md` its final form
   (section 3 below). The record is a later commit; it names that commit and the SHA-256 of the protocol text at it.
2. **`Frozen on: <day>`** (the line G8's `LookRecords.frozen_on` reads, `records.py:20`) and **`First counted
   session: <S>`**, the first A7 `regular` session after it; planned 25 and 26 Oct, S held open for the owner (section
   5). If the merge to `main` slips past 25 Oct IST, both
   lines move to the merge's IST day and the next regular session before the merge, never back-dated (owner, 21 Oct,
   "v4 freeze answers" (1): "Frozen on = the day the judge passes the freeze and the owner signs; go-live = the next
   trading session"). Live rows made on or before `Frozen on:` (22-23 Oct today) are never counted.
3. **Preconditions as met** (section 4 below), each with its evidence: the judge's PASS (file and SHA); ChatGPT's
   review **not held: paused by the owner on 22 Oct** (DESK_DECISIONS "Cut-list accepted"; `docs/JUDGE.md` rule 9);
   the owner's sign-off (row of 24 Oct, quoted); items A-E (rows of 15 Oct, quoted); X of 1.6.
4. **Byte-checked table:** one row per file, path and SHA-256, printed by `tools/v4_freeze_table.py` from
   `freeze_check.byte_checked` (one list, so the record and the check cannot disagree). Contents in section 2.
5. **Recorded, not byte-checked:** path, SHA-256 at the protocol commit and why not checked (section 2).
6. **Settings v4 reads from `config.yaml`**, each with its value at the freeze and why it is not frozen (section 2).
7. **Slot registrations:** the 15 rows of `research/forecasts/v4_slots.csv` written in the freeze commit, copied
   verbatim (section 5).
8. **Ledger rows (B4):** the trial ids added to `research/ledger.csv` in the freeze commit (section 6).
9. **Owner decisions quoted**, each with its `docs/DESK_DECISIONS.md` row date and title (line numbers drift): 15 Oct
   A-C ("A accept, B accept, C accept"), D ("3 B"), E ("merge G6, E option 2"), miss caps ("Both 10%"), V6b scored,
   the v4 timeline; 16 Oct misses from `effective_start` ("Yes, from the declared start"), G11 replaces the v2 AI run
   ("A: v4 replaces v2"), A2 dropped (orchestrator ruling); 21 Oct "v4 freeze answers"; 24 Oct release by 14:45 ("1 -
   Option A"), `system_late` warns ("2 - Option A"), W3 both yardsticks, W8 ("W8 - yes"), v4 pack live Monday, the
   sign-off; and G7b's wordings W1-W8 as they land in the protocol.
10. **Disclosure (protocol section 8):** every exploratory back-fill and every pre-freeze score run, each with its
    source, forecaster and question, first and last day, row count, method SHA-256 and the SHA-256 of its
    `backfill_exploratory` rows, as of the freeze commit's parent; plus the pre-freeze live rows (22 Oct onward) and
    G8's pre-freeze reports (`research/forecasts/v4_scores/2026-10-10`, `-17`, `-24`). Printed by the freeze tool
    (criterion 9), never typed by hand. Today's sources, checked on `main` 2e6603f9: `research/forecasts/v4/` (G7:
    `base_rate`, `trailing`, `ewma_094`, `har_daily`, `v6_ewma_t4`, `v2_close_blend`, `v3_close_blend`,
    `v7_vix_vs_mean20`, 2017-01-03 to 2026-10-15, 2,410 back-fill rows per file; M1: `weather_vix_v1`,
    `weather_checklist_v0` to 2026-10-19, 2,412 rows; M1's `weather/` day files 2017-2025), and G7b's Drive back-fills
    (EOD IV30 proxy, raw and premium-adjusted implied, V4/V5, part f) by their receipts, if archived by then (none
    under `receipts/data/v4` on `main` today; the record then says "none archived").
11. **Known limits:**
    - **Replay libm limit** (register row, judge 508): `math.erf`'s last bit differs between glibc 2.39 (sessions) and
      2.43 (Actions since 21 Oct), so G1 v3's byte-comparing `forecast-scores replay` can say "not reproduced" on a
      post-21-Oct day; `fno/forecast_scoring/replay.py` is byte-checked by `FREEZE_v3.md`, so no edit; until v3's
      next version such a result is checked by hand for last-bit-only differences. The freeze's platform is recorded:
      Python, numpy and glibc versions of the session that ran the freeze tool (today 3.13.17, 2.5.3, 2.39).
    - **v3 silent git read** (register row): `fno/forecast_scoring/wiring.py`'s `last_commit` reads a failed
      `git log` as "", which fails closed (NotFrozen). v4 does not use it; v3's next version fixes it.
    - **2027 calendar missing:** NSE's 2027 rows are not in `nse_sessions.csv`; from Tue 22 Dec 2026 V4's terms, from
      29 Dec V5's, are void until they are added (G7b's limit); the stop-rule review date rests on a weekday fallback
      until then (section 7).
    - **Not byte-checked by design:** shared files in item 5 and the settings in item 6 (each says what protects it).
    - **The check is a test and the look's refusal** (criterion 4), not a guard on every daily write: a change to a
      frozen file between two looks turns CI red and stops the next look; rows written meanwhile by changed code
      carry its method hash and are found by G7's and M1's hash gates.
12. **What a change means:** any change to a byte-checked file, or a new file in a byte-checked folder, is a new
    version (v5's own record), never an edit of this one.

## 2. The file lists (section 10 of the protocol, widened to every file that decides a v4 baseline, outcome or score)

**The rule (round 2, judge 597 SF3 and its import-walk note):** every file is classed by what its bytes do, and an
import walk proves the classes cover everything, so no file on a v4 input path is missed by hand (judge 596 found
three such: A16b's `candle_rv_table.py`, `rv_table.py`, `row_files.py`).
- **Byte-checked** (`freeze_check.BYTE_CHECKED_GLOBS`): v4's own files whose bytes decide a v4 value. A change breaks
  the freeze: the look refuses (criterion 4), a new version is needed.
- **Recorded** (`freeze_check.RECORDED`, path -> reason): files shared with other stories or other versions whose
  bytes still decide a v4 value. The record holds each SHA-256 and reason; every v4 report prints one line per
  recorded file changed since the freeze (criterion 12), so a change is seen, never silent. The reason names the
  lock: an earlier freeze that already byte-checks it, a hash carried in every record (the pack's `iv30_method`), or
  the tests that pin its behaviour.
- **Not deciding** (`freeze_check.NOT_DECIDING`, path -> reason): composition roots, storage, alerts, clocks and
  readers that move bytes without computing a v4 value. Named in the record, not hashed; the walk stops at them.
- **The walk (criterion 11):** from every byte-checked and recorded module, every `fno` module it imports (top-level
  or inside a function) must be in one of the three classes; a stale entry (reached by nothing, or in two classes)
  fails too. Modelled on S1's `tests/evaluation/test_scoring_closure.py` (judge 229), whose `imported` helper it
  reuses. The walk is re-run on the merged tree with G7b and G11, so their new imports are classed before the freeze.

**Byte-checked:**

| Files | Why | On `main` now? |
|---|---|---|
| `research/forecasts/PROTOCOL_v4.md`, `PROTOCOL_v4_calibration.md` | the protocol | yes; final wording missing (section 3) |
| `fno/forecast_v4/*.py` | every rule and number (G6); **new:** `pricing.py`, the rate (below) | yes |
| `tools/v4_*.py`, `research/forecasts/v4_*.json`, `v4_*.md`, `tests/fixtures/forecast_v4/v4_golden.json` | calibration tools and tables, golden example | yes |
| `fno/forecast_v4_rules/*.py` | G7 and G7b: baselines, rule forecasters, outcomes' series, records, the pack capture, W8's ratio window reader | **partly**: G7, G7b part a, b1, steps 3-4 merged (62023dbdd); steps 5-6 on `story/g7b-completion` (3033da0c9); the `Pack` adapter, `forecast-v4 capture-pack`, the V4/V5 outcome and proxy-drift writers not built |
| `fno/forecast_scoring/v4/*.py` | G8: scoring, comparisons, looks, day labels, deadlines, this check | **partly**: G10 completion merged; G7b's `drive_forecasts.py` and its `inputs.py`/`wiring.py` edits on the G7b branch |
| `fno/forecast_scoring/scores.py` | G4's log-score clip and bins in v4's reported scores (judge 177) | yes |
| `fno/intraday/realised_vol.py`, `session_rv.py`, `status.py`, `slots.py` | A16's V1 arithmetic and void rule (judge 177) | yes |
| M1's `METHOD_FILES` (`fno/weather/wiring.py`) | V6's `rules` slot (decision 70) | yes |
| **new:** `fno/v4_pack/*.py` | G10's pack, release, day labels (`system_late` days are out of scoring), 15:10 deadline (late = miss), the pack binding guard; the pack's IV30 is V2's raw and premium-adjusted input | yes, but **G10's `story/v4pack-rehearsed-live` changes `wiring.py` and must land before the freeze** (blocker 6) |
| **new:** `fno/quotes/v4_extras.py` | the `v4` window's V4 expiry and future quote (G10 completion 3a), v4 only | yes |
| **new:** `fno/ai/v4_*.py`, `agents/forecast/book2_hybrid_v2.md`, `book3_ai_v2.md` | G11's v4-only files: which AI book-days become rows or misses, the pack binding, the slots' registration; the prompts are the registered forecasters | **no**: `story/g11-ai-books-v4`, to merge tonight; G11's builder confirms through the orchestrator |

**Recorded (shared; each with its lock), the rulings so far** (the walk adds every other reached file, each with a
one-line reason in `freeze_check.RECORDED` or `NOT_DECIDING`, listed in the record):

| File | Decides | Shared with | Lock |
|---|---|---|---|
| `fno/constants.py`, `fno/desk/settlement.py`, `fno/research_data/calendar.py`, `fno/research_engine/implied_vol.py` | names; V5's settlement; the session set; Black-76 | every story | section 10's own list; v4's tests (`tests/forecast_v4/`), v1/v2 golden values for Black-76 |
| `fno/forecast/iv30.py`, `fno/research_engine/volatility_features.py`, `close_series.py`, `fno/research_data/panel_reader.py`, `fno/forecast/live_pack.py`, `fno/research_data/quote_snapshots.py` | the EOD IV30 proxy (premium ratio window) and the live IV30's parts | G1 v1-v3 | **byte-checked by `FREEZE.md`/`FREEZE_v2.md`/`FREEZE_v3.md`** (strongest lock: their tests fail on any edit) |
| `fno/research_engine/live_features.py`, `features.py`, `event_features.py` | the pack's live ATM IV30 (V2's raw and premium-adjusted input) | the desk (B7) | the pack's `iv30_method` hashes their bytes in every pack (`v4_pack/wiring.IV30_METHOD_FILES`), so a pack made on changed code names a different method; v2's golden cases |
| `fno/quotes/quote_validity.py` | W5's "live two-sided quote" for V4/V5 legs and the future | A4's 3 pm quotes | G7b's live-quote tests (`tests/forecast_v4_rules/`) |
| `fno/research_data/expiries.py`, `fno/analytics.py` (`norm_cdf`) | V4/V5 expiries; V5's option-implied probability | the desk, G13 | G7b's terms and probability tests (hand-computed values) |
| `fno/storage/creation_times.py`, `fno/storage/raw_source.py` | V5's `first_seen_at` and settlement file path | O9, E7 | G7b's outcome tests |
| `fno/intraday/rv_table.py`, `candle_rv_table.py`, `row_files.py`, `document.py`, `snapshot_files.py`, `clock.py`, `ledger.py` | V1's outcome rows; W8's ratio window (A16b's candles, `backfill_window`, judge 596); the pack's clock check | A16, A16b, G14 | A16's and A16b's tests; G7b names the W8 reader module (asked through the orchestrator) |
| `fno/ai/versions.py`, `fire.py`, `outcome.py`, `scoring_gate.py`, `stop_rule.py`, `run_terms.py` and their AI imports (`answer.py`, `envelope.py`, `seal.py`, `submissions.py`, `timing.py`, `transcript_audit.py`, `audit_plan.py`, `draw_seed.py`, `coverage.py`, `rules.py`, `paths.py`, `pointer.py`) | the AI books' records, misses, versions | the v1/v2 AI run (G5) | hashed in the record's "AI registration" table with G11's slot rows (owner, 21 Oct (3), second half; judge 597.1 m2); G11's tests; each AI row carries its prompt hash |
| `fno/ai/receipts.py` | GitHub push times behind the 15:10 deadline (late = miss) | F1, O8 | the deadline tests (`tests/v4_pack/test_deadline.py`) |

**Not deciding (named, not hashed), examples:** `fno/config.py`, `fno/models.py`, `fno/composition.py` (reached
through `v4_pack/cli.py`), `fno/daily/wiring.py`, `fno/storage/*` wiring and stores, `fno/alerts/sender.py`,
`fno/health/*`, `fno/pipeline/trigger.py`, `fno/rehearsal/*`, `fno/global_cues/*` (M1's US flag, outside its
`METHOD_FILES`), `fno/quotes/window.py` (the capture window; the cutoff is enforced in `terms`),
`fno/research_engine/ledger.py` (git), `fno/weather/records.py`, `drivers.py`, `model.py` (row shapes and the card's
drivers, outside M1's `METHOD_FILES`).

**Data, not hashed (it grows):** `research/data/nifty-panel/warmup_closes.csv` (O6, outcomes of V2, V3, V6, V7),
A16's `rv/` rows, A16b's candle rows, `research/data/calendar/nse_sessions.csv` (2027 rows to come), the Drive
archives. Each row's own provenance and the readers' checks protect them; the record says so.

**The rate (round 2, judge 597 SF1 and SF2; G10's builder's three conditions).** Protocol 1.4 fixes 6.5%; `config.yaml`
`risk_free_rate: 0.065` is read by other stories and may move (A21's T-bill capture,
`fno/price_distribution/records.py:31`).
- **Where:** a new module `fno/forecast_v4/pricing.py`, `V4_RISK_FREE_RATE = 0.065`. Evidence: it is byte-checked by
  the `fno/forecast_v4/*.py` glob; it is in no other method hash (M1's `METHOD_FILES`, `fno/weather/wiring.py:28-33`,
  list only `forecast_v4/terms.py` and `sessions.py` from that package; G7's `METHOD_FILES`, `IMPLIED_METHOD_FILES` and
  G7b's `PACK_METHOD_FILES` are paths inside `fno/forecast_v4_rules/`), so no committed row's hash moves and no
  back-fill is regenerated. **Also in the pack's IV30 method** (G10's view): `pricing.py` joins
  `v4_pack/wiring.IV30_METHOD_FILES`, so every pack's `iv30_method` covers the rate (no test pins that digest:
  `tests/v4_pack/test_release_run.py:124` checks its form only; the first live pack is 26 Oct, so no released pack
  changes). Not in `terms.py` (M1's hash would move: 2,400+ weather files regenerated) and not in `live_features.py`
  or `iv30.py` (shared; `iv30.py` is byte-checked by v1, so an edit would break v1's freeze). Exactly 0.065, so 26
  Oct's first pack is unchanged (G10's condition 1). Round 1's code put it in `fno/v4_pack/model.py`; round 2 moves it.
- **Every v4 reader of the configured rate today, each fixed:** (1) the pack's IV30 rule, `fno/v4_pack/wiring.py:54`
  (this story, G10's agreement, merged after or rebased on `story/v4pack-rehearsed-live`, then
  `tests/rehearsal/test_v4_pack_live.py` and `tests/v4_pack` rerun: G10's condition 3); (2) G7b's EOD proxy for the
  back-fill and the premium ratio window, `fno/forecast_v4_rules/wiring.py:77` `build_atm_iv30(cfg)`, which reads
  `cfg["risk_free_rate"]` inside v1's frozen `fno/forecast/wiring.py:17` (that file cannot change): G7b builds
  `PanelAtmIv30(Black76(), V4_RISK_FREE_RATE)` in its own wiring instead (G7b's file; asked through the
  orchestrator); (3) G7b's V4/V5 terms (`option_terms.OptionTerms(model, rate, calendar)`), wired in its adapter, not
  built yet: it passes `V4_RISK_FREE_RATE`. The EOD values are unchanged while the config holds 0.065, so the
  back-fill's rows do not move (its method hash moves only if G7b's wiring is in `IMPLIED_METHOD_FILES`; G7b says).
- **Test (criterion 3):** no byte-checked or recorded v4 module reads `cfg["risk_free_rate"]` or calls a known config
  reader of it (`build_atm_iv30`), scanned over the walk's classes; and each rate user gets 0.065 with the config set
  to 0.10.

**Other settings v4 reads from `config.yaml`** (recorded with their freeze values; not frozen):
- `quotes.windows.v4` (14:30-14:40): when A4e captures; the cutoff itself is enforced by `terms.V4_CAPTURE_START` and
  `V4_PACK_WINDOW_END` in `v4_pack/codec.py:119-131`, so a config edit cannot put a later quote in a pack.
- `daily.live_from.*` (`weather`, `forecasts_v4`, `v4_pack`, G7b's `forecasts_v4_pack`, G11's `ai_books_v4`): which
  days run; a late date makes misses, never better scores.
- The freeze date: read by BG1 from `FREEZE_v4.md`'s `Frozen on:` (section 7), no config key.

## 3. The protocol's final form (one commit, before the record)

- **G7b's wordings W1-W8** (G7b completion text, "Protocol wordings to add before the freeze"): G7b's builder writes
  them (its scope item 7); **not on `main` or the G7b branch today** (`grep traded_today PROTOCOL_v4.md`: 0). They
  land first.
- **Then this story's edits:** (a) the status line, true before and after the record exists: "**Status: final text.**
  Frozen by `research/forecasts/FREEZE_v4.md` (section 10), which names this text's commit; nothing counts under v4
  before that record exists"; (b) section 10's list widened to section 2 above (G10's pack, G11's AI files, the IV30
  files) and "ChatGPT's review" marked paused by the owner (22 Oct); (c) section 1.4's rate named as
  `pricing.V4_RISK_FREE_RATE`, and `pricing.py` added to the "Reference code" list; (d) section 10 names the slot
  registry `research/forecasts/v4_slots.csv` as append-only after the freeze (judge 597 m1; section 4 already names
  the file, line 226, but not that rule). One commit, the protocol commit; nothing else changes it after.
- `tests/forecast_scoring_v4/test_freeze_check.py`'s draft branch (`"**Status: DRAFT, not frozen.**"`) reads the new
  status line instead.

## 4. Preconditions (protocol section 10) and their state, 24 Oct 2026

| Precondition | State | Evidence or owner |
|---|---|---|
| The judge's PASS | protocol text: judges 414, 430, 436 (pieces 1-1d, 3); the final form and this freeze: **not yet** | this story's judge |
| ChatGPT's review | **not a precondition now:** paused by the owner, 22 Oct ("Cut-list accepted"); stated in the record | `docs/JUDGE.md` rule 9 |
| G7 and G8 code exists | **not complete:** G7b steps 5-6 on its branch; adapter, CLI, V4/V5 and drift writers not built | G7b builder session_017GCFK7, judge K |
| Owner's items A-C | given 15 Oct | DESK_DECISIONS 15 Oct row 121 |
| Owner's items D and E | **written:** 11 D ("Owner chose a stricter rule (3 B)", rule E+D in 5.3) and 11 E ("Decided: option 2, the share cut", `confirmatory.crash_dominated`) | `PROTOCOL_v4.md` lines 393-423 |
| X of 1.6 frozen | **met:** 0.006104597099330481, 1,661 sessions, revision `1d68c447`, nearest rank | `terms.MOVED_AFTER_CUTOFF_X`/`_SAMPLE`, `v4_moved_after_cutoff.json`, `tests/forecast_v4/test_cutoff_move.py` |
| Go-live date and `Frozen on:` | written by this story | section 1 item 2 |
| Owner's sign-off | given 24 Oct | DESK_DECISIONS 24 Oct, "The owner signs off protocol v4" |

**What still blocks the freeze commit, in order:**
1. **G7b completion on `main`:** steps 5-6 (judged), then the `Pack` adapter, `forecast-v4 capture-pack`, the O1 step
   `forecasts_v4_pack` and the V4/V5 outcome and proxy-drift writers. They decide V2's primary baseline (a family
   member's yardstick) and V4/V5's outcomes, all in byte-checked folders. Section 10 ("v4 is frozen only once that
   code exists") and the owner's 24 Oct row both require them.
2. **G11 on `main`** (`ai register-v4-slots`, the AI files of section 2). Without it the AI slots cannot be
   registered at the freeze, and **cannot be registered later** for V6a, V6b and V7: `slot_file.py:66-69` refuses an
   `effective_start` after a question's first eligible session, and their base rate is eligible on Mon 26 Oct. They
   would stay "not started" (p = 1) for all of v4. (The owner's 21 Oct answer (3), "freeze with the AI slots
   unregistered", is replaced by the 24 Oct row: "G11's AI books (slots registered at the freeze)".)
3. **The rate** (section 2): `fno/forecast_v4/pricing.py` and the pack's wiring line (this story; G10's builder
   agreed, 24 Oct), and G7b's two readers (G7b's builder).
4. **G7b's wordings W1-W8** in the protocol, then this story's protocol commit (section 3).
5. **Main green** with the merged tree (full gates once, `docs/JUDGE.md` merge procedure).
6. **Known pending changes to byte-checked files land first** (judge 597 SF3): G10's `story/v4pack-rehearsed-live`
   (`fno/v4_pack/wiring.py`); any other open branch touching a byte-checked file is listed by the freeze tool from the
   register and the branches at the freeze, and either lands or waits for v5.

**Said plainly:** Sunday holds only if item 1 passes judge K on Sunday. If not, nothing is frozen early: `Frozen on:`
becomes the merge's day and the first counted session the next one. Freezing without V2's live code would break
section 10 and the owner's row; it is not offered.

**Owner's keep-or-change list:** the owner's 21 Oct answer (4) asked for it before signing; it was not produced
before the 24 Oct sign-off. The orchestrator puts the table below to the owner (24 Oct ruling); the code does not
wait for the answer, the freeze commit does.

### Keep or change: every decision the record quotes (owner's 21 Oct answer (4); orchestrator, 24 Oct: "prepare the
keep-or-change list ... I put it to the owner")

Rows of `docs/DESK_DECISIONS.md` by date and title. Recommendations are reasoning only unless marked.

| # | Decision (owner's words) | Source row | Recommended | Why, in one line |
|---|---|---|---|---|
| 1 | A: Test A "yes" needs Holm at 0.02 per look, two looks ("A accept") | 15 Oct, "G6 protocol v4 choices A, B, C confirmed" | keep | caps false "yes" at 5% over both looks; costs about 20 more outcomes at r = 3 |
| 2 | B: no power report at the review means option 2, code only ("B accept") | same row | keep | no projected date, no "continue to settle" |
| 3 | C: the premium-adjusted ratio window uses the labelled EOD IV30 proxy from 1 Jan 2024 ("C accept") | same row | keep | without it V2 has no primary until about late 2028 |
| 4 | D: a stricter claim rule, chosen by measured size: rule E+D ("3 B") | 15 Oct, "G6 item D" | keep | the only measured rule within size in every cell; said plainly, it makes V1, V2, V6a near-unclaimable |
| 5 | E: windows with more than 10% 2% days are not judged ("merge G6, E option 2") | 15 Oct, "G6 item E: option 2" | keep | removes the measured crash-year errors; some evidence (one crash) |
| 6 | Verdicts on observed days only, with a miss cap ("Observed days + miss cap"; replaces "Base rate") | 15 Oct, "Missed forecast days" | keep | a filled-in day would make a forecaster that never ran look futile |
| 7 | Miss caps 10% of baseline days and 10% of 2% days ("Both 10%") | 15 Oct, "Protocol v4 miss caps confirmed" | keep | a member that did not run is "undecided, operations", never judged |
| 8 | V6b stays a scored member; "V6 report-only" withdrawn | 15 Oct, "Protocol v4: V6b stays a scored member" | keep | V6b is the only member with a measured path (about 14-22 years); dropping it leaves Test A no claimable member |
| 9 | v4 timeline: 14:30 cutoff, one pack, one 15:10 deadline, 15:15 snapshot | 15 Oct, "v4 timeline" | keep, as revised by #16 | the one clock every family shares |
| 10 | A sharp move after the cutoff is flagged, not blocked ("Flag, don't block") | 15 Oct, "A sharp move after the data cutoff" | keep | nothing is dropped; X frozen at 0.0061 |
| 11 | System-late days out for every family; a late family is charged a miss | 15 Oct, "Lateness" | keep | no family gains from a late pack |
| 12 | Honest times, pack window to 14:40 ("Honest times, window to 14:40") | 15 Oct, "v4 data cutoff" | keep | every field keeps its real observation time |
| 13 | Misses from each slot's declared `effective_start` ("Yes, from the declared start") | 16 Oct, "v4 misses count from each slot's declared effective_start" | keep | a family cannot dodge misses by starting late |
| 14 | A2 fallback pack dropped; labels `A` and `system_late` only | 16 Oct, "Orchestrator rulings, evening" (1) | keep | A16's 14:30 mark can never hold a complete pack |
| 15 | At the freeze the AI books' v4 run replaces the v2 AI run ("A: v4 replaces v2") | 16 Oct, "G11: at the v4 freeze ..." | keep | one daily AI run cannot serve both deadlines |
| 16 | The pack is released by 14:45, cutoff 14:40 unchanged ("1 - Option A") | 24 Oct, "The v4 pack is released by 14:45" | keep | the data cutoff does not move; a later release is `system_late`, never scored |
| 17 | A `system_late` day makes the card warn ("2 - Option A") | 24 Oct, "A system_late day makes the card warn" | keep | operations only; no score effect |
| 18 | V1 and part f carry both premium-adjusted yardsticks, intraday and close ("both") | 24 Oct, "W3: both yardsticks" | keep | reported only, never pooled |
| 19 | A16b's candle back-fill fills option A's ratio window ("W8 - yes") | 24 Oct, "W8" | keep | yardstick scale only, never a forecast input, outcome or base rate; drift line on every report |
| 20 | v4 pack live Monday 26 Oct ("v4 pack live Monday - Option A") | 24 Oct, "The v4 pack goes live Monday 26 Oct 2026" | keep | the first counted session |
| 21 | Frozen on = the day the judge passes and the owner signs; go-live the next session | 21 Oct, "v4 freeze answers" (1) | keep | Frozen on 25 Oct, counted from 26 Oct |
| 22a | Freeze with the AI slots unregistered | 21 Oct, "v4 freeze answers" (3), first half | **replaced** by #24 | registered later they would be refused for V6a/V6b/V7 (section 4, blocker 2) |
| 22b | "The AI files are hashed in their own registration when G11 goes live" | same row, second half | keep (judge 597.1 m2) | G11's shared AI files (section 2, recorded) get their SHA-256 in the record's own "AI registration" table, written in the same freeze commit as G11's 10 slot rows: hashed when the AI slots register, not in the v4 file table |
| 23 | v4 freezes with V6a/V6b (V1 when ready); V2-V5 later under their own record (orchestrator, owner informed) | 16 Oct, "v4 freezes with V6a/V6b" | **replaced** by #24 and 24 Oct "Close v4 in full first" | one freeze, every question built |
| 24 | The owner signs off v4; slots registered at the freeze ("Consider v4 sign off") | 24 Oct, "The owner signs off protocol v4" | keep | this freeze |
| 25 | Superseded and not quoted as rules: "A missed day scores as the base rate" (15 Oct, replaced by #6); "V6 becomes descriptive" (15 Oct, withdrawn by #8) | 15 Oct | listed for completeness | the record names them as replaced |
| 26 | G7b's wordings W1, W2, W5, W6, W7 (not yet owner-decided; W3 and W8 are #18-19, W4 dropped) | G7b completion text | owner to sign with the freeze | each is in the G7b text's plain-words table |

## 5. `research/forecasts/v4_slots.csv` (protocol 4 and 5.6; `slot_file.COLUMNS`)

Written in the freeze commit; every row `effective_start` = **S, the first counted session**, and `registered_on` =
`Frozen on:`. **S is held open (orchestrator, 24 Oct): the owner decides between Mon 26 Oct and the first session
the AI books can fire.** What follows from S, said plainly:
- `slot_file.py:66-69` refuses an `effective_start` after a question's first eligible session, the first live session
  after `Frozen on:` with a primary value; V6a, V6b and V7's base rate has a value on every session. So every row's
  start must be the first session after `Frozen on:`, and **`Frozen on:` must be the calendar day before S or
  earlier, but not before the previous session** (S = Tue 27 Oct needs `Frozen on: 2026-10-26`; Monday's live rows
  are then before the freeze and never counted).
- `daily.live_from.ai_books_v4` is set to S **in the freeze commit** (G11 C13; orchestrator, 24 Oct), so the AI books
  fire on the first counted session; a later date leaves `not_fired` misses from S.
- G11's 10 rows are written by `python -m fno ai register-v4-slots --print` on the freeze tree and pasted into the
  freeze commit, before 09:15 IST of S (G11's command refuses after).

| Question | `rules` | `hybrid` | `ai_team` |
|---|---|---|---|
| V1 `v1_rv_next_session` | `v1_close_blend` (G7) | `book2_hybrid_v2` | `book3_ai_v2` |
| V2 `v2_rv_next_5_sessions` | `v2_close_blend` (G7b part a) | `book2_hybrid_v2` | `book3_ai_v2` |
| V6a `v6_abs_move_2pct_next_session` | `weather_vix_v1` (M1, decision 70) | `book2_hybrid_v2` | `book3_ai_v2` |
| V6b `v6_abs_move_2pct_within_5_sessions` | `weather_vix_v1` (M1, decision 70) | `book2_hybrid_v2` | `book3_ai_v2` |
| V7 `v7_vix_higher_in_5_sessions` | `v7_vix_vs_mean20` (G7b part a) | `book2_hybrid_v2` | `book3_ai_v2` |

- The rules rows are this story's; the 10 AI rows come from `python -m fno ai register-v4-slots --print` (G11 C13)
  run on the freeze tree, pasted unchanged (its forecaster ids are G11's `versions.current_version`; the table shows
  the ids G11's text names).
- **V7's `rules` row, a choice for the orchestrator:** G7b labels `v7_vix_vs_mean20` "reported" and V7 is
  descriptive-only (p = 1, never in Test A). Recommendation (reasoning only): register it, because G11 registers a
  question's AI rows only once its `rules` row exists, and a V7 slot left empty can never be registered later (its
  base rate is eligible on 26 Oct). Nothing about Test A changes either way.
- **Consequences, said plainly:** V1's slots start counting misses only once V1's primary (HAR daily) has a live
  value (V1 is `not_started` until A16 has 20 non-void sessions: every V1 row on 22-23 Oct is `not_started`). V2's
  start only once G7b's capture writes a live premium-adjusted value. The AI slots count misses from 26 Oct: if
  `daily.live_from.ai_books_v4` is set later than 26 Oct, every session between is a `not_fired` miss (G11 C13), and
  a missed 2% day while fewer than 10 exist makes that member "undecided, operations" at a look (protocol 4).
- After the freeze the file is append-only: a later row is a new slot only; editing a frozen row changes a member.

## 6. The ledger rows (B4, `research/ledger.csv`)

One row per question scored under v4, as `forecasts-v1`/`-v2` did (trials 32-41): experiment `forecasts-v4`, kind
`prospective`, `hypothesis` `yes` for the confirmatory members' questions (V1, V2, V6a, V6b) and `no` for V3, V4, V5
(reported) and V7 (descriptive), `registered_on` 2026-10-25, `protocol_path` `research/forecasts/PROTOCOL_v4.md`,
`protocol_commit` the protocol commit; written with `Ledger.register` (next free ids at the commit; 100-107 if
nothing lands first). Recommendation (reasoning only): per question, not per slot: the family's count (15) is fixed
by the protocol (5.7), and v1/v2 registered per question.

## 7. The stop-rule review date (BG1)

**Changed after judge 597.2 (orchestrator, 24 Oct: coordination with BG1-t, `story/bg1t-test-a-inputs`):** BG1-t
removes `budget.stop_rule.v4_freeze_date` and reads the freeze date from `FREEZE_v4.md`'s `Frozen on:` line, one
source; so the freeze commit sets no config key. Whichever of the two merges second carries the change.
**Effect, said plainly:** BG1's review date (`stop_rule_tracker.review_date`: the last session of the sixth full month
after the freeze) moves from the projected **end of May 2027** (freeze month November) to **Fri 30 Apr 2027** for a
25 Oct freeze, one month earlier, and rests on a weekday fallback until NSE's 2027 calendar is added. Test A's input
"protocol v4's registered family, frozen" gets its path (`research/forecasts/FREEZE_v4.md`) in BG1-t too.

## 8. Acceptance criteria (each with its code, its test, the plant that must break it; good, bad, boundary, empty)

1. **The list** (`freeze_check.BYTE_CHECKED_GLOBS`, `RECORDED`, `NOT_DECIDING`): the three classes of section 2.
   Test: named files in their class; no file in two classes; G: a file of each folder; B: a recorded file never
   byte-checked; Bd: `__pycache__` left out; E: an empty folder adds nothing. Plants: drop the `fno/v4_pack` glob;
   move `fno/constants.py` into the byte-checked list; move a recorded file to `NOT_DECIDING`. **The freeze tool refuses
   while any listed glob or path matches no file** (self-review: G11's prompts and `run_terms.py` are not on `main`
   yet, so a table printed now would leave them out silently).
2. **The protocol commit** (new `freeze_check.protocol_problems(record, git)`, reusing B4's `Git`): the record has
   exactly one `Protocol commit:` line; that commit is an ancestor of HEAD, is the last commit that changed
   `PROTOCOL_v4.md` (section 10: "the commit that adds this text in its final form"), and the text at it hashes to
   the table's value. Tests on a
   temporary git repository: G: intact; B: a commit not in history, a protocol edited after it; Bd: the protocol
   commit equal to HEAD; E: no `Protocol commit:` line. Plants: skip the ancestry check; compare with HEAD's text.
3. **The rate** (`fno/forecast_v4/pricing.V4_RISK_FREE_RATE = 0.065`): the pack's IV30 rule and G7b's two users
   run at it, and no code path takes a config value (`build_iv30_rule()` takes none); `pricing.py` is in
   `IV30_METHOD_FILES`; no module in the walk's classes reads `cfg["risk_free_rate"]` or calls `build_atm_iv30`. G: the
   three users; B: a planted config read; Bd: a comment naming the setting is not a read; E: a module with no rate.
   Plants: read the config again in the pack's wiring; drop `pricing.py` from `IV30_METHOD_FILES`.
4. **The look refuses a broken freeze** (G8's look command, `fno/forecast_scoring/v4/cli.py`): a recorded look stops,
   writing nothing, while `freeze_problems` is not empty, naming each; the report's first line prints "v4 freeze:
   intact" or the problems. The check is a required argument (no default that reads "intact"). **A shallow clone is
   "freeze not checked (shallow clone)" in the report, never "BROKEN", and a look refuses on it** (self-review: the
   weekly post-mortem workflow, `.github/workflows/postmortem-weekly.yml:46`, checks out shallow and commits the
   report; its `fetch-depth: 0` is LR1's lane-1 change, asked through the orchestrator). G, B (one changed file), Bd
   (a file added after; a shallow clone), E (no record: exploratory, as today). Plants: ignore the problems; print
   without refusing; read a shallow clone as intact.
5. **The record matches the repository** (existing `test_once_the_record_exists_the_repository_matches_it`, plus):
   `Frozen on:` parses; `First counted session:` is the first A7 regular session after it; the recorded list equals
   `recorded()`; the settings section names each key of section 2 with its value at the freeze. Plants: edit one
   hashed file by one byte (fails); a first session on a holiday; drop a recorded file.
6. **Slots:** `v4_slots.csv` read through G8's real `build_slot_registry()` (G11's name for today's
   `wiring._registry`) gives 15 members, all effective on S; the record's copied rows are the file's first 15
   rows, unchanged (append-only). B: an edited forecaster; Bd: a 16th appended row passes; E: no file before the
   freeze (existing test, kept). Plants: change one frozen row; start one row a session after S.
7. **Ledger:** the `forecasts-v4` rows exist, one per question, `protocol_commit` equal to the record's, through
   `read_ledger`. Plants: a wrong protocol commit; a missing V6b row.
8. **Freeze date:** with the record in place, BG1-t's `build_review_date()` gives the date from `FREEZE_v4.md`'s
   `Frozen on:` (2027-04-30 for 25 Oct, with the weekday-fallback note); BG1-t's test, run on the merged freeze
   tree. Plant: a `Frozen on:` one month later moves it to 2027-05-31.
9. **Disclosure** (new module beside `freeze_check`, printed by `tools/v4_freeze_table.py`; it refuses a dirty tree, so
   "as of commit" is true; a record file it cannot parse is named, never a traceback; Drive live rows made before
   the freeze are listed by receipt beside Drive back-fills, folders taken from G7b's constants): one row per source
   with
   first and last back-fill day, row count, method SHA-256(s) and the SHA-256 of its back-fill rows; pre-freeze live
   rows and reports listed apart; Drive back-fills from receipts. Tests on fixture folders: G mixed file; B a file
   whose rows carry two method hashes (both listed); Bd a file of live rows only (no back-fill line); E an empty
   folder ("none"). The record's disclosure section equals the tool's output at the freeze. Plants: count live rows
   as back-fill; drop M1's day files.
10. **Protocol text:** the status line and section 10's widened list are read by `tests/forecast_v4/
    test_protocol_text.py`. Plant: the old draft line.

11. **The walk** (S1's pattern, `imported` reused): from every byte-checked and recorded module, every reached `fno`
    module is in a class; every `RECORDED` and `NOT_DECIDING` entry is reached and in one class only; reasons are
    non-empty. G: today's tree; B: a new import of an unclassed module (a fixture module); Bd: an import inside a
    function counts; E: a module with no `fno` import. Plants: drop `fno/intraday/candle_rv_table.py` from the
    classes (the walk names it and its importer); leave a stale entry.
12. **Recorded drift is printed:** after the freeze, the report prints one line per recorded file whose SHA-256
    differs from the record's ("recorded file changed since the freeze: <path> (<reason>)"); the look prints the same
    lines and still runs (recorded files do not break the freeze, by design of section 10). G: none changed; B: one
    changed; E: before the freeze, nothing. Plant: compare with the wrong hash column.

Every new file under 350 lines; the freeze tool and check stay pure functions apart from git and file reads.

## 9. Gap list (protocol section 10, 8, 4, 5.6, 1.6, 11; response 287; the orchestrator's 24 Oct brief)

| Requirement | Covered by |
|---|---|
| The commit of the protocol's final form named | section 3; criterion 2 |
| SHA-256 of the protocol, calibration, `fno/forecast_v4/`, tools and tables, golden fixture | criterion 1 (existing list) |
| Every G7 and G8 file deciding a baseline, outcome or score | criterion 1; blocker 1 (G7b on `main`) |
| Files outside G7/G8 that now decide one (G10's pack, G11's AI files, the IV30 files, A16b's candle readers) | criteria 1, 11; section 2 |
| No file on a v4 input path missed by hand (judges 596, 597) | criterion 11 |
| A shared file that decides a v4 value changes after the freeze | criterion 12 (printed), section 2's locks |
| The four recorded files of section 10 (+ `rv_table.py`, rest of `fno/weather/`) | criterion 5 |
| A value that decides a baseline outside every file (the rate), every reader of it | criterion 3; section 2 "The rate" |
| Known pending changes to byte-checked files | blocker 6 |
| The first counted session S held open; `ai_books_v4` = S in the freeze commit | section 5 |
| Ledger row (B4) with the freeze | criterion 7 |
| A change after the freeze is a new version | criteria 4, 5; record item 12 |
| `Frozen on:` and the go-live date (G8) | criterion 5 |
| Preconditions: judge, ChatGPT (paused), G7/G8 code, A-E, X | section 4 (states each); the record item 3 |
| Disclosure of back-fills with commits and ranges (section 8) | criterion 9 |
| Slot registration, `effective_start` no later than first eligible (4, 5.6) | criterion 6; G8's `slot_file.py` (merged) |
| AI slots registered at the freeze (owner 24 Oct) | section 5; blocker 2 (G11's command) |
| The freeze date for BG1's review | criterion 8 (BG1-t reads `Frozen on:`; no config key) |
| Known limits: libm replay, v3 silent read, 2027 calendar | record item 11 (text, read by criterion 5's test) |
| M1's stale method hash (response 250 item 10) | merged with piece 3 (M1's hash gate); G7's gate; nothing to build |
| Back-fills regenerated on the frozen code | out: each owner's hash gate fails the suite on a stale row (G7, M1, G7b), so the merged tree is current |
| v3's `last_commit` onto B4's `Git` | out: a v3 file under `FREEZE_v3.md`; v3's next version |
| Stop-rule tracker's Test A input path | out: BG1's file, sent to its owner (section 7) |
| W1-W8 wordings | out: G7b's scope item 7; blocker 4 |
| Setting `ai_books_v4`, `forecasts_v4_pack` dates; the AI routine prompt | out: the owner's, after their stories merge |

## 10. Order of work

1. This text, pushed alone; the judge checks it against the protocol and the owner's rows.
2. Freeze code on this branch (criteria 1-4, 9, 10's test change; the rate constant), self-reviewed by independent
   agents, plants run one at a time; judge.
3. When G7b and G11 are on `main` and W1-W8 are in the protocol: merge `main`; the protocol commit (section 3); then
   the freeze commit: `FREEZE_v4.md` (tool output pasted), `v4_slots.csv` (rules rows plus G11's `--print`), the
   ledger rows, `daily.live_from.ai_books_v4` = S; full gates on the merged tree; the judge's final check of the
   exact SHA; merge on 25 Oct IST (no merge 14:00-16:15 IST on a session day).
4. After merge (JUDGE.md rule 8): `python -m fno forecast-v4-scores report` on the merged `main` shows "v4 freeze:
   intact" and 15 registered members; `ai register-v4-slots` (without `--print`) answers "already registered".

**Depends:** G6 pieces 1-3 (merged), G7b completion, G10 completion (merged), G11, the owner's sign-off (given) ·
**Size:** M · **Status:** story text for the judge (rule 1); no code before its check

## Round 2: answers to judge 597 (read at 2f48524dc), by number

Also folded in from the builder's self-review of the round-1 code (an independent agent; findings and their fixes go
in Claims): a shallow clone read as a broken freeze (criterion 4), a byte-checked entry that matches no file (criterion
1), the check's arguments defaulting to "intact" (criterion 4), two `Protocol commit:` lines and an ancestor that is
not the final-text commit (criterion 2), and the disclosure's robustness and Drive live rows (criterion 9).

- **SF1, accepted.** The rate moves to `fno/forecast_v4/pricing.py` (outside M1's `METHOD_FILES`, evidence in section
  2) and joins the pack's `IV30_METHOD_FILES` (G10's view); not `terms.py`. Round 1's code had it in
  `fno/v4_pack/model.py` (also outside every method hash, but not where a protocol number belongs); round 2 moves it.
- **SF2, accepted.** Section 2 names the three readers (the pack, G7b's EOD proxy through v1's frozen
  `build_atm_iv30(cfg)`, G7b's V4/V5 terms); criterion 3's test scans the walk's classes for a config read or a call
  of `build_atm_iv30`.
- **SF3, accepted, with the walk.** Byte-checked = v4's own files; recorded = shared files that decide a v4 value, each
  with its lock and a drift line (criterion 12); `fno/ai/versions.py`, `fire.py`, `outcome.py`, `scoring_gate.py`,
  `stop_rule.py`, `run_terms.py` move to recorded; `live_features.py` and `iv30.py` too (locks: the pack's
  `iv30_method`, v1-v3's freezes). Pending changes land first (blocker 6).
- **m1, partly.** Section 4 of the protocol already names `research/forecasts/v4_slots.csv` (line 226); the protocol
  commit adds the append-only rule in section 10 (section 3 (d)).
- **Import walk (orchestrator's note, judges 596-597), accepted:** criterion 11; A16b's `candle_rv_table.py`,
  `rv_table.py` and `row_files.py` are recorded with A16b's tests as their lock, and G7b names the W8 reader module.
- **The first counted session S** is held open for the owner (section 5), with what it forces on `Frozen on:`.
- **Judge 606 (round 1 on the code, blocking: G11's unclassed modules):** classed as judge B lists: `run_terms.py`,
  `budget_stop.py` (a stop is a `not_fired` miss, so it decides misses: agreed, moved from my first "not deciding")
  and `record_writer.py` recorded in the AI registration table; `usage_ledger.py`, `statistics.py` (G11's cost line
  only), `alerts/sender.py`, `pipeline/trigger.py`, `budget/constants.py` and `budget/report.py` (the stop's names and
  meter shape) not deciding; `timing.py` dropped (no longer reached). `fno/forecast/wiring.py`'s reason now says it
  leaves the rate refusal, and the walk marks it stale, once G7b's wiring stops importing it.
- **After the PASS (judge 597.2, orchestrator, 24 Oct):** m3, `fno/quotes/recorder.py` is recorded (A4's capture
  behind the pack; lock: A4's baseline-bytes test), with the five capture modules it imports; criterion 8 reads the
  freeze date from `FREEZE_v4.md` (BG1-t), no config key.
- **m2 (addendum 597.1), accepted:** keep-or-change row 22 splits: 22a replaced by the 24 Oct sign-off; 22b kept, and
  it is how SF3's shared AI files are hashed (section 2's AI row: the record's "AI registration" table, in the same
  freeze commit as G11's rows).

## Orchestrator rulings on this text (24 Oct 2026)

- V7's `rules` slot is `v7_vix_vs_mean20`; all 15 rows effective on S (section 5; S held open for the owner).
- 8 ledger rows, one per question (section 6).
- The keep-or-change table above goes to the owner through the orchestrator.
- The rate: this story adds the constant and the one wiring line unless G10's builder objects (asked by the
  orchestrator). G11's builder confirms the AI file list (asked by the orchestrator). BG1's Test A path is routed to
  BG1's builder.
- Judge: B (session_01AfgnvV9T8Zpbm6riR6HaEi). The freeze code starts in parallel; the freeze commit waits for G7b and
  G11 on `main`.

## Claims

### Freeze code, rounds 1-2 (criteria 1-4, 9, 11, 12; branch `story/v4-freeze`)

Criteria 5-8 and 10 are the freeze commit's (the record, the slot and ledger rows, the freeze date, the protocol
commit); they are built when G7b and G11 are on `main`.

- **Code:** `fno/forecast_scoring/v4/freeze_classes.py` (new: the three classes; on the tree merged with `main` of 24 Oct
  evening, G11 included: 139 byte-checked files, 62 recorded with their lock, 50 not deciding with a reason);
  `freeze_check.py` (`FreezeCheck`, `check`, `unmatched`, `recorded` with G11's own "AI registration" table, `drift`, `protocol_problems`, `rate_readers`);
  `freeze_disclosure.py` (new); `cli.py` and `wiring.py` (`build_freeze_check`; the report's first lines; the look
  refuses unless the freeze holds; the check is a required keyword argument); `fno/forecast_v4/pricing.py` (new,
  agreed byte for byte with G7b's builder); `fno/v4_pack/wiring.py` (`build_iv30_rule` at the v4 rate, `pricing.py`
  in `IV30_METHOD_FILES`; G10's builder agreed); `tools/v4_freeze_table.py` (refusals, all three classes, platform,
  disclosure).
- **Tests:** `tests/forecast_scoring_v4/test_freeze_check.py`, `test_freeze_protocol_commit.py`, `test_freeze_rate.py`,
  `test_freeze_look_refusal.py`, `test_freeze_walk.py`, `test_freeze_disclosure.py`, `test_freeze_tool.py`; four older
  look tests pass the now required check explicitly (`helpers.intact`).
- **Plants (19, all caught; 3 survived the first run and their tests were tightened):** criterion 1: the `v4_pack` glob
  dropped, `fno/constants.py` byte-checked, `unmatched` blind to recorded files; 2: no ancestry check, an earlier
  commit with the same text accepted, two `Protocol commit:` lines accepted, a shallow clone read as checked; 3: the
  pack at another rate, `pricing.py` out of the IV30 method, the reader scan blind to `build_atm_iv30`; 4: the look
  ignoring the check, the report without its freeze line; 9: live rows read as back-fill, Drive live rows not cut at
  the freeze day, M1's day files dropped; 11: A16b's `candle_rv_table.py` out of the classes; 12: drift on the wrong
  hash, drift dropped from `check`; the tool ignoring a dirty tree.
- **Self-review (an independent agent on round 1's code), each fixed or answered:** (B1) the weekly post-mortem's
  shallow checkout would print "BROKEN": a shallow clone is "NOT CHECKED" and the look refuses; the workflow's
  `fetch-depth: 0` is `story/lr1-fetch-depth` (orchestrator's assignment); (B2) G7b's EOD proxy reads the configured
  rate: named, and `rate_readers` keeps the tool refusing until G7b's change lands; (B3) a listed file matching
  nothing: `unmatched`, the tool refuses; (B4) the check defaulted to "intact": now required; (S5) unclassed v4
  inputs: the walk, criterion 11; (S6) two protocol commit lines: refused; (S7) a broken CSV, an empty file, missing
  columns, an empty receipt: `DisclosureError` naming the file; (S8) Drive live rows: listed by receipt, folders from
  G7b's constants; (S9) the protocol text compared after git's text decoding: **kept, said plainly**: a CRLF or
  non-UTF-8 protocol would read as "not the text the record pins", which fails safe, and the file is UTF-8 with LF;
  (m10) the rate test now checks the built rule and the scan; (m11) the platform line names "unknown", the tool
  refuses a dirty tree; (m12) the protocol commit must be the last commit that changed the protocol; (m13) the rate
  moved to `pricing.py` (judge 597 SF1).
- **Real output sample** (committed code, this branch, 24 Oct 2026; the tool refuses until G11 and G7b land, by
  design):

```
$ python tools/v4_freeze_table.py --frozen-on 2026-10-25
freeze tables NOT printed:
matches no file: agents/forecast/book2_hybrid_v2.md
matches no file: agents/forecast/book3_ai_v2.md
reads the configured rate (protocol 1.4: pricing.py only): fno/forecast_v4_rules/wiring.py
reads the configured rate (protocol 1.4: pricing.py only): fno/forecast/wiring.py
```

  The disclosure on `main`'s data (round 1's run): G7's 14 back-fill files 2017-01-03 to 2026-10-15 (2,410 rows each,
  method `21f62594f26f`), M1's 4 files and its day files to 2026-10-19 (2,412 rows, `a49c62612a46`), live rows of
  22-23 Oct apart, G8's reports of 10, 17 and 24 Oct.
- **Gates:** see the commit message of the pushed head.
