# Response 157: protocol v4 freeze checklist (prepared before ChatGPT review 113)

Prepared by the A16/G8 builder, who owns the freeze now (the G6 session no longer exists; orchestrator, 15 Oct 2026).
Lane 1: a judge and ChatGPT before the freeze commit. Nothing here is frozen yet.

## Order
1. G10's text is merged (55726493: judge 161 addendum 3 PASS; ChatGPT review 113 answered in response 159, its fixes
   checked by the judge). Still to do: G10 built and merged: protocol section 1.6, the 14:30/14:40/15:10
   times in `terms.py`, G7's and M1's capture check at 14:30, G8's day labels, and **X's number** (computed from A16b's
   checked closes; it needs A16b's Drive archive).
2. **One protocol commit** with the text edits below (lane 1, judge).
3. **The freeze commit**: `research/forecasts/FREEZE_v4.md`, the ledger row (B4) with the slot registrations, the
   freeze check test, G8's registration adapter (judge, then ChatGPT, rule 9).
4. Go-live (the owner's routine change to 14:05 and the AI books' v4 prompt, G11) on the date the record states.

## Protocol text edits (step 2), each checked against its source
| Item | Where | Text to add or change | Source |
|---|---|---|---|
| Section 11 E decided | 11 E and 5.3 | "**Decided: option 2** (owner, 15 Oct 2026): a window whose 2% days are more than 10% of its scored outcomes is not judgeable at that look, for every member (`confirmatory.crash_dominated`); at n = 125 a judgeable window holds at most 12 such days, so the 13+ band starts at n = 130" | `DESK_DECISIONS.md` 15 Oct ("G6 item E: option 2"); G8 built it |
| V6b stays scored | 5.6, 11 D/E | no edit needed: the protocol never wrote "V6 report-only" (checked: only V7 is descriptive-only, line 207); the record quotes the owner's row "V6b stays a scored member" | `DESK_DECISIONS.md` 15 Oct (row 182) |
| Intraday HAR skips void sessions | 3.1 | "**HAR (intraday)** forms its 1-, 5- and 22-session means over the usable (non-void) sessions; a void session is skipped, not a reason to be missing" (otherwise about 68% of days would have no V1 primary at A16's 5% voids) | judge 127, note for the G6 session; G7's code does this |
| Freeze start and "not started" | 4 (miss rule) | already in section 4 (lines 179-181); add: "a forecaster that starts only after the freeze counts misses from its first live forecast; the days before it are not started" | judge 156 notes 1 and 3 |
| Back-fills disclosed | 8 | "Run before the freeze, exploratory, never counted: G7's V6 back-fill (`f891d9b`, 2017-01-03 to 2026-10-14; `base_rate`, `v6_ewma_t4`) and M1's weather back-fill (`6b7eaba`, same days; `weather_vix_v1`, `weather_checklist_v0`), each labelled `backfill_exploratory`; G8's exploratory reports and demo look (response 126)" | the two commits; G8 claims |
| G10's changes | 1.2-1.6, 3.1, 4, 8, 10 | as G10 lists them (after ChatGPT 113) | story G10 |
| Long line | 4 | the one line over 120 characters ("such days, missing **any** ...") rewrapped | judge 156 note 2 |

## FREEZE_v4.md (step 3), modelled on `FREEZE_v3.md`
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
  decision 70; orchestrator, 15 Oct).
- **Recorded, not byte-checked:** `fno/constants.py`, `fno/desk/settlement.py`, `fno/research_data/calendar.py`,
  `fno/research_engine/implied_vol.py` (section 10), plus `fno/intraday/rv_table.py` (V1's outcomes) and
  `fno/forecast/iv30.py` (frozen under v1-v3 already), and the rest of `fno/weather/` (the US flag and the card stay
  free).
- **Owner confirmations quoted, each with its `docs/DESK_DECISIONS.md` row (all 15 Oct 2026):** items A, B, C
  ("A accept, B accept, C accept", line 121); D ("3 B", line 123); E ("merge G6, E option 2", line 157); the miss caps
  ("Both 10%", line 177); the 60-minute fill decides (line 181); V6b stays a scored member (line 182); the v4 timeline
  (line 184), flagged not blocked (line 185), lateness (line 186) and honest times with the 14:40 window (line 194).
  Line numbers as on main today; the record quotes each row's text too, so a later insertion cannot misdirect it.
- **Disclosures:** both back-fills (above); the 2017-26 base rates (section 8); G8's exploratory runs.
- **V1's method pinned (judge 177, should-fix 1, option b with a):** the record names A16's method `rv-quote-15m-v1`
  (`fno/intraday/realised_vol.py:49`), and V1 counts only A16 rows of that method: `series.live_intraday_rv` today
  ignores the rows' `method` column, so a new sampling method (A16's own rule above 5% voids) would feed V1 silently.
  This is a G7 change before the freeze, with a test (a row of another method is not read). The four A16 files above
  are byte-checked too, so the pinned method's arithmetic cannot change in place.
- **Slot registrations** (ledger rows G8 reads): V6a and V6b `rules` = `weather_vix_v1` (decision 70); V1 `rules` =
  `v1_close_blend` (G7) once V1 starts; V2 `rules`: none yet (phase 2); every `hybrid` and `ai_team` slot: none until
  G11 registers the AI books' v4 versions. An empty slot stays at p = 1. **Later registrations** (V1 rules when V1
  starts, the G11 AI slots) are appended ledger rows, each before its slot's first counted forecast (protocol section
  6); G8's adapter reads every row, not only the freeze's.

## Code in the freeze commit (step 3)
- A freeze check test like `tests/forecast/test_freeze_v2.py`: every byte-checked file still has its hash (the golden
  fixture's included), and the record's protocol commit is in history.
- G7: `series.live_intraday_rv` reads only rows whose `method` is the pinned one (test: a row of another method is
  not read).
- G8's slot registry adapter reading the ledger row (one class plus one line in `fno/forecast_scoring/v4/wiring.py`),
  replacing `NoRegistrations`.

## Settled by the orchestrator (15 Oct)
- Go-live date: set once ChatGPT 113 and the freeze review pass; planned for 22-23 Oct 2026 (21-23 are sessions, 20 is
  a holiday). The record keeps `YYYY-MM-DD` until then.
- `fno/weather/`: only M1's `METHOD_FILES` are byte-checked; the rest is recorded, not checked.

## Revision 1: judge 177 (FAIL, 3 should-fix): all accepted

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
