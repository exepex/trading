# Response 95: design v2 of the research tool and the re-plan, review request (ChatGPT and the judge)

Owner, 14-15 Oct 2026: review by "judge plus ChatGPT"; future slices follow design v2; no old-plan story starts until
it passes. Branch `story/x-design-v2` (lane 1: rule documents). Documents only, no code.

## What to read

`docs/design_v2/README.md` (index), then `01_overview.md`, `05_volatility_research.md` and `REPLAN.md` first; the
layer files (`02_`, `03_`, `04_`), `06_risk_and_alerts.md`, `07_ai_team.md`, `08_budget_and_stop_rules.md`,
`09_limits.md`, `REPLAN_new_stories.md` and `OWNER_SUMMARY.md` after. Binding inputs that are **not** under review: the
14 Oct rows of `docs/DESK_DECISIONS.md` (eight layers, volatility focus, Rs 20 lakh with Rs 10,000 per trade, the ten
differentiators, the eight missing pieces, the trading principles).

## The design in eight lines

1. Every output is a scored claim: forecasts, weather colours, daily cards (including "no trade") and alerts.
2. Forecast first, trade second: forecasts are scored daily and settle skill faster than trades, though not fast.
   With Holm across about 15 comparisons and 80% power, a daily question needs (3.55 x r)^2 outcomes: 316 at r = 5
   (about 15 months), 1,264 at r = 10 (about 5 years). A monthly trade rule needs over 100 years (n = (2 x SD /
   mean)^2 gave 1,200-2,000 trades for the condor's +153, response 92). No question is known to settle in months.
3. A new forecast protocol v4 for movement size (V1-V7), with QLIKE for variance forecasts, the implied-volatility
   baseline as the primary bar, Holm, registered minimum effects and a power check after 60 outcomes.
4. The weather becomes a scored forecaster of large moves (v0 checklist as its baseline); RED still blocks new trades
   (owner) and its "price of calm" is reported.
5. A strategy factory with gates: idea card, cost wall (expected gross at least 2x full cost), data-spend register,
   sample plan, registration, one test.
6. A paper desk on Rs 20 lakh with correlation buckets, owner-timing fills, after-tax results and an index-fund
   benchmark.
7. A daily phone card with a devil's advocate (code checks can block; AI objections cannot, and are scored).
8. A stop-rule review about 6 months after v4's freeze, judged only on questions with enough independent outcomes,
   with three results (yes, no, undecided); underpowered never counts as "no", and the owner pre-chooses what
   "undecided" leads to.

## Questions where I most want to be challenged

1. **Statistics of "beats baseline" (05, 5.5).** Is a moving-block bootstrap of Diebold-Mariano loss differences, block
   at least the horizon and never under 5, with Holm across the family, the right test for V1-V7? Would a HAC t-test
   (Newey-West) be more honest for 6-12 month samples? Are the minimum effects (3% QLIKE, Brier skill 0.02) sensible?
2. **Primary baseline choice (05, 5.3).** I make the implied-volatility baseline the bar for V2, V3 and V5, not HAR.
   Too harsh, or exactly right because only beating the market's own number can pay?
3. **V5 (straddle-implied move) and V4 (weekly VRP).** Are these the right money-linked targets, or is there a cleaner
   one (for example, the delta-hedged straddle return)? We cannot delta-hedge in practice within the Rs 10,000 cap.
4. **The cost wall's 2x (03, 3.1).** Too strict, too loose, or wrong in kind (should it be in volatility points per
   vega, as 5.6 suggests)?
5. **Effective sample (01, 1.3 point 4; 06, 6.2).** I claim parallel NIFTY strategies add little evidence and stock
   options around results are the main source of independent events. Do you agree, and is R2's feasibility question
   the right first step?
6. **Weather (02, 2.3).** Is redefining it as P(|move| >= 2%) next session and over 5 sessions sound, and are thresholds
   at 2.5x and 1.5x the base rate reasonable?
7. **Devil's advocate (07, 7.3).** Is "objections never veto, but are scored" the right design, or does it waste the
   advocate?
8. **House forecast (07, 7.4).** Baseline until a forecaster passes, then the passing one or an equal-weight average,
   changed only quarterly. Is this too slow?
9. **Stop rule (08, 8.2).** Is the two-test rule (forecast skill; shadow money) exact enough to be applied without
   argument on the day?
10. **Re-plan (REPLAN.md).** Any built or planned story missed or misclassified; any slice order that breaks a
   dependency. In particular: S3 and F9 code built early so S1 v1 can freeze (owner's option A), and AI books trading
   only once something is worth trading.
11. **What is missing or over-built** for an owner who wants accuracy and evidence, not speed.

## Known weak points (my own red team)

- The ordering "forecast skill first" is reasoning, not evidence: a forecast can beat its baseline and still not pay.
- If Groww offers no 15-minute history, V1 and intraday HAR start late (09, item 10), and the stop rule leans on V6 and
  V2 on close proxies.
- Every threshold proposed (buckets, weather, effects, CUSUM) is reasoning only; none is fitted to data on purpose.
- The hosting choice for the 15-minute jobs places a broker key somewhere; the safest option is also the least
  reliable.
- The design does not promise an edge. The most likely result is "no edge found", well measured.

Please write the review to `reviews/chatgpt/review_<n>_design-v2.md`. Each point I accept or reject will get its
reason and evidence in the next response.

## Revision 1 (judge 96, 15 Oct 2026): what changed

Judge 96 failed d48bdfc on three must-fixes; the orchestrator and I checked and accepted all three, and the should-fixes:
1. **Power arithmetic.** My 155-620 outcomes used an unadjusted one-sided 5% test, but the test is Holm across about
   15 comparisons, whose first step is 0.05 / 15. Recomputed: n = (3.55 x r)^2, 316 at r = 5 and 1,264 at r = 10 (114
   at r = 3). "Skill in months" is dropped everywhere; section 5.5 has a table by horizon (`01` 1.3 and 1.7, `05` 5.5,
   `OWNER_SUMMARY.md`, this file).
2. **Stop rule.** Tests A and B now have three results; underpowered is "undecided", never "no"; the owner's options
   on "undecided" and my recommendation are in `08` 8.2.
3. **frozen_files.** REPLAN no longer adds G8 or E8 to S1's decided list: G8 is frozen by v4's own freeze, and E8's
   inclusion is owner decision 12 with its reason and costs.
Should-fixes: REPLAN section 1 statuses read from `reviews/judge/README.md`; decisions cited by date and title; slice A
dates marked as targets; SEBI loss figures cited by study and year (secondary summaries named as such); the straddle
arithmetic and the card example use NIFTY's real 14 Oct level (about 22,620 at 15:00) instead of 25,000.
