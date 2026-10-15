# Epic M: market weather (layer 3)

Roles: risk manager (owner), volatility trader, statistician, quantitative modeller. Goal: a calm, fast answer to "is
today dangerous?", published as probabilities that are scored like any forecast, with a colour from thresholds the
owner accepted (design v2 section 2.3; `docs/DESK_DECISIONS.md`, 15 Oct 2026 "Weather thresholds accepted"). The
weather is a survival signal, not a profit signal: response 94 found that the v0 rule added money for no weekly
structure. Story template and definition of done: `docs/IMPLEMENTATION_PLAN.md`.

---

## M1. Weather as a scored forecaster

**Repository:** trading · **Lane:** 1 (forecast records; the colour gates new trades: RED blocks new entries, and a
missing weather reading blocks new trades, owner "4 A"). **Quality rule 9 applies** (orchestrator, 15 Oct): M1 can
change a trade decision (the owner's test: "would this change a buy/sell signal, a trade or a stop decision?": yes,
through RED and "missing"), so ChatGPT reviews it after the judge's PASS and before the merge. A finding that changes
neither the probabilities, the colour nor the block is noted in one line, not a new round.

**Description:** As the risk manager, I want each NSE session's weather published at the 15:00 cutoff:
- the probability of a 2% NIFTY move in the next session and within the next 5 sessions;
- a colour from the owner's thresholds;
- the drivers behind it.

Both the weather model and the v0 checklist are scored under protocol v4's V6 questions, so the owner can see
whether the weather forecasts danger better than the base rate before it is trusted.

**Context and why:**
- Design 2.3 makes the weather a scored forecast: `p_big_1d`, `p_big_5d`, a colour from registered thresholds, the
  maximum RED frequency, and the drivers. The v0 checklist (response 94's frozen rule) becomes "weather baseline v0".
- REPLAN slice A item 8: "weather as a scored forecaster (V6; the v0 checklist as its baseline)".
- Protocol v4 (merged at 597487f, not frozen) defines the targets exactly. V6a is `abs(ln(close(d+1) / close(d))) >=
  0.02` and V6b any of the next 5 such returns, over regular sessions only. Section 5.6 gives V6's `rules` slot to
  "M1's weather model"; the base rate is V6's primary baseline. M1 follows the protocol's log-return definition, not
  design 2.3's looser "2% move".
- G7 (story text on `story/g7-baselines`) builds V6's outcomes, base rate and record layout, and registers its own
  V6 forecaster `v6_ewma_t4` as "reported only" because the `rules` slot is M1's (orchestrator decision 70). M1 calls
  G7's code and never re-implements it.
- The owner's 15 Oct rules: keep the design simple; test real cases only.

**Scope.** In:
1. **`WeatherModel`** (strategy; `fno/weather/`), two classes:
   - **`ChecklistV0`**, the baseline: response 94's frozen rule (`research/2026-10-14-weekly-weather/PROTOCOL.md`
     section 5), unchanged:
     - the inputs: `vix_ratio`, `vix_change5`, `move5`, `rv10` and `event`;
     - RED at 1.30 / +20% / 2.0% / 25%;
     - AMBER at 1.10 / +10% / 1.25% / 18% or a scheduled event;
     - GREEN otherwise.

     It has two modes:
     - *as of close* (the study's own: closes up to and including the decision day; used only to reproduce
       response 94);
     - *live* (point in time at `d`'s 15:00 cutoff: closes up to `d-1`; an event is a scheduled row of
       `events.csv` announced on or before `d` and dated in `d+1..d+5`, the V6b horizon).

     As a forecaster its probabilities are the share of V6a (and V6b) events among the most recent 750 resolved
     regular sessions before the cutoff that had the **same v0 colour**. The window needs at least 500 sessions, as
     G7's base rate. A colour with no session in the window gives "missing". No other minimum: the Brier score
     already punishes a noisy share (reasoning only).
   - **`VixScaledWeather`**, the first model, with zero fitted parameters (design 5.7 rule 5: at most 5):
     - `s_t` = India VIX close of session `t-1` / 100 / sqrt(252). That is the daily volatility the market priced, known
       at `t`'s cutoff.
     - For each of the most recent 750 sessions `t` resolved before the cutoff (at least 500, else missing), the
       standardized moves `z = r / s_t` of its next return (V6a) and of its next 5 returns (V6b), each divided by
       that window's own `s_t`.
     - `p_big_1d` = the share of those `t` with `abs(z) x s_d >= 0.02`.
     - `p_big_5d` = the share with any of its 5 `abs(z) x s_d >= 0.02`.

     The model takes the market's priced volatility for today and the tail shape of the last three years. The
     tails come from the data, not from an assumed distribution, and the 5-session clustering from real windows.
     Reasoning only on whether it beats the base rate: VIX is forward-looking and prices scheduled events; that is
     what the forward score will tell. It differs from G7's `v6_ewma_t4` (past returns, assumed t tails).
