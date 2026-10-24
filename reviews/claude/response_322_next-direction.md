# Response 322: what next after EDGE1, decision paper for ChatGPT review and the owner

Orchestrator, 22 Oct 2026. Asked by the owner after EDGE1 (research/edge1/RESULTS.md) found no rule-based edge. Review requested from ChatGPT (owner: "We will not proceed until we get a proper review from ChatGPT, and ChatGPT and you both agree"). Corrections made by the orchestrator after checking: NIFTY lot is 65 (config.yaml lot_sizes); the SEBI average-loss figure is from memory and unverified; most option premiums in the examples are Black-Scholes model prices (reasoning only).

# What next after EDGE1: options, evidence and a hybrid plan (decision paper, 22 Oct 2026)

Research and paper trading only. Nothing here places an order. Sources are repository files at `main` a18679c0.
Labels: **strong evidence**, **some evidence**, **reasoning only**. Rupees are for 1 lot.

**Facts used in the examples:** NIFTY closed at 22,811 and India VIX at 15.68 on 21 Oct 2026
(`research/data/nifty-panel/warmup_closes.csv`). **The NIFTY lot is 65, not 75** (75 until the Dec 2025 contracts,
65 from Jan 2026, NSE/FAOP/70616; `config.yaml`, `research/edge1/LOT_CHECK.md`); BANKNIFTY is 30. Premiums marked
"model" are Black-Scholes at VIX-like volatility (reasoning only); real quotes are named where we have them.

## 1. The short answer

- Nine rounds of testing (98 counted trials) found **no rule-based index option trade that beats costs inside the
  house cap**. The one passer reversed out of sample. [strong evidence for what was tested]
- **Why, in one line of arithmetic** (my calculation, reasoning only, on exposed data): options are on average priced
  a little above the move that follows (implied 30-day vol minus the next 20 days' realised: mean +1.3, median +2.1
  vol points, positive on 72% of 1,900 days 2019-2026, worst -67 in March 2020; `research/forecasts/golden_iv30_rv20.csv`).
  A straddle earns about Rs 3,400 a lot per vol point, so the premium is real (the naked sales averaged +Rs 1.4k to
  +4.7k a trade in EDGE1 run 2). A condor that fits the Rs 10,000 cap earns only about **Rs 480 a vol point**, so
  about **Rs 650 a month** at the average premium, against **Rs 810-940 of round-trip costs**
  (`reviews/claude/response_92_first-strategy-candidates.md`). The cap shrinks the trade below its fixed costs.
- So the money in short volatility sits in the tail the cap forbids. Any plan that "finds an edge" by loosening the
  cap is really a decision to carry crash risk; it must be made as that, by the owner, not discovered by a backtest.
- **My recommendation (some evidence):** a hybrid whose core is a *decision tool and journal* for the owner's own
  trades, with strict sizing rules, plus at most **one** new fresh-data research test and the already-registered B0
  measurement. No naked legs, no new edge hunts on spent data. Details in section 5.

## 2. What we have and what it already says

**Live today** (`docs/DESK_DECISIONS.md`, 21-22 Oct): the morning (08:50) and evening (20:05) forecast editions in
#fno-forecast with G13's price distribution and G13b's NIFTY/BANKNIFTY ranges (live from 22 Oct, first match 26 Oct);
the weather and the v4 rule forecasts (switched on 21 Oct; v4 is "an honest daily yardstick, not a path to proof": no
member provable in useful time, V6b 14-22 years); the 3 pm Groww and NSE chains (from 14 Oct), 15-minute marks,
pre-open capture; Books 1-3 paper desk (frozen once no position is open).

**Data** (`docs/DATA_USE_MAP.md`, `research/DATA_SPEND.md`). Spent or exposed: NIFTY monthly options 2019-2026,
NIFTY weekly options 2019-2026, BANKNIFTY monthly options, index and VIX closes, events, global cues, implied ranges.
**Still fresh (the only clean history left):** NIFTY monthly option and future 15-minute candles **2019-2023**;
participant-wise OI (FII/DII/pro/client) **2019-2026, 1,935 sessions**; stock event moves 2022-2026. Everything
recorded live (3 pm quotes, 15-minute quotes) is fresh day by day. Flows have only 6 sessions.

**What each study found** (`research/LEDGER.md`, folders under `research/`):

