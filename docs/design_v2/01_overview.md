# 1. Overview and principles

## 1.1 The goal (owner, 14-15 Oct 2026, condensed)

A research tool, not a trading platform. More accurate and more honest than the broker's research, which "screwed me
multiple times". It forecasts F&O prices, says when to buy, when to sell and when **not** to trade, alerts fast on
danger, and learns from many paper trades. Speed is not the goal (no one beats high-frequency firms from a phone);
accuracy and evidence are. Every win and loss is backed by evidence: "no place for luck".

Design v2 turns that into one rule: **every output of the tool is a scored claim.** A forecast, a weather colour, a
trade card, a "no trade" and an alert each leave a permanent record that is later checked against what happened.

## 1.2 What the evidence says so far (read this before the layers)

| Test | What was tested | Result | Label |
|---|---|---|---|
| Experiment 1 (frozen, judge 56) | Monthly protected NIFTY premium (condor, iron flies), 2019-23 holdout | Nothing passed; condor gross +408 a trade vs about 814 costs | strong evidence |
| Response 92 (re-read of experiment 1 data) | Costs and proof horizon | Condor gross +978 (2024-26, seen) / +408 (2019-23) vs costs Rs 810-940 a four-leg trade | strong evidence (costs) |
| Response 94 (frozen weekly study) | 5 weekly defined-risk structures, about 390 trades each, and a RED weather filter | All negative after costs (mean -665 to -3); RED did not separate bad weeks; RED weeks were better for the condor and bull call spread | strong evidence for "no edge shown" |
| Response 92, statistician | Trades needed to prove a +153 edge at SD 2,700-3,400 | n = (2 x SD / mean)^2 = 1,200-2,000 trades, 100-165 years at 12 a year | strong evidence (arithmetic) |

Three plain conclusions:
1. **The variance premium exists gross, and costs eat it** at one lot with a Rs 10,000 cap (strong evidence).
2. **Retail-sized, defined-risk NIFTY option trades on daily-close information have shown no edge** in two independent
   tests (some evidence that none exists; strong evidence that none was shown).
3. **Trade P&L is a slow judge.** At 12 or even 50 trades a year a small edge cannot be told from luck in any useful
   time (strong evidence, arithmetic).

## 1.3 What design v2 does about it (the six consequences)

1. **Forecast first, trade second.** A forecast is scored every trading day; a trade settles once a month. Settling
   forecast skill is still slow, but much faster than trade P&L. With the registered tests (Holm across about 15
   comparisons, 80% power) a daily question needs about 316 outcomes if the noise-to-effect ratio r is 5 and 1,264 if
   it is 10: about 15 months or 5 years of daily scoring (section 5.5). A monthly trade rule needs over 100 years
   (response 92). No question is known to settle in months: that would need r of about 3 or less, which is measured
   after 60 outcomes, not assumed. So the tool's first product is scored forecasts, and a trade idea is only funded
   when it rests on a forecast that has already beaten its baseline (reasoning only for the ordering; strong evidence,
   arithmetic, for the sample sizes).
2. **Movement size before direction** (owner decision). Volatility clusters and is forecastable; daily direction is
   close to a coin toss (strong evidence: published studies and our own Q1 base rates). Direction is still forecast and
   scored, and nobody expects much from it.
3. **The cost wall is the first gate.** An idea whose plausible gross per trade is below twice its full round-trip cost
   (charges plus pads, C1) is not tested at all. Section 5.6 and `03_layers_factory_desk.md`.
4. **Independent events, not parallel copies.** Ten NIFTY strategies open in the same week are one bet on NIFTY's
   movement, not ten. Evidence grows with independent events: different weeks, and different underlyings such as stock
   options around company results (about 4 results a year for each of about 200 F&O stocks). Rs 20 lakh buys
   parallelism; only independence buys evidence (reasoning only; checked by the correlation buckets in section 6).
5. **"No trade" is the expected output for a long time.** Until something passes, the daily card says "no trade" with
   the reason. That is a result, not a failure.
6. **New information, not new filters on old prices.** The 2019-26 daily NIFTY option prices are spent (36+ trials,
   two frozen tests). New tests need new information: 15-minute intraday quotes, real bid/ask at 15:00 (from 13 Oct
   2026), global cues, participant positioning (A8), company results for stock options. Each is a new registered study.

## 1.4 Principles (binding; from DESK_DECISIONS 12-14 Oct)

- **Research and paper only.** The tool never places, modifies or cancels a real order. Groww is read-only data.
- **Worst loss fixed at entry.** Bought options, or spreads with bought protection; never unprotected selling; no
  reliance on stop-loss orders (gaps jump them). Rs 10,000 maximum loss per trade including charges.