2. **The colour.** The operative colour is `VixScaledWeather`'s (decision 71, owner confirmed, 15 Oct 2026 (docs/DESK_DECISIONS.md)):
   - The record labels it "not yet proven" until G8 has scored the model against v0 and the base rate.
   - If G8 shows that the model does not beat both, the colour falls back to v0. That change is a recorded decision
     in `docs/DESK_DECISIONS.md`, applied through one constant (`WEATHER_OPERATIVE_MODEL`); it is never automatic.
   - Why (reasoning only): v0 was RED on 26% of response 94's weeks, above the owner's 15% maximum.

   The base rates `b1` and `b5` are G7's 750-session V6a and V6b base rates:
   - **RED** when `p_big_1d >= max(0.10, 2.5 x b1)` or `p_big_5d >= max(0.35, 2.5 x b5)`;
   - **AMBER** when `p_big_1d >= max(0.06, 1.5 x b1)` or `p_big_5d >= max(0.20, 1.5 x b5)`;
   - **GREEN** otherwise;
   - **not scored** when a probability or a base rate is missing. The record says so, and under the owner's "4 A"
     rule it blocks new trades like RED. The v0 colour is recorded beside it as the baseline.

   The thresholds are the owner's (15 Oct 2026), constants in `fno/constants.py`.
3. **Maximum RED frequency:**
   - each record states the share of RED among the most recent 250 **live** records;
   - above 15%, the record is marked `over_alarming`, for the post-mortem: a new version must be proposed, never a
     retune in place; RED still blocks;
   - with fewer than 250 live records it says "not enough data yet";
   - the back-fill's RED share is printed separately, labelled exploratory.
4. **Drivers** (descriptive only; never an input to the probabilities or the colour):
   - v0's four inputs, each with the v0 threshold it crosses;
   - the scheduled events in `d+1..d+5` (type and date, public rows of `events.csv`);
   - the overnight US move.

   The US move is read only through A17b's `CueReader` / `reading_for` (S&P 500 and Nasdaq 100, both private cues,
   owner a927390). A `stale` or `none` reading is refused and shows "not available". Otherwise it is a flag, `large`
   when the latest US close-to-close log return is at least 2% in absolute value (the same 2% as V6, no new number),
   else `normal`. **The flag is private (orchestrator decision 72):** it is written only to the private weather part in
   Drive (`derived/weather/<YYYY>/<d>.json` in the owner's Drive, beside the private cue tables). The public record
   says "US move: private". Neither the flag, the value nor the return ever reaches the repository. Without the Drive
   settings the private part is not written; the capture says so, and the public record is unaffected.
5. **Records:**
   - The probabilities go in G7's layout, `research/forecasts/v4/<forecaster>/<question>.csv`, one row per day with
     `day, value, status, label` and G7's audit columns. There are two forecasters:
     - `weather_vix_v1`: slot `rules` for V6a and V6b;
     - `weather_checklist_v0`: slot `reported`, the baseline.
   - The weather record, `research/forecasts/v4/weather/<YYYY>/<d>.json`, holds:
     - the two probabilities and the two base rates;
     - the colour, the v0 colour and the status;
     - the RED share and the `over_alarming` flag;
     - the drivers;
     - the label (`live` or `backfill_exploratory`);
     - the inputs' SHA-256 and `made_at` (UTC with offset).

     Every input of the public record is public (closes, VIX, events); the US flag is only in the private part
     (Scope item 4).
   - A reader, `WeatherRecords.for_day(d)`, for the card. T1 is not changed in this story: the card keeps "Weather:
     not yet scored (M1 pending)" until a follow-up T1 change reads this record (gap list).
6. **Commands:**
   - `python -m fno weather capture [--day D]`: writes `d`'s records before the 15:00 cutoff from inputs first seen
     before it; after the cutoff it writes nothing and says so (as G3 and G7). On a day that is not a regular session
     (holiday, weekend, special, muhurat: protocol v4 section 2) it writes nothing and says "not a v4 session".
   - `python -m fno weather backfill`: from 2017, every row `backfill_exploratory`; it ends before the first live
     day, and a rerun gives identical files.
   - Wiring in a new `fno/weather/wiring.py` (design 2.3 names it), added to the CLAUDE.md list.

Out (with reasons):
- **Scoring, pairs, claims, the family decision and the window regime line:** G8. It reads M1's records with
  `forecast_v4.confirmatory.judgeable` / `event_band`, the claim and futility thresholds (`operative_thresholds` in
  `tools/v4_brier_bands.py`) and `forecast_v4.regime.window_regime`. M1 writes records only.
- **Registration in the ledger:** at v4's freeze, as G7 (protocol 5.6: the first version registered before its first
  counted forecast).
