# Response 156: protocol v4 freeze checklist (prepared before ChatGPT review 113)

Prepared by the A16/G8 builder, who owns the freeze now (the G6 session no longer exists; orchestrator, 15 Oct 2026).
Lane 1: a judge and ChatGPT before the freeze commit. Nothing here is frozen yet.

## Order
1. ChatGPT review 113 of G10 (response 155) answered; G10 built and merged: protocol section 1.6, the 14:30/14:40/15:10
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
  (G8) and `fno/weather/` (M1, V6's rules slot, decision 70).
- **Recorded, not byte-checked:** `fno/constants.py`, `fno/desk/settlement.py`, `fno/research_data/calendar.py`,
  `fno/research_engine/implied_vol.py` (section 10), plus `fno/intraday/rv_table.py` (V1's outcomes) and
  `fno/forecast/iv30.py` (frozen under v1-v3 already).
- **Owner confirmations quoted:** items A, B, C ("A accept, B accept, C accept"); D ("3 B"); E ("merge G6, E option 2");
  "V6b stays a scored member"; the miss caps ("Both 10%", G9); the v4 timeline rows (G10). Each with its date.
- **Disclosures:** both back-fills (above); the 2017-26 base rates (section 8); G8's exploratory runs.
- **Slot registrations** (the ledger row G8 reads): V6a and V6b `rules` = `weather_vix_v1` (decision 70); V1 `rules` =
  `v1_close_blend` (G7) once V1 starts; V2 `rules`: none yet (phase 2); every `hybrid` and `ai_team` slot: none until
  G11 registers the AI books' v4 versions. An empty slot stays at p = 1.

## Code in the freeze commit (step 3)
- A freeze check test like `tests/forecast/test_freeze_v2.py`: every byte-checked file still has its hash, and the
  record's protocol commit is in history.
- G8's slot registry adapter reading the ledger row (one class plus one line in `fno/forecast_scoring/v4/wiring.py`),
  replacing `NoRegistrations`.

## Open before the freeze (to the owner or the orchestrator)
- The go-live date (G10 says about a week).
- Whether `fno/weather/` is byte-checked in full (it holds M1's v0 checklist too) or only its V6 model files; proposed:
  in full (simplest, nothing in it changes after the freeze without a new version).
