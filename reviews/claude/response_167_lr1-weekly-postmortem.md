# Response 167: LR1 weekly post-mortem v1, story text and claims (for the judge)

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

## Revision 1 (after the owner's answers, 15 Oct 2026, relayed by the orchestrator)

Owner: Q1 "one report": G4's Monday post is retired and LR1 carries its lines (`forecast-scores.yml` change is part
of LR1's judged change). Q2: the AI writer and the devil's advocate are **in v1**, the simple way. Q3: Saturday
10:41 IST. The story text changed in Q1 and Q2; the forecasts, weather and data-health parts are unchanged.

What changed (story text `docs/stories/LR-learning.md`):
- Two steps: `postmortem weekly --post` (10:41) writes the lines and fires the writer; `postmortem publish` (11:41)
  checks and posts once.
- The writer is fired through the existing `RoutineTrigger` / `RoutineFireTrigger` / `UnconfiguredTrigger` and
  `FireFailed` (the AI books' path in `fno/ai/fire.py`), with a pointer holding only the Saturday and the lines file's
  SHA-256. Its routine records its run with F8's `record-usage --self-timed --purpose books_and_roles`. It is not fired
  when BG1's signal is `stop` (design 7.6 stops the post-mortem writer before the advocate). No second AI caller.
- The devil's advocate is a **code** check of four rules: the SHA line, size and no links or mentions, every number
  in the prose appears verbatim in the lines, and no numbers in words. Any failure drops the prose: the lines are
  posted alone with one alert. The lines are posted in every case.
- Nothing the AI writes can decide a trade: only `publish.py` reads the prose file (AST test).

New claims:

| # | Claim | Evidence |
|---|---|---|
| 9 | The fire path is reused, not rebuilt: `RoutineTrigger.fire(pointer: FiredText)` takes any one-line pointer. | Strong: `fno/pipeline/trigger.py`. |
| 10 | F8 records a fired routine's usage only by its own timing record (`record-usage --self-timed`); tokens are unknown. | Strong: `fno/budget/self_timed.py` docstring. |
| 11 | BG1's stop order names the "post-mortem writer" before the advocate and the AI forecasters. | Strong: `AI_ROLE_STOP_ORDER` in `fno/budget/constants.py`. |
| 12 | A code number check is surer than a second AI for "every number matches the lines". | Reasoning only. Its limit (meaning is not checked) is in Known limits. |

Open point for the orchestrator (not blocking the judge): I read "the devil's advocate checks every number in the
prose against the lines" as a code check. If the owner meant a second AI call, that is T3's objection role and adds
one more routine plus its budget line; say so and I revise.

## Revision 2 (owner, 15 Oct 2026, relayed by the orchestrator: the devil's advocate is BOTH)

The owner chose both: the exact code check of the numbers and a second AI that reads the report and raises
objections (REPLAN's devil's advocate, the role T3 uses, issue #105). Judge 167 addendum 1's note is applied too.

What changed in `docs/stories/LR-learning.md`:
- **One routine, two steps** (the owner asked for small setup): step 1 writes the summary, step 2 reads only the
  committed lines and summary and writes at most 5 objections, each tied to a line `[L<n>]`. It is one fire, has one
  F8 self-timed record (`role_or_bundle` "weekly post-mortem: writer and devil's advocate"), and BG1 `stop` skips both.
- **The objecting AI is built once, for T3:** `fno/advocate/` holds the `Advocate` port, the `RoutineFileAdvocate`
  adapter, `ObjectionCheck`, and the shared number tokenizer and `NumberCheck`. `publish` depends only on the port.
  My register row says T3 reuses it.
- **The objections are their own labelled section**, checked for form and numbers. They never change a number. A
  failure or missing setup gives "advocate not run: <reason>" and nothing else changes.
- **Rule 3 matches whole number tokens** (judge 167 addendum 1): "4 sessions" against "40%" fails (test 13).
- **The owner's setup checklist** is in the text: one routine, two secrets, one hand-run check.

New claims:

| # | Claim | Evidence |
|---|---|---|
| 13 | F8 accepts a bundle name for one session that works for two roles. | Strong: `usage_ledger.py` column `role_or_bundle`; `record-usage --role` is free text. |
| 14 | One routine is enough: both steps read only committed files and the fire path takes one pointer. | Some evidence (the AI books do the same with one routine per book). |
| 15 | Objections from the same session as the summary are less independent than from a second routine. | Reasoning only; stated in Known limits, owner chose small setup. |

## Code round (after judge 167 addendum 2 PASS)

Branch `story/lr1-weekly-postmortem`. New: `fno/learning/` (week, readers, three sections, report, writer, publish,
cli, wiring) and `fno/advocate/` (numbers, port, routine_file); `.github/workflows/postmortem-weekly.yml`;
`docs/stories/LR1-owner-checklist.md`; 52 tests in `tests/learning/` and `tests/advocate/`. Changed: the Monday post
removed from `forecast-scores.yml`; two secret names in `fno/constants.py`; `postmortem` in `fno/cli.py`; the new
composition root listed in `CLAUDE.md`. Every file is under 90 lines.

Two choices made while coding (story text updated for both):
1. **A separate `postmortem fire` command.** If `weekly --post` fired the routine itself, the routine could start
   before the job pushed the lines, find no file and write nothing. So the job writes, commits and pushes the lines,
   then fires (strong: the routine reads `main`).
2. **The card line uses T1's own `misses(log, day)`** instead of a new reader. A TEST delivery is not counted, and
   the words match the next card's (strong: `fno/cards/deliveries.py`).

Live dry run on this branch, `python -m fno postmortem weekly --week-ending 2026-10-17`, writes nothing:
- **Forecasts:** "Protocol v4: no G8 score report yet" (no schedule has written one; the new job writes it first).
  G4's own summary of `scores/2026-10-15.json` follows.
- **Weather:** 12-14 Oct GREEN (back-fill, v0 AMBER), no 2% move after 12 or 13 Oct, 14 Oct unresolved; 15-16 Oct
  "missing". No live weather record exists yet.
- **Data health:** 3 pm captures on 14 Oct (2.7 minutes after 14:55) and 15 Oct (10.7 minutes after), "none" on the
  other days. "No card on record" every day: 15 Oct's only delivery is the TEST. A16: 0 of 20. Complete days: 0 of 5.
  These rows show the real state of the inputs, not a code fault.

Desk note (some evidence, exploratory back-fill only, not counted): G8's report run for this check
(`forecast-v4-scores report --as-of 2026-10-15`, not committed) shows weather_vix_v1 against the base rate on V6a
with relative improvement 0.1756, p 0.0021 (batch means), over 1,907 back-fill days. v6_ewma_t4 shows 0.1449. Both
are back-fill; only forecasts after the v4 freeze count.

Known gaps: the routine's prompt is checked only by the owner's hand run (checklist step 3). The number check needs
numbers exactly as the lines print them, so a rounded number ("0.04" for "0.0391664") drops the summary. That is
deliberate: the routine is told to copy numbers exactly.