- **Slack alert on an upgrade to RED, intraday upgrades from the live monitor, the price of calm:** M2 and LM1
  (REPLAN).
- **Applying "RED blocks new entries" and "missing weather blocks new trades" in the desk:** no strategy is approved
  and no paper trade can open today. The block belongs at the desk's entry gate (with C4 or T2), a small story of its
  own, using `WeatherRecords.for_day`.
- **Showing the weather on the daily card:** a follow-up T1 change, after M1 merges.
- **Adding `weather capture` to the daily routine:** a schedule change, at v4's freeze (as G7).
- **The design's other driver ideas** (realised volatility beyond v0's `rv10`): v0's four inputs already give it.

**Gap list** (design 2.3, REPLAN M1, protocol v4 for V6, the orchestrator's brief):

| Requirement (source) | Where |
|---|---|
| `p_big_1d`, `p_big_5d` as V6a and V6b exactly (design 2.3; protocol 1.2) | criteria 4, 11 |
| Colour from the owner's thresholds, with floors and base-rate multiples (design 2.3; decision of 15 Oct) | criterion 5 |
| Which colour is operative; "must beat v0 and the base rate to replace it" (design 2.3; decision 71) | criterion 5 ("not yet proven" label; the fallback is a recorded decision) |
| Maximum RED frequency 15% over 250 sessions, "over-alarming", never retuned in place | criterion 6 |
| Drivers: VIX level and change, recent large moves, realised volatility, overnight US move, scheduled events | criterion 7 (the US move in Drive only, decision 72) |
| v0 checklist as weather baseline v0, scored on the same questions | criteria 1-3 |
| One weather record a session at 15:00 | criteria 8, 9 |
| Intraday upgrades (amber to red only) and a Slack alert on RED | Out: LM1, M2 |
| `WeatherModel` strategy, scored with the forecast scoring, wiring `fno/weather/wiring.py` | criteria 3, 4, 12; scoring: G8 |
| Evaluation: Brier, log score against the base rate; red frequency; price of calm | G8 (scores), criterion 6 (red frequency), M2 (price of calm) |
| Base rate primary for V6 (protocol 3.2) | criterion 5 uses it; scoring: G8 |
| `rules` slot for V6 is M1's (protocol 5.6; decision 70) | criterion 8 |
| Regular sessions only (protocol 2) | criteria 9, 11 |
| Only forecasts after the freeze count; back-fill exploratory (protocol 8) | criterion 10 |
| `judgeable`, `event_band`, `operative_thresholds`, `regime.window_regime` (orchestrator) | Out: G8 uses them on M1's records |
| Global cues only through `CueReader` / `reading_for`, stale or none refused (orchestrator) | criterion 7 |
| Card's weather line consistent with M1; T1 unchanged (orchestrator) | criterion 8 (`for_day` reader); T1 change: Out |
| RED blocks new entries; missing weather blocks new trades (owner 14 Oct, "4 A") | criterion 5 (status); enforcement: Out (no strategy approved yet) |

**Acceptance criteria** (each with a test on committed data or a hand-computed fixture: positive, negative, boundary
and empty cases):
1. `ChecklistV0` in *as of close* mode reproduces response 94's colours on all 396 of its decision days, from the
   committed closes and events (`research/2026-10-14-weekly-weather/trades.json`, field `weather`: 157 GREEN, 137
   AMBER, 102 RED). Every day matches, not only the counts.
2. `ChecklistV0` in *live* mode reads closes up to `d-1` only, and events announced on or before `d` and dated
   `d+1..d+5`. Each of the eight thresholds is tested at, just under and just over. An event announced after `d`
   is not seen.
3. v0's probabilities are the colour-conditional shares over the most recent 750 resolved sessions (499 resolved:
   missing; 500: present). A colour absent from the window gives "missing" (hand-computed fixture).
