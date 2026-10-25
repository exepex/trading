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
recorder-watch, `lab release-check`, `records certify closes`, and the Book 1, 2 and 3 desk (`versions`, `pack`, `decisions`,
`snapshot`, `fills`, `exits`, `trade_marks`, `book1`, E6's reviews): owner, 25 Oct 2026 (DESK_DECISIONS "Correction: Books 1, 2
and 3 stay"): nothing working is removed, and none of these forecasts or reads a forecast.

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

1. `postmortem-weekly.yml` also built a weekly data-health summary besides the forecast scores and the AI routine; with
   its Saturday schedule removed, nothing posts that summary. Keep it off, or split the data-health part out later?
2. Protocol v4 is frozen with slots starting 26 Oct (`research/forecasts/FREEZE_v4.md`); with forecasting off every v4
   slot day would be a miss if v4 is ever restarted. Annotate the freeze record, or leave it as history?

## Claims

Tip: the pushed SHA in the judges' message. Main merged in (no code or workflow change on main since the base).

1. **Forecasting steps off.** `tests/daily/test_capture_only.py::test_every_forecasting_step_of_the_daily_run_is_not_live_on_the_first_session_and_after`
   builds the real wiring per session (26, 27 Oct, 2 Nov) and runs all 15 forecasting steps: each records `not_live`.
   Sample from the built wiring, 26 Oct: `weather`, `forecasts_v4`, `v4_release`, `v4_deadline`, `forecasts_v4_pack`,
   `card`, `price_distribution(+scores)`, `price_ranges(+scores)`, `premium_ranges(+scores)`, `recommend`: "not_live: no
   live date set (config.yaml daily.live_from)"; `ai_fire`, `ai_collect`: "not_live: no AI book is live today".
   School: `python -m fno school run --session 2026-10-26` prints `school off`, exit 0 (code `school:OFF` is registered).
2. **Captures kept.** Same file: steps `quotes`, `quotes_done`, `candles`, `close_read`, `close_recheck`, `margin_check`
   are unchanged; `close_read`/`close_recheck` keep 2026-10-23; the `v4` part is a part of 26, 27 Oct and 2 Nov
   (started with nifty, nse, indices). No capture code or capture workflow is edited.
3. **Keys apart.** `fno/daily/wiring.py:262` gives the release/deadline `live[v4_release]`; `fno/daily/v4_part.py:35`
   keeps `v4_pack`. `test_the_built_run_gives_its_quote_parts_the_capture_key_not_the_release_key` checks the built run.
4. **Workflows.** `forecast-capture`, `forecast-scores`, `v4-fire`, `postmortem-weekly` are `workflow_dispatch` only; the
   set of manual-only workflows is pinned to those four plus `routine-fire-probe`, so no capture lost a trigger.
5. **Lab and recommender.** `python -m fno lab open --day 2026-10-26` and `lab close`: "not live (config
   forecast_lab.live_from.<edition>: None); nothing posted", exit 0, also with no Drive settings or with invalid ones (before:
   `DriveSignInRefused`, exit 1). `recommend check`: "not live ...; nothing checked", exit 0. Tests: `test_a_lab_edition_without_a_live_date_builds_...`,
   `tests/forecast_lab/test_lazy_edition_parts.py`, `tests/recommend/test_cli.py`.
6. **Health.** `FORECASTS_FROM = None` for the three forecast expectations; every capture expectation keeps its date
   (`tests/health/test_expectations_and_cli.py`).
7. **AI trap.** `ai_books_v4` stays dated (null restarts the v2 AI fire); pinned in `test_the_repository_config_holds_exactly_...`.
8. **Plants.** 11 planted breakages (card on, v4 capture on the release key, release on the capture key, scores schedule back,
   eager lab build, forecast health on, school on, recommend check ungated, `ai_books_v4` null, v4 capture off, post-mortem
   schedule back): all 11 made a test fail.
9. **Self-review.** One independent read-only review agent on the diff: no blocking finding; its should-fix (AI-step cases
   ran with no session day) and a wiring check were fixed. Not fixed, by choice: the stale step list in CLAUDE.md's daily
   section (the new note above it covers it), two leftover imports in the health table, a substring match in the workflow
   test.
10. **Gates (tree before the last two test-only commits).** `ruff check`, `ruff format --check`, `check_imports`,
   `check_records`, `check_numbers` clean; `python -m pytest -q -n auto`: 18,076 passed, 1 skipped, 13 xfailed.
   The final tip is re-checked with the fast gates and the changed test files.

Known limits: the `v4-pack release/deadline` commands still read `v4_pack` themselves (frozen `fno/v4_pack/wiring.py`
untouched), so only a hand run could start them; owner-side scheduled sessions and connectors outside the repository
were not checked; market-publish was not run (needs the database).
