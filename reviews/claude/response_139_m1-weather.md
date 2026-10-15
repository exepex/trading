# Response 139: M1 code, the market weather as a scored forecaster

Story: `docs/stories/M-weather.md` M1 (text PASS: judge 129). Branch `story/m1-weather-forecaster`, built on main after
G7's merge (d5d94c6). Lane 1; quality rule 9 applies: judge A first, then ChatGPT (review 106 covered the text).

## What it does (plain words)

Each regular session before 15:00 IST, `python -m fno weather capture` writes:
- two probabilities of a 2% NIFTY log move (next session; within 5 sessions);
- a colour from the owner's thresholds;
- the drivers.

It does this for two forecasters:
- `weather_vix_v1`, the model: yesterday's VIX scaled by the tail shape of the last 750 sessions;
- `weather_checklist_v0`, the baseline: response 94's frozen checklist, turned into a probability by colour.

The model's colour is the operative one, labelled "not yet proven" (decision 71, owner to confirm). The US-move flag
goes only to the owner's Drive (decision 72). Nothing places an order. Nothing was run live: every write in this
round went to a temporary folder.

## Desk view (every role, briefly)

- **Risk manager (some evidence, exploratory: 2017-2026 is spent, protocol 8).** On the 1,904 back-fill days where both
  colours exist, v0 is RED on 513 (26.9%) and the model on 121 (6.4%). The owner's maximum is 15%, so v0 would be
  `over_alarming`; the model is not. This is what decision 71 expected (v0 RED on 26% of response 94's weeks).
- **Volatility trader (some evidence).** On the 2024 election-result crash, the model said AMBER on 4 Jun (p1 0.068,
  p5 0.295) and RED on 5 Jun (p1 0.139, p5 0.527). v0 was RED on both days. The model reads yesterday's VIX, so it is
  one day late on a surprise that VIX did not price. That is a known limit in the story, and G8's score will show
  its cost.
- **Statistician (strong evidence for the arithmetic, reasoning only for its value).** An independent recompute
  (its own script, no `fno.weather` imports) matched every figure to full float precision on 2026-10-15, 2024-06-04
  and 2024-06-05: base rates, both models' p1 and p5, v0's inputs, colours and v0's probabilities. Whether the model
  beats the base rate is unknown until G8 scores the live records. For V6a this will likely never be settled (story,
  Known limits).
- **Today, 2026-10-15 (real data):** base rates b1 0.0267, b5 0.104. Model p1 0.0227, p5 0.096: GREEN. v0 is AMBER
  (vix_ratio 1.154 and move5 1.64% reach AMBER), with v0 p1 0.0247 and p5 0.1004. No events in the next 5 sessions.

## Claims table (criterion → code → test)

| # | Claim | Code | Tests (`tests/weather/`) |
|---|---|---|---|
| 1 | As of close reproduces all 396 colours (157/137/102), day by day | `checklist_v0.colour_as_of_close` (study's own window, judge note 3) | `test_checklist_v0::test_as_of_close_reproduces_all_396_colours_of_response_94` |
| 2 | Live: closes to the previous regular session; events announced by d, dated after d up to the 5th regular session; 8 thresholds at, under and over; late announcement unseen | `v0_live.ChecklistV0`, `checklist_v0.v0_colour` | `test_each_threshold_*` (8 x 3), `test_live_inputs_*`, `test_the_live_event_window_*`, `test_the_four_inputs_equal_a_hand_computation`, `test_a_sunday_budget_inside_the_5_sessions_counts_as_an_event` |
| 3 | v0 probability is the same-colour share over 750 resolved (499 → not eligible, 500 → value); a colour absent from the window → missing | `v0_live.ColourBaseRate` | `test_forecasters::test_v0_*` |
| 4 | Model equals a hand computation; 499/500; missing VIX → missing; look-ahead | `vix_scaled.VixScaledWeather` | `test_vix_model_*`, `test_a_doubled_vix_*`, `test_each_window_is_scaled_by_the_vix_of_its_own_previous_session`, `test_a_standardized_move_scaled_exactly_to_2pct_counts`, `test_the_window_keeps_the_most_recent_750`, `test_a_missing_vix_*`, `test_no_input_after_the_cutoff_*` |
| 5 | Floors and multiples at, under and over; floor binds when the base rate is low, the multiple when it is high; missing → `not scored`; operative model named, "not yet proven"; the constant switches to v0 | `colour.weather_colour`, `day.WeatherDays.colours` | `test_colour::*` |
| 6 | 37/250 is not over_alarming, 38/250 is; 249 → "not enough data yet"; back-fill not counted | `records.red_share`, `WeatherRecords.live_colours_before` | `test_red_share_over_250_live_records`, `test_back_fill_records_never_count_toward_the_250` |
| 7 | Drivers with v0 levels and events; US flag `large` at 2% and `normal` just under; stale or none → not available; flag only in Drive; never in a repository file or printed line; no Drive → said so, public record still written; drivers change nothing | `drivers.py`, `capture._save_private` | `test_drivers::*`, `test_privacy_and_point_in_time::test_the_flag_*`, `test_without_drive_settings_*`, `test_the_us_flag_changes_no_forecast_and_no_colour`, `test_no_committed_v4_file_holds_a_us_flag`, `test_the_printed_capture_never_shows_the_flag` |
| 8 | G7 layout for both forecasters and slots; an invalid value is refused and nothing is written; every record field; `for_day` gives None for a day without a record | `day.FORECASTERS`, G7 `record`/`write`, `records.WeatherRecords` | `test_capture_before_the_cutoff_writes_*`, `test_an_invalid_value_is_refused_*`, `test_a_rerun_the_same_day_keeps_the_first_record` |
| 9 | Before the cutoff it writes; at or after it, nothing; holiday, weekend, special and muhurat → "not a v4 session" | `capture.capture_weather` | `test_no_record_on_a_day_that_is_not_a_regular_session` (4 real 2026 days), `test_at_or_after_the_cutoff_*` |
| 10 | Back-fill from 2017, all `backfill_exploratory`, ends before the first live day, rerun byte-identical, RED share printed as exploratory | `capture.backfill_weather` | `test_the_back_fill_is_exploratory_*` |
| 11 | Nothing first seen after the cutoff reaches d's record (closes, VIX, a late event, the inputs hash); d-1 is the previous REGULAR session (judge note 1) | `day.py`, `wiring.previous_regular`, `capture` stale-closes refusal | `test_nothing_first_seen_after_the_cutoff_*` (3 real days), `test_the_previous_session_is_the_previous_regular_one` (special 20 Jan 2024, muhurat 12 Nov 2023) |
| 12 | `WeatherModel` interface; one composition root (`fno/weather/wiring.py`, in CLAUDE.md); constants in `fno/constants.py`; every file under 120 lines | `model.py`, `wiring.py` | `tests/test_code_size.py`; the gates |

Judge note 2 (the printed output never shows the flag): `test_the_printed_capture_never_shows_the_flag` runs the real
CLI with a sentinel flag. `test_the_flag_goes_only_to_the_private_drive_part` checks every written file and line.

## Choices the story text did not spell out (each stated so the judge can disagree)

1. **The capture refuses when the committed closes do not reach the previous regular session.** Otherwise a missing O6
   close would silently use the VIX of two sessions ago. There is no record that day, so the card shows the weather
   as missing, which blocks trades (owner "4 A").
2. **The event window is by date:** after d, up to the 5th regular session. A Sunday Budget (1 Feb 2026) counts for
   29 Jan 2026. The independent recompute found this: its first reading, events only on regular-session dates,
   differed by 0.0001 on p1 and 0.003 on p5, with no colour change. Its move is inside the next regular return, so
   the date window is the right reading (reasoning only). I propose a one-line clarification of the story text:
   "dated after d and on or before the 5th regular session after d".
3. **A 1e-12 tolerance in the colour comparison only.** In floating point 1.5 x 0.20 = 0.30000000000000004, so a share
   exactly at a multiple would miss it. Shares move in steps of 1/750, so the tolerance never lifts a value that is
   truly under. v0's frozen rule keeps the study's exact comparisons, which the 396-day reproduction needs.
4. **`made_at` is in UTC** with its offset, as the story says. G7's own rows use IST; both are unambiguous.
5. **A same-day rerun keeps the first record.** The same content with a later `made_at` writes nothing. Different
   content (an input changed) prints "nothing written" and exits 1, with no traceback and nothing half-written.
6. **`status`** is `scored`, or `not scored: <each missing figure and its status>`, so the future entry gate can say
   why a day is blocked.
7. **`method_sha256`** covers M1's method files plus G7's `series.py` and `baselines.py`, G6's `terms.py` and `sessions.py`, and `weather/wiring.py` (judge 129
   addendum 1, note 1: both decide v0's event window and the previous regular session). A change
   in G7's outcomes or base rate changes M1's numbers, so it must change the hash (review finding 2).
8. **`--day`** exists as the story says, but any day other than today is refused (as G7: a later day would lack its
   previous close).
9. **`_prefix_hashes` is a 6-line duplicate of G7's private helper.** I kept it so G7's method-hashed `capture.py` is
   not changed. Changing that file would change G7's `method_sha256` on its record rows. A shared helper can come with
   v4's freeze.

## Self-review (two independent agents) and my answers

- **Spec review: no must-fix.**
  - Should-fix 1, the missing `status` field: accepted and fixed (choice 6, with a test).
  - Should-fix 2, the method hash missing G7's files: accepted and fixed (choice 7).
  - Note 3: G7's `first_live_day` also sees M1's live rows, so the first weather capture also ends G7's back-fill.
    That is acceptable: both start live at v4's freeze, the same day (reasoning only). Flagged for the orchestrator.
  - Note 4: v0 goes "not scored" when the A7 calendar cannot give 5 sessions ahead, for example in late December
    without next year's NSE rows. The operative model's colour is unaffected. This is added to the known limits below.
  - Note 5, a rerun traceback: fixed (choice 5).
  - Note 6, a weak committed-file check: strengthened. The test now scans `research/forecasts/v4/` for any `us_move`
    flag value.
- **Numbers review:** every figure matched (above). Its one difference was choice 2.

## Planted breaks

One break per criterion was planted in a copy of the tree, 48 in all. Each made `tests/weather` fail: **48/48 caught**.
The script is in the builder's scratchpad (`mutate_m1.py`).

The first run missed 4, now covered by new tests:
- the median including today;
- `s_t` from the forecast day's own VIX;
- `>` instead of `>=` at exactly 2%;
- the inputs hash reading d's row.

## Real output sample (committed data, written to a temporary folder, no Drive)

```
back-fill (exploratory): 2409 days; colours AMBER 149, GREEN 1634, RED 121, not scored 505; RED share 5.0%
9636 v4 rows added
weather 2026-10-15: GREEN (not yet proven: G8 has not scored it against v0 and the base rate); 4 v4 rows written
private part NOT saved to Drive: the owner's Drive settings are not set
```

The 505 "not scored" days are 2017-2018 and early 2019, before 500 resolved sessions exist.

The v4 row for 2026-10-15 in `weather_vix_v1/v6_abs_move_2pct_next_session.csv` reads:
`2026-10-15,0.02266666666666667,ok,live,1,rule,rules,<method>,<inputs>,2026-10-15T09:25:00+00:00`.

## Gates

- `pytest -q`: 5297 passed;
- `ruff check fno tests tools`: clean;
- `ruff format`: done;
- `tools/check_imports.py`: clean;
- the record-scan hook is on.

## Gap list (what is not done, and where it goes)

- The card still says "Weather: not yet scored (M1 pending)": a T1 follow-up reads `WeatherRecords.for_day`.
- "RED blocks new entries" and "missing blocks new trades" are not enforced yet: the desk's entry gate, a story of
  its own.
- Scoring: G8. Registration in the ledger: at v4's freeze.
- `weather capture` is not in the daily routine: a schedule change at v4's freeze. No schedule was touched.
- The back-fill has not been committed to the repository. That is a data commit for the orchestrator to schedule
  after the merge (`python -m fno weather backfill`).
- Known limits, added to the story's: v0 goes quiet when the calendar ends within 5 sessions (note 4). The model is
  one day late on a surprise VIX did not price (4 Jun 2024).
