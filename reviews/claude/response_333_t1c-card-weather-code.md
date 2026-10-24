# Response 333: T1c code, the card shows M1's live weather record: claims (for the card's judge)

**Branch:** `story/t1c-card-weather`. **Text:** `docs/stories/T-cards.md`, T1c (judge 401 PASS), with two
amendments explained below. **Lane:** 1. **Unblocks:** O11 go-live row 8 (orchestrator, via M1's builder, 23 Oct).

## Text amendments since judge 401 (please check them)

1. **A record that is not `live` is never today's weather** (M1's builder, 23 Oct). The text at judge 401 showed a
   back-fill with a "(back-fill, exploratory)" label. Criterion 5 now treats it like a missing record:
   - the card says "Weather: no live reading for <d> (the record is <label>, not today's weather)" and "No new
     trades";
   - no colour is shown;
   - the record is still listed by its SHA-256.
2. **Chances are shown with one decimal, not whole percents** (self-review). On the real 23 Oct record, whole percents
   showed the model's 2.9% and the base rate's 2.7% both as "3%", which hid that the model is above the base rate.

## Criteria, code and tests

| # | Criterion | Code | Test (each fails when that code is broken; mutations run) |
|---|---|---|---|
| 1 | A scored live record shows colour, operative, proof, chances, base rates and v0, and is listed by SHA-256 | `fno/cards/recorded_weather.py` `weather`, `_scored_lines` | `test_a_live_green_record_...` (the real 23 Oct record) |
| 2 | No record, unreadable or not a dict, wrong day: "no reading" plus the block, no colour | `weather`, `_parsed` | `test_no_readable_record_...` (4 cases). Mutation: day check removed fails it |
| 3 | Not scored: why plus the block; a colour other than GREEN/AMBER/RED or a malformed chance fails closed | `SHOWN`, `_chances`, `_is_chance` | `test_a_not_scored_record_...`, `test_a_colour_m1_never_writes_...` (3), `test_a_malformed_chance_fails_closed_...` (8). Mutation: range check removed fails 2 |
| 4 | RED adds "no new entries"; GREEN and AMBER do not | `_scored_lines` | `test_only_red_adds_no_new_entries`. Mutation: RED line removed fails it |
| 5 | Only `live` is today's weather | `weather` (label check) | `test_a_back_fill_record_is_never_today_s_weather_...` (the real 14 Oct back-fill) |
| 6 | No driver; only committed bytes are read | the adapter reads no `drivers`; `CommittedRecords` | `test_no_driver_value_reaches_the_card`; `test_the_app_reads_the_real_committed_record_and_an_uncommitted_file_reads_as_no_reading` |
| 7 | `PendingWeather` gone; the wiring builds `RecordedWeather` | `fno/cards/wiring.py` `_weather`; `fno/cards/weather.py` deleted | O11's T1c strict xfail is now a real check (`tests/e2e_acceptance/test_expected_missing.py`) |
| - | A weather source that raises still says "no new trades" | `fno/cards/card.py` `_guarded(..., extra)`; `WEATHER_BLOCKS` moved to `sections.py` | `test_a_weather_source_that_raises_still_says_no_new_trades`. Mutation: extra line dropped fails it |
| - | An older record without `v0_status` (judge 401 minor) | `_v0_line`, `NO_REASON` | `test_an_unscored_v0_shows_its_reason_and_an_older_record_without_one_never_raises` |

## Builder self-review (quality rule 3)

Two independent review agents ran on the diff, one for correctness and one for silent failures. Both had been
stopped by the weekly limit on 16 Oct, so this is their first full run.

| Finding | Action |
|---|---|
| A scored record with an unexpected colour ("BLUE", None, missing) was shown as a reading | FIXED: only GREEN, AMBER and RED are shown; anything else is not scored, with its reason named |
| Malformed shapes (`probabilities` a string, an entry a list, `value` a string) raised; the guard then dropped the owner's "no new trades" line | FIXED twice: `_chances` never raises (type checks), and the card's guard adds `WEATHER_BLOCKS` to the weather fallback |
| `value` not checked to be a chance (True printed "100%"; NaN; outside 0..1) | FIXED: `_is_chance` needs a finite, non-bool number in [0, 1] |
| Whole percents hid 2.9% against 2.7% | FIXED: one decimal (text amendment 2) |
| `_weather(records, root)` had an unused `root` | FIXED: removed |
| A git failure (e.g. "dubious ownership") reads as "not committed", so a real record shows "no reading" | KEPT (older T1 code, `committed.py`). It fails safe: it blocks trades and names the record as missing. Telling the two apart is a separate T1 change |
| The real-record test depends on the 23 Oct record staying committed | KEPT: records are write-once (M1), so it stays |
| The card is not live yet (`daily.live_from.card: null`) | Noted: this reaches #fno-desk only once the owner sets the card's live date |

## Real output sample (quality rule 6)

Dry runs (`python -m fno card daily --on <d>`, no post, nothing written), from the committed records:

```
23 Oct (live record):
Weather: GREEN (weather_vix_v1, not yet proven: G8 has not scored it against v0 and the base rate)
Chance of a 2% NIFTY move: next session 2.9% (base rate 2.7%); within 5 sessions 12.9% (base rate 10.4%)
Checklist v0: AMBER

14 Oct (back-fill record):
Weather: no live reading for 2026-10-14 (the record is backfill_exploratory, not today's weather)
No new trades while the weather reading is missing (owner rule).
```

**Gates:** see the push message.
