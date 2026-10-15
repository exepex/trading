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
