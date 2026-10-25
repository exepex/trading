# 2026-10-25: STAB1 builder (capture only, forecasting off)

Builder session_01M9XcuJUSSW6U1KBv1hC4cS (Sonnet), for the orchestrator session_01Mt6dcBU5kp2htdPN2KmiZH; judges P
session_01Bv9Bn74EaHNNYAen66KsLp and Q session_01R97adLHpBi5iPjJiQQvhWE. Branch `story/stab1-capture-only`.

## The owner's words (as quoted in the builder's brief)

> we are not going live ... We are not doing any kind of forecasting, we are not doing any kind of predictions ... I want my system to be stable, to be more predictable, more reliable ... I don't want any system that is not reliable and work on half-baked solutions

> When I say we switch off the forecast, we did not mean that we turn off the data capturing, whether it is 15 minutes data capture from Grow, NSC, and the live feed from Grow ... Data capture will never stop. Only forecasting ... As far as the forecasting is concerned, if there is any, we turn it off. So tell me if there is anyone.

> every removal and cleanup needs to be reviewed thoroughly by a judge and independent judge. We don't want to break the system

## Decisions so far

- The orchestrator's hypothesis was checked line by line against the code, not taken as given. Findings that differ:
  - `daily.live_from.ai_books_v4` must stay dated: null would restart the v2 AI fire and collection
    (`fno/ai/fire.py:42`, `fno/ai/collect.py:44`).
  - `v4_pack` gated the `v4` capture part, the release and the 15:10 check; the capture keeps `v4_pack`, the other two
    get the new key `v4_release` (null). The release and deadline children read `v4_pack` themselves in the v4-frozen
    `fno/v4_pack/wiring.py`, which is not touched; only the daily steps call them on a schedule.
  - Four workflows forecast, not three: `postmortem-weekly.yml` (Saturday; v4 scores report and an AI routine) too.
    All four keep only manual dispatch.
  - `lab open` and `lab close` did a Drive sync of G13b's records before they looked at the live date; they now build
    nothing when not live. `recommend check` had no switch; it prints "not live" without one.
  - The health check expected the v2 forecast records and the AI books' sealed forecasts every session; those
    expectations are off (they would have alerted "missed" from Monday).
- The Book 1, 2 and 3 desk (`desk book1`, fills, exits, marks) is left running and untouched: it forecasts nothing and
  reads no forecast, and the owner's correction of 25 Oct (DESK_DECISIONS "Correction: Books 1, 2 and 3 stay") says
  nothing working is removed. The orchestrator relayed it to this builder in two messages (the desk stays; the morning
  and evening routines keep their capture commands, only `lab open` and `lab close` are gated).

## Open questions

1. `postmortem-weekly` also reported data health; with it off, nothing posts a weekly data-health summary. Keep it off?
2. The v4 protocol is frozen with slots effective 26 Oct; with forecasting off every v4 slot day is a miss if v4 is ever
   restarted. Does the owner want the v4 freeze record annotated?
