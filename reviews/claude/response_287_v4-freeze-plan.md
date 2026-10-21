# Response 287: the protocol v4 freeze plan, taken over (response 157 as written, response 250 folded in)

From the R2/G7 builder (session 0185gR5DmoDh2zBAvgRU4CEB), 21 Oct 2026 IST. **Owner of the v4 freeze from today**
(orchestrator's ruling, 21 Oct: "you take over response 157 as written and fold your response 250 into it. One plan,
one owner"). Response 157 was written by the A16/G8 builder (01VK88Lx, now parked) on branch `freeze/v4-checklist`
(c3fe3b0d) and never merged; its number and its ChatGPT request (172) were never registered under O12, so the plan
lives here under a claimed number. Its text is kept whole in the appendix; everything above it is what changed since.

Lane 1: judge B for each piece; ChatGPT already reviewed the plan (review 119, answered as 157's revision 2); the
owner signs the freeze commit. Nothing is frozen yet: `research/forecasts/FREEZE_v4.md` does not exist on main
(841294c8).

## The order (accepted by the orchestrator, 21 Oct) and its state on main 841294c8

| # | Piece | State | Owner |
|---|---|---|---|
| 1 | **One protocol text commit** (lane 1, judge B): G10's seven edits (story G10, "The exact PROTOCOL_v4.md changes"), with A2 dropped (below); 157's table (11 E decided, intraday HAR skips void sessions, misses from `effective_start`, back-fill disclosures, one long line) | **not done**: PROTOCOL_v4.md still says the 15:00 cutoff (line 38) and has no section 1.6, while the code refuses at 14:30 since G10 part 1 | R2/G7 |
| 2 | **G11 round 2b** (the structured stop-rule flag) | parked with G11 (story/g11-ai-books-v4 f538aa06, not merged); the freeze uses the "p = 1" path for every `hybrid` and `ai_team` slot unless the orchestrator unparks G11 | G11 owner if unparked |
| 3 | **Freeze code** (judge B): the freeze check test (byte-checked files and the golden fixture); G8's ledger registration adapter replacing `NoRegistrations`, refusing an `effective_start` after the slot's first eligible session; `scoring._miss_start` from `effective_start`; the "IV30 and Black-76 never called" proof test (ChatGPT 119); M1's method-hash gate with its back-fill regenerated | not built | R2/G7 (M1's gate with M1's owner) |
| 4 | **The freeze commit**: `FREEZE_v4.md` (hashes, `Frozen on: YYYY-MM-DD`, go-live date, owner quotes with their rows, disclosures), the ledger rows, G7's back-fill regenerated if a G7 method file moved | after 1-3; judge B, then the owner's sign-off | R2/G7 |

**Already merged since 157 was written:** A16's void-share count start (`story/a16-void-share-start`), the weather
constants move into M1's `METHOD_FILES` (`story/x-weather-constants`), the look's reconciliation
(`story/g8-look-reconcile`), G10's cohorts, V1's method pin (732db7e), G7b part a (V2, V3, V7 and their back-fill),
G8's V7 outcome from G7's `vix_up_outcomes` and its named `VixCloseMissing` stop, G7's gap fix, the `pack_sha256`
column in G7's records.

**Date, said plainly (reasoning only):** the freeze commit is ready for the owner about **27-28 Oct**, if pieces 1 and
3 each pass judge B in one or two rounds; 22-23 Oct is not reachable. Every day of slip is a day without counted v4
forecasts; nothing breaks meanwhile.

## What changed since response 157 (folded from response 250 and later decisions)

1. **A2 dropped (orchestrator, 16 Oct evening, DESK_DECISIONS):** A16's 14:30 mark has no India VIX, one monthly only
   and no next monthly on expiry days, so it never makes a complete pack. The day labels are `A` and `system_late`
   only; piece 1 writes section 1.6 without `A2`, and the change joins the owner's sign-off list.
2. **The ledger rows (piece 4):** V1 `rules` = `v1_close_blend` (counts once A16 has 20 live non-void sessions); V2
   `rules` = `v2_close_blend` (G7b; V2's primary, the premium-adjusted implied baseline, does not exist until G7b part
   b, so every V2 pair is missing and counted); V6a and V6b `rules` = `weather_vix_v1` (decision 70; `v6_ewma_t4`
   reported only); V7's three slots at p = 1 (descriptive only); `hybrid` = `book2_hybrid_v2` and `ai_team` =
   `book3_ai_v2` only if G11 is unparked and live, else every AI slot at p = 1. V3-V5 are not members; V2-V5's own
   implied baselines come under a later freeze record.
3. **Byte-checked additions to 157's list:** G7's `fno/forecast_v4_rules/` now also holds `vix_rule.py` and
   `constants.py` (G7b; "every file of `fno/forecast_v4_rules/`" covers them). If G11 is unparked: `fno/ai/v4_rows.py`,
   `scoring_gate.py`, `outcome.py`, `stop_rule.py` and `fire.py` (they decide which AI days are misses; agreed with
   G11's owner, 16 Oct). `fno/v4_pack/` is not in the live path of any counted member under this freeze (V6a, V6b,
   V1 read closes and A16 rows only) and stays out, said in the record.
4. **M1's committed rows carry a stale method hash** (2495d512 against the tree's, because M1's `METHOD_FILES`
   include `fno/forecast_v4/terms.py`, which G10 changed). Fix as G7's: M1's back-fill regenerated on the frozen code
   in the freeze commit (values unchanged, only the hash) and a gate test like G7's
   (`test_every_committed_g7_record_row_carries_this_trees_method_hash`).
5. **G7's back-fill gate** already fails the suite on a stale hash, so piece 4 regenerates G7's back-fill only if a G7
   method file moved after piece 3.
6. **The live capture (go-live, after the freeze, the owner's schedule):** today no v4 forecast is live (every G7 and
   M1 row is `backfill_exploratory`). O1's daily run starts at 14:33 and both captures refuse from 14:30, so: the
   routine starts at 14:05 from the go-live day, O1's follow-up starts both captures at the run's start (agreed with
   the O1 builder, 16 Oct), and `daily.live_from.weather` and `.forecasts_v4` are set to the go-live date in the same
   commit as the start-time line.
7. **A missing VIX close:** G8 stops (`VixCloseMissing`, exit 1) and G7 leaves the V7 day unresolved; kept on purpose
   (orchestrator, 16 Oct): a quiet void would move G8's comparison regimes.
8. **N+1 focus (owner, 21 Oct):** V1 and V6a (next-session questions) stay members; nothing in the plan drops them.
   G13b's price ranges are scored only by G13b and v4's questions only by G8 (one scorer per question, agreed 21 Oct).

## Open items from the judges (to apply when the freeze work resumes)

- **Judge 409 should-fix 1:** section 4's miss start must read "a session **after** the freeze", not "on or after":
  G8 clamps to the day after the freeze (`scoring._miss_start`, `reconcile.py:49`), and section 10 counts only days
  after `Frozen on:`.
- **Judge 409 blocking 1 (resolved):** piece 1's A2 code removal duplicated G10 part 2b (story/g10-part2b-release); piece
  1 was withdrawn. G10's seven edits are the G10 builder's (story/g10-protocol-edits); this plan's remaining protocol
  items go on top of them.
- **Judge 409 note:** keep every edited line within 120 characters (section 1.4's ATM line was 125).
- **Paused:** the owner's phase-1 scope freeze (21 Oct): piece 4 and the owner's dates wait for the owner's review.

## The owner's sign-off list (at the freeze commit)

- Section 11 items A-C (given 15 Oct), D ("3 B") and E (option 2), each quoted with its DESK_DECISIONS row.
- The four G7b wordings in sections 1.5 and 3.1 (judge 258 add. 3 PASS).
- G10's timeline as written in piece 1, with A2 dropped.
- Misses counted from each slot's `effective_start` (owner, 16 Oct, "Yes, from the declared start").
- The go-live date and the routine's 14:05 start.

## Appendix: response 157 as written (A16/G8 builder; branch `freeze/v4-checklist`, c3fe3b0d)

### Response 157: protocol v4 freeze checklist (prepared before ChatGPT review 113)

Prepared by the A16/G8 builder, who owns the freeze now (the G6 session no longer exists; orchestrator, 15 Oct 2026).
Lane 1: a judge and ChatGPT before the freeze commit. Nothing here is frozen yet.

#### Order
1. G10's text is merged (55726493: judge 161 addendum 3 PASS; ChatGPT review 113 answered in response 159, its fixes
   checked by the judge). Still to do: G10 built and merged: protocol section 1.6, the 14:30/14:40/15:10
   times in `terms.py`, G7's and M1's capture check at 14:30, G8's day labels, and **X's number** (computed from A16b's
   checked closes; it needs A16b's Drive archive).
2. **One protocol commit** with the text edits below (lane 1, judge).
3. **The freeze commit**: `research/forecasts/FREEZE_v4.md`, the ledger row (B4) with the slot registrations, the
   freeze check test, G8's registration adapter (judge, then ChatGPT, rule 9).
4. Go-live (the owner's routine change to 14:05 and the AI books' v4 prompt, G11) on the date the record states.

#### Protocol text edits (step 2), each checked against its source
| Item | Where | Text to add or change | Source |
|---|---|---|---|
| Section 11 E decided | 11 E and 5.3 | "**Decided: option 2** (owner, 15 Oct 2026): a window whose 2% days are more than 10% of its scored outcomes is not judgeable at that look, for every member (`confirmatory.crash_dominated`); at n = 125 a judgeable window holds at most 12 such days, so the 13+ band starts at n = 130" | `DESK_DECISIONS.md` 15 Oct ("G6 item E: option 2"); G8 built it |
| V6b stays scored | 5.6, 11 D/E | no edit needed: the protocol never wrote "V6 report-only" (checked: only V7 is descriptive-only, line 207); the record quotes the owner's row "V6b stays a scored member" | `DESK_DECISIONS.md` 15 Oct (row 182) |
| Intraday HAR skips void sessions | 3.1 | "**HAR (intraday)** forms its 1-, 5- and 22-session means over the usable (non-void) sessions; a void session is skipped, not a reason to be missing" (otherwise about 68% of days would have no V1 primary at A16's 5% voids) | judge 127, note for the G6 session; G7's code does this |
| Miss start: `effective_start` and "not started" | 4 (miss rule) | replace the start rule in section 4 (lines 179-181): "a **registered** slot counts misses from its `effective_start` (a session on or after the freeze, before its first eligible session, named in its registration row), so every baseline-observable day from then is observed or missed, even before its first forecast; an **unregistered** slot is `not_started`" (revision 2; replaces "from the first live forecast") | ChatGPT review 119; judge 156 notes 1 and 3 |
| Back-fills disclosed | 8 | "Run before the freeze, exploratory, never counted: G7's V6 back-fill (`f891d9b`, 2017-01-03 to 2026-10-14; `base_rate`, `v6_ewma_t4`) and M1's weather back-fill (`6b7eaba`, same days; `weather_vix_v1`, `weather_checklist_v0`), each labelled `backfill_exploratory`; G8's exploratory reports and demo look (response 126)" | the two commits; G8 claims |
| G10's changes | 1.2-1.6, 3.1, 4, 8, 10 | as G10 lists them (after ChatGPT 113) | story G10 |
| Long line | 4 | the one line over 120 characters ("such days, missing **any** ...") rewrapped | judge 156 note 2 |

#### FREEZE_v4.md (step 3), modelled on `FREEZE_v3.md`
- The protocol commit (step 2) and a line **`Frozen on: YYYY-MM-DD`** (G8 reads it; a look refuses without it; only
  live forecasts of later days count).
- The go-live date (G10) and the timeline it starts.
- **Byte-checked SHA-256** (protocol section 10): `PROTOCOL_v4.md`, `PROTOCOL_v4_calibration.md`, every file of
  `fno/forecast_v4/`, `tools/v4_*.py` and their committed `research/forecasts/v4_*.{json,md}` tables,
  `tests/fixtures/forecast_v4/v4_golden.json`, every file of `fno/forecast_v4_rules/` (G7), `fno/forecast_scoring/v4/`
  (G8), `fno/forecast_scoring/scores.py` (G4's log-score clip 0.01-0.99 and 10 calibration bins, which v4's reported
  scores use through `fno/forecast_scoring/v4/scores.py`; judge 177; the verdicts use `fno/forecast_v4/loss.py`), A16's
  V1 arithmetic and void rule `fno/intraday/realised_vol.py`, `session_rv.py`, `status.py` and `slots.py` (judge 177),
  and M1's own `METHOD_FILES` (`fno/weather/wiring.py:28-32`: `checklist_v0.py`, `v0_live.py`,
  `vix_scaled.py`, `colour.py`, `day.py`, `wiring.py`; the files M1's `method_sha256` covers, V6's rules slot,
  decision 70; orchestrator, 15 Oct), plus a seventh M1 file, `fno/weather/constants.py` (V6's colours and thresholds; `story/x-weather-constants`,
  judge 192 PASS, adds it to M1's `METHOD_FILES`). **The freeze commit comes after that move merges.**
- **Before the freeze commit (judge 189, judge B's condition):** G10 part 2's moved-after-cutoff flag, written by
  A16's 15:30 run into its rv row (orchestrator's go, 16 Oct), changes `fno/intraday/session_rv.py`, which is
  byte-checked; it lands before the freeze or becomes a new version.
- **Before the freeze commit (owner, 16 Oct):** A16's void-share count start (`story/a16-void-share-start`) changes
  `fno/intraday/session_rv.py`, which is byte-checked; it lands before the freeze.
- **Before the freeze commit (G7b, 16 Oct):** G8's V7 outcome moves to G7's `series.vix_up_outcomes` (one rule, as V6):
  `fno/forecast_scoring/v4/outcomes.py` drops its own `vix[i + horizon] > vix[i]` and `g7_series.py` adapts G7's
  function, with an equality test on the committed closes. Both files are byte-checked.
- **Also before the freeze commit (judge 206, response 213):** the look's reconciliation
  (`fno/forecast_scoring/v4/reconcile.py`, merged 4b8912fc/16e082a7 then replaced by `story/g8-look-reconcile`): a
  confirmatory look refuses while any scheduled AI slot-day up to its date has no v4 record row (G11 writes one per
  slot-day once settled). It changes `fno/forecast_scoring/v4/`, which is byte-checked.
- **Recorded, not byte-checked:** `fno/constants.py`, `fno/desk/settlement.py`, `fno/research_data/calendar.py`,
  `fno/research_engine/implied_vol.py` (section 10), plus `fno/intraday/rv_table.py` (V1's outcomes) and
  `fno/forecast/iv30.py` (frozen under v1-v3 already), and the rest of `fno/weather/` (the US flag and the card stay
  free).
- **Owner confirmations quoted, each with its `docs/DESK_DECISIONS.md` row (all 15 Oct 2026):** items A, B, C
  ("A accept, B accept, C accept", line 121); D ("3 B", line 123); E ("merge G6, E option 2", line 157); the miss caps
  ("Both 10%", line 177); the 60-minute fill decides (line 181); V6b stays a scored member (line 182); the v4 timeline
  (line 184), flagged not blocked (line 185), lateness (line 186) and honest times with the 14:40 window (line 194).
  **Confirmed by the owner on 16 Oct 2026 (line 213):** misses count from each slot's declared `effective_start`
  ("Yes, from the declared start (Recommended)"), replacing "from the first live forecast" in line 177's rule. **Recorded
  (line 214):** v4 freezes with V6a and V6b (V1 when A16 is ready); V2-V5 later in G7 phase 2 under their own record.
  The freeze commit still needs the owner's final sign-off after the build passes. Line numbers as on main today; the record quotes each row's text too, so a later insertion cannot misdirect it.
- **Disclosures:** both back-fills (above); the 2017-26 base rates (section 8); G8's exploratory runs.
- **V1's method pinned (judge 177, should-fix 1, option b with a):** the record names A16's method `rv-quote-15m-v1`
  (`fno/intraday/realised_vol.py:49`), and V1 counts only A16 rows of that method: `series.live_intraday_rv` today
  ignores the rows' `method` column, so a new sampling method (A16's own rule above 5% voids) would feed V1 silently.
  This is a G7 change before the freeze, with a test (a row of another method is not read). The four A16 files above
  are byte-checked too, so the pinned method's arithmetic cannot change in place. Built and PASSED (732db7e, judge 177
  addendum 4). **The record says in one line (judge B's note):** a row of another method is skipped, not void, so if
  A16 ever writes a new method, V1 stops resolving (no outcome, no score) until a new freeze record pins it.
- **Slot registrations** (ledger rows G8 reads): V6a and V6b `rules` = `weather_vix_v1` (decision 70); V1 `rules` =
  `v1_close_blend` (G7) once V1 starts; V2 `rules`: none yet (phase 2); every `hybrid` and `ai_team` slot: none until
  G11 registers the AI books' v4 versions. An empty slot stays at p = 1. **Later registrations** (V1 rules when V1
  starts, the G11 AI slots) are appended ledger rows, each before its slot's first counted forecast (protocol section
  6); G8's adapter reads every row, not only the freeze's. **The ledger adapter refuses a row whose `effective_start`
  is after its slot's first eligible session (judge 184's note):** a later start would hide misses, and nothing checks
  that yet. It is built with the freeze's ledger adapter, with a test.

