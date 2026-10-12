# Wave 0 judgment, round 8 (2026-10-12)

**Verdict: PASS.** N22 and N23 are both fixed for the headlines they named. The new STRONG_DOLLAR rule causes one new minor problem (N24): it now cancels or flips some good-news rupee and IT headlines. None of these can enlarge a trade by themselves, but one shape is common enough that it is worth a small fix next round. Nothing is blocking or should-fix.

## Commands and results
- Checkout: `git fetch origin claude/beautiful-pascal-566jb5 && git checkout --detach origin/claude/beautiful-pascal-566jb5`. HEAD is **3374f6d**, "Fix wave 0 round 7 minors: tail never swallows another index's low; strong dollar is bad news". Its parent is 97dcec6.
- Diff 97dcec6..HEAD: `fno/live/news/classifier.py` (the MOVE_TAIL middle word and the new `STRONG_DOLLAR`, which is added to the `costs` loop with a score of -1), `tests/live/test_news_fixes.py` (4 new cases) and the judgment files. Nothing else changed.
- `python -m pytest -q`: 200 passed.
- `ruff check fno tests`: All checks passed.
- `ruff format --check fno tests`: 136 files already formatted.
- File sizes: the largest are fno/live/services.py (337), fno/strategies.py (321) and fno/journal.py (320). fno/html_report.py (722) is exempt. Nothing is over 350.
- The new tests do test the fix: run against a parent export, 4 failed and 43 passed. A first attempt reported a false all-pass, because the editable install had imported the worktree's `fno`. I reran it with the parent forced to the front of `sys.path`.
- `git status --short`: clean. I changed no repository files. My probes are in /tmp/judge8: probe.py, heads.txt, the parent and head exports, and `fix/`, which is a scratch copy for trying the suggested fix.

## N22: CLOSED
Scores, parent → HEAD:
- "Dollar falls after Nifty lows" +1 → 0
- "Crude falls after Sensex lows" +1 → 0
- "Rupee rises after market lows" +1 → 0
- "Crude falls after Nifty-50 lows" +1 → 0

The level qualifiers still work: "Crude falls after 3-month highs" +1, "Rupee rises after 52-week lows" +1, "after session lows" +1, "Crude eases from multi-year highs" +1.

## N23: CLOSED
- "Rupee hits record low on strong dollar" 0 → -1
- "Rupee weakens on strong dollar demand" 0 → -1
- Also fixed: "Rupee falls 20 paise on strong dollar" 0 → -1, "Rupee opens weaker on firm dollar" 0 → -1, "Strong dollar weighs on rupee" +1 → -1, "Rupee settles 9 paise lower at 83.30 on strong dollar" 0 → -1.
- No double counting: macro signs are summed and then reduced to a sign, so a rupee fall plus a strong dollar is still -1, not -2.

## Round-7 regression set
I reran 47 headlines from round 7 (N21, LEVEL_STOP, the tail clauses, the tail-swallow cases and the leftover edge cases) on the parent and on HEAD. The only changes are the N22 and N23 fixes listed above. The known contrived leftovers are unchanged: "Rupee hits a high and a low" is still -1.

## STRONG_DOLLAR probes you asked for
| Headline | Parent → HEAD | Right? |
|---|---|---|
| Rupee gains despite strong dollar | +1 → 0 | Wrong, should be +1 |
| Dollar strength fades, rupee rises | +1 → 0 | Wrong, should be +1 |
| Strong dollar inflows into Indian equities | +1 → -1 | Wrong (inflows are good). Contrived |
| Rising dollar bonds yields | 0 → -1 | Acceptable (rising yields are bad anyway). Contrived |

## New findings

### N24 (minor): STRONG_DOLLAR cancels or flips some good news
**Cause.** STRONG_DOLLAR is scored -1 and added to the macro sum even when:
- the headline also has a rupee move going the other way ("despite"),
- the dollar strength is fading,
- "strong dollar" describes something else (inflows, revenue).

**Realistic shapes that are now wrong** (parent → HEAD):
- **Rupee rises despite a firm dollar.** This is a fairly common PTI or Reuters daily rupee shape.
  - "Rupee rises 5 paise to 83.12 against US dollar despite firm dollar" +1 → 0
  - "Rupee recovers 8 paise despite strong dollar" +1 → 0
  - "Nifty ends higher despite strong dollar" +1 → 0
- **Dollar strength fading.** This is an occasional Reuters shape.
  - "Rupee set to open higher as dollar strength eases" +1 → 0
  - "Rupee recovers as dollar strength fades" +1 → 0
- **"Strong dollar inflows".** This is occasional in rupee reports.
  - "Rupee gains on strong dollar inflows" +1 → 0
  - "Rupee rises on strong dollar inflows from FPIs" +1 → 0
- **Wrong sign on a results story** (rare, but possible in IT results headlines):
  - "TCS reports strong dollar revenue growth" +1 → -1
  - "Strong dollar revenue growth for TCS" +1 → -1
- **Wrong sign when the rupee holds up:**
  - "Rupee holds steady despite firm dollar" 0 → -1
  - "Rupee holds firm despite strong dollar" +1 → -1
- **Debatable, not counted as errors.** "IT stocks gain on strong dollar" +1 → 0: a strong dollar helps IT exporters. "Gold/Metals fall on strong dollar" 0 → -1.

**Failure scenario.**
- In the common cases, good macro news becomes neutral. The fast_news vote is lost. A direction-0 important story can also trigger the news_shock wait guard. Both make the desk more cautious, so this cannot enlarge a trade.
- The sign flips (the TCS revenue and "rupee holds") give a wrong bearish vote. That vote only matters if other votes agree with it enough to tip the strong-evidence sizing in `market_view._is_strong`, and lots stay capped by `max_planned_loss`. These shapes are rare. This is the same class as earlier classifier minors.

**Fix (small, and I checked it in /tmp/judge8/fix).**
- Make STRONG_DOLLAR a fallback cause: count it only when no rupee or cost move has matched (`if not macro`), still removing the phrase before word counting.
- Do not match it after "despite".
- Do not match it before a fade word or a non-currency noun: `(?!\s+(?:inflows?|revenues?|deposits?|bonds?|fades?|eases?|wanes?|ebbs?|cools?))`.
- With these changes all 20 realistic probes come out right: "despite firm dollar" +1, "dollar strength eases" +1, "strong dollar inflows" +1, "strong dollar revenue growth" +1, "Rupee holds steady despite firm dollar" 0. The N23 cases stay -1.
- Add the "despite" headline, the "dollar strength eases" headline and the TCS revenue headline as tests.

**Is it worth fixing?** Yes, but only for the "despite" and "strength eases" shapes, because they are real and recurring. The "inflows", "bonds" and "revenue" shapes alone would not be worth fixing, but the same lookahead covers them for free.

**Final verdict: PASS.** N22 and N23 are closed. N24 is a minor finding and I recommend fixing it next round.