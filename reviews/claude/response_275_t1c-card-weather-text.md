# Response 275: T1c, the card shows M1's weather record: story text claims (for Judge E)

**Branch:** `story/t1c-card-weather` (docs only). **Text:** `docs/stories/T-cards.md`, section T1c. **Lane:** 1 (the
card decides what the owner sees about a trade). **Found by:** the O11 replay (orchestrator, 16 Oct 2026).

| # | Claim | Evidence |
|---|---|---|
| 1 | The card ignores M1 today. | Strong: `fno/cards/weather.py` `PendingWeather` always returns "Weather: not yet scored (M1 pending)". `fno/cards/wiring.py` builds it. |
| 2 | M1's record has the fields the card needs, and they are stable. | Strong: the record `research/forecasts/v4/weather/2026/2026-10-14.json` (committed) holds `day`, `colour`, `status`, `label`, `operative`, `proof`, `v0_colour`, `probabilities`. M1's builder confirmed these are stable (16 Oct; `v0_status` added the same day). |
| 3 | Unscored values have exact forms. | Strong: `status` is "scored" or "not scored: ..." (`fno/weather/day.py:100,120`). The colour can be `WeatherColour.NOT_SCORED`. `_status` marks a day not scored if any operative or base-rate value is missing, so a scored record always has its probabilities. |
| 4 | Reading the committed bytes, not `for_day` on disk, is the right source. | Strong: every card section reads through `CommittedRecords` and lists its records with their SHA-256 (`UsedRecord`, `fno/cards/sections.py`). In O1's run the weather step commits before the card (M1's builder). An uncommitted record therefore reads as "no weather", the honest result. |
| 5 | The owner's "missing weather blocks new trades" stays on the card. | Strong: owner "4 A" (15 Oct), quoted in `fno/cards/weather.py` and `fno/weather/constants.py` (NOT_SCORED "blocks new trades like RED"). Criteria 2 and 3. |
| 6 | No private data can reach the card. | Strong: the record keeps the US flag out (M1 Scope item 4, `"us_move": "private"`), and the adapter never reads `drivers` (criterion 6). |
| 7 | A RED card next to a TRADE status cannot happen today. | Strong: the card's status is always `NO TRADE` while no version is at `paper` (`playbook/registry.csv` holds only B0, `research`). The status reading the weather is T1 slice B (Out). |
| 8 | The blocking itself is not in this story. | M1's text, Out, names it as the desk entry gate's own story. T1c only shows it. |
| 9 | Size and design. | One adapter behind the existing `WeatherSource` port, one wiring line, and `PendingWeather` removed (no dead code). The "not scored" string is M1's constant, imported, never copied. |

**Gap list:** in the text (M1's card requirement, owner "4 A", T1's "never a colour it did not score", privacy, the
SHA-256 footer; the desk's block is Out).

**Splits:** M1's builder (013xqaNT) agreed the reader and the fields (16 Oct), and will warn before any move of these
records to Drive (O9). No other register row touches `fno/cards/weather.py`, and T1 and T2 are mine.

**Owner effect (when built):**
- Today the card shows "no reading", because only back-fills (to 14 Oct) are committed.
- From the day `weather capture` runs live, it shows the colour, the chances against the base rate, and "not yet
  proven".