#### Code in the freeze commit (step 3)
- A freeze check test like `tests/forecast/test_freeze_v2.py`: every byte-checked file still has its hash (the golden
  fixture's included), and the record's protocol commit is in history.
- G7: `series.live_intraday_rv` reads only rows whose `method` is the pinned one (test: a row of another method is
  not read).
- G8's slot registry adapter reading the ledger row (one class plus one line in `fno/forecast_scoring/v4/wiring.py`),
  replacing `NoRegistrations`.

#### Settled by the orchestrator (15 Oct)
- Go-live date: set once ChatGPT 113 and the freeze review pass; planned for 22-23 Oct 2026 (21-23 are sessions, 20 is
  a holiday). The record keeps `YYYY-MM-DD` until then.
- `fno/weather/`: only M1's `METHOD_FILES` are byte-checked; the rest is recorded, not checked.

#### Revision 1: judge 177 (FAIL, 3 should-fix): all accepted

1. **V1's inputs not frozen (accepted; strong evidence: `fno/forecast_v4_rules/series.py:79-86` reads `status` and
   `rv_session`, never `method`).** Both of the judge's options: (b) the record pins A16's method `rv-quote-15m-v1` and
   G7 reads only that method's rows (a G7 change with a test, before the freeze), so a new A16 method cannot feed V1
   silently; and (a) A16's `realised_vol.py`, `session_rv.py`, `status.py` and `slots.py` are byte-checked, so the
   pinned method cannot change in place. (b) alone would let an in-place edit through; (a) alone would let a wiring
   switch to a new class through (reasoning only).