- **Days or weeks, not minutes.** Prefer holds of days to weeks; no expiry-day or intraday scalping.
- **Rules locked before results.** Every idea, threshold and pass mark is written, hashed and registered in
  `research/ledger.csv` before its result is seen; a change is a new version, never a silent edit.
- **Win rate is not the target.** The measures are net profit per rupee risked after all costs and 31.2% tax, the worst
  loss, and evidence beyond luck (an interval that excludes zero).
- **Paper records when the owner would have acted**, not when the signal fired; the owner never overrides on paper.
- **The real-money pass mark is written before results and never lowered because time passed.** Real money starts at
  1 lot, after a written small real-money test. Groww API automation only later, by the owner's explicit decision
  after checking SEBI's retail algo rules.
- **Personal use only.** Sharing calls for money needs SEBI research-analyst registration.

## 1.5 The eight layers on one page

```
 (1) DATA ──► (2) FORECASTS ──► (3) WEATHER ─────────────┐
   NSE files,   every forecaster,   green/amber/red,      │
   15-min       probabilities,      a scored forecast     ▼
   quotes,      scored next day     of large moves   (4) STRATEGY FACTORY
   VIX, global        │                                ideas registered once,
   cues, OI,          │ house forecast                 cost wall, shadow test
   results            ▼                                    │ passed ideas
                (6) TRADE CARD ◄── devil's advocate ◄── (5) PAPER DESK
                 Slack to phone        attacks          fills at owner's time,
                 incl. "no trade"      every call       costs, tax, risk buckets
                      │                                    │ open trades
                      ▼                                    ▼
                (8) LEARNING LOOP ◄────────────────── (7) LIVE MONITOR
                 weekly post-mortem, why-wrong          15-min checks, exit plan,
                 reviews, drift, new versions           danger alerts
```

## 1.6 Where each owner requirement lives

| Differentiator or missing piece (owner, 14 Oct) | Layer and file |
|---|---|
| Permanent score for every call | 2, 3, 6: every forecast, colour and card is a record scored later (`02_`, `04_`) |
| Calibrated probabilities, not targets | 2: proper scores and calibration tables (`05_volatility_research.md`) |
| "No trade" as a first-class answer | 6: the daily card always exists; "no trade" has a reason code (`04_`) |
| Devil's advocate attacks every call | 6 and AI team (`07_ai_team.md`) |
| Rules locked before results, versioned | 4 and 8 (`03_`, `04_`); anti-overfitting rules (`05_` section 5.7) |
| Forecasters weighted by proven record | 2: the house forecast (`07_ai_team.md` section 7.4) |
| Worst case shown up front | 6: maximum loss in rupees and the crash replay on every card (`04_`, `06_`) |
| Profit after all costs and tax | 5: net of C1 charges, pads and 31.2% tax (`03_`) |
| Fitted to the owner | 5 and 6: capital, loss cap, reaction time, discipline record (`03_`, `06_`) |
| Why-it-was-wrong review of every loss | 8 (`04_`) |
| Volatility focus | 2 and 5 (`05_volatility_research.md`) |
| "Do nothing" benchmark (NIFTY index fund) | 5 and 8: on every scoreboard (`03_`, `08_`) |
| Drift detection | 8 (`04_`), rule in `05_` section 5.8 |
| Stock options around results | 1 and 4: feasibility study first (`REPLAN_new_stories.md`, R2) |
| Owner never overrides on paper | 5 (`03_`) |
| Small real-money test before scaling | `08_budget_and_stop_rules.md` |
| AI budget cap and whole-project stop rule | `08_budget_and_stop_rules.md` |
| Personal use only (SEBI) | `08_` and `09_limits.md` |

## 1.7 The evidence ladder (how an idea earns money on paper and then real money)

| Rung | What must be shown | Typical time |
|---|---|---|
| 0 Idea | Who pays and why; passes the cost wall; registered with its test before data is read | days |
| 1 Forecast skill | The forecast it rests on beats its baseline on the frozen test (section 5.5) | about 15 months to 5 years for a daily question; longer for 5- and 20-day questions |
| 2 Shadow | Recorded daily decisions at real 15:00 quotes, never in a book; no disaster | runs in parallel with rung 1 |
| 3 Paper | Owner approves; S1's uncertainty criterion on paper (lower bound above zero) | 6+ months, often years |
| 4 Real, 1 lot | The written real-money test (section 8.4) | 3-6 months |
| 5 Scale | Real results inside paper's interval; owner decides | owner |

An idea may skip rung 1 only if it needs no forecast (for example, a pure cost or structure effect), and then it needs
a pre-registered sample size from its expected edge and SD (section 5.5) before any claim.