4. `VixScaledWeather`: `p_big_1d` and `p_big_5d` equal a hand computation on a small fixture. 499 resolved sessions
   give missing and 500 give a value. A missing VIX close for `d-1` gives missing. Changing any input after the
   cutoff (`d`'s close, a later VIX) changes no forecast for `d` (look-ahead test).
5. Colour: each of the four conditions at its threshold (RED or AMBER), just under, and just over. The floor binds
   when the base rate is low, and the multiple binds when it is high (one case each). A missing probability or base
   rate gives `not scored`, never a colour. The record names the operative model and labels it "not yet proven";
   with `WEATHER_OPERATIVE_MODEL` set to v0, v0's colour is the operative one (test).
6. RED frequency: with 250 live records, 37 RED (14.8%) is not `over_alarming` and 38 RED (15.2%) is. With 249 live
   records it says "not enough data yet". Back-fill records never count toward the 250.
7. Drivers:
   - v0's inputs are shown with the thresholds they cross, and the events of `d+1..d+5`;
   - the US flag reads `large` at an absolute log return of 2% and `normal` just under;
   - `stale` and `none` readings give "not available";
   - the flag is written only to the private Drive part (a fake store in tests); the public record says "US move:
     private", and a test finds no US flag, value or return in any repository file;
   - without the Drive settings the private part is not written, the capture says so, and the public record is
     still written;
   - the drivers never change the probabilities or the colour (test: the same forecast with and without them).
8. Records:
   - G7's layout for both forecasters (`weather_vix_v1` in slot `rules`, `weather_checklist_v0` in `reported`), with
     invalid values refused and never written;
   - the weather record with every field of Scope item 5;
   - `WeatherRecords.for_day(d)` returns the record, or "none" when there is no record for that day.
9. Capture: before the cutoff it writes `d`'s records. After the cutoff it writes nothing and says so. On a holiday,
   weekend, special or muhurat day it writes nothing ("not a v4 session").
10. Back-fill from 2017: every row `backfill_exploratory`, ending before the first live day; a rerun is
    byte-identical. It prints the back-fill's RED share and colour counts, labelled exploratory.
11. Point in time: no input first seen after `d`'s cutoff reaches `d`'s probabilities, colour or drivers. The V6
    outcomes used for the windows are G7's, resolved before the cutoff.
12. Engineering:
    - interfaces: `WeatherModel`, plus G7's record writer and A17b's reader reused;
    - one composition root (`fno/weather/wiring.py`, listed in CLAUDE.md);
    - constants in `fno/constants.py`;
    - no file or class over 350 lines;
    - the gates pass.

**Test plan:** `tests/weather/`:
- the 396-day reproduction (criterion 1), from committed files;
- hand-computed fixtures for both models and the colour;
- threshold boundaries (at, under, over);
- look-ahead tests;
- the 249/250 and 499/500 windows;
- empty inputs: a missing VIX close, too short a history, no event rows, and a `stale` or `none` cue.

Only real cases (owner, 15 Oct): no imagined failure modes of sources.

**Judge verifies:**
- recomputes one day's `p_big_1d`, `p_big_5d`, base rates and colour by hand from the committed closes and VIX;
- checks v0's 396-day reproduction;
- moves a later close and checks no earlier forecast changes;
- checks that no private cue value is written.

**Known limits:**
- **V6a will almost surely never be claimed under v4, and V6b only slowly** (protocol 8 and 11: claim thresholds
  near 1e-14 for V6a; V6b needs about 3-4 years in windows with 5 or more 2% days). The weather's score will mostly be
  descriptive for a long time; it still gates trades by the owner's choice.
- The VIX close of `d-1` is a day old at `d`'s 15:00. A same-day 15:00 VIX would need a separate series in history
  and live, so it is not used.
- The model assumes the VIX-to-realised relation of the last 750 sessions holds today; a regime change shows first as
  miscalibration in G8's reliability table.
- v0's colour-conditional shares rest on few RED sessions in calm years.
- `events.csv` lists events up to 4 Dec 2026; 2027's rows must be added by A6's routine, or v0's event condition goes
  quiet.
- The back-fill uses 2017-2026, which is spent (protocol 8): exploratory only.

**Depends:**
- G6 (merged, not frozen);
- **G7's code** (V6 outcomes, the base rate, the record writer; it must merge first);
- O6 (closes and VIX closes), A6 (events), A17b (`CueReader`, merged).
- A15 is helpful, not required: the 2017-2026 VIX closes suffice for the 750-session window.

**Size:** M · **Status:** story text for the judge's check (quality rule 1); code waits for that check and G7's
merge.

**Decisions taken (orchestrator, 15 Oct 2026, response 113):**
1. **Decision 71:** the model's colour is operative, labelled "not yet proven" until G8 scores it against v0 and the
   base rate; it falls back to v0 if G8 shows that it does not beat both, as a recorded decision. **Owner confirmed, 15 Oct
   2026 (docs/DESK_DECISIONS.md).**
2. **Decision 72:** the US-move flag stays in Drive with the private cue tables; the public record says "US move:
   private".
3. Quality rule 9 applies: a ChatGPT review after the judge's PASS.

---

## M2. Weather alerts and the price of calm

**Repository:** trading · **Issue:** #122 · **REPLAN:** slice B (`REPLAN_new_stories.md`, Weather) · **Lane:** 1 (new
story; Slack)

