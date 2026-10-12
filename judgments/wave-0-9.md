# Wave 0 judgment, round 9 (2026-10-12)

**Verdict: PASS.** N24 is fixed. Nothing is blocking, should-fix or new minor. The round-8 and round-7 regression sets only changed where the fix meant them to.

## Commands and results
- Checkout: `git fetch origin claude/beautiful-pascal-566jb5 && git checkout --detach origin/claude/beautiful-pascal-566jb5`. HEAD is **5ebcd44**, "Fix wave 0 round 8 minor: a strong dollar is a cause only when stated as one". Its parent is 3374f6d.
- Diff 3374f6d..HEAD: `fno/live/news/classifier.py` (new `STRONG_DOLLAR` regex, and the scoring in `direction()`), `tests/live/test_news_fixes.py` (4 new cases) and the judgment files. Nothing else changed.
- `python -m pytest -q`: 204 passed.
- `ruff check fno tests`: All checks passed.
- `ruff format --check fno tests`: 136 files already formatted.
- File sizes: the largest are fno/live/services.py (337), fno/strategies.py (321) and fno/journal.py (320). fno/html_report.py (722) is exempt. Nothing is over 350.
- The new tests really test the fix. I ran HEAD's `test_news_fixes.py` against a parent export, with the parent's `fno` confirmed first on sys.path (`/tmp/judge9/parent/fno/__init__.py`). Result: **4 failed, 47 passed**, and the 4 failures are exactly the 4 new cases.
- `git status --short`: clean. I changed no repository files. My probes are in /tmp/judge9 (probe.py, run.sh, base.txt, new.txt, the parent and head exports, and the outputs).

## N24: CLOSED
How the fix works:
- STRONG_DOLLAR does not count when "despite" comes before it.
- It does not count when a fade word (eases, fades, cools) or a non-currency noun (inflows, revenue, bonds) comes after it.
- It counts -1 only when no rupee or cost move is in the headline.

Every realistic shape from round 8 is now right (parent → HEAD):
- "Rupee rises 5 paise to 83.12 against US dollar despite firm dollar" 0 → +1
- "Rupee recovers 8 paise despite strong dollar" 0 → +1
- "Nifty ends higher despite strong dollar" 0 → +1
- "Rupee set to open higher as dollar strength eases" 0 → +1
- "Rupee recovers as dollar strength fades" 0 → +1
- "Rupee gains on strong dollar inflows" 0 → +1
- "Rupee rises on strong dollar inflows from FPIs" 0 → +1
- "TCS reports strong dollar revenue growth" -1 → +1
- "Strong dollar revenue growth for TCS" -1 → +1
- "Rupee holds steady despite firm dollar" -1 → 0
- "Rupee holds firm despite strong dollar" -1 → 0 (0 is acceptable)

N23 still holds. These all stay at -1:
- "Rupee hits record low on strong dollar"
- "Rupee weakens on strong dollar demand"
- "Rupee falls 20 paise on strong dollar"
- "Rupee opens weaker on firm dollar"
- "Sensex, Nifty fall on strong dollar, FPI selling"
- "Rupee likely to open lower on strong dollar"
- "Strong dollar demand from importers weighs on rupee"
- "Dollar strength to weigh on rupee: analysts"

New realistic variants I tried also come out right:
- "Rupee rises 4 paise to 83.10 despite strong dollar overseas" +1
- "Rupee settles 3 paise higher at 83.25 despite dollar strength overseas" +1
- "Sensex, Nifty climb despite firm dollar overseas" +1
- "Sensex, Nifty rise as dollar strength eases" +1
- "Rupee gains 10 paise even as firm dollar weighs" +1
- "Rupee unchanged at 83.20 despite firm dollar" 0
- "Rupee falls even as dollar strength eases" -1

## Regression sets (77 headlines: round 8 plus round 7 and earlier), parent vs HEAD
- The only changes are the 15 intended N24 fixes listed above, plus one contrived headline: "Rising dollar bonds yields" -1 → 0.
- N22 still holds: "Dollar falls after Nifty lows", "Crude falls after Sensex lows" and "Rupee rises after market lows" all score 0.
- The level-qualifier cases and the "hits ... high after lows" family are unchanged.

## Findings
No blocking, should-fix or minor findings.

**Noted, not worth fixing.** These are contrived, rare, or were already wrong before this fix. None can enlarge a trade.
- **A fade word before "dollar strength" is not handled.** "Easing dollar strength lifts rupee" scores -1 (it was -1 on the parent too), and "Sensex rallies on easing dollar strength" scores 0. Headlines usually put the fade verb after the phrase ("dollar strength eases"), and that form is handled. The fix, if it ever matters, is a negative lookbehind for `(?:easing|fading|waning|cooling)\s+`.
- **"despite" with a word in between, and "in spite of", only work for rupee headlines.** "Nifty gains despite US dollar strength" scores 0. Rupee headlines with these shapes are right because the rupee move already wins.
- **"strong" stays as a positive word when the phrase is "strong dollar inflows".** So "Rupee falls despite strong dollar inflows" and "Rupee slips as strong dollar inflows dry up" score 0. They were -1. Both are rare, and strong inflows are themselves good news.
- **Some misses come from the general word-count scorer, not from this fix**, and are unchanged from the parent:
  - "Strong dollar, high crude to keep rupee under pressure" 0
  - "Stronger dollar, higher yields weigh on Nifty" 0
  - "Rupee recovers early losses despite strong dollar" 0 (it was -0.5)
- **Debatable cases, unchanged:** "IT stocks rally on strong dollar" 0, "Rupee trades flat amid strong dollar" -1, and "Gold/Metals fall on strong dollar" -1.

**Final verdict: PASS**