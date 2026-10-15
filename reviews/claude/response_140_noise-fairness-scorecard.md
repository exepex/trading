# Response 140: noise, fairness, all-F&O recording and the scorecard (owner decisions of 15 Oct 2026)

Written by Claude, 15 Oct 2026 IST, from the handover `conversations/2026-10-15_handover_noise_fairness.md` and the
owner's answers in the project thread. For ChatGPT and the judge: please review the reasoning and the plan.

## Owner decisions (docs/DESK_DECISIONS.md, 15 Oct 2026)
1. E1-E5 approved with the E1 amendment (response 137).
2. A missed forecast day scores as the no-skill base rate; a missed decision is NO TRADE.
3. The 3 pm recorder records all F&O (every index and stock F&O chain), NIFTY first, data only.
4. S1's headline stays; four supporting measures are added (below).

## Found in the code (strong evidence)
- The capture starts on the `.canonical` push but still sleeps until 15:10 IST (`.github/workflows/forecast-capture.yml`
  lines 86-89), so the AI books get about 5 minutes. The pack's content is the same whenever built (15:00 cutoff).
- Times live in several places: `fno/quotes/recorder.py:36`, `fno/forecast/schema_v2.py:18`, `fno/ai/timing.py:13-15`,
  the YAML wait.
- Protocol v4 (draft) already has 1- and 5-session questions (V1, V2, V6a, V6b, V7, section 1.2) and says only V6b is
  realistically claimable (section 11 D). More short questions do not fix noise; more independent days do.
- Protocol v4 section 4 drops "forecaster missing" dates: conflicts with decision 2; must change before the freeze.
- The recorder's scope is NIFTY only (`UNDERLYING = "NIFTY"`, story A4 "Out: other underlyings"), although the owner
  directed all index and stock F&O on 13 Oct. NSE's daily F&O file (all contracts, no bid/ask) is archived already.
- Design v2's do-nothing benchmark (`docs/design_v2/03_layers_factory_desk.md:110`) is not built; the scoreboards
  report no drawdown, no largest-loss share and no luck control.

## Scorecard by role (what exists, what is added)
| Role | Measure | Status |
|---|---|---|
| Portfolio manager | Net per rupee of risk after every cost (headline, S1 `primary_metric`) | exists (proposal) |
| Statistician | 120 days, one-sided 95% lower bound, block bootstrap, Holm (S1 `uncertainty_criterion`) | decided 14 Oct; 6 blocks over-claim (S1 notes it) |
| Statistician, red team | Random-strategy percentile: 1,000 random strategies, same limits, fills, costs | **added** |
| Owner (design v2) | Against NIFTY 50 index fund and cash, after 31.2% tax | **added** |
| Risk manager | Maximum drawdown and worst day, rupees and share of the brake | **added** |
| Mathematician, behavioural | Largest loss as share of total gains; average win vs average loss | **added** |
| Options strategist | Scoreboard A, one lot, NO TRADE = 0 | exists (proposal) |
| Volatility trader | Edge at entry (implied paid vs realised after), diagnostic only | reported later |
| Execution, tax | E6 execution costs, C1 tax line | exist |
| Analyst | Results per regime (`fno/forecast_v4/regime.py`) | reported |
Left out on purpose: win rate alone, Sharpe on short samples, more forecast measures (multiple testing).

## Plan (each lane 1 unless noted)
0. Verify the 16 Oct 3 pm run (setup before 14:52, `started_at` by 15:00, forecast v2 20 of 20 with IV30).
1. This file (lane 3).
2. Story E2+E5: release on `.canonical`; `fno/timeline.py` for the times it touches; v4 section 4 base-rate rule.
3. Daily 18:00 IST health check (GitHub Actions; one #fno-desk line).
4. Backfill test compares decompressed content (`tests/forecast/test_backfill.py:44`).
5. All-F&O 3 pm recording, NIFTY first; measure Groww's limits in a test run.
6. The four scorecard measures plus edge at entry.
7. Rule-family history tests on 2019-2025 end-of-day data, labelled exploratory.

## Questions for ChatGPT
1. Is base-rate scoring of missed days right for QLIKE point questions (V1-V3), where "base rate" must mean a named
   no-skill forecast (we propose the primary baseline's value)?
2. Any measure above you would drop or add, with reasons?
3. All-F&O capture inside 14:55-15:10: any reason to split stock chains into a later window?

## Red team of this plan (Claude, same day)
1. Step 7 is exploratory only: the 2019-2023 holdout is used up (DESK_DECISIONS 13-14 Oct; experiment 2 is forward).
2. E2's earlier release gives AI books about 17 minutes with the pack while live prices move; verify their network
   allow-list blocks market sites and log fetches before E2 (F-ai-layer lines 34-48 say no network; the live
   forecast books push to GitHub, so this must be checked).
3. `fno/timeline.py` must import the frozen `GENERATION_DEADLINE` from `fno/forecast/schema_v2.py` (hashed by the v2
   freeze), never move it.
4. All-F&O: one recorder per underlying group, each with its own completeness and canonical file; NIFTY's recorder
   and its byte-identical baseline untouched, so illiquid stock chains can never leave NIFTY's day without a canonical.
5. All-F&O builds on the Drive-only raw-quote story (DESK_DECISIONS 15 Oct, "6 A").
6. E5 for point questions V1-V3: a miss scores as the primary baseline's forecast (no base rate exists for QLIKE).
7. Define the random strategy (same structures and sizes, random direction and strike, 1,000 seeded runs) and the
   do-nothing benchmark (per rupee of capital tied) in S1 before its freeze.
8. Add S1's t-based check: 120 days is about 6 bootstrap blocks, which over-claims.

## Second red team (three independent reviewers, each finding checked against the code by Claude)

### Decisions that need the owner again
- **D2 base-rate scoring has a futility flaw (strong, code + simulation).** An imputed day gives d = 0, but the
  futility test adds margin x b_t > 0 for it (`fno/forecast_v4/confirmatory.py:110-122`), so a slot that never ran
  becomes "futile" (all-zero differences, n = 130: p = 8e-8), and futility at look 1 is final; a false "no" rises
  from 0.4% to 2.4% at 40% misses. Imputed days also count toward the 5-day gate and the crash cut
  (`fno/forecast_scoring/v4/comparison.py:92-95`, `look.py:62-65`). Proposed fix: claims, futility and gates on observed
  days only; misses reported beside them; a slot above a fixed miss share is "undecided, operational", never futile;
  misses start counting only from the slot's first counted forecast; apply per question (a null answer is a miss:
  `fno/forecast_scoring/scoring.py:96-98`).
- **D3 "everything now" cannot fit 14:55-15:10 (strong, measured).** NSE's 14 Oct F&O file: 219 option underlyings
  (213 stocks, 6 indices incl. NIFTYFPI), about 8,000 contracts in a 5% band, one Groww `get_quote` each (the chain has
  no bid/ask, A16 story lines 54-58): about 30 minutes at the safe 5 a second, about 2 hours at today's sequential
  pace. Proposed: time slots (NIFTY 14:55-15:00 and pushed at once; other indices next; stocks after), each with its
  own `started_at`.

### Recording all F&O (strong unless marked)
1. Stock chains always fail today: expiry history keeps only index options (`INDEX_OPTION = "IDO"`,
   `fno/quotes/expiry_listing.py:18,62`); stocks are "STO".
2. One commit at the end of the routine would miss forecast-capture's 15:13 latest start
   (`fno/pipeline/capture_gate.py:30-33`): NIFTY must commit and push alone first.
3. Illiquid chains (NIFTYFPI 0 of 120 traded on 14 Oct) trigger `CROSS_CHECK_ALERT` (`fno/quotes/cli.py:14-17`), which
   tells the reader to mark the day closed in the calendar: cross-check on NIFTY only.
4. No point-in-time universe: build it from the previous day's NSE file, store its SHA-256 (entrants, leavers,
   survivorship).
