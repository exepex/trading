# Wave 0 judgment, round 7 (2026-10-12)

**Verdict: PASS.** N21 is closed. The new MOVE_TAIL clause brings in one small, minor regression (N22). I also found an older minor issue that is not new in this round (N23). No blocking or should-fix finding is open.

## Commands and results
- `git fetch origin claude/beautiful-pascal-566jb5 && git checkout --detach 97dcec6`: OK. `git rev-parse --short HEAD` returned 97dcec6.
- Diff c27fc67..97dcec6: the classifier regexes (`LOW_LEVEL`, `HIGH_LEVEL`, `LEVEL_STOP`, `LEVEL_FILLER`, a third `MOVE_TAIL` clause), the runner docstring (the nit is fixed), tests, and the judgment files. No other logic changed.
- `python -m pytest -q`: 196 passed.
- `ruff check fno tests`: All checks passed.
- `ruff format --check fno tests`: 136 files already formatted.
- File sizes: the largest are fno/live/services.py at 337 lines, fno/strategies.py at 321 and fno/journal.py at 320. fno/html_report.py (722) is exempt. Nothing is over 350.
- The new tests fail on the old code, as the builder says: with the HEAD test file run against a c27fc67 export, 5 failed and 38 passed.
- `git status --short`: clean afterwards. I changed no repository file. My probes are in /tmp/judge7 (probe.py, heads.txt and a parent export). Each headline was scored on the parent and on HEAD.

## N21: CLOSED
Scores (parent → HEAD):
- **Round-6 headlines, now correct:**
  - -1 → +1: "Rupee hits 3-week high after lows", "record high after lows", "peak after record lows", "two-week high off lows", "one-month high from lows", "high from lows", "strongest since lows of 2023", "a high after lows", "a 3-week high after lows".
  - -1 → 0: "Rupee hits back from lowest levels", "Rupee hits importers with lowest margins".
- **LEVEL_STOP does not block real headline shapes:**
  - Still -1: "Rupee hits record low against dollar", "lifetime low on FPI outflows", "record low amid FPI selling", "all-time low against US dollar", "a fresh record low against the US dollar", "all-time low on weak data", "record low vs dollar", "lowest since March", "fresh low as crude surges", "record low; Sensex falls 500 points".
  - Still +1: "Rupee hits one-year high amid inflows", "strongest level since July", "two-week high as FPIs return".
- **The new MOVE_TAIL clause, cost and rupee moves:**
  - Same sign as before and correct: "Crude jumps from 3-month lows" -1, "Rupee falls from record highs" -1, "Dollar rises after lows" -1, "Yields ease off highs" +1, "Crude falls off record highs" +1, "Crude surges 4% off lows" -1, "Yields rise from lows of 2023" -1.
  - Fixed by the change, now correct: "Rupee recovers from lows" 0 → +1, "Rupee rebounds off lows" 0 → +1, "Rupee slips from highs" 0 → -1, "Crude rises after highs" 0 → -1.
- **The tail does not swallow a separate clause:**
  - "Rupee rises after lows; Sensex falls" = 0 (rupee +1 and Sensex -1 are both counted).
  - "Crude drops off highs as Sensex slides" = 0 (it was +0.5 because "highs" counted as good news).
  - "Dollar rises off lows, Nifty hits record high" = 0 (it was -0.5).
- **Leftover edge cases (contrived, not a finding):**
  - "Rupee hits a high and a low" and "Rupee hits a peak a low" still score -1. The optional `a/an` comes after the negative lookahead, so "a high" gets past the stop.

## New findings
- **N22 (minor; a regression from the new MOVE_TAIL clause): the tail can swallow another index's high or low.**
  - Cause: the clause is `(after|from|off|since)(\s+[\w-]+)?\s+(highs?|lows?)`, and the optional middle word can be anything, including an index name.
  - Evidence (parent → HEAD):
    - "Dollar falls after Nifty lows": 0 → +1
    - "Crude falls after Sensex lows": 0 → +1
    - "Rupee rises after market lows": 0 → +1
  - The bad news that the market hit lows is removed with the move, so a mixed headline reads as good news.
  - Failure scenario: such a headline nudges the market view bullish and does not count as bad news in the news guard or exits. The headline shape is rare, and it cannot enlarge a trade.
  - Fix: limit the middle word to level qualifiers, e.g. `(?:record|fresh|recent|lifetime|all-time|multi-year|session|intraday|\d+-\w+)`, or exclude subjects such as `(?!(?:nifty|sensex|market|stocks?)\b)`. Add "Crude falls after Sensex lows" (expected 0) to the tests.
- **N23 (minor, older code, not a regression): "on strong dollar" cancels a rupee fall.**
  - "Rupee hits record low on strong dollar" and "Rupee weakens on strong dollar demand" both score 0 at HEAD and at the parent. "strong" is in `POSITIVE`, so it cancels the rupee's -1.
  - This is a common real headline shape. The failure is a missed bad-macro signal, which only weakens the news guard and exits.
  - Fix: score "strong dollar" or "dollar strength" as a cost rise (-1), or drop "strong" when it comes right before "dollar". Add a test for the record-low headline (expected -1).

**Final verdict: PASS.** N21 is closed. N22 and N23 are minor and do not block the wave; I recommend fixing them in the next round.