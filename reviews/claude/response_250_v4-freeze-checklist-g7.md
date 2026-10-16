# Response 250: protocol v4 freeze checklist, G7's side (for the owner, about 21 Oct 2026)

From the R2/G7 builder (session 0185gR5DmoDh2zBAvgRU4CEB), at the orchestrator's request, 16 Oct 2026 IST. G7 phase 1 and G7b
part a are merged (8367029a). This lists what must happen at or before the v4 freeze (planned 22-23 Oct) for G7's
forecasters to count, with one owner per line (10 lines; 9 and 10 added after the orchestrator's
notes of 16 Oct). Evidence labels as the project uses them.

## Why it matters, in one line

Today **no G7 forecast is live**. Every row in `research/forecasts/v4/` is the exploratory back-fill (strong evidence:
no `live` label in any G7 file; no workflow or routine runs `forecast-v4 capture` or `weather capture`). Only forecasts
made after the freeze count (protocol 8), so a freeze without item 2 gives the stop rule's Test A nothing to count from
G7 or M1.

## The checklist

| # | Item | Owner | State on 16 Oct |
|---|---|---|---|
| 1 | **Ledger registration (B4) with the freeze**: V1 `rules` = `v1_close_blend`; V2 `rules` = `v2_close_blend`; V6a and V6b `rules` = M1's weather model (decision 70; `v6_ewma_t4` reported only); V7's three slots stay at p = 1 (descriptive only, `terms.DESCRIPTIVE_ONLY`); `hybrid` and `ai_team` slots = G11's books, or empty (p = 1) if G11 is not live by then | G6 freeze session (01MgTu3L1T3y6R18ATTwbFub) writes the rows; ids from me (G7), M1 (013xqaNTCbSBytKgqpfaYFqZ) and G11 (01XFXpbkyixX7SuXeQCp5EnX) | ids exist in code (`fno/constants.py`, `fno/forecast_v4_rules/constants.py`); rows not written |
| 2 | **Live capture from the freeze day, before 14:30 IST**: O1's daily run already has both steps (`weather capture`, `forecast-v4 capture`, each from `config.yaml daily.live_from`), **but the routine starts at 14:33**, and both captures refuse from 14:30:00 (G10), so as it stands every day writes nothing: a miss for every G7 and M1 slot. Fix: the routine starts at 14:05 from the freeze day (G10's planned go-live time), and `daily.live_from.weather` and `.forecasts_v4` are set to the freeze date | the owner (routine time, `live_from` dates); O1 builder (014zYLf18PgCzR7YoHs1X5Dp) confirms the step order | O1 passed, merges once main is green; the O1 builder confirmed the reading (strong evidence: the code) |
| 3 | **Back-fill regenerated on the frozen code**: `python -m fno forecast-v4 backfill` after deleting G7's folders, in the freeze commit if any G7 method file changed since; disclosed in `FREEZE_v4.md` as exploratory (protocol 8) | me (G7) | gate in place: `test_every_committed_g7_record_row_carries_this_trees_method_hash` fails on a stale back-fill |
| 4 | **G8 reads V7 from G7's rule** (`series.vix_up_outcomes`) before the freeze commit, then G7's gap fix (a missing VIX close voids V7, judge 267's note) with its `sessions` argument | A16/G8 builder (01VK88LxJvV1Gi7Wbr3D4fzp), then me | G8 switch PASSED (judge 267), waits for main to be green; my fix `story/g7b-vix-gaps` 19e681a5 PASSED (judge 268), merges after G8's switch with the `sessions` argument in G8's adapter |
| 5 | **The owner signs the four G7b wordings** in `PROTOCOL_v4.md` (1.5: V5's `first_seen_at` fallback; 3.1: flagged IV30 gives no implied value; V4/V5 base rates live only; trailing and EWMA read the last session before `d`) | the owner, with the freeze | drafted and judged (judge 258 add. 3 PASS); a test reads them |
| 6 | **`FREEZE_v4.md` hashes G7's files** that decide a baseline or forecast: `fno/forecast_v4_rules/{series,baselines,rules,vix_rule,capture,records,constants,wiring}.py` (wiring: the method-file list and the record folder) | G6 freeze session | not written (the freeze record does not exist yet) |
| 7 | **Main green before the freeze commit**: 3 risk tests fail on main since A14c's 2026-10-16 stress-factor row (df9bfaff; factor 2.1 against the pinned 1.45 seed) | A14c owner (01Vm1WnH8i9waM8EJG8zwWqg) | red; reported to the orchestrator 16 Oct |
| 8 | **G10 part 2's `pack_sha256` column** in G7's records, if it lands before the freeze: same commit regenerates the back-fill (item 3) | A16/G8 builder proposes, I build | agreed, not started |
| 9 | **`fno/ai/v4_rows.py` is hashed in `FREEZE_v4.md`** (judge 275's condition): it decides which AI book-days become misses (every failed run a miss, a pending day no row), so it decides scored outcomes like G7's files. Hash it beside item 6's list | G6 freeze session; G11 builder (01XFXpbkyixX7SuXeQCp5EnX) confirms the file list | merged with G11 round 1; not yet in any freeze list |
| 10 | **M1's committed rows carry a stale method hash** (2495d512 against the tree's 6a295227): M1's METHOD_FILES include `fno/forecast_v4/terms.py`, which G10 changed (`V4_LATEST_FIRE`). Fix as G7's: M1 regenerates its back-fill on the frozen code in the freeze commit (values unchanged, only the hash moves) and adds the same gate test G7 has (every committed row's `method_sha256` equals the tree's hash), so a stale hash fails the gates instead of a re-run refusing later. Said plainly: G7's METHOD_FILES do not include `terms.py`, so G7's hash cannot catch a `terms` change; that is covered because `FREEZE_v4.md` hashes every file of `fno/forecast_v4/` itself, and before the freeze every row is exploratory | M1 builder (013xqaNTCbSBytKgqpfaYFqZ) | found by the G10 builder 16 Oct; not fixed |

## Item 2: the capture time (for the owner's choice)

- **What O1 does** (story/o1-daily-run, read 16 Oct): one command, `python -m fno daily run`, started by the owner's
  routine at 14:33 IST. It runs the steps in order: the quote parts start, then A14c's margin check, then `weather capture`
  and `forecast-v4 capture` as child processes, each live only from its `daily.live_from` date (null today).
- **Why 14:33 fails:** both captures compare the clock with the 14:30:00 cutoff (`capture_day`,
  `terms.V4_CAPTURE_START`, G10's single clock for every family). At 14:33 they print "nothing written" and exit 0, so
  every day would be a miss under G9. Strong evidence: the code on both branches.
- **The inputs are not the problem:** both read committed closes up to `d-1` only, so the content is identical at any time
  on `d`. Loosening the cutoff for them would break G10's rule that no family gets more time than another, so it is not
  proposed.
- **Recommended root fix: the routine starts at 14:05 from the freeze day.** This is the time G10 already set for
  go-live (owner's "v4 timeline" row). The two steps then run around 14:06-14:10; the quote parts start at 14:05 and wait
  for their 14:30-14:40 window. Reasoning only for the minutes; the O1 builder confirms the order.
- **Alternative:** a second, earlier scheduled fire of the same command that runs only the two steps. More moving parts;
  only if the routine cannot move.
- **Not proposed:** an Actions cron. GitHub started morning crons 4-5 hours late (register row "A14 cron early").
- A late day stays honest either way: a step that reaches the check at or after 14:30 writes nothing and says so.
- **O1 builder's answer (16 Oct):**
  - The reading is right. At 14:33 both steps are recorded `refused`, one alert each, and the day ends "day done with
    problems: weather, forecasts_v4". So the miss is loud, but it would happen every day.
  - They reject the second fire: two schedules, one run log and one checkout is the race O1 removed. Agreed.
  - **Order (O1 follow-up, lane 1, judge D):** run weather and forecasts_v4 before `margin_check` (up to 600 s), so
    nothing that can block sits before them except the 120 s history fetch and E2c's Drive download. That Drive
    download has per-request timeouts but no overall limit, so a slow Drive day could push the captures past 14:30.
    **Root fix agreed (O1 builder):** both captures start as child processes at the run's start, before the history
    fetch and the Drive download, as O1 already does for the quote parts. They read no private file. Each result is
    recorded and committed in its own step. Both changes go into one O1 follow-up story for judge D, sent to G7 and M1
    before any code; until then both steps stay `not_live`.
  - **Gate:** `daily.live_from.weather` and `.forecasts_v4` are set no earlier than the first day the stored routine
    starts at 14:05, in the same commit as the CLAUDE.md start-time line.
  - G7 agrees with both. M1's builder confirms for the weather step.

## Not in this freeze (said plainly)

- **V1** shows `not_started` until A16 has 20 live non-void sessions (first live session 16 Oct; earliest about
  mid-November, some evidence). Nothing to do at the freeze.
- **V2's primary baseline** (premium-adjusted implied) does not exist until G10's pack and G7b part b. Until then every
  V2 pair is missing (counted, never filled), so V2 cannot be judged even with `v2_close_blend` registered. V3, V5
  and the implied baselines come later under their own record (decision of 16 Oct); V4 waits for G11.
- **A missing VIX close** in a future O6 row: G8 stops (`VixCloseMissing`: "VIX close missing for <day>: fill it via O6", exit 1) when a regular session lacks its VIX close, while G7's `vix_up_outcomes` leaves that day unresolved. No v4 report runs until O6 fills it. Accepted: a quiet void would also move G8's comparison regimes (orchestrator, 16 Oct; G8's line on story/g8-vix-missing-line, G7's on story/g7b-vix-gaps, judge 268 PASS). No committed regular close lacks VIX today (strong evidence: 2,411 of 2,411).
- Honest expectation (protocol 11 D): V1, V2 and V6a will almost surely never be claimed; only V6b can be, slowly.
  The freeze makes the record countable; it does not make any forecaster good.