**Description:** As the owner, I want one DANGER message in #fno-desk on the first session the weather turns RED, with
the numbers behind it, so that I learn of it before the 15:00 market rather than from the card. And, once the desk has
shadow trades, I want a monthly line showing what the RED rule cost or saved, so that I keep "red means no new trade"
knowing its price.

**Context and why:**
- Design 2.3 ("Outputs": "a Slack alert on any upgrade to RED") and 6.5 (DANGER: "Weather upgraded to RED"). REPLAN
  M2: "RED upgrades as DANGER alerts; the monthly shadow result of trades RED blocked, beside the losses avoided".
- **What exists today (strong evidence, code on `main`):**
  - M1 writes one live weather record per regular session (`fno/weather/capture.py` `capture_weather`), refused at or
    after the 14:30 IST cutoff (`fno/forecast_v4_rules/capture.py`, `CUTOFF = V4_CAPTURE_START`). Back-fill records
    are labelled `backfill_exploratory`.
  - O1 (branch `story/o1-daily-run`) runs `weather` as its first steps after `margin_check`, live only from
    `config.yaml` `daily.live_from.weather` (null today), and the card last.
  - Intraday upgrades ("from the live monitor, layer 7: amber to red only", design 2.3) need LM1, which is not built.
  - No paper version is approved and no shadow trade exists (R1 is not built). So nothing is blocked by RED yet.
- So the only RED upgrade that can happen in a real day now is **the daily record**: today's live record is RED and the
  previous regular session's was not. M2 v1 alerts on that, and only that.

**Scope.** In:
- **(a) The DANGER alert** (new package `fno/weather_alerts/`, outside M1's files; split agreed with the M1 builder,
  see the end of this section):
  - `python -m fno weather-alert --day YYYY-MM-DD`, run by O1 as step `weather_alert`, right after `weather` (one row
    in O1's step table, agreed with the O1 builder).
  - Rule, read from M1's committed records through `WeatherRecords` (never recomputed):
    - today's record is `label: live` and its operative colour is RED, and
    - the previous regular session's record is missing, back-fill, or not RED.
    RED on two sessions in a row alerts once, on the first. Never on a back-fill record, never on `not scored`.
  - The message, PAPER ONLY, first line saying what it means (design 6.5): "DANGER (paper only): weather turned RED for
    <d> (was <colour> on <previous>). Owner rule: RED means no new paper entry today." Then, copied from the record:
    the operative model's `p_big_1d` and `p_big_5d` against the base rates, the v0 colour, the v0 inputs with the
    level each reaches, the scheduled events in the next 5 sessions, and `red_share` and `over_alarming` as written.
  - The owner-delay line (design 6.5, owner decision of 15 Oct 2026): "If you act 60 minutes later, the paper record
    assumes: no change (the weather stops only new entries)."
  - **Never the US-move flag**: it is private (decision 72). The alert reads only the public record.
  - Honesty line while the desk does not enforce RED (M1 Out): "The desk does not yet refuse entries on RED (no version
    is at paper); this is the rule it will apply." It is removed by the story that adds the enforcement.
  - One alert per day at most: an alert record `research/alerts/weather/<YYYY>/<d>.json` (condition, the weather
    record's SHA-256 and `made_at`, Slack's sent time and outcome), written once. A rerun with the record present
    sends nothing. "alert NOT sent" is recorded and printed; O1 alerts a failed step once.
  - Not live before `daily.live_from.weather`: no live records exist, so the command prints "no live weather record"
    and sends nothing.
