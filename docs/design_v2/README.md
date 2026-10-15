# Design v2: Omenix F&O as an honest research tool

**Status: PROPOSED (15 Oct 2026), for the judge and ChatGPT (owner: "judge plus ChatGPT").** Nothing here changes a
frozen protocol, a built story or an owner decision. Where design v2 needs a change to one of them, it says so and
the change goes through its own lane-1 story, freeze or owner decision. Written by the design-v2 session on branch
`story/x-design-v2`. The review request is `reviews/claude/response_95_design-v2.md`.

**Conditions before this design is binding:** ChatGPT's full review 95 raised four blocking contradictions (B1 timing of
the advocate and the card, B2 the stop rule with zero shadows, B3 the QLIKE zero case, B4 forward shadows before
forecast skill). Revision 3 resolves them (`reviews/claude/response_97_design-v2-full-review.md`); the design is binding
only after the judge checks that revision and the owner approves it.

The owner's decisions that bind this design are the 14 Oct 2026 rows of `docs/DESK_DECISIONS.md` (eight layers,
volatility focus, Rs 20 lakh paper account with a Rs 10,000 per-trade cap, the ten differentiators, the eight missing
pieces, the trading principles, "future slices follow design v2"). They are not reopened here.

## Files

| File | What it covers |
|---|---|
| [OWNER_SUMMARY.md](OWNER_SUMMARY.md) | One page for the owner: what we build, in what order, rough cost, what it can and cannot promise |
| [01_overview.md](01_overview.md) | Goal, what the evidence so far says, principles, the eight layers on one page, where each differentiator lives |
| [02_layers_data_forecast_weather.md](02_layers_data_forecast_weather.md) | Layers 1-3: data, daily probabilistic forecasts, market weather |
| [03_layers_factory_desk.md](03_layers_factory_desk.md) | Layers 4-5: strategy factory, paper desk |
| [04_layers_card_monitor_learning.md](04_layers_card_monitor_learning.md) | Layers 6-8: trade card and alerts, live monitor, learning loop |
| [05_volatility_research.md](05_volatility_research.md) | The forecasting and volatility research programme: targets, baselines, scores, what "beats baseline" means, anti-overfitting rules |
| [06_risk_and_alerts.md](06_risk_and_alerts.md) | Risk on a Rs 20 lakh account with many strategies, correlation buckets, alert classes |
| [07_ai_team.md](07_ai_team.md) | The AI team's roles, the devil's advocate, weighting forecasters by record |
| [08_budget_and_stop_rules.md](08_budget_and_stop_rules.md) | Monthly AI and data budget, the whole-project stop rule, the real-money gate, SEBI |
| [09_limits.md](09_limits.md) | What is honestly not achievable |
| [REPLAN.md](REPLAN.md) | Every planned-but-unbuilt story: keep, change, drop or new; new slice order; S1 items affected |
| [REPLAN_new_stories.md](REPLAN_new_stories.md) | The new stories design v2 adds, one paragraph each |

## How to read the evidence labels

Every claim carries one of the project's labels: **strong evidence** (our own data with a frozen test, or published
studies), **some evidence** (data, but thin, one-day or exposed), **reasoning only** (no data yet). A number without a
label is arithmetic on a cited number.

## What design v2 replaces and what it keeps

- **Keeps:** every built story, every frozen protocol (G1 v1-v3, experiment 1, the weekly-weather study), the S1
  decisions of 14 Oct, the three approaches (rules, hybrid, AI team: owner, 13 Oct), the judge lanes, the code rules.
- **Replaces:** the order of future work (`docs/BUILD_MAP.md` slices 3-5 and `docs/IMPLEMENTATION_PLAN.md` milestones
  M2-M7 for unbuilt stories). `docs/DESK_DESIGN.md` stays the record of the approved framework; where the two differ,
  design v2 governs future work once approved.
- **Does not decide:** any number marked "owner decides". Those are collected in `REPLAN.md`, section 5.
