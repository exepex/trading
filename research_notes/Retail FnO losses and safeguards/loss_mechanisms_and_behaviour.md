# How retail option buyers in Indian F&O lose money: mechanisms, behaviour and detectable signals

Scope: NSE/BSE index and stock options, retail option buying, intraday to 2-day holds. Research date: 12 Oct 2026.
Convention: "Cited Findings" come from the linked source. Worked examples I computed myself (mostly a Black-Scholes approximation, ATM premium ≈ 0.4 × S × σ × √T) are labelled as inferences and are not sourced figures.

## 0. Baseline: how big the problem is (SEBI studies)

### Takeaway
SEBI's studies show that about 9 in 10 individual F&O traders lose money in every year it has measured. About 92% of individual losses come from options, and about 97% of individuals mainly buy options. Transaction costs alone account for roughly a quarter of the net loss.

### Cited Findings
- FY22–FY24 (study published Sept 2024): about 93% of over 1 crore individual F&O traders lost money, averaging about ₹2 lakh per trader including costs. Aggregate losses were above ₹1.8 lakh crore. Only 1% made more than ₹1 lakh profit after costs. — [Outlook Money](https://www.outlookmoney.com/invest/93-of-individual-traders-suffered-losses-in-fo-in-last-3-years-sebi-study)
- Same study: over 75% of loss-making traders kept trading despite repeated losses. Traders under 30 rose from 31% (FY23) to 43% (FY24) of participants, and 93% of them lost money in FY24, against 79% of traders over 60. — [Outlook Money](https://www.outlookmoney.com/amp/story/invest/93-of-individual-traders-suffered-losses-in-fo-in-last-3-years-sebi-study)
- FY22–FY24 transaction costs for individuals were about ₹50,000 crore: 51% brokerage, 20% exchange fees. The FY24 average was about ₹26,000 per person. The top 3.5% of loss-makers (about 4 lakh traders) lost an average of ₹28 lakh each. — [Moneylife](https://www.moneylife.in/article/93-percentage-of-individual-traders-lost-rs18-lakh-crore-in-equity-fo-in-past-3-years-sebi/75210.html)
- FY25 (study published 7 Jul 2025): about 91% of individuals lost money. Net losses rose 41% to ₹1,05,603 crore, from ₹74,812 crore in FY24. — [Business Standard](https://www.business-standard.com/amp/markets/news/net-losses-of-traders-in-fo-widens-in-fy25-sebi-study-125070701221_1.html). Later revised to about ₹1.12 lakh crore. — [Moneylife, Aug 2026](https://www.moneylife.in/article/92-percentage-of-aggregate-losses-incurred-by-individuals-are-from-options-trading-sebi-study/81429.html)
- FY26 (SEBI DEPA studies, Aug 2026) — all from [Moneylife](https://www.moneylife.in/article/92-percentage-of-aggregate-losses-incurred-by-individuals-are-from-options-trading-sebi-study/81429.html):
  - 87.7% of individuals lost money. Net loss was about ₹91,685 crore, and the average loss about ₹1.17 lakh.
  - About 92% of individual losses came from options.
  - About 97% of individuals mainly bought options; about 2% mainly sold them.
  - Gross trading loss before costs was about ₹72,000 crore, and transaction costs were about ₹25,000 crore (₹24,859 crore per [Outlook Money](https://www.outlookmoney.com/invest/sebi-futures-options-study-transaction-costs-traders-losses-fy26)).
  - About 79% of traders with both winning and losing quarters had average gains smaller than their average losses.
  - About 90% of traders who lost in two consecutive years kept trading and lost again.
  - Of those who stopped trading after a quarter, 86–89% had lost money in the prior quarter.
  - Traders with no equity holdings lost 93% of the time, against 58% for portfolios above ₹10 crore.
  - Proprietary traders made about ₹44,000 crore gross and FPIs about ₹14,000 crore; 99% of those profits went to algo entities.
- SEBI intraday cash-equity study (FY23): 71% of individual intraday traders lost money, rising to 80% among those making more than 500 trades a year. — [Moneylife](https://moneylife.in/article/7-out-of-10-individual-intraday-traders-in-equity-cash-segment-make-losses-sebi-study/74733.html)

### Inferences
- Costs of about ₹25k crore against a net loss of about ₹92k crore means costs are roughly 27% of the net loss. Even a trader who broke even before costs would lose money after them.
- The counterparty to retail option buying is mostly algorithmic proprietary traders and FPIs. The prior that a retail buyer has an edge should be very low.
- Two signals point to a payoff-asymmetry problem a tool could target: winners are smaller than losers (79%), and frequent trading goes with more losses. The disposition effect and "cut winners early" are the likely causes.

### Gaps
- I could not access the SEBI study PDFs directly. The figures come from press coverage, and different outlets give slightly different FY25 totals.

## 1. Time decay (theta)

### Takeaway
An at-the-money (ATM) option's time value falls roughly with the square root of time left. So decay speeds up sharply in the last 1–3 days, and a weekly ATM option loses most of its value in its final two sessions if spot does not move.

### Cited Findings
- Zerodha Varsity's worked example shows the curve:
  - At 120 days to expiry the premium is 350; at 100 days, 300; at 20 days, about 150. Below that it accelerates to under 50 near expiry.
  - Time value with 1 day left is about 30 paise, against ₹5–8 with 20 or more days left.
  - Decay acceleration is stronger for ATM and OTM options than for ITM options. This last point comes from the author's reply to a reader comment.
  - Source: [Zerodha Varsity – Theta](https://zerodha.com/varsity/chapter/theta/)
- In SEBI's FY26 data, 59% of index-option turnover was in same-day (0DTE) contracts, 75% within one day of expiry, and 97% within one week. — [Moneylife](https://www.moneylife.in/article/92-percentage-of-aggregate-losses-incurred-by-individuals-are-from-options-trading-sebi-study/81429.html)
- NSE working-paper evidence: on average, 87% of a contract's lifetime volume trades in its last five days. — [Agarwal & Ghosh, CFR working paper](https://www.cfr-cologne.de/download/workingpaper/cfr-25-09.pdf)
- Current expiry calendar: since 1 Sep 2025, the Nifty 50 weekly expires on Tuesday and the BSE Sensex weekly on Thursday. Bank Nifty, FinNifty and Midcap Nifty are monthly only, following SEBI's one-weekly-index-per-exchange rule (effective 20 Nov 2024). Monthly Nifty expires on the last Tuesday. — [Share.Market](https://www.share.market/buzz/insights/weekly-expiry-days-in-indian-fo-markets/); [Bajaj Finserv](https://www.bajajfinserv.in/nse-revises-nifty-expiry-day)

### Inferences
- Worked example (my calculation; Nifty 25,000, IV 12%, spot unchanged, calendar days):

  | Days to expiry | ATM premium |
  |---|---|
  | 30 | ≈ ₹344 |
  | 7 | ≈ ₹166 |
  | 2 | ≈ ₹89 |
  | 1 | ≈ ₹63 |

  - Half of the 7-day premium is gone by about 1.75 days left.
  - At 1 DTE, theta is about ₹31 per day, roughly half the remaining premium.
  - A buyer holding 1 DTE → expiry loses about 50% overnight unless Nifty moves more than about 0.25%.
- Weekend effect: a position opened on Friday with weekly expiry on Tuesday carries 3 calendar days of decay over a weekend with no trading. How much of that is already in Friday's price depends on how market makers model weekends. I have not verified this, so it is a gap.
- Detectable signals:
  - Days/hours to expiry.
  - Theta as % of premium per day: |θ|/premium.
  - Breakeven move: the premium paid divided by spot, compared with the expected move over the holding period (σ√t).
- Rules a system could use:
  - Minimum 3–5 trading days to expiry for directional buys; never open new long options on expiry day.
  - Block the trade if θ/premium exceeds about 10–15% per day.
  - Require the target move to be at least 1.5× the breakeven move.
  - Prefer the next-week or monthly contract.

### Gaps
- I found no published NSE statistic on the "typical decay profile" by moneyness for Nifty weeklies. It can be computed from NSE bhavcopy data.

## 2. Implied volatility crush (results, RBI, Budget, elections)

### Takeaway
Implied volatility (IV) rises before scheduled events and collapses after them. Index-level drops of 12–34% in India VIX in a single day are documented. A buyer can get the direction right and still lose money.

### Cited Findings
- 2014 and 2019 general elections: India VIX fell about 34% and 30% on results day. — [Business Standard](https://www.business-standard.com/amp/markets/news/india-vix-index-sharply-slumps-20-the-biggest-drop-in-five-years-124042301001_1.html)
- 2024 election, a counter-example where the surprise produced an IV spike rather than a crush — [Business Today](https://www.businesstoday.in/amp/markets/market-commentary/story/exit-polls-2024-market-volatility-fizzles-out-as-india-vix-plunges-431900-2024-06-03); [Business Standard](https://www.business-standard.com/amp/markets/capital-market-news/nifty-above-21-950-mark-fmcg-shares-advance-vix-slumps-25-32-124060500281_1.html):
  - After the exit polls (3 Jun), VIX fell about 22% to 19.11, from about 24.
  - On results day (4 Jun), it spiked; reported figures range from +24% to +42%, reaching 26.7–29.8.
  - On 5 Jun, it fell 25.32% to 19.97.
- Budget, 1 Feb 2025: India VIX was down 12.2% at midday (14.26) and down about 17% later (14.38). — [Business Standard](https://www.business-standard.com/amp/markets/capital-market-news/indices-trade-with-tiny-losses-vix-drops-over-12-125020100994_1.html); [Outlook Money](https://www.outlookmoney.com/amp/story/invest/union-budget-2025-budget-fails-to-cheer-markets-sensex-and-nifty-trade-in-red-post-budget-session)
- Budget, 1 Feb 2026: VIX rose about 11% to 15.09, because the Budget itself raised F&O STT, a negative surprise. — [HSBC MF market flash](https://www.assetmanagement.hsbc.co.in/assets/documents/mutual-funds/en/0b268914-8e60-438e-810f-5764bf6bb00e/monday-market-flash-february-02-2026.pdf)
- Single stocks: Infosys Q4 FY24 results (18 Apr 2024) are an illustration of an IV-inflated ATM call ahead of results. Real before/after IV figures were not given. — [OneTradeJournal](https://onetradejournal.com/strategies/earnings-trading-strategy). The same pre-event IV rise is described for RBI policy and the Budget. — [Upstox community](https://community.upstox.com/t/what-happens-when-iv-crashes-after-earnings-or-major-events-and-how-to-trade-it/12047)

### Inferences
- Vega arithmetic (my calculation): a 7-DTE ATM Nifty option at IV 16% ≈ ₹222. If IV falls 25% to 12% while spot is unchanged, it is worth ≈ ₹166, a 25% loss from IV alone.
  - ATM premium is roughly linear in IV, so the % drop in IV ≈ the % drop in premium.
  - Nifty would need to move about 0.25% in the buyer's favour just to offset it.
- Signals:
  - A known event inside the holding window: results date, RBI MPC date, Budget, election results, US FOMC/CPI.
  - IV percentile/rank vs the past 1 year.
  - Option IV vs realised volatility (IV/RV ratio).
  - Spread between front-week IV and next-week IV, which shows event pricing in the term structure.
- Rules:
  - No long options held through scheduled events unless deliberately trading the event with a sized "IV crush" haircut.
  - IV percentile cap (e.g. no buying above the 70th–80th percentile).
  - IV/RV cap (e.g. 1.3).
  - Block stock-option buys within N days before results.

### Gaps
- I found no sourced before/after IV figures for single-stock results or RBI policy days. NSE option-chain history would be needed.
- The 2024 election-day VIX figures differ between reports.

## 3. Expiry-day gamma and 0DTE trading

### Takeaway
0DTE options are cheap and have very high gamma, so small spot moves produce large % swings. This draws retail traders in, but theta is also at its maximum and most contracts expire worthless. SEBI's data show turnover and losses concentrated there despite the 2024 reforms.

### Cited Findings
- 59% of index-option turnover in FY26 was in 0DTE contracts. — [Moneylife](https://www.moneylife.in/article/92-percentage-of-aggregate-losses-incurred-by-individuals-are-from-options-trading-sebi-study/81429.html)
- SEBI's Oct 2024 package targeted expiry-day speculation — [Zerodha Z-Connect](https://zerodha.com/z-connect/business-updates/sebis-new-rules-for-index-derivatives-heres-whats-changing); [Business Standard](https://www.business-standard.com/amp/markets/news/sebi-announces-six-key-changes-to-curb-speculation-in-derivatives-trading-124100101316_1.html):
  - One weekly index per exchange.
  - Contract size raised to ₹15–20 lakh from ₹5–10 lakh (from 20 Nov 2024).
  - Extra 2% ELM on short options on expiry day.
  - No calendar-spread margin benefit on expiry day.
  - Upfront collection of option premium (1 Feb 2025).
  - Intraday monitoring of position limits (1 Apr 2025).
- The Nifty expiry moved to Tuesday partly because of SEBI's aim to reduce retail participation in short-dated index derivatives. — [Business Standard](https://www.business-standard.com/amp/markets/news/nse-bids-adieu-to-thursday-expiry-as-dates-swap-come-into-effect-explained-125082800635_1.html)
- Why short-dated options attract retail: low nominal prices, quick resolution and lottery-like skewness. — [Agarwal & Ghosh](https://www.cfr-cologne.de/download/workingpaper/cfr-25-09.pdf)

### Inferences
- Worked example (my calculation): on expiry morning with about 6 trading hours left (≈ 0.25 day), Nifty 25,000, IV 12%, the ATM premium ≈ ₹31.
  - A 100-point move in favour takes it to roughly ₹100+, about 3×.
  - Flat spot takes it to about 0 by 15:30.
  - The payoff is close to binary, so expected value is negative after spread, costs and the IV premium.
- Signals: DTE = 0; time of day; gamma/premium ratio; whether a position is opened after 13:00 on expiry day.
- Rules:
  - Block new long positions with DTE = 0 (or less than 1).
  - If allowed at all, cap expiry-day risk at a small fixed % of capital and one trade.
  - Force exit (paper) by a set time rather than holding to settlement.

### Gaps
- SEBI does not publish (in the coverage I found) loss rates split by 0DTE versus other trades. The concentration of losses on expiry is inferred from turnover shares.

## 4. Deep OTM "lottery" options

### Takeaway
Retail traders show a documented preference for cheap OTM options, and that preference shifted toward riskier OTM strikes when lot sizes were raised. Deep OTM short-dated options almost always expire worthless.

### Cited Findings
- On NSE, when lot sizes and margins were raised to curb speculation, trading moved to smaller-ticket, riskier, more affordable OTM options. This is consistent with financial constraints and lottery preferences. — [Agarwal & Ghosh, CFR WP 25-09](https://www.cfr-cologne.de/download/workingpaper/cfr-25-09.pdf); [AEA 2026 abstract](https://www.aeaweb.org/conference/2026/program/paper/StD8aadb)
- In Indian stock options, OTM call volume and the skewness of the risk-neutral density change as a stock nears its 52-week high or low (anchoring). — [Saurav, Agarwalla & Varma, J. Futures Markets 2023](https://ideas.repec.org/a/wly/jfutmk/v43y2023i11p1531-1558.html)
- US evidence: OTM options are the main lottery-like security, and the demand for them is driven by retail. — referenced in the same search, Filippou et al. (not India) via [BU](https://open.bu.edu/items/7a8eab09-3abe-4aab-adb6-4364f999cefb)
- Indian *stock* investors were not found to overpay for lottery-like stocks. This is a contrary data point for equities, not options. — [Sharma & Chakraborty 2019](https://ideas.repec.org/a/eme/sefpps/sef-04-2018-0099.html)

### Inferences
- Probability of expiring in the money ≈ N(d2), my calculation:
  - Nifty 25,000, IV 12%, 1 day left: the 1-σ move is about 157 points.
    - A strike 300 points OTM has about a 3% chance.
    - A strike 500 points OTM has well under 0.1%.
  - With 7 days left (σ ≈ 415 points), a strike 500 points OTM has about 11%.
- Implied volatility skew (higher IV on far OTM puts) and the minimum ₹0.05 tick add a relative cost. A ₹2 option with a ₹0.10 spread costs 5% just to cross.
- Signals: |delta| below about 0.15–0.20; premium below a set rupee amount; distance from spot in σ units; probability of ITM.
- Rules:
  - Minimum |delta| of about 0.25–0.30 (or a maximum distance in σ, e.g. ≤ 1σ).
  - Minimum premium (e.g. ≥ ₹20–30 for Nifty, so costs and tick are under about 2% of it).
  - Disallow strikes with probability of ITM below about 15%.

### Gaps
- I found no SEBI figure for the share of retail option volume in deep OTM strikes or their realised loss rate. The NSE papers are working papers.

## 5. Bid-ask spreads, slippage and illiquid strikes or stock options

### Takeaway
What matters is the spread relative to the premium. It is small for ATM Nifty weeklies but can be 5–20% of premium on far strikes and illiquid stock options, so slippage can exceed every statutory cost.

### Cited Findings
- NSE treats impact cost as the realistic cost of execution: the bid-ask spread captures the cost of a small trade, and impact cost rises with order size. — [NSE](https://www.nseindia.com/static/products-services/indices-impact-cost); [Nifty Indices](https://niftyindices.com/resources/index-concepts/impact-cost)
- The relative spread is what matters: a ₹2 spread is 1% of a ₹200 premium but 10% of a ₹20 premium. — [AlgoTest](https://algotest.in/blog/what-is-liquidity-in-trading/)
- NSE reduced the tick to ₹0.01 for stock options priced below ₹250. In the ONGC example given, the spread could narrow from ₹0.05 to ₹0.01 per unit; this is a broker illustration. — [Upstox community](https://community.upstox.com/t/tighter-spreads-lower-impact-costs-how-the-new-1-paisa-tick-size-for-stock-options-saves-you-money/12625)

### Inferences
- Round-trip spread cost ≈ the full spread (half on entry, half on exit) plus market-order slippage.
- Example: a stock option quoted 9.50/10.50 costs about 10% of premium per round trip before fees.
- Signals: (ask − bid)/mid; open interest and volume at the strike; depth at the best bid and offer; number of strikes away from ATM.
- Rules:
  - Maximum spread of about 1–2% of mid for index options and about 3% for stock options.
  - Minimum OI and volume thresholds.
  - Limit orders only.
  - Restrict trading to index options or the most liquid F&O stocks.

### Gaps
- I found no sourced statistic on typical NSE option spreads by moneyness or stock. It must be measured from live option-chain data.

## 6. Transaction costs, overtrading and STT on exercise

### Takeaway
Since the 1 Apr 2026 STT hike, statutory and broker costs on a round trip are under 1% of premium for normal-priced index options. They are much higher for cheap options because brokerage is fixed per order, and frequent trading compounds this into a large drag (about 27% of net retail losses in FY26). STT on exercised ITM options is now charged on intrinsic value, so the old "STT trap" is small.

### Cited Findings
- Budget 2026-27 STT rates, effective 1 Apr 2026 — [5paisa](https://www.5paisa.com/news/stt-hike-on-fo-to-take-effect-from-april-1-amid-rising-options-activity); [Outlook Money](https://www.outlookmoney.com/invest/stt-hike-from-april-1-2026-budget-what-it-means-for-futures-and-options-traders):
  - Options sold: 0.10% → 0.15% of premium.
  - Options exercised: 0.125% → 0.15% of intrinsic value.
  - Futures: 0.02% → 0.05%.
- Earlier, from 1 Oct 2024: the option-sale STT rose from 0.0625% to 0.1%. — [Business Standard](https://www.business-standard.com/amp/budget/news/budget-2024-steep-stt-increase-to-tame-retail-frenzy-in-derivatives-market-124072301145_1.html)
- STT on exercise applies to intrinsic value × quantity, not contract value. — [Zerodha support](https://support.zerodha.com/category/trading-and-markets/trading-faqs/articles/options-on-expiry-day). Older Motilal Oswal and Angel One pages describe it as notional value; that is outdated (pre-2017 regime). — [Motilal Oswal](https://www.motilaloswal.com/blog-details/effect-of-stt-on-option-exercise/1335)
- Individuals paid about ₹25k crore in transaction costs in FY26, about ₹1 lakh crore cumulatively over FY22–FY26, and the average was about ₹26k per trader in FY24. — [Moneylife](https://www.moneylife.in/article/92-percentage-of-aggregate-losses-incurred-by-individuals-are-from-options-trading-sebi-study/81429.html); [Moneylife 2024](https://www.moneylife.in/article/93-percentage-of-individual-traders-lost-rs18-lakh-crore-in-equity-fo-in-past-3-years-sebi/75210.html)
- Loss-maker share rises with trade frequency: 80% at more than 500 trades a year in intraday cash. — [Moneylife](https://moneylife.in/article/7-out-of-10-individual-intraday-traders-in-equity-cash-segment-make-losses-sebi-study/74733.html)

### Inferences
- Worked round trip (my calculation): lot of 75, buy and sell at ₹100. Fee rates other than STT are from my memory of standard schedules and are **not verified here**: ₹20 per order brokerage (Groww's F&O flat fee), NSE transaction charge ≈ 0.035% of premium, stamp 0.003% on buy, GST 18%.
  - Costs: brokerage ₹40, exchange ≈ ₹5.3, STT 0.15% × ₹7,500 = ₹11.3, stamp ≈ ₹0.2, GST ≈ ₹8.2. Total ≈ ₹65, or ₹0.87 per unit (0.9% of premium).
  - At a ₹10 premium the total is ≈ ₹49, or ₹0.65 per unit (**6.5% of premium**), because brokerage is fixed per order.
  - Add a 1-tick or larger spread and a ₹10 option needs a 7–10% favourable move just to break even.
- Overtrading: a strategy with +0.5% gross edge per trade becomes negative after about 1% in costs and spread. At 5 trades a day for 250 days, about 1% per round trip on the capital deployed is a very large annual drag.
- STT on exercise example: Nifty call ITM by ₹2 at expiry, 75 quantity → STT = 0.15% × 2 × 75 ≈ ₹0.23. That is negligible, but the buyer still loses the bid-ask and gets only intrinsic value. Physical settlement of ITM *stock* options means delivery obligations and margins; this is a separate risk, so close before expiry.
- Signals: count of trades per day and per week; cost as % of premium for each order; ratio of cumulative costs to gross P&L.
- Rules:
  - Minimum premium so total costs are ≤ 1–2% of premium.
  - Expected move must be at least 3× the round-trip cost.
  - Maximum 2–3 trades per day.
  - Close stock options before expiry.

### Gaps
- Exchange transaction-charge and stamp-duty rates were not verified in this session. Check Groww's and NSE's current charge pages.
- Current Nifty lot size (75 vs 65 after periodic revision) is not verified.

## 7. Leverage, position sizing and risk of ruin

### Takeaway
A long option can go to zero, so sizing by "number of lots I can afford" rather than "% of capital at risk" leads to ruin. Larger contract sizes since Nov 2024 (₹15–20 lakh notional) push small accounts toward cheap OTM strikes, which makes this worse.

### Cited Findings
- Contract size was raised to ₹15–20 lakh. — [Zerodha Z-Connect](https://zerodha.com/z-connect/business-updates/sebis-new-rules-for-index-derivatives-heres-whats-changing)
- About 78% of traders had equity portfolios below ₹1 lakh, and they bore about 70% of aggregate losses on about half of turnover. — [Moneylife](https://www.moneylife.in/article/92-percentage-of-aggregate-losses-incurred-by-individuals-are-from-options-trading-sebi-study/81429.html)
- Constraints push traders to more affordable OTM options. — [Agarwal & Ghosh](https://www.cfr-cologne.de/download/workingpaper/cfr-25-09.pdf)

### Inferences
- Risk of ruin (my arithmetic):
  - At a 40% win rate, the probability of 5 straight losses is 0.6⁵ ≈ 7.8%, and of 10 straight losses ≈ 0.6%.
  - Risking 20% of capital per trade, 5 straight losses leave 33% of capital.
  - Risking 2%, the same 5 losses leave 90%.
  - Recovering from a 67% drawdown requires +200%.
- Signals: premium at risk as % of account; total open premium; consecutive-loss counter; drawdown from equity peak.
- Rules:
  - Maximum premium at risk per trade of about 1–2% of capital.
  - Maximum total open premium of about 5%.
  - Daily loss limit (e.g. 3%) leading to a lockout.
  - Weekly and monthly drawdown circuit-breakers.

### Gaps
- No India-specific study on retail sizing was found.

## 8. Behavioural biases

### Takeaway
SEBI data show the footprints of the disposition effect (small wins, large losses), persistence after losses, and young or low-wealth traders losing the most. Academic Indian evidence covers equities more than F&O. SEBI has regulated finfluencers since Aug 2024 and is taking enforcement action.

### Cited Findings
- About 79% of traders' average gains were smaller than their average losses. About 90% of traders who lost two years in a row kept trading and lost again. — [Moneylife](https://www.moneylife.in/article/92-percentage-of-aggregate-losses-incurred-by-individuals-are-from-options-trading-sebi-study/81429.html)
- Over 75% of loss-makers continued trading (FY22–24). — [Outlook Money](https://www.outlookmoney.com/invest/93-of-individual-traders-suffered-losses-in-fo-in-last-3-years-sebi-study)
- An ISB study found that Indian retail equity investors show a larger disposition effect than US, Japanese, Chinese or Finnish investors, plus overconfidence. — [Business Standard](https://www.business-standard.com/article/markets/retail-investors-tend-to-lose-in-stock-markets-says-isb-study-112120100043_1.html)
- Overconfidence and the disposition effect are both present in Indian index stocks, with overconfidence predominant. — [IJBE (Ganesh et al.)](https://ijbe.fcu.edu.tw/past_issues/NO.19-3/abstract/19-3-3.html); [Global Business Review 2017](https://ideas.repec.org/a/sae/globus/v19y2017i5p1303-1321.html)
- Finfluencers:
  - SEBI regulations barring regulated entities from associating with unregistered advice-givers or people making performance claims took effect 29 Aug 2024. A 22 Oct 2024 circular gave 3 months to end such ties. — [Outlook Business](https://www.outlookbusiness.com/markets/sebi-directs-regulated-entities-to-sever-ties-with-finfluencers-in-3-months)
  - A Jan 2025 circular bars educators from using market price data from the preceding 3 months. — [Business Standard](https://www.business-standard.com/markets/news/sebi-finfluencer-circular-live-stock-data-market-education-rules-125013000571_1.html)
- Enforcement:
  - "Baap of Chart" (Md. Nasiruddin Ansari): banned Oct 2023 with ₹17.2 crore disgorgement. — [SCC Online](https://www.scconline.com/blog/?p=305999)
  - Avadhut Sathe Trading Academy: interim order Dec 2025 impounding ₹546 crore for unregistered advice. — [LiveLaw](https://www.livelaw.in/amp/corporate-law/sebi-cracks-down-on-finfluencer-avadhut-sathe-impounds-546-crore-for-providing-unregistered-investment-advice-312335)

### Inferences
- These biases are detectable from the tool's own trade journal:
  - **Disposition effect:** average holding time of losers vs winners; average win vs average loss; share of winners closed below target.
  - **Revenge or after-loss trading:** a new entry within N minutes of a losing exit; position size after a loss compared with the baseline.
  - **Averaging down:** adding to a losing long option.
  - **Overconfidence:** size increasing after a winning streak; trade count trending up.
  - **FOMO:** entries after a large intraday move has already happened (e.g. more than 1σ) or chasing a premium already up more than 50% on the day.
  - **Tips:** trades with no rule-based signal attached.
- Rules:
  - Pre-defined stop and target on every trade (stop ≤ 30–40% of premium; target ≥ 1.5–2× the stop).
  - No averaging down on long options.
  - Cooling-off period (e.g. 30–60 minutes) after a loss.
  - Lockout after 2 consecutive losses in a day.
  - No size increase after a win streak.
  - Every trade must come from a system signal.

### Gaps
- I found no peer-reviewed Indian F&O-specific study on revenge trading or the disposition effect. The SEBI aggregates are suggestive only.

## 9. Overnight gap risk (1–2 day holds)

### Takeaway
Overnight positions are exposed to gaps from global markets and events that a stop-loss cannot protect against. For long options, a gap against the position combines with overnight theta and often an IV drop.

### Cited Findings
- On 4 Jun 2024 (election results), the Sensex fell more than 5,000 points intraday and VIX spiked. This was an event gap that exit polls had not anticipated. — [Business Standard](https://www.business-standard.com/amp/markets/news/sensex-plunges-over-4-000-points-intraday-check-factors-behind-the-fall-124060400591_1.html)

### Inferences
- An overnight hold at 2 DTE moving to 1 DTE costs about 30% of ATM premium in theta alone (₹89 → ₹63 in the example in section 1), before any gap.
- Signals: event calendar for the overnight window; distribution of Nifty overnight gaps (open vs previous close) from history; GIFT Nifty and US futures moves.
- Rules:
  - No overnight holds into an event, or when DTE after the hold would be 1 or less.
  - Size overnight positions at half the intraday size.
  - Treat the stop-loss as non-binding for overnight risk: the maximum loss is the full premium.

### Gaps
- I found no sourced statistic on the Nifty overnight gap distribution. Compute it from historical OHLC (e.g. % of days with |gap| > 0.5% or > 1%).
