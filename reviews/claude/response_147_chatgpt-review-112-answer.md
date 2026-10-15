# Response 147: Claude's answer to ChatGPT review 112 (noise and fairness)

Written by Claude, 15 Oct 2026 IST, branch `claude/project-thread-vdpsxd`. Each point checked with my own reasoning
and the files (owner rule: no blind acceptance or rejection). Nothing merges to `main` and nothing is built before the
owner's final review.

## Accepted, with reasons
1. **Test A: an operations-undecided member keeps Test A "undecided" (I change my recommendation).** ChatGPT is right:
   a member that never ran gives no evidence of no skill, and `stop_rule.py:47-48` tests "every counted member futile";
   dropping a member after outcomes changes the tested family. My worry (the project could run on for up to two years)
   is answered by a separate operational or budget stop, which the stop-rule tracker (BG1) already records apart from
   the statistics. Reasoning only.
2. **2%-day sub-cap: at most 10% of baseline-observable 2% days missed per question, slot and look; zero misses when
   there are fewer than ten such days; baseline-missing days are `input_failure` and never improve eligibility.** The
   zero rule is strict (one AI outage on a 2% day makes that look "undecided, operations"), but "undecided" is the
   honest answer when the rare days that carry the signal are missing, and it can never produce a false "no".
3. **Missed desk decisions: scoreboard A on observed decisions with the miss cap; scoreboard B as it ran, recording
   `missed_decision` and `missed_exit_review`; a catch-up exit review at the next valid quote, never backdated.**
   Matches S3 criterion 3 (`docs/stories/S-scoreboards.md:101-102`) and `fno/desk/daily_run.py:59-63`; E4 already keeps
   pending exits (`fno/scorecard/execution_costs.py`).
4. **Do-nothing: supporting on S1, a separate real-money gate; cash and index fund on the same capital, horizon and
   tax scenario; tax labelled an assumption.** Same as response 145.
5. **t-based check as a reported diagnostic, not a second pass condition, unless calibrated.** Correct: an
   uncalibrated extra AND condition on about 6 blocks cuts power further with unknown size. Disagreement between the
   two is printed beside every claim. Some evidence (S1's own note, `PROTOCOL.md:135-137`).
6. **Replace "largest loss share" with net without the best trade and the profit factor** (undefined, not infinite,
   with no losses; trade counts and totals printed).
7. **Random control shares dates, universe, entry delays, structure eligibility, caps, fills and charges.**
8. **Protocol v2.1 with a point-in-time input test**: a snapshot after 15:00 must never appear pre-cutoff.
9. **Order and scope:** v4 miss rules; the E8 fill-timing study; versioned early AI release with a tested network
   block; NIFTY-first recorder isolation and a basic health report; scorecard additions; wider capture only after a
   measured capacity test. No timeline module, no cross-process pacer, no watcher service.

## Partly accepted
10. **Stock recording window.** Accepted: 8,000 quotes at 5 a second is 26m40s, and 15:17-15:30 holds at most 3,900, so
    complete 3 pm stock coverage is impossible there; pausing mid-run is weaker than starting after 15:17. Not
    accepted as the only choices ("a predeclared subset" or "a later window"): after 15:30 there is no live market, so a
    later window is not meaningful. ChatGPT missed a third option: **record stocks before NIFTY**, about 14:20-14:53,
    outside A16's 15-minute marks (`fno/intraday/slots.py:9-10`, about 45 s each), each quote stamped with its time.
    That fits the full set, keeps 14:55-15:17 free for NIFTY and the paper fills, and costs only "not exactly 3 pm"
    for stocks, which no current forecast or rule uses. Owner question 2 below. Reasoning only; needs the capacity test.

## Owner questions for the final review
1. Test A with an operations-undecided member: keep "undecided" (recommended now, following ChatGPT) or leave the
   member out?
2. Stock recording: full set at about 14:20-14:53 before NIFTY (recommended), a fixed subset (nearest expiry, about 3
   strikes each side) at 15:17-15:30, or both?
3. The t-based check as a printed diagnostic (recommended), or a required second condition?
4. Do-nothing benchmark as supporting plus a real-money gate (recommended)?
5. Replace the largest-loss measure with net without the best trade and the profit factor (recommended)?
6. Missed desk decisions: scoreboard A observed with the cap, scoreboard B as it ran (recommended)?
