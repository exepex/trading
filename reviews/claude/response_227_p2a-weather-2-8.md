# Response 227: P2a part 2, contract 2.8.0, the labelled back-fill and `weather_history` (claims for judge D, lane 1)

Builder: session 013xqaNTCbSBytKgqpfaYFqZ, branch `story/p2a-weather-2-8` from main at 18c6e1e1 (P2a part 1 merged).
Story: `docs/stories/W3-fno-screens.md`, step 1. Part 1 was judge 218 with addendum 1.

## What changed

1. **Re-pin to 2.8.0** (`contracts/omenix-dashboard/`).
   - The files are byte copies from `exepex/omenix-dashboard` at the merge candidate `story/fno-2-8-merge` 0e2d58e.
     The screens lead says its `api/` files are final.
   - Four new schema files are added: fno-weather-history, fno-scoreboards, fno-budget and fno-data-health. No file
     was removed. `contract_version` is 2.8.0.
   - **Pending:** `pin.json`'s `commit` must become the dashboard's main merge SHA once it exists. If the `api/` bytes
     at that SHA are identical, only that one field changes; a pin test checks every file's SHA-256 either way.
2. **`weather`, the labelled back-fill (2.8.0's three fields):**
   - `recent[]` shows each record's colour with its `label` (live or backfill_exploratory; null without a record).
   - `red_share` counts the live records once any exists, else the back-fill, and says which in `basis`. As M1 counts
     it, all records of the basis are counted, an unscored day as not RED, and over-alarming is judged only at 250.
   - `scores[]` are still G8's alone (judge 218): not_enough_data, no number, and `exploratory` true while only the
     back-fill exists.
   - Today's colour is still only ever a live record's.
3. **`weather_history`, new** (`weather_history_block.py`, `FnoWeatherHistory`):
   - It lists every M1 record up to the session, oldest first, as {session, colour, label}, with counts by colour
     and label.
   - Colour and label only, judge 217's strict form: no chance of a big move, no usual chance, no input value, no
     `reaches` colour, no US cue.

## On real data (14 Oct 2026)

- `weather`: not_published (back-fill only). The recent strip shows 10 back-fill colours, labelled. Red share is 13 of
  250 back-fill records = 5.2%, basis backfill_exploratory, not over-alarming.
- `weather_history`: 2,409 rows, 2017-01-03 to 2026-10-14. Counts: GREEN 1,634, AMBER 149, RED 121, not scored 505,
  live 0, back-fill 2,409. These match the story's table exactly.

## Tests

| Claim | Test |
|---|---|
| History rows and counts are the record files' own, recounted straight from the folder | `tests/market_read_models/test_weather_history_page.py::test_every_committed_record_up_to_the_day_is_a_row_oldest_first_and_the_counts_are_the_files_own` |
| A history row carries only session, colour and label (no chances, values, `reaches` or US cue) | `test_a_row_carries_only_its_session_colour_and_label` |
| The empty state before the first record | `test_a_day_before_the_first_record_publishes_the_empty_history` |
| The real recent strip shows the back-fill, labelled, and the closes' own 2% moves | `test_weather_page.py::test_the_real_recent_strip_shows_the_back_fill_labelled_and_the_closes_own_2pct_moves` |
| The real red share is recounted from the last 250 records, basis back-fill; the scores are exploratory | `test_the_real_session_is_not_published_from_a_back_fill_record_and_every_number_is_the_records` |
| Once live records exist the share counts them (basis live) and the page still scores nothing | `test_once_live_records_exist_the_red_share_counts_them_and_the_page_scores_nothing` |
| Pin version 2.8.0; the page counts (1,271 pages, 20 blocks) | `test_market_contract_and_run.py`, `test_market_publish_read_back.py` |

Gates: ruff, format and `tools/check_imports.py` clean; `pytest -n auto` 6,840 passed.

## A point for the judge (reasoning only)

The red share's back-fill basis shows the share as a fact about history (labelled), never a published colour count.
Under M1's rule, live records replace the back-fill as the basis from the first live record. The share then starts
over at 1 record, and over-alarming waits for 250 live ones.
