# Response 188: M2, weather alerts and the price of calm: story text and claims (for the judge)

**Story text:** `docs/stories/M-weather.md`, section M2. Branch `story/m2-weather-alerts`. Issue #122, REPLAN slice B.
Lane 1. Text only.

## Claims

| # | Claim | Evidence |
|---|---|---|
| 1 | M1 writes one live record per regular session, refused at or after 14:30 IST. | Strong: `fno/weather/capture.py` `capture_weather`; `fno/forecast_v4_rules/capture.py` `CUTOFF = V4_CAPTURE_START`. |
| 2 | The live record holds every field the alert shows; the US-move flag is only in the private Drive part. | Strong: `research/forecasts/v4/weather/2026/2026-10-14.json` (`drivers.us_move: "private"`); `capture.py` `_save_private`; decision 72. |
| 3 | O1 runs `quotes`, `margin_check`, `weather`, `forecasts_v4`, then the desk, and the card last (after 15:15); `weather` is live only from `daily.live_from.weather` (null today). | Strong: O1 builder, 15 Oct (`story/o1-daily-run` at 81f4cd11, `fno/constants_operations.py`); `docs/stories/O1-daily-run.md`. |
| 4 | Intraday upgrades need LM1, which is not built. | Strong: design 2.3 "Outputs"; REPLAN LM1 (slice B, depends on A16). |
| 5 | Nothing is blocked by RED today: no version at paper, and the desk does not enforce RED. | Strong: T1's `RegistryStatus`; M1 Out list; T2's gap list. |
| 6 | Part (b) has no data source until R1 shadows exist; any number before then would be invented. | Strong: R1 is not built (work register); design 2.3 "never claims the weather protects anything". |
| 7 | An alert at the record's time (before 14:30 under G10) is earlier than the card. | Some evidence: O1's run order; G10's 14:05 start (O1 text). |

## Split with other builders

- **M1 builder (013xqaNTCbSBytKgqpfaYFqZ):** asked on 15 Oct: M2 in its own package, reading M1's records only. Reply
  pending.
- **O1 builder (014zYLf18PgCzR7YoHs1X5Dp): agreed, 15 Oct.** One `weather_alert` step after `weather`, with its
  conditions (no-record line, exit codes, no "nothing written:", 10-minute stop, code after O1 merges), all in the
  text. Its reasons (strong: O1's code): the card runs after 15:15, too late; and M1's capture is a scored
  forecaster's command.