| Study | What was tested | Result |
|---|---|---|
| Desk 1 (trials 1-21) | trend, long/short straddle, condors, debit spreads, IV>RV filter | trend 50-52% (no edge); long straddle -Rs 3.25 lakh; condors positive only on discovery data |
| Experiment 1 (22-31) | 8 protected sell/buy policies 2019-23, F1 vol-premium, VIX and event filters | **all fail**; P1 condor -34,486 over 60 months; F1 and VIX filters did worse than their opposite |
| Trial 42 | put credit spread, model | -Rs 243 a trade |
| Weekly (43-52) | 5 weekly structures, RED-weather filter, 396 weeks | all negative or zero (W5 condor -224 a trade, max loss in 21% of weeks); filter did not help |
| R2 (53) | stock options around results | **cost wall**: needs a 49-101% edge on price |
| R1b re-screen | monthly condor through the cost wall | screened out on both periods (net on bound -454 / -991) |
| GR1 (56-70) | 11 ways to sharpen implied ranges (VIX, events, global cues, RV...) | none sharper out of sample; implied stays |
| EDGE1 (71-98) | 24 monthly SC2/SC3/SF variants x 4 exits | 23 fail run 1; BANKNIFTY SF TP50 -Rs 337 a trade in run 2 (p 0.91) |

**Direction:** the rule forecasts have **no directional skill**. "NIFTY up in 20 days": Brier 0.2449 vs 0.2455 for
the base rate (p 0.89) and 0.2479 for the market's own number (p 0.49), 674 days 2024-26
(`research/forecasts/scores/2026-10-22.json`; 0.25 is a coin flip). Only the volatility question q3 beat the base
rate (p 0.017, overlapping windows, so weaker than it looks).

**House rules** (`config.yaml`, `docs/stories/C-code-roles.md` C5, `research/FACTORY_RULES.md`): Rs 20 lakh paper
books; max loss Rs 10,000 a trade incl. costs; Rs 30,000 a risk bucket; Rs 1.5 lakh open risk; Rs 50,000 new risk a
day; Rs 1.2 lakh drawdown brake; no naked short leg; every idea is a counted trial; spent data can only be exploratory;
real money only through `research/evaluation/REAL_MONEY_GATE.md`.

**Outside facts** (some evidence: SEBI studies via press and broker summaries; the PDFs were not read, `docs/design_v2/09_limits.md`):
about 93% of individual F&O traders lost money FY22-24 (average loss about Rs 2 lakh each over the three years, costs
included), 87.7% in FY26; most retail are option buyers; 59% of index-option turnover is same-day expiry. The variance
risk premium (options priced above later realised moves) is documented in index options worldwide, India included
(strong evidence that it exists; it is small and pays mostly through crash risk).

## 3. Candidate directions (14)

Each: what it is, a rupee example, what our data says, data status, chance of a real edge, build cost
(builder + judge days, reasoning only), worst loss per lot vs the Rs 10k cap, evidence label.

**C1. Owner's decision journal scored against the forecast.** The owner writes each real or intended trade (why,
entry, exit, size). The tool scores it after costs against "no trade" and against the forecast range. *Example:* owner
buys a 22,800/23,000 call spread for 104 points = Rs 6,760 (model); the journal records the evening range said "most
likely 22,650-22,950"; at expiry it shows Rs -6,760 + costs, and that the trade bet against the tool's own range.
*Data:* nothing to test; every entry is fresh. *Edge chance:* it creates none, but it is the only way to learn whether
the *owner* has one. *Build:* 3-5 + 1-2 days (a Slack/CLI form, a CSV, a weekly score; MA1, the dashboard paper
account, is size L and "later"). *Risk:* whatever the owner trades; the journal enforces nothing. **Reasoning only.**

**C2. Paper-trade the owner's own ideas.** The owner proposes; the tool fills at the next valid 3 pm or 15-minute
quote, applies the caps and costs, and keeps a separate Manual account (Rs 5 lakh, 13 Oct limits). *Example:* owner
proposes a 23,300/23,500 call credit spread; tool fills at the bid/ask, books Rs 900 of costs, refuses it if the max
loss passes Rs 10k. *Data:* fresh, forward. *Edge chance:* unknown; honest paper record after 30-50 trades shows if it
is worth real money. *Build:* 4-7 + 2 days if done on the desk's existing fill code (lane 1: fills). *Risk:* paper
only; cap Rs 10k a trade. **Reasoning only.** Combine with C1: one log, two kinds of entry (real and paper).

