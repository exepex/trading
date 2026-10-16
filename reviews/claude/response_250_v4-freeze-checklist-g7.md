# Response 250: protocol v4 freeze checklist, G7's side (for the owner, about 21 Oct 2026)

From the R2/G7 builder (session 0185gR5DmoDh2zBAvgRU4CEB), at the orchestrator's request, 16 Oct 2026 IST. G7 phase 1 and G7b
part a are merged (8367029a). This lists what must happen at or before the v4 freeze (planned 22-23 Oct) for G7's
forecasters to count, with one owner per line. Evidence labels as the project uses them.

## Why it matters, in one line

Today **no G7 forecast is live**. Every row in `research/forecasts/v4/` is the exploratory back-fill (strong evidence:
no `live` label in any G7 file; no workflow or routine runs `forecast-v4 capture` or `weather capture`). Only forecasts
made after the freeze count (protocol 8), so a freeze without item 2 gives the stop rule's Test A nothing to count from
G7 or M1.

## The checklist

| # | Item | Owner | State on 16 Oct |
|---|---|---|---|
| 1 | **Ledger registration (B4) with the freeze**: V1 `rules` = `v1_close_blend`; V2 `rules` = `v2_close_blend`; V6a and V6b `rules` = M1's weather model (decision 70; `v6_ewma_t4` reported only); V7's three slots stay at p = 1 (descriptive only, `terms.DESCRIPTIVE_ONLY`); `hybrid` and `ai_team` slots = G11's books, or empty (p = 1) if G11 is not live by then | G6 freeze session (01MgTu3L1T3y6R18ATTwbFub) writes the rows; ids from me (G7), M1 (013xqaNTCbSBytKgqpfaYFqZ) and G11 (01XFXpbkyixX7SuXeQCp5EnX) | ids exist in code (`fno/constants.py`, `fno/forecast_v4_rules/constants.py`); rows not written |
| 2 | **Live capture from the freeze day, before 14:30 IST**: O1's daily run already has both steps (`weather capture`, `forecast-v4 capture`, each from `config.yaml daily.live_from`), **but the routine starts at 14:33**, and both captures refuse from 14:30:00 (G10), so as it stands every day writes nothing: a miss for every G7 and M1 slot. Fix: the routine starts at 14:05 from the freeze day (G10's planned go-live time), and `daily.live_from.weather` and `.forecasts_v4` are set to the freeze date | the owner (routine time, `live_from` dates); O1 builder (014zYLf18PgCzR7YoHs1X5Dp) confirms the step order | O1 passed, merges once main is green; timing asked of the O1 builder 16 Oct |
| 3 | **Back-fill regenerated on the frozen code**: `python -m fno forecast-v4 backfill` after deleting G7's folders, in the freeze commit if any G7 method file changed since; disclosed in `FREEZE_v4.md` as exploratory (protocol 8) | me (G7) | gate in place: `test_every_committed_g7_record_row_carries_this_trees_method_hash` fails on a stale back-fill |
| 4 | **G8 reads V7 from G7's rule** (`series.vix_up_outcomes`) before the freeze commit, then G7's gap fix (a missing VIX close voids V7, judge 267's note) with its `sessions` argument | A16/G8 builder (01VK88LxJvV1Gi7Wbr3D4fzp), then me | G8 switch PASSED (judge 267), waits for main to be green; my fix `story/g7b-vix-gaps` 19e681a5 with judge B |
| 5 | **The owner signs the four G7b wordings** in `PROTOCOL_v4.md` (1.5: V5's `first_seen_at` fallback; 3.1: flagged IV30 gives no implied value; V4/V5 base rates live only; trailing and EWMA read the last session before `d`) | the owner, with the freeze | drafted and judged (judge 258 add. 3 PASS); a test reads them |
| 6 | **`FREEZE_v4.md` hashes G7's files** that decide a baseline or forecast: `fno/forecast_v4_rules/{series,baselines,rules,vix_rule,capture,records,constants,wiring}.py` (wiring: the method-file list and the record folder) | G6 freeze session | not written (the freeze record does not exist yet) |
| 7 | **Main green before the freeze commit**: 3 risk tests fail on main since A14c's 2026-10-16 stress-factor row (df9bfaff; factor 2.1 against the pinned 1.45 seed) | A14c owner (01Vm1WnH8i9waM8EJG8zwWqg) | red; reported to the orchestrator 16 Oct |
| 8 | **G10 part 2's `pack_sha256` column** in G7's records, if it lands before the freeze: same commit regenerates the back-fill (item 3) | A16/G8 builder proposes, I build | agreed, not started |

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

## Not in this freeze (said plainly)

- **V1** shows `not_started` until A16 has 20 live non-void sessions (first live session 16 Oct; earliest about
  mid-November, some evidence). Nothing to do at the freeze.
- **V2's primary baseline** (premium-adjusted implied) does not exist until G10's pack and G7b part b. Until then every
  V2 pair is missing (counted, never filled), so V2 cannot be judged even with `v2_close_blend` registered. V3, V5
  and the implied baselines come later under their own record (decision of 16 Oct); V4 waits for G11.
- Honest expectation (protocol 11 D): V1, V2 and V6a will almost surely never be claimed; only V6b can be, slowly.
  The freeze makes the record countable; it does not make any forecaster good.
