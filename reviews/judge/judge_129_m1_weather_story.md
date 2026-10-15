# Judge 129: M1 story text, weather as a scored forecaster: `story/m1-weather-forecaster` 438b8bcec84e5529501a3f43dd8a52c1d244a1d7 (quality rule 1, text only; judge A)

**Number note.** M1 has no response file yet, so I used 129, the next free judge number.

**What I checked:**
- `docs/stories/M-weather.md`, the only change from main 36d2db8;
- response 94's study (`research/2026-10-14-weekly-weather/`);
- T1's weather section (`fno/cards/weather.py`);
- DESK_DECISIONS 15 Oct: "Weather thresholds accepted" and "4 A".

All of it under the owner's 15 Oct rules: real cases only, and "would this change a buy/sell signal, a trade or a stop
decision?".

## The orchestrator's four points (real paths)

**1. The point-in-time 15:00 reading: SOUND.**
- Live v0 reads closes up to `d-1`, plus events announced on or before `d` and dated `d+1..d+5`.
- `VixScaledWeather` uses VIX(`d-1`) for `s_d`, and the same lag for every window session (`s_t` = VIX(`t-1`), target
  `ln(close(t+1)/close(t))`). Each window session must be resolved before the cutoff, through G7's outcomes. The
  forecast and its history are therefore built the same way, with no look-ahead.
- Criteria 4 and 11 carry the look-ahead tests. Criterion 9 makes the capture write nothing after 15:00.
- These inputs reach the repository the evening before (O6's daily closes, e.g. 911555d for 15 Oct). A late O6 run
  gives "missing", which blocks, as the owner chose.

**2. v0's 396 colours from committed files: VERIFIED myself, 396 of 396.**
- I ran response 94's own `weather()` from `study.py` over today's committed `research/data/nifty-panel/warmup_closes.csv`
  and `research/data/events/events.csv`, for every row of `trades.json`.
- Result: **0 mismatches**. Counts: 157 GREEN, 137 AMBER, 102 RED, as the story says.
- Criterion 1 is therefore reachable from committed files today.
- One point for the code round: the study evaluates on the day before entry with events in `(entry, expiry]`, and the
  story's *as of close* mode must use exactly that rule (`study.py:142,163`), not the live mode's `d+1..d+5`.

**3. No US value or flag reaches the repository: SOUND as written, with one line to add (note 2).**
- The cue is read only through A17b's `CueReader`.
- The flag goes to the private Drive part only, and the public record says "US move: private".
- Criterion 7 has a test that greps every repository file, and a no-Drive case where the public record is still
  written.
- Not stated: that the command's printed output never shows the flag. The capture will run on a schedule at v4's
  freeze, so its log is a real output path. See note 2.

**4. "4 A" against T1's card: CONSISTENT.**
- On `main`, `fno/cards/weather.py` shows "Weather: not yet scored (M1 pending)" with "No new trades while the weather
  reading is missing (owner rule)". That fails closed.
- M1's `not scored` blocks "like RED", the same rule.
- M1 leaves T1 unchanged, and enforcement at the desk's entry gate is Out (no strategy is approved).
- So the card keeps blocking after M1 merges, until the follow-up T1 change reads `WeatherRecords.for_day`. That is the
  fail-closed side, consistent with "4 A".

## A real-data check of the model (exploratory, some evidence)

I computed `VixScaledWeather` with the story's rule over the committed history, using regular sessions only and
windows of 750, ending before the cutoff, with at least 500 sessions. I applied the owner's thresholds, with the base
rates from the same windows. This is my approximation of the rule, not the built code. Colours per year:

| Year | GREEN | AMBER | RED |
|---|---|---|---|
| 2019 | 206 | 12 | 12 |
| 2020 | 115 | 50 | 85 |
| 2021 | 217 | 30 | 0 |
| 2022 | 230 | 16 | 1 |
| 2023 | 245 | 0 | 0 |
| 2024 | 226 | 13 | 6 |
| 2025 | 235 | 8 | 4 |
| 2026 to 14 Oct | 160 | 20 | 13 |

- RED runs at 0-5% in normal years. The 250-session RED share passes 15% only around the 2020 crash: its maximum is 34%,
  and 16% of the 250-session windows are above 15%. Today's share is 5.2%, and the last five sessions are GREEN.
- So `over_alarming` would mark the crash and little else.
- That supports decision 71's reason: v0 was RED on 26% of response 94's weeks. This is exploratory, on the spent
  period, as the story itself labels the back-fill.

## Other checks

- **Thresholds.** RED is `max(0.10, 2.5 × b1)` / `max(0.35, 2.5 × b5)`, and AMBER is `max(0.06, 1.5 × b1)` /
  `max(0.20, 1.5 × b5)`. These are exactly the owner's accepted figures (DESK_DECISIONS 15 Oct, line 108).
- **Rule 9** is stated, with the owner's test. Decision 71 is marked for the owner to confirm.
- **Engineering.** The design has one strategy interface and one composition root, and reuses G7 and A17b with no
  copy. The dependency on G7's code is stated, and the code waits for it.

## Notes (one line each; none changes a probability, colour or block, so none is a finding)

1. Define `d-1` and `t-1` as the previous **regular** session, as V6 counts. A muhurat or a special Saturday session,
   both real yearly cases, then never supplies the VIX close.
2. Criterion 7: also "the command's printed output never shows the US flag or value". The capture's log will be a
   scheduled job's output.
3. Criterion 1: the *as of close* mode uses the study's event window `(entry, expiry]` from the day before entry, as
   `study.py` does.

### Verdict: PASS for 438b8bcec84e5529501a3f43dd8a52c1d244a1d7 (story text)

- **No should-fix.**
- **v0's reproduction is verified from committed files** (396 of 396). The point-in-time rule and the private-flag rule
  are sound, and "4 A" is consistent with T1's card.
- **The three notes** are one-line text additions.
- **Next:** ChatGPT's rule-9 review. The code waits for G7's merge.