- **(b) The price of calm: a slot that waits on R1** (no code now, no invented source):
  - The port `BlockedShadowSource` is named here and built with R1: per RED live day, each registered version's
    shadow decision that the RED rule blocked, its matched shadow fill, its maximum loss and its net at exit.
  - The monthly line, when built: "<month>: RED on <n> sessions; <k> entries blocked; risk avoided Rs <sum of maximum
    losses>; their shadow net Rs <sum> (positive = calm cost money)". Until R1 exists the line is not shown anywhere;
    no number is estimated (design 2.3: "the design never claims the weather protects anything").
  - Where it shows (later): LR1's first post-mortem of each month, as one line read from the port.

Out (each with where it goes):
- Intraday RED upgrades and AMBER WARNINGs: LM1 (layer 7), once A16 runs live.
- The desk refusing entries on RED or `not scored` (owner "4 A"): the story that first approves a version to paper
  (M1 Out; T2's gap list).
- A `not scored` day: no DANGER. The card names the missing weather, and O1 alerts a failed `weather` step.
- The price of calm's code: R1.

**Design:**
- `fno/weather_alerts/rule.py`: `RedUpgrade`, which decides from two records (today, previous) whether to alert. Pure;
  no I/O.
- `fno/weather_alerts/message.py`: the message lines from one public record.
- `fno/weather_alerts/records.py`: `AlertRecords`, written once.
- `fno/weather_alerts/cli.py` and `wiring.py`: `WeatherRecords` (M1), the A7 calendar's previous regular session
  (M1's `previous_regular`), the existing `AlertSender`.
- No change to any `fno/weather/` file.

**Acceptance criteria:**
1. A live RED record after a live GREEN or AMBER one sends one DANGER message with the fields above, copied from the
   record. A test compares each number with the planted record.
2. RED after RED sends nothing; RED after a missing or back-fill previous record sends one.
3. A back-fill RED, a `not scored` record and a missing record send nothing, each with its printed reason.
4. The message never contains the US-move flag or any field of the private part (a test plants one in Drive's fake).
5. A second run for the same day sends nothing ("already alerted"); "alert NOT sent" is recorded and printed.
6. The command reads only committed public weather records and writes only its alert record (AST and file tests).
7. The message carries the PAPER ONLY first line, the owner-delay line and, while the desk does not enforce RED, the
   honesty line.
8. (Later, with R1) the price-of-calm line comes only from `BlockedShadowSource`; before R1 it does not appear.

**Test plan:** fakes for the records, the calendar, Slack and the alert store.
1. Positive: GREEN then RED; AMBER then RED; missing then RED.
2. Negative: RED then RED; back-fill RED; `not scored`.
3. Privacy: a planted private US flag never reaches the text.
4. Once per day: a rerun; a Slack failure.

**Known limits:**
- A RED that appears only during the session (after the 14:30 record) is not seen until LM1.
- The alert comes at about the record's time (before 14:30 IST under G10); the card follows later the same day.
- A record that changes colour back the next day sends nothing (only upgrades alert, design 2.3).

**Split agreed with the M1 builder (session 013xqaNTCbSBytKgqpfaYFqZ) and the O1 builder (session
014zYLf18PgCzR7YoHs1X5Dp):** pending their replies; see claims file.

**Depends:** M1, O1 (`weather_alert` step), T1 (the card shows the colour), A7, R1 (part b only) · **Size:** S ·
**Status:** story text, waiting for the judge
