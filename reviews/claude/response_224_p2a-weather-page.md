# Response 224: P2a part 1, the weather page and the contract's log line (claims for judge D, lane 1)

Builder: session 013xqaNTCbSBytKgqpfaYFqZ, branch `story/p2a-weather`. Story: `docs/stories/W3-fno-screens.md` (merged
at 90b4902d; judge 216, addenda 1-3), part 1 and build-order step 1. This is the **`weather`** page only (contract
`FnoWeather`, 2.7.0, already pinned). `weather_history` waits for two things: the owner's answer on the weather levels
(public, or private from now on) and contract 2.8.0 (`FnoWeatherHistory`, the screens lead's).

## What it does

- **`FnoWeatherBlock`** (`fno/market_read_models/weather_block.py`, `weather_parts.py`) is appended to
  `build_market_blocks()`. It rides the existing 07:10 run, with no new job, publisher or schedule.
- **Its input** is `WeatherInputsReader` (`weather_inputs.py`), wired in `fno/market_read_models/wiring.py`. It reads:
  - M1's records through `WeatherRecords.for_day` only: the day's record and up to 251 earlier sessions';
  - NIFTY's committed closes (`warmup_closes.csv`, O6) for whether a 2% move came. A move counts only once resolved by
    the publication's day.
  - It writes nothing.
- **Published only from a live record that M1 scored.** A back-fill record, a live record with a figure M1 could not
  compute, or no record at all gives `not_published`, the missing input named (story M1 or G7), colour null, and
  `blocks_new_entries` true (fail closed).
- **On today's real data** (every record is back-fill), each session publishes `not_published`: "only a back-fill
  (exploratory) record exists for this session: M1's live job is not running yet". The base rates are the record's
  own; the recent strip shows the real 2% moves with no colour; red share 0; every score `not_enough_data`.

## Criteria and their tests

| # | Claim | Test |
|---|---|---|
| 1 | Built from the real source, validated as stored and as served, every number re-read from the source | `tests/market_read_models/test_weather_page.py`: the real 14 Oct 2026 record (base rates, status, the recent strip's 2% moves recomputed from the closes file); a 260-session live fixture (figures, times usual, drivers, red share, Brier by hand). Read back by hash: the existing publish tests now count the page (1,270 pages, 19 blocks) |
| 2 | No Drive-only input | Not applicable. The weather's only private field, the US cue, is never read here, and the page has no Drive input |
| 3 | A validation failure prints the path and rule only | `tests/market_read_models/test_contract_log_line.py` plants an out-of-range number and a wrong enum. The message names `payload/p_big_1d: breaks 'maximum'`, never the value |
| 4 | Never sent: no level, no `reaches`, no US cue | `test_the_page_never_carries_a_level_a_reaches_colour_or_the_us_cue`: no `reaches`, `us_move` or `private` in the page; no driver text holds any of M1's levels as formatted, or the words floor, turns, level or threshold |

## Changes outside the new files, for the judge to check

1. **`contract.py` (privacy rule 3, every page):** `ContractBroken` now prints the path and the rule it breaks, never
   jsonschema's message (which quoted the value).
   - For a missing or unexpected field it adds the field names: keys, never values.
   - Under `anyOf`/`oneOf` it reports the closest alternative of the right type, so a nullable object's failure is
     named in its object branch.
2. **`tests/market_read_models/test_p1_t1_card.py` (the screens lead's test):**
   - It asserted that the bad enum *value* "new_reason" appears in the message, which is exactly what rule 3 forbids.
   - It now asserts the path and rule, and that the value is absent.
3. **Page counts in two publish tests:** 1,269 to 1,270 pages, 18 to 19 blocks (the one new page).
4. **`example_rows()`** gives the weather block an empty input, which yields the not-published state.

## Choices the story text left open (some evidence or reasoning only; accept or reject)

1. **Recent, red share and scores count live records only. The story said "from the back-fill, labelled
   exploratory".**
   - The 2.7.0 schema has no field to label a colour or a score exploratory (`recent[]` holds session, colour and
     big_move only; `FnoWeatherScore` has no label).
   - So publishing back-fill colours or scores there would show them as the weather's real record. M1 itself marks
     its back-fill records "not counted (back-fill)" for the red share.
   - **Proposal to the screens lead:** add `label` to `recent[]` and an `exploratory` flag to `FnoWeatherScore` in
     2.8.0 (additions only). Then the back-fill can show, labelled. Until then the history page is where the
     back-fill belongs.
2. **Scores are computed here, descriptively.**
   - What is computed: the mean Brier of the operative model's live probabilities against the base rate's and v0's in
     the same records, over live days resolved by the session; the status is `scoring` from 10 days.
   - The verdict stays `not_tested`, because the frozen test is G8's looks.
   - This overlaps G8's scoring function. The alternative is reading G8's report, but G8's committed report has no
     live weather row and no stable live-cohort shape yet. If the judge sees this as a second scorer, the fix is a
     reader of G8's report when G8 publishes live V6 rows, and it swaps in one function.
3. **The drivers, defined without levels, as agreed (response 219, addendum 2):**
   - Each of v0's four inputs that changed since the previous session's record, its value in plain words.
   - `push` is the sign of the change; ordered by |change| / the input's median absolute change over the last 250
     records.
   - Scheduled events follow, each "riskier" (an event has no size to rank).
   - The input names map to the contract's drivers: vix_ratio to vix_level, vix_change5 to vix_change, move5 to
     recent_big_moves, rv10 to realised_volatility.
4. **The rest of the page:**
   - `model_version` is the record's `operative` (`weather_vix_v1`);
   - `intraday` is empty (LM1 not built);
   - `price_of_calm` is `not_measured_yet` (no shadow fills, E8).

## Gates

- `ruff check`, `ruff format`, `tools/check_imports.py`: clean.
- `pytest -n auto`: 6,832 passed on `story/p2a-weather`, branched from main at 90b4902d.
