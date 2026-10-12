# Large players in Indian F&O and the patterns that hurt retail option buyers

Research date: 12 October 2026. Scope: India (NSE/BSE equity derivatives). Allegations (interim/ex-parte orders, show-cause notices) are kept separate from final findings. Where sources disagree, both are given.

## 1. SEBI vs Jane Street: alleged expiry-day strategy, amounts, and what happened next

### Takeaway
SEBI's ex-parte interim order of 3 July 2025 alleges that Jane Street pushed BANKNIFTY up in the morning of expiry days by buying constituent stocks and futures. At the same time it held large bearish index-option positions, then dumped the stocks and futures in the afternoon ("intraday index manipulation"). On other days it moved the index in the last two hours ("extended marking the close"). Jane Street deposited ₹4,843.57 crore and trading restrictions were lifted. As of October 2026 there is **no final SEBI order**: the case is before SAT and the probe has widened. All of it is still **allegation / prima facie finding**, not an adjudicated finding.

### Cited findings
- **Order and parties:** ex-parte interim order dated 3 July 2025 against JSI Investments Pvt Ltd, JSI2 Investments Pvt Ltd, Jane Street Singapore Pte Ltd and Jane Street Asia Trading Ltd. It barred them from the securities market and impounded ₹4,843.57 crore of alleged unlawful gains (18 expiry days: 15 BANKNIFTY and 3 NIFTY). Banks were told not to allow debits. — [Mondaq/MHCO](https://www.mondaq.com/india/securities/1648508/sebi-update-%7c-interim-order-against-jane-street-group-for-alleged-index-manipulation)
- **Review period:** variously given as 1 Jan 2023 to 31 May 2025 ([Mondaq/MHCO](https://www.mondaq.com/india/securities/1648508/sebi-update-%7c-interim-order-against-jane-street-group-for-alleged-index-manipulation)) and 1 Jan 2023 to 31 Mar 2025 for the segment P&L ([Moneylife](https://www.moneylife.in/article/jane-street-accused-of-massively-rigging-of-indias-derivatives-market-sebi-orders-ban-escrow-of-rs4843-crore-illegal-gains/77585.html)). The May 2025 NIFTY days fall after March, which explains the longer window.
- **Mechanism ("intraday index manipulation"), worked example 17 Jan 2024:**
  - *Patch I, 09:15 to about 11:47:* net buying of ₹4,370.03 crore in BANKNIFTY constituent stocks and stock futures. BANKNIFTY rose from 46,573.93 to 47,176.97. Over the same period the group built bearish options positions (bought puts, sold calls).
  - *Patch II, 11:49 to close:* it sold the same constituents and pushed the index down, in line with its options book. Net profit for that day: ₹734.93 crore. — [Mondaq (index manipulation explained)](https://www.mondaq.com/india/commoditiesderivativesstock-exchanges/1648134/sebis-interim-order-against-jane-street-allegations-of-index-manipulation-explained)
  - The buys were often placed above the last traded price. In stocks such as Kotak Bank, SBI and Axis Bank they sometimes exceeded 20% of market-wide volume, and on several expiry days the group's trading alone accounted for the index's morning rise. — [ECGI blog](https://www.ecgi.global/publications/blog/expiry-day-and-the-governance-of-algorithmic-trading-the-jane-street-episode)
  - Scale mismatch: BANKNIFTY options notional turnover that day was cited as about ₹1.03 crore crore (₹1,03,17,127 crore), against about ₹1.05 lakh crore of cash plus futures turnover in the 12 constituents. A small loss in the cash leg could therefore lever a much larger options gain. — [Mondaq](https://www.mondaq.com/india/commoditiesderivativesstock-exchanges/1648134/sebis-interim-order-against-jane-street-allegations-of-index-manipulation-explained)
- **"Extended marking the close":**
  - On 10 July 2024 and two other expiry days, the group waited for the last two hours, then sold stocks, stock futures and BANKNIFTY futures worth about ₹2,800 crore while carrying a ₹44,154 crore short BANKNIFTY options position. Gain: ₹225 crore.
  - In May 2025, on three NIFTY expiries (bullish variant), it bought ₹4,911 crore of NIFTY constituents and futures in the last two hours while long ₹38,297 crore of NIFTY options. On 15 May 2025 its delta went from −₹17,125.75 crore at the open to +₹38,297.01 crore at the close. — [Moneylife](https://www.moneylife.in/article/jane-street-accused-of-massively-rigging-of-indias-derivatives-market-sebi-orders-ban-escrow-of-rs4843-crore-illegal-gains/77585.html); the ₹4,911 crore figure is also in [Moneycontrol via TradingView](https://tr.tradingview.com/news/moneycontrol%3A0e6320645094b%3A0-how-jane-street-allegedly-manipulated-index-closing-on-expiry-days)
- **Overall P&L, Jan 2023 to Mar 2025 (per SEBI):** total net gain ₹36,671 crore. Index options profit ₹44,358 crore. Losses: stock futures ₹7,208 crore, index futures ₹191 crore, cash ₹288 crore. — [Moneylife](https://www.moneylife.in/article/jane-street-accused-of-massively-rigging-of-indias-derivatives-market-sebi-orders-ban-escrow-of-rs4843-crore-illegal-gains/77585.html)
  - Conflicting figures: other coverage gives "over ₹43,000 crore" in index options ([Mondaq](https://www.mondaq.com/india/commoditiesderivativesstock-exchanges/1648134/sebis-interim-order-against-jane-street-allegations-of-index-manipulation-explained)) and about ₹36,500 crore total profit ([share.market](https://www.share.market/buzz/futures-and-options/sebi-vs-jane-street-36500-crore-profit-a-massive-ban-what-you-need-to-know)). Check against the SEBI order PDF.
- **Profit on the 15 BANKNIFTY expiry days:** ₹3,914 crore in index options. — [Mondaq/MHCO](https://www.mondaq.com/india/securities/1648508/sebi-update-%7c-interim-order-against-jane-street-group-for-alleged-index-manipulation)
- **Prior warning:** NSE sent a caution letter on 6 February 2025 against large index-option positions and pattern trading. SEBI alleges the conduct continued, notably on 15 May 2025. — [Moneylife](https://www.moneylife.in/article/jane-street-accused-of-massively-rigging-of-indias-derivatives-market-sebi-orders-ban-escrow-of-rs4843-crore-illegal-gains/77585.html); [Mondaq](https://www.mondaq.com/india/commoditiesderivativesstock-exchanges/1648134/sebis-interim-order-against-jane-street-allegations-of-index-manipulation-explained)
- **Investigation history:**
  - Media reports in April 2024 led to the inquiry, and NSE submitted its report on 13 November 2024. — [Mondaq](https://www.mondaq.com/india/commoditiesderivativesstock-exchanges/1648134/sebis-interim-order-against-jane-street-allegations-of-index-manipulation-explained)
  - Jane Street told SAT that NSE's November 2024 review and SEBI's Integrated Surveillance Department (December 2024) found no manipulation and proposed that the matter "may not be pursued further". SEBI then formed a new inter-departmental team. — [TechTimes, 5 Oct 2026](https://www.techtimes.com/articles/328567/20261005/jane-street-tells-india-tribunal-sebis-own-reports-found-no-manipulation-before-567m-order.htm)
- **Retail harm (SEBI's view):** the order says the activity "misled lakhs of retail options traders". — [Moneylife](https://www.moneylife.in/article/jane-street-accused-of-massively-rigging-of-indias-derivatives-market-sebi-orders-ban-escrow-of-rs4843-crore-illegal-gains/77585.html)
- **Afterwards:**
  - Jane Street deposited the full ₹4,843.57 crore in escrow on 14 July 2025, reserving its rights. On 21 July 2025 SEBI said the trading ban, account freezes and asset-transfer restrictions would cease to apply, subject to continuing compliance. — [ECGI](https://www.ecgi.global/publications/blog/expiry-day-and-the-governance-of-algorithmic-trading-the-jane-street-episode)
  - Jane Street sought more time to reply in late July 2025 ([Business Standard](https://www.business-standard.com/markets/news/jane-street-seeks-more-time-from-sebi-to-respond-to-july-3-order-125072801373_1.html)).
  - It appealed to SAT in September 2025, and SAT asked SEBI to explain withheld documents within three weeks. SAT adjourned a hearing in February 2026. On 5 October 2026 SAT heard Jane Street's plea for SEBI records, with no ruling reported. SEBI counsel said the probe had widened to other indices. — [TechTimes](https://www.techtimes.com/articles/328567/20261005/jane-street-tells-india-tribunal-sebis-own-reports-found-no-manipulation-before-567m-order.htm); see also [The420.in](https://the420.in/jane-street-sebi-sat-appeal/), [Reuters via Yahoo](https://finance.yahoo.com/news/exclusive-us-trading-firm-jane-095454014.html)
  - The probe reportedly extends to Sensex and other strategies, and Jane Street hired lobbyists in December 2025. — [Business Standard](https://www.business-standard.com/markets/news/jane-street-hires-lobbyists-after-20-years-amid-sebi-investigation-125122401325_1.html)
- **Market impact:** F&O turnover fell about 21% on the expiry day after the ban. — [Business Standard](https://www.business-standard.com/amp/markets/news/fo-turnover-dips-21-expiry-day-jane-street-ban-125071001169_1.html)

### Inferences
- The alleged pattern is the textbook reason a retail buyer should distrust a strong one-directional morning move on expiry day. A move driven by one large participant's cash and futures buying can reverse in the afternoon, and the reversal favours whoever holds the opposite options book.
- Jane Street's defence (the exchange and SEBI surveillance first found nothing) shows the line between "aggressive hedging or arbitrage" and "manipulation" is contested. A retail system should treat the pattern as a risk regardless of legality.

### Gaps
- No final SEBI order and no SAT judgment on the merits as of October 2026. I did not find whether a formal show-cause notice for final directions was issued, or its date.
- I did not read the SEBI order PDF directly, so the segment P&L figures (₹44,358 crore vs "over ₹43,000 crore") are not reconciled.

## 2. Who takes the other side: SEBI data on proprietary, FPI and algo profits; algo share of volume

### Takeaway
In every SEBI study, individuals are the only category with aggregate losses. Proprietary traders and FPIs take most of the profits, and almost all of those profits go to entities using algorithms.

### Cited findings
- **FY24 (SEBI study, 23 Sep 2024):**
  - Proprietary traders made about ₹33,000 crore and FPIs about ₹28,000 crore in gross trading profit, while individuals lost over ₹61,000 crore (all before costs).
  - 97% of FPI profits and 96% of proprietary-trader profits came from algo trading.
  - 93% of over 1 crore individuals lost money over FY22 to FY24 (average about ₹2 lakh including costs), totalling about ₹1.8 lakh crore. Only 1% made over ₹1 lakh after costs.
  - Sources: [Moneylife](https://www.moneylife.in/article/93-percentage-of-individual-traders-lost-rs18-lakh-crore-in-equity-fo-in-past-3-years-sebi/75210.html); [Business Standard](https://www.business-standard.com/amp/opinion/editorial/a-losing-proposition-odds-are-against-individuals-in-f-o-trading-124092401316_1.html); [Outlook Money](https://www.outlookmoney.com/invest/93-of-individual-traders-suffered-losses-in-fo-in-last-3-years-sebi-study)
- **FY25 (SEBI study, 7 Jul 2025):** about 91% of individuals lost money. Net losses after costs were ₹1,05,603 crore, up from ₹74,812 crore in FY24, and unique individual traders fell 20%. — [Business Standard](https://www.business-standard.com/amp/markets/news/net-losses-of-traders-in-fo-widens-in-fy25-sebi-study-125070701221_1.html); [The Week/PTI](https://www.theweek.in/wire-updates/business/2025/07/07/dcm92-biz-sebi-derivatives-study.html). The 2026 study revises FY25 net losses to about ₹1.12 lakh crore (₹1,11,788 crore). — [Finnovate summary](https://www.finnovate.in/learn/blog/sebi-fno-trader-losses-fy26-individual-derivatives); [Corplaw Updates](https://www.corplawupdates.in/updates/sebi-equity-derivatives-retail-trader-study-fy26)
- **FY26 (SEBI PR 50/2026, 20 Aug 2026):**
  - 87.7% of individuals lost money. Net losses were ₹91,685 crore (gross about ₹72,000 crore), with an average loss of about ₹1.17 lakh. Options accounted for about 92% of losses.
  - Active individuals fell from 98.1 lakh to 78.6 lakh.
  - Gross profits: proprietary traders about ₹44,000 crore, FPIs about ₹14,000 crore, corporates about ₹8,000 crore, MFs and LLPs about ₹3,000 crore each. 99% of FPI and proprietary profits went to "algo entities" (entities with at least one algo order in the year).
  - Sources: [Corplaw Updates](https://www.corplawupdates.in/updates/sebi-equity-derivatives-retail-trader-study-fy26); [Moneylife](https://www.moneylife.in/article/92-percentage-of-aggregate-losses-incurred-by-individuals-are-from-options-trading-sebi-study/81429.html). One secondary source gives proprietary profit as ₹45,955 crore in FY25 and ₹44,483 crore in FY26 (unverified against the SEBI PDF). The individual-trader count also differs, 7.86 million vs 8.75 million in SEBI's summary.
- **Expiry concentration (FY26):** about 59% of index-options turnover was same-day expiry (0DTE), about 75% within one day of expiry and about 97% within a week. — [Corplaw Updates](https://www.corplawupdates.in/updates/sebi-equity-derivatives-retail-trader-study-fy26)
- **Algo and proprietary share of volume:**
  - Algos were about 70% of F&O trading in FY25 and 69% of equity-derivative trades in April (NSE data cited by [Outlook Business](https://www.outlookbusiness.com/amp/story/markets/algos-have-rewritten-the-script-for-trading-in-india-its-time-for-retail-investors-to-play-it-smart)).
  - Algos crossed 50% of cash-market turnover in FY25 ([Business Standard](https://www.business-standard.com/markets/news/in-a-first-machines-overtake-humans-in-nse-s-cash-market-trades-125041500893_1.html)).
  - Proprietary traders had a 48% share of equity options vs 39.3% for individuals in June 2026 (broker blog citing NSE, [Swastika](https://www.swastika.co.in/blog/nse-turnover-surges-in-june-a-23-month-high-and-what-it-means-for-retail-investo)). Another source says 52.3% of options premium turnover is proprietary, undated ([Marketcalls](https://www.marketcalls.in/futures-and-options/the-state-of-indias-stock-market-what-every-retail-investor-needs-to-know-in-2025.html)).

### Inferences
- The counterparty to a retail options buyer is, in aggregate, mostly algorithmic proprietary desks (domestic and globally-owned) and FPIs, operating with co-location, market-making and premium-selling books.
- With about 59% of index-options turnover being 0DTE, expiry-day trading is where retail and fast algorithms meet most directly.

### Gaps
- I found no NSE primary figure for the algo share of *options* turnover specifically. The 70% F&O figure is from press citing NSE.
- No public SEBI breakdown of profits by named firm except the Jane Street order.

## 3. Option sellers vs buyers

### Takeaway
Retail in India is overwhelmingly on the *buy* side of options, and SEBI's own data show buyers lose far more often. Sellers lose less often but suffer much larger losses when they do (tail risk). Large sellers are mainly proprietary and FPI algo desks.

### Cited findings
- **SEBI FY26 random sample of 5,050 traders:**
  - About 93% of individuals were "only option buyers", about 4% "mostly buyers" and about 2% "mostly sellers".
  - About 90% of only-buyers were loss-makers vs about 44% of mostly-sellers.
  - The average loss among loss-making sellers was about ₹51.7 lakh vs about ₹1.3 lakh for buyers. SEBI calls this "tail-risk asymmetry in option selling".
  - Only about 15.4% of trader-quarters were profitable.
  - Traders active more than 100 days were 42% of traders but generated 94% of turnover and 87% of losses.
  - Among FY22 to FY26 traders, about 0.5% were profitable in all five years and 65.6% lost in every year.
  - SEBI notes the seller and futures sub-groups are small, so treat those numbers as indicative.
  - Source: [Zerodha TradingQnA summary of SEBI study](https://tradingqna.com/t/win-rate-capital-experience-what-sebi-found-about-f-o-traders/197266)
- **Options vs futures (FY26):** 87.7% of individuals lost money in options vs about 66% in futures. — [Finnovate](https://www.finnovate.in/learn/blog/sebi-fno-trader-losses-fy26-individual-derivatives)

### Inferences
- Premium-selling economics: buyers pay time value plus implied-volatility premium, and on 0DTE most out-of-the-money options expire worthless. Sellers collect this premium repeatedly but need large margin and hedging, and they occasionally take very large losses. Desks with scale, hedging and low costs capture the edge.
- The reason institutional sellers "win more often" is structural, not proof of manipulation.

### Gaps
- No SEBI split of institutional option selling by category (how much of short gamma is proprietary vs FPI).
- No Indian peer-reviewed estimate of the volatility risk premium was found in this session.

## 4. Max pain and expiry pinning

### Takeaway
Rigorous evidence for pinning exists for **US single stocks**, not convincingly for Indian indices. Max pain is a heuristic. Under tight liquidity and heavy OI concentration, pinning toward a big strike is plausible, but it is not reliable enough to trade on.

### Cited findings
- **US single stocks (Ni, Pearson and Poteshman, JFE 2005):** optionable stocks cluster at strikes on expiry dates (1996 to 2002). Returns are altered by at least 16.5 bp on average, and no effect appears for non-optionable stocks or the Fridays before or after expiry. The authors attribute this to delta-hedge rebalancing and to manipulation by proprietary traders. — [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0304405X05000577); [CXO Advisory](https://www.cxoadvisory.com/equity-options/stock-price-pinning-at-options-expiration/)
- **Weekly options:** a later study finds clustering for high-volume weekly options with a large strike grid and supports both the hedging and manipulation hypotheses. — [WPUNJ paper](https://www.wpunj.edu/Weekly%20Options%20on%20Stock%20Pinning%20upto%20page%208.pdf)
- **India:** Gupta, Metia and Trivedi (SSRN) tested NSE expiry days for abnormal volume, price movement, reversal and pinning. I could only read the abstract, so the results are unconfirmed. — [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=619701)
- **Practitioner view:** practitioner pages describe max pain as a theory, not a rule. It shifts intraday as OI changes and is questionable for highly liquid indices. — [Equities India glossary](https://equitiesindia.com/glossary/max-pain-theory); [TrueData](https://www.truedata.in/blog/max-pain-theory-does-it-really-work)

### Inferences
- The Jane Street allegations show that the index can be pushed *away* from or *toward* levels that suit a large options book, which is the manipulation channel of pinning.
- Treat high-OI strikes as likely friction or magnet zones near expiry, not as targets.

### Gaps
- No peer-reviewed India-specific estimate of index pinning frequency or accuracy was found.

## 5. Open-interest traps and sudden unwinding

### Takeaway
I found no documented study showing OI build-up being used deliberately as a lure in India. This is mostly market folklore. What is documented is that large intraday positions, which end-of-day OI hides, can move the index. SEBI responded in 2025 with delta-based OI and intraday position limits.

### Cited findings
- SEBI moved from notional OI to delta-based "futures-equivalent" OI by a 29 May 2025 circular, phased in from July to December 2025. — [Probe42](https://resources.probe42.in/regulatory-updates/sebi-updates/analysis-of-profits-losses-in-the-equity-derivatives-segment/); [Bajaj Broking](https://www.bajajbroking.in/blog/sebi-notifies-new-f-and-o-rules-with-higher-index-limits-and-risk-measures)
- **Intraday index-option limits:** SEBI circular of 1 September 2025, effective 1 October 2025, set limits per entity of ₹5,000 crore net intraday (FutEq) vs ₹1,500 crore end-of-day, and ₹10,000 crore gross per side. Limits are monitored by at least four random snapshots, including one between 14:45 and 15:30, and expiry-day breaches attract an additional surveillance deposit or penalty. — [Outlook Money](https://www.outlookmoney.com/invest/equity/sebi-outlines-new-framework-for-monitoring-of-intraday-position-limits-for-index-derivatives); [GlobalTrading](https://www.globaltrading.net/?p=39459)
- The press links the limits to Jane Street. It reports Jane Street's net position of about US$4.5 billion on 17 January 2024 and calls the new limit a tenth of that. SEBI's circular cites only "outsized intraday future equivalent positions… on the day of contract expiry". — [GlobalTrading](https://www.globaltrading.net/?p=39459)
- **Expiry-day framework (effective 20 Nov 2024 onward):** one weekly-expiry benchmark per exchange, larger lot sizes, and other measures. — [Value Research](https://www.valueresearchonline.com/stories/224848/sebi-rewrites-fo-rules-to-curb-expiry-day-speculation/); [Business Standard](https://www.business-standard.com/amp/markets/capital-market-news/sebi-sees-dip-in-derivatives-turnover-91-of-retail-traders-lose-money-in-fy25-125070800660_1.html)

### Inferences
- End-of-day option-chain OI, which is what retail sees, can miss intraday positions that are far larger. "Support at the highest put OI" can disappear when those writers cover.
- Sharp OI drops at a strike near price (writers covering) are a better warning sign than the absolute OI level.

### Gaps
- No empirical Indian evidence that OI walls hold, or that OI is used deliberately as bait.

## 6. Stop-loss hunting and liquidity grabs

### Takeaway
I found no Indian regulatory finding or academic study that specifically documents stop hunting around the previous day's high/low or round numbers. The closest documented analogue is spoofing or false depth, which SEBI flagged in the new closing auction. Treat "stop hunting" as plausible microstructure behaviour (orders cluster at obvious levels) rather than proven manipulation.

### Cited findings
- SEBI's 12 Sep 2026 consultation paper flags that unrestricted cancellations in the closing auction created "spoofing and phantom liquidity" concerns. It proposes making limit orders placed more than ±1% from the reference price non-cancellable. — [Outlook Money](https://www.outlookmoney.com/amp/story/invest/sebi-proposes-changes-to-closing-auction-session-fo-settlement-rules-key-proposals-explained)

### Inferences
- Stops placed exactly at obvious levels are easy liquidity for anyone needing to fill size. Using volatility-based stops placed away from round numbers is a reasonable precaution, though not evidence-based for India.

### Gaps
- No India-specific evidence on stop hunting was found in this session.

## 7. Opening and closing moves, the closing-price window and expiry afternoons

### Takeaway
The closing mechanism changed in 2026. Since **3 August 2026**, more than 200 F&O stocks have closed via a **Closing Auction Session (CAS)** instead of the old 3:00 to 3:30 PM VWAP. Early sessions showed sharp, illiquid closing moves (NIFTY's official close was 0.6 to 0.8% away from its 3:15 level). SEBI is now consulting on how expiry settlement prices are set. Expiry-day closes are a documented manipulation target (Jane Street's "extended marking the close").

### Cited findings
- **Old method:** the closing price was the VWAP of the last 30 minutes (3:00 to 3:30 PM), which was seen as open to influence by large traders. — [share.market](https://www.share.market/buzz/circulars/closing-auction-session/)
- **CAS:**
  - SEBI proposed it in 2024 and issued a circular on 16 Jan 2026. NSE published operational guidelines on 18 Mar 2026 ([NSE circular](https://nsearchives.nseindia.com/content/circulars/CMTR73362.pdf)), and CAS went live on 3 Aug 2026 ([Bigul](https://bigul.co/blog/market-update/sebi-rolls-out-new-closing-price-mechanism-closing-auction-session-cas-to-begin-august-3-2026)).
  - Timings as reported: continuous trading for eligible stocks ends at 3:15 PM, the auction runs 3:15 to 3:35 PM, and derivatives trade until 3:40 PM. Stocks without derivatives keep the VWAP close. — [Business Today, 5 Aug 2026](https://www.businesstoday.in/markets/stocks/story/explained-why-closing-auction-session-is-triggering-sharp-market-swings-547396-2026-08-05)
  - In the first sessions, NIFTY's official close was about 0.8% (day 1) and 0.6% (day 2) above its 3:15 level while index futures barely moved. Goldman Sachs attributed this to thin institutional participation. — [Business Today](https://www.businesstoday.in/markets/stocks/story/explained-why-closing-auction-session-is-triggering-sharp-market-swings-547396-2026-08-05)
  - Timing details vary by source (the consultation paper mentions a "10-minute CAS" and a five-minute transition gap), so check the NSE circular.
- **SEBI consultation of 12 Sep 2026 (comments were due 3 Oct 2026):**
  - It observed concentrated trading in expiring options during the CAS window, sharply higher per-minute premium turnover, and speculative turnover in the five-minute gap between sessions. Traders also mistook the Indicative Index Value for the actual index.
  - It proposes expiry settlement by either (1) a blended VWAP of the last 30 minutes of continuous trading plus the CAS, or (2) reverting to the last-30-minute continuous VWAP for at least one year.
  - Source: [Outlook Money](https://www.outlookmoney.com/amp/story/invest/sebi-proposes-changes-to-closing-auction-session-fo-settlement-rules-key-proposals-explained)
- **Expiry-day afternoon:** Jane Street's alleged "Patch II" reversal started at about 11:49, and the "extended marking the close" trades came in the last two hours (see section 1).

### Inferences
- The last 15 to 40 minutes of the session, particularly on expiry days, became more dangerous for retail options holders after CAS. The final settlement price can diverge from the last traded index level, and expiring premiums react violently.
- For the open, I found no Indian study in this session quantifying first-15-minute volatility. That the morning was the "push" leg in the Jane Street pattern is the only documented link.

### Gaps
- No sourced data on pre-open session (9:00 to 9:15) behaviour or first-15-minute volatility for NIFTY or BANKNIFTY.
- The final SEBI decision on expiry settlement-price methodology was not found (consultation closed 3 Oct 2026).
- Exact CAS sub-windows need confirmation from NSE circulars.

## 8. Information asymmetry: front-running, leaks, flows

### Takeaway
Documented Indian cases are mostly about front-running large client orders, not about news. They show that large-order information leaks and is monetised ahead of the flow.

### Cited findings
- **Ketan Parekh front-running case:** SEBI interim order of 2 Jan 2025.
  - It barred Ketan Parekh and two others and impounded ₹65.77 crore from 22 entities.
  - Rohit Salgaocar (Singapore-based) allegedly passed non-public information about a "big client's" orders, and front-runners got instructions via WhatsApp from contacts saved as "Jack" or "Boss", traced to Parekh.
  - No evidence was found against brokers Motilal Oswal or Nuvama.
  - Sources: [The Week/PTI](https://www.theweek.in/wire-updates/business/2025/01/02/dcm54-biz-sebi-ketan-parekh.html); [Moneylife](https://moneylife.in/article/ketan-parekh-21-others-caught-in-frontrunning-scam-sebi-asks-them-to-disgorge-rs6577-crore-illegal-gains/76010.html)
  - Press reports linked the "big client" to Tiger Global; this is a press inference, not SEBI's naming. — [YourStory](https://yourstory.com/2025/01/mystery-big-client-sebi-ketan-parekh-probe-tiger-global)
  - SEBI later (dated 2 Feb, reported 2026) issued show-cause notices to six Capital Group-linked FPIs over lapses in safeguarding confidential trade information (period 1 Jan 2021 to 20 Jun 2023). These are allegations and the outcome is unknown. — [Angel One](https://oga-prod.angelone.in/news/market-updates/sebi-issues-show-cause-notice-to-6-capital-group-linked-fpis-in-ketan-parekh-case)

### Inferences
- Retail sees FPI flow data and block deals only after the fact (provisional FII/DII data comes after the close). Institutions and their counterparties see the flow first. A retail buyer cannot win a speed race on news.

### Gaps
- I did not research results-leakage cases (for example, the WhatsApp leaks of company results in 2017) in this session, so no sourced figures.
- No study of how fast news reaches index-options prices in India.

## 9. Practical detection rules for a retail options-buying system

### Takeaway
Based on the documented cases and data above, the highest-value guards are about **time of day and expiry**, **outsized one-directional moves on expiry**, and **the closing window**. Pure OI or max-pain signals have weak evidence.

### Cited findings (the evidence base for each rule)
- **Expiry concentration and 0DTE losses:** 59% of index-options turnover is 0DTE. — [Corplaw Updates](https://www.corplawupdates.in/updates/sebi-equity-derivatives-retail-trader-study-fy26)
- **Morning push then afternoon reversal on expiry (alleged Jane Street Patch I/II):** [Mondaq](https://www.mondaq.com/india/commoditiesderivativesstock-exchanges/1648134/sebis-interim-order-against-jane-street-allegations-of-index-manipulation-explained)
- **Last-two-hours moves on expiry ("extended marking the close"):** [Moneylife](https://www.moneylife.in/article/jane-street-accused-of-massively-rigging-of-indias-derivatives-market-sebi-orders-ban-escrow-of-rs4843-crore-illegal-gains/77585.html)
- **CAS closing jumps of 0.6 to 0.8% and expiring-option activity in the auction window:** [Business Today](https://www.businesstoday.in/markets/stocks/story/explained-why-closing-auction-session-is-triggering-sharp-market-swings-547396-2026-08-05); [Outlook Money](https://www.outlookmoney.com/amp/story/invest/sebi-proposes-changes-to-closing-auction-session-fo-settlement-rules-key-proposals-explained)
- **Buyers lose about 90% of the time; frequent traders take 87% of losses:** [TradingQnA SEBI summary](https://tradingqna.com/t/win-rate-capital-experience-what-sebi-found-about-f-o-traders/197266)

### Inferences (proposed rules; these are my design suggestions, not sourced facts)
1. **Avoid buying options expiring the same day (0DTE)**, or apply a much higher bar, such as no new entries on the contract's expiry day.
2. **No new entries after about 14:30 on expiry day**, and no holding expiring options into the 15:15+ CAS window or settlement.
3. **Flag expiry-morning divergence:** if the index rises or falls more than X% before noon on expiry while the constituent breadth or volume pattern looks concentrated (a few heavyweights carrying the move), treat a reversal as likely and avoid chasing.
4. **Avoid entries in the closing window on any day** (from about 15:00), because the closing price is set by an auction that can jump 0.5 to 1% on thin participation.
5. **OI signals are context, not triggers.** Alert on sudden OI drops (unwinding) at strikes near spot rather than buying because of "big put OI support". Do not use max pain as a target.
6. **Avoid the first few minutes after the open** until volatility settles. This is a reasonable heuristic, though not evidenced in this session.
7. **Place stops away from round numbers and the previous day's high/low** (heuristic).
8. **Cap trade frequency.** SEBI data show more active traders account for a disproportionate share of losses.

### Gaps
- None of these rules has been back-tested here, and the thresholds (X%, cut-off times) need calibration on NSE intraday data.
- Expiry days changed in 2025 (for example, NIFTY moved to Tuesday). Confirm the current expiry calendar from NSE before hard-coding it.