2. **`fno/forecast_scoring/scores.py` byte-checked** (G4's clip and bins behind v4's reported log score and
   calibration).
3. **Register:** the "G6 freeze" row now names this session as owner, with its status.
Notes: later registrations are appended ledger rows read in full; the golden fixture's hash is in the freeze test;
each owner quote carries its `DESK_DECISIONS.md` row and date.

#### Revision 2: ChatGPT review 119 (CHANGE, 2 points), accepted by the orchestrator

1. **IV30 and Black-76 are not in v4's live path today (traced; strong evidence).** Importing all 48 modules of
   `fno/forecast_v4/`, `fno/forecast_v4_rules/`, `fno/forecast_scoring/v4/` and `fno/weather/` never loads
   `fno/forecast/iv30.py`. It loads `fno/research_engine/implied_vol.py` only as an import side effect:
   `forecast_v4_rules/wiring.py` and `weather/wiring.py` import `INTRADAY_FOLDER` from `fno/intraday/wiring.py`, whose
   alert sender comes from `fno/composition.py`, which imports `Black76`. No v4 function calls it; a grep finds no
   use outside `forecast_v4/units.py`'s own arithmetic.
   - **Proof in the freeze code:** a test runs one real day of G7's capture, M1's weather and G8's report with
     `Black76` and `PanelAtmIv30` replaced by objects that raise if called; the outputs equal the unpatched run.
   - **Said plainly:** the questions that would need IV30 or Black-76 (V2 and V3's premium-adjusted and raw implied
     baselines, V4, V5) have no code yet (G7 phase 2). Under this freeze only V6a and V6b count (and V1 once A16 has
     20 sessions). V2-V5 start counting only under a later freeze record that byte-checks their code, then including
     `iv30.py` and `implied_vol.py`. Constants and the calendar are not frozen in bulk (unchanged).
2. **Prospective start for a registered slot (accepted).** Each slot registration names an `effective_start`, a
   session on or after the freeze and before the slot's first eligible session. From that day every
   baseline-observable day counts as observed or missed, even before the slot's first forecast, so a registered
   family cannot avoid misses by delaying its first submission. A slot not yet registered stays `not_started`. This
   replaces G9's "from the first live forecast" for registered slots (a G8 change in `scoring._miss_start`, built with
   the freeze code; the protocol's section 4 line says it). Test: a registered AI slot with `effective_start` day 1
   misses days 1-3 and submits on day 4, giving 3 misses.
3. **V1's method filter is not built yet** (confirmed). Its test uses the same dates with an `rv-quote-15m-v1` row and
   a row of a new method: only the v1 row is read. It is built and judged with its test before the freeze commit.
