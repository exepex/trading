# Response 162: LR1 weekly post-mortem v1, story text and claims (for the judge)

**Story text:** `docs/stories/LR-learning.md`, LR1. Branch `story/lr1-weekly-postmortem`. Issue #106, REPLAN slice A
item 13. Lane 1 (new story, Slack, a new schedule). No code yet: code starts only after a judge PASS of this text.

## What LR1 v1 is

One Saturday report, to #fno-desk and `research/postmortems/<YYYY>/<week-ending>.{md,json}`, with three sections only:
forecasts (read from the committed G4 and G8 reports), weather (M1's records plus G7's V6a outcome rule) and data health
(3 pm capture markers and sidecars, T1 deliveries, A16 session count). It reports; it never decides or changes a trade.

## Claims

| # | Claim | Evidence |
|---|---|---|
| 1 | Slice A's LR1 covers only forecasts, weather and data health. | Strong: `REPLAN.md` slice A item 13; issue #106. |
| 2 | No score is computed a second way: v4 numbers are copied from G8's committed report JSON, v1-v3 lines are G4's own `weekly_summary`; "new this week" is a subtraction of two committed counts. | Strong (by design; test 7 enforces it by import check, test 4 by equality). |
| 3 | No v4 report is written by any schedule today (`research/forecasts/v4_scores/` does not exist on `main`; no workflow runs `forecast-v4-scores`), so LR1's job must run G8's own `report` command first. | Strong: `ls` on main 35e999a; `grep` of `.github/workflows/`. |
| 4 | G4 already posts a Monday summary to #fno-desk (`forecast-scores.yml`, cron `41 3 * * 1`). Two weekly score posts would duplicate one function. | Strong: the workflow file. |
| 5 | The weather miss rule (GREEN day followed by a 2% move) is design 4.3's own confident-miss case for weather, and its outcome comes from the one V6 rule (`series.big_move_outcomes`), not a new one. | Strong: design 04 section 4.3; G8's `outcomes.py` uses the same function. |
| 6 | Weather records on `main` today are back-fill only (`label: backfill_exploratory`); live weather capture is scheduled only at the v4 freeze (M1 Out list). So until then the weather section is exploratory. | Strong: `research/forecasts/v4/weather/2026/2026-10-14.json`; `docs/stories/M-weather.md` line 141. |
| 7 | Dropping the AI writer and devil's advocate from v1 loses nothing now: the text is code-built lines with no free prose to check, and it saves AI cost. | Reasoning only. |
| 8 | Size S: about 6 small modules, each well under 350 lines, plus one workflow. | Some evidence (comparable: T1's `fno/cards/` modules are 36-122 lines each). |

## Questions for the orchestrator (owner where noted)

1. **G4's Monday post.** Options: (A) LR1's workflow replaces it: remove the Monday step from `forecast-scores.yml`
   in LR1's change (G4's daily scoring stays); (B) keep both posts. **Recommendation: A** (one weekly report; the G4
   lines are in LR1 unchanged). This touches G4's workflow, so it needs your go (one builder per function).
2. **AI writer and devil's advocate** (REPLAN text says "an AI writer may cite only them; the devil's advocate
   reviews"). Options: (A) out of v1, added with T3 in slice B; (B) in v1. **Recommendation: A** (reasoning only: no
   prose to check yet, no budget used, keeps it S). The owner should confirm since the REPLAN text names them.
3. **Day and time.** Design 4.3 says Saturday, "owner may pick the day". Proposed Saturday 10:41 IST. Any other choice
   is one cron line.

## Known limits (also in the story text)

Exploratory before the v4 freeze; "new this week" is a count difference, not a weekly score; late files show next
week; no Groww-vs-NSE agreement or A11 revisions in v1; no Slack retry (the repository copy stays).
