# Builder's response to wave 0, round 7 (minors; the wave passed)

| # | Fix | Evidence |
|---|---|---|
| N22 | The word between "after/from/off/since" and "highs/lows" in MOVE_TAIL is limited to level qualifiers (record, fresh, recent, lifetime, all-time, multi-year, session, intraday, "3-month"), so another index's low is never swallowed | classifier.py `MOVE_TAIL`; "Crude falls after Sensex lows" and "Rupee rises after market lows" in `test_rupee_hits_without_a_level_says_nothing` (score 0) |
| N23 | "strong/stronger/firm/surging/rising dollar" and "dollar strength" score as a cost rise (-1) and are removed before the word count, so "strong" no longer cancels a rupee fall | classifier.py `STRONG_DOLLAR`; "Rupee hits record low on strong dollar" and "Rupee weakens on strong dollar demand" (-1) |