**C3. Position-sizing rules for whatever the owner trades.** Kelly sizing (bet a fraction of capital set by the edge)
gives **zero** when the measured edge is zero, which is our state. So the rule is fixed-fractional: risk at most 0.5%
of capital a trade (Rs 10,000 on Rs 20 lakh), 1.5% per bucket, a monthly loss stop. *Example:* a Rs 6,400 max-loss
condor = 0.32% of Rs 20 lakh, allowed; a naked strangle with a Rs 50,332 measured worst loss = 2.5%, refused. *Build:*
1-2 days (the C2 caps already exist; a calculator in the journal). *Risk:* lowers it. **Strong evidence** for the maths
(Kelly with no edge is zero), reasoning only for the exact percentages.

**C4. Volatility-regime-filtered defined-risk sale** (sell only when implied is rich vs realised, or VIX high).
*Example:* B0's condor on 14 Oct quotes: credit Rs 1,809, structural max loss Rs 8,351, costs about Rs 850.
*Data says:* tested three times and failed: experiment 1 P4 (F1>0) -29,190 and P7 (VIX above median) -25,281, both
worse than their opposite; weekly RED filter did not help; GR1's VIX scaling did not sharpen ranges. Data **spent**:
forward-only. *Edge chance:* low (about 1 in 10, reasoning only), because of the vega-vs-cost arithmetic in section 1.
*Build:* a forward shadow 3-5 + 2 days; proof needs about 133 trades (EDGE1's sample plan: about 25 years monthly).
*Risk:* Rs 8-10k a lot. **Some evidence against.**

**C5. Tail-hedged short vol with a wider cap** (sell near strikes, buy wings 400-500 points out; max loss Rs 25-30k).
*Example (model):* sell 23,300 C / 22,300 P, buy 23,800 C / 21,800 P: credit about 230 points = Rs 15,000, max loss
(500 - 230) x 65 = Rs 17,500 plus costs. Its vega is about Rs 900 a vol point (model), about 1.9x the capped condor:
about Rs 1,200 a month at the average premium against about Rs 850 of costs. Thin, but not hopeless on paper. *Data:* not tested at this width (EDGE1 kept every structure under Rs 10k); all history spent, so a
historical run would be exploratory only. *Edge chance:* low to moderate (reasoning only). *Build:* 3-5 + 2 days
(forward shadow) after an owner rule change. *Risk:* **Rs 17-20k a lot, 2x the cap**; a March-2026-type month takes
most of it. **Reasoning only.** Needs an explicit owner decision to raise the per-trade cap for this one shadow.

**C6. Calendar and diagonal spreads** (sell the near month, buy the next; bets on the term structure).
*Example (model):* sell 30-day 23,300 C (244), buy 60-day 23,300 C (449): debit 205 points = Rs 13,300, above the cap;
an OTM version near Rs 6-8k fits. *Data:* never tested; response 92 rejected it for "no next-month quote history";
the bhavcopy has next-month closes, but far months are thinly traded (stale closes, EDGE1's impossible-price problem).
*Edge chance:* low; no stated source of edge. *Build:* 5-8 + 2 days. *Risk:* the debit, Rs 6-10k. **Reasoning only.**

**C7. Event volatility** (RBI, Budget, elections, results: sell rich pre-event premium or buy cheap).
*Example:* buy a 2-day ATM straddle before the Budget, about 212 points = Rs 13,800 (model), above the cap.
*Data:* R2 (stock results) hit the cost wall; experiment 1's event filter (P6) still lost -18,468; GR1's event scaling
did not sharpen ranges; only 61 index events since 2019 (about 8 a year), so any test is tiny. *Edge chance:* low.
*Build:* 4-6 + 2. *Risk:* up to the premium (buy) or unlimited (naked sell). **Some evidence against.**

**C8. Expiry-day (0-1 day) trading.** *Example:* sell a NIFTY straddle on expiry morning for about 110 points = Rs
7,150; a 1% move costs about Rs 7,600. *Data:* monthly option candles 2019-2023 are **fresh** (the only fresh option
price history); weekly closes spent. SEBI: this is where most retail turnover, and losses, sit. Needs reactions within
minutes; the owner decides once a day (E8 fills at R = 60 minutes). *Edge chance:* very low for this owner.
*Build:* 8-12 + 3. *Risk:* a 2-3% gap day wipes several weeks. **Some evidence against** (SEBI, our weekly results).

**C9. NIFTY vs BANKNIFTY relative value** (dispersion-like). *Example:* sell a BANKNIFTY condor, buy a NIFTY one when
BANKNIFTY implied is unusually high relative to NIFTY. *Data:* untested; BANKNIFTY 3 pm chains have 2 sessions;
BANKNIFTY monthly closes exposed. Doubles legs, so doubles the Rs 850 cost. *Edge chance:* very low. *Build:* 6-10 +
3. *Risk:* Rs 10-20k (two capped structures). **Reasoning only.**

**C10. Directional trades from our forecasts.** *Example:* buy a call spread when the forecast middle is above spot.
*Data:* q1 shows no directional skill (Brier 0.2449 vs 0.2455); trend 50-52%; weekly bull/bear spreads -3 and -321 a
trade; FL1's middle-vs-close score starts 26 Oct (fresh, forward). *Edge chance:* very low. *Build:* none (already
scored). *Risk:* the debit, Rs 5-7k. **Strong evidence against** for the rule forecasts tested.

**C11. Participant OI as a fresh signal** (FII/pro positioning predicting next month's move size or premium).
*Example:* when FII index-future net short is in its top 10%, does next month's realised beat implied? *Data:*
**fresh**, 8 years, read by nothing today (`docs/DATA_USE_MAP.md`). The only clean historical test left on index
behaviour. *Edge chance:* low (about 1 in 10, reasoning only); a positive result would still need forward proof, and
then a structure that beats costs. *Build:* 4-6 + 2 (registered study, one Holm family). *Risk:* none (study).
**Reasoning only.**

**C12. Hedging the owner's real stock portfolio with index puts** (insurance, not profit). *Example (model):* a
3-month 21,700 put about 240 points = Rs 15,800 a lot protects about Rs 14.8 lakh of NIFTY-like stock (22,800 x 65)
below -5%; about 1.1% a quarter, 4-5% a year. A put spread (buy 21,700, sell 20,500) costs about half and protects
only to -10%. *Data:* the premium we measured means insurance loses money on average (strong evidence globally); it
pays in crashes (March 2020, March 2026). Value depends on whether the owner holds stocks and how closely they track
NIFTY (beta). *Edge chance:* none by design; it trades return for smaller drawdowns. *Build:* 2-4 + 1 (a cost and
coverage calculator in the report). *Risk:* the premium paid. **Strong evidence** that it costs money on average;
reasoning only for whether it suits the owner.

**C13. Paper-test naked selling with strict limits** (option 3). *Example:* NIFTY strangle 23,800 C / 21,800 P, about
190 points = Rs 12,350 credit (model), margin about Rs 1-1.3 lakh. *Data:* EDGE1 measured it: mean +Rs 3,823 (NIFTY
NS, run 2, 43 trades, 74% wins) but **worst -Rs 50,332**; BANKNIFTY straddle worst -Rs 84,883. A stop-loss does not
help on gap days (both worst trades were March 2026). Data spent. *Edge chance:* the average is probably positive
(some evidence); the question is survival. *Build:* 3-5 + 2 (paper shadow). *Risk:* **2.6-8.5x the cap per lot**;
the risk manager's C2 refuses it today. **Some evidence** (positive mean, ruinous tail).

**C14. Stop building; keep the cheap live parts.** Keep the morning/evening report, captures and scores; freeze new
studies. *Cost:* near zero; saves the builder and judge days. *Risk:* none. **Reasoning only**, but it is the honest
default if the owner does not want to trade by hand.

**Also considered, dropped:** long volatility in "cheap" regimes (long straddle -3.25 lakh, P3 fly gains reversed);
re-testing old ideas on spent data (exploratory only by rule); AI books as an edge (no evidence yet, 0 counted days
for Books 2-3).

## 4. The desk roles

- **Mathematician:** the cap fixes the vega at about Rs 480 a vol point; fixed costs need about 1.8 points of premium
  just to break even. No filter can fix arithmetic. Kelly says size zero until an edge is measured.
- **Statistician:** monthly ideas cannot be proven: 133 trades = 25 years. Weekly gives about 50 a year but weekly data
  is spent and the results were negative. The owner's journal will also be slow: 50 trades is a first look, not proof.
  The only clean historical tests left are participant OI and the 2019-23 candles.
- **F&O trader (disagrees with the risk manager):** the premium is there; we keep refusing to be paid for the risk
  that pays. A wider-cap condor (C5) on paper is a fair, bounded test. I would run it forward.
- **Options strategist:** agrees with the maths: fewer legs and wider wings are the only levers, and doubling the
  wings only doubles the vega (C5: about Rs 900 a vol point), so even C5's margin over costs is thin. Calendars and
  dispersion add legs and costs with no stated edge; I would not spend days on them.
- **Risk manager (disagrees with the trader):** March 2026 lost Rs 50-85k a naked lot; a Rs 17-20k C5 loss is 2x the
  cap and could repeat 2-3 times in a bad quarter. Paper-only is acceptable; any real-money step stays behind the RM gate.
- **Portfolio manager:** if the owner holds stocks, hedging them is the one use of options here with a clear purpose.
  Otherwise the best "return" is not losing the Rs 2 lakh the average retail trader lost.
- **Analyst:** the tool's proven value today is measurement: honest ranges, honest costs, honest scores. Build the
  journal around that, and spend research only on fresh data.

## 5. Three hybrid packages

**Package A, "Decide better" (recommended).** *Runs:* the live forecast editions (no change); C1+C2 as one journal
and Manual paper ledger (real and paper entries, scored after costs vs "no trade" and vs the forecast range); C3
sizing calculator; B0's already-registered condor measurement continues (no new trial). *Cost:* about 6-9 builder
days + 2-3 judge days. *Success:* after 50 owner entries or 6 months, the paper record is positive after costs and
beats "no trade"; then, and only then, the RM gate applies. *Stop:* paper record negative after 30 entries, or a single
paper loss above Rs 10k (sizing failure). *Never:* naked legs, 0-1 day trading, new tests on spent data.

**Package B, "Decide better + one honest research shot".** Package A plus C11 (participant OI study on fresh 2019-26
history, one registered Holm family, about 4-6 + 2 days). *Success:* passes its registered mark; then it gets a
forward shadow (not a book). *Stop:* a fail is final (no re-tuning); no second fresh-data study until A has 6 months.

**Package C, "Insurance + decide better"** (only if the owner holds a stock portfolio). Package A plus C12: a weekly
line in the report with the cost of a 3-month 5% and 10% NIFTY put or put spread for the owner's portfolio size and
beta, and a journal entry type for hedges. *Cost:* about 2-4 + 1 extra days. *Success:* measured as drawdown reduced
per rupee of premium, not as profit. *Stop:* the owner's stock exposure falls below the cost of a lot.

**Not recommended now: a C5 wider-cap shadow** (trader's choice). If the owner wants it: paper only, one frozen
rule, Rs 25k cap for that shadow alone, stop after 2 losses above Rs 15k or 12 months, judged once. Expect "no
verdict" after a year (12 trades).

**My recommendation: Package A, or B if the owner wants research to continue. Some evidence:** the edge studies give
strong evidence that the tested rules fail and the vega-vs-cost arithmetic explains why; the journal's value is
reasoning only. **Main reason I might be wrong:** the premium is real and C5 might capture it within a tolerable
loss; by not testing it we may leave the only plausible systematic edge untested. A second reason: the owner may not
trade by hand at all, in which case A's journal is unused and C14 (stop) is the better answer.

## 6. Questions the owner must answer to choose

1. Do you intend to trade real money by hand in the next 6-12 months, or only learn on paper?
2. What is the most you accept losing on one real trade, and in one bad month, in rupees? (House cap is Rs 10k a trade.)
3. Would you raise the per-trade cap for one paper shadow (C5) to about Rs 25k, knowing a bad month can take Rs 17-20k a lot?
4. How many minutes a day can you give? The journal needs about 5 minutes a trade; intraday ideas need you at the screen.
5. Do you hold a stock portfolio (size and type: NIFTY-like large caps, or mid/small caps)? If yes, do you want it hedged?
6. Is paper-trading naked sales (C13) off the table for good, or only for real money?
7. Should research continue on the fresh data (participant OI, C11), or stop at the journal and live reports (C14)?
8. Which instruments would you actually trade: NIFTY monthly, NIFTY weekly, BANKNIFTY monthly, stock options?
9. How will you judge success in 6 months: paper profit, fewer mistakes, or a smaller worst month?
10. Is the dashboard Manual account (MA1, size L, "later") still wanted, or is a Slack/CLI journal enough?

*Method note:* the vol-premium and vega figures in section 1 are my descriptive calculations on exposed data
(`research/forecasts/golden_iv30_rv20.csv`, Black-Scholes at VIX 15.7, 30 days); they are not a trial, decide nothing
by themselves, and use realised volatility on a 20-session window against 30-day implied (a horizon mismatch).
