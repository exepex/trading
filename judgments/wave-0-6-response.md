# Builder's response to wave 0, round 6 (minor; the wave passed)

| # | Fix | Evidence |
|---|---|---|
| N21 | The words between "hits" and the level stop at any other level word or a linking word (back, from, with, after, off, since, against, amid, on), so "hits 3-week high after lows" is a high and "hits importers with lowest margins" says nothing. A trailing "after/from/off/since ... lows/highs (of 2023)" now belongs to the move, so it is not scored again as bad news | fno/live/news/classifier.py `LEVEL_FILLER`, `LEVEL_STOP`, `MOVE_TAIL`; tests: 3 new +1 headlines and `test_rupee_hits_without_a_level_says_nothing` (5 fail on the previous code) |
| Nit | `_load_reference_if_needed` docstring says "from 08:45 to the close" | fno/live/runner.py |

The runner's import of `DEFAULT_ACTIVE_FROM` from the news schedule is kept on purpose: the outage alert starts with the same pre-market window as the news.