5. An attempt has no end time (`recorder.py:153` checks only before an attempt): rows after 15:30 must be invalid.
6. Expiry file re-parsed per call (0.81 s each, about 440 calls): parse once per day.
7. A16 and E3 share the Groww key at 15:00 and 15:15; the A4 provider has no pacer: one shared rate budget, NIFTY first
   (some evidence).
8. Scope: NIFTY weeklies, BSE SENSEX, futures per underlying and lot sizes are not recorded (owner's choice).
9. About 2.9 MB per attempt: never under `research/data/quotes/`; A4b (Drive only) first.

### Timing and fairness (strong unless marked)
10. Waiting past 15:00 adds nothing: the pack keeps only rows by 15:00:00 (`fno/forecast/live_pack.py:33`); 15 Oct's
    pack had `fields: []`. Release at the earlier of a pre-15:00 canonical or about 15:01.
11. Event release makes the Groww/NSE fallback depend on arrival order (`fno/forecast/capture.py:36,44-54`): choose
    the source by rule, NSE only after Groww's day is final.
12. The AI prompt runs `reveal` with a 600000 ms timeout (`agents/forecast/book3_ai_v1.md:67`); sealing at 15:02
    means a 13-minute wait, so the reveal may be killed and the day lost: new prompt version with E2 (some evidence).
13. The pack commit has no retry (`forecast-capture.yml:101-107`); a rejected push loses only the AI books' day.
14. The NSE job's push uses the Actions token and starts nothing: if the Groww routine fails, the release waits on
    cron. Let the NSE job dispatch the capture.
15. E3/E4 as written: desk deadline 15:12 vs forecast lock 15:15 on different clocks; the timetable refuses equal
    times (`fno/desk/timetable.py:40-41`); E8 now judges fills at T+60. Use GitHub push time as the one lock clock,
    lock before snapshot, E4 = the same E8 fill rule.
16. Two packs exist (forecast v2 pack and the desk's common pack): E1 must name which each record cites; rename the
    rules EQ1-EQ5 (story E2 already exists).
17. Special sessions that closed F&O at 12:30 (2 Mar and 18 May 2024 in the calendar) would record stale quotes as
    complete: add session close times to the calendar.
18. Health check: wrong day if cron is hours late, "none" canonicals look committed, 20 of 20 is not the normal
    count, push times must come from GitHub, nothing watches the watcher (some evidence).
19. A missed desk run is not "flat": exits run only inside it (`fno/desk/daily_run.py:59-63`).
20. More places hold times: `config.yaml` desk.timetable, `fno/composition.py:88`, `LATEST_START`,
    `quote-recorder-nse.yml`, `CARD_VALID_UNTIL`, the hashed prompts, S1 `timetable`.

### Scoring and statistics (strong unless marked)
21. "Missed decision = NO TRADE" contradicts S3 criterion 3 (`docs/stories/S-scoreboards.md:101-102`) and is not
    neutral on scoreboard A: use NO TRADE on scoreboard B only.
22. The headline is net per rupee-day of risk (`fno/scoreboard/series.py:31-32`): it penalises longer holds; label it
    and add net per rupee of entry max loss.
23. "X beats Y" on raw rupee differences is not risk-normalised (`research/evaluation/PROTOCOL.md:123-124`).
24. The do-nothing benchmark is a real-money gate (`docs/design_v2/08_budget_and_stop_rules.md:83`), a point
    comparison with no uncertainty; fix one tax treatment per instrument.
25. S1 says the book brake is Rs 30,000 (`PROTOCOL.md:191`); the books' config says Rs 1,20,000 (`config.yaml:57`).
26. The random strategy controls selection luck, not window luck; freeze its design; descriptive, not in Holm.
27. A zero-risk resample scores 0.0 (`fno/scoreboard/uncertainty.py:45`), biasing the bound toward 0.
28. Largest-loss share is unstable near zero gains: use largest loss over the entry max-loss cap.
