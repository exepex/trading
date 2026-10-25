# STAB1: capture only, forecasting off (lane 1)

Owner, 25 Oct 2026: "we are not going live ... We are not doing any kind of forecasting, we are not doing any kind of
predictions ... I want my system to be stable, to be more predictable, more reliable ... I don't want any system that is
not reliable and work on half-baked solutions"; "Data capture will never stop. Only forecasting ... As far as the
forecasting is concerned, if there is any, we turn it off"; "every removal and cleanup needs to be reviewed thoroughly by
a judge and independent judge. We don't want to break the system".

Builder: session_01M9XcuJUSSW6U1KBv1hC4cS. Judges: P session_01Bv9Bn74EaHNNYAen66KsLp, Q session_01R97adLHpBi5iPjJiQQvhWE
(two judges, each with a file). Branch `story/stab1-capture-only`. Nothing is deleted: every switch is reversible by the
owner's later decision. Story ING1 (the separate ingestion layer) is not started here: no capture is moved or
restructured.

## What is switched off (from Monday 26 Oct 2026's runs)

| Item | What it forecasts or does | Where it runs | The switch |
|---|---|---|---|
| Weather | M1's per-day weather colour | daily run step `weather` | `daily.live_from.weather: null` |
| v4 rule forecasts | G7's rule forecasts | daily step `forecasts_v4` | `daily.live_from.forecasts_v4: null` |
| v4 release and 15:10 check | the v4 pack's release record and its deadline verdicts | daily steps `v4_release`, `v4_deadline` | new key `daily.live_from.v4_release: null` (was shared with the capture's `v4_pack`) |
| v4 pack rows | G7b's pack-derived v4 rows | daily step `forecasts_v4_pack` | `daily.live_from.forecasts_v4_pack: null` |
| T1 card | the daily card to #fno-desk | daily step `card` | `daily.live_from.card: null` |
| Price distribution + scores | G13 valuation record and distributions | daily steps `price_distribution`, `price_distribution_scores` | their keys `null` |
| Price ranges + scores | G13b 15:45 NIFTY/BANKNIFTY ranges | daily steps `price_ranges`, `price_range_scores` | their keys `null` |
| Premium ranges + scores | G13d next-session premium ranges | daily steps `premium_ranges`, `premium_range_scores` | their keys `null` |
| Recommender | the day's recommendation and its #fno-desk line | daily step `recommend`; evening `recommend check` | `daily.live_from.recommend: null`; `recommend check` prints "not live" when it is null |
| Market school | the 15:00 paper decisions and report sections | daily step `school` | `school.enabled: false`, `school.reports: false` |
| Lab editions | the 08:50 forecast and 20:05 check in #fno-forecast | owner routines `lab open`, `lab close` | `forecast_lab.live_from.morning/evening: null`; a not-live edition builds nothing |
| v2 forecasts + AI books | v2 baselines, Book 1 forecast, `ai fire`/`ai collect` (v2 and v4) | `forecast-capture.yml` | schedule and push triggers removed (manual dispatch stays) |
| Forecast scores | `forecast-scores run` | `forecast-scores.yml` | schedule removed (manual dispatch stays) |
| v4 AI fire | `ai fire --protocol v4` | `v4-fire.yml` | push trigger removed (manual dispatch added) |
| Weekly post-mortem | v4 report, forecast scores summary, AI routine | `postmortem-weekly.yml` | schedule removed (manual dispatch stays) |
| Health expectations | "Forecast v2 records" and the AI books' "sealed forecast" | `fno health check` | their live date is `None` |

`daily.live_from.ai_books_v4` stays `2026-10-26` on purpose: a null there would **restart the v2 AI fire**
(`fno/ai/fire.py:42`, `fno/ai/collect.py:44`). `daily.live_from.v4_pack` stays: it now gates only the 14:32-14:40 `v4`
capture part (and the day-label start used by the scoring code, which no longer runs).

## What keeps running, unchanged

Groww 15-minute marks (A16), candle catch-up (A16b), the 3 pm NIFTY and NSE quotes, `record-indices`, the `v4`-window
quote capture, pre-open (A22, global cues), closes reads and rechecks (A4h), NSE files (bhavcopy, participant OI,
FII/DII, index closes), Drive archiving, margins data and the margin check, market-publish, health check, capture-watch,
recorder-watch, `lab release-check`, `records certify closes`, Book 1's desk steps (see Open question 1).

## Criteria

1. Every forecast, score, card, recommendation and school step of the daily run records `not_live` or "school off" on a
   session day with the real `config.yaml`; the day still ends `day done`.
2. The captures listed above are still steps or parts of the day with the real `config.yaml`, including the `v4`
   capture part on 26 Oct and later.
3. The v4 capture's key and the v4 release's key are separate: a null release key does not remove the capture part.
4. The four forecasting workflows have no `schedule` or `push` trigger; every other workflow's triggers are unchanged.
5. `lab open` and `lab close` with no live date build no composer (no Drive sync) and exit 0; `recommend check` with no
   live date builds nothing and exits 0.
6. The health check expects no forecast record and no AI sealed forecast, and still expects every capture it expected.
7. No alert is raised by a switched-off item (daily run, health check, capture-watch).

## Open questions for the owner (via the orchestrator)

1. Book 1's rule-based paper desk (`desk book1`, fills, exits, marks) is retired by DESK_DECISIONS 25 Oct but its
   removal is a later judged story; it forecasts nothing and reads no forecast, so STAB1 leaves it running. Switching
   it off is a separate decision.

## Claims

(filled in at the pushed SHA)
