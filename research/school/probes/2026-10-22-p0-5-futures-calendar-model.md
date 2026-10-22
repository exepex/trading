# P0 probe 5: futures and calendar/diagonal payoff and margin model

Market school stage P0 (response 327, section 4; WORK_REGISTER "MS-P0 market school probes"). Builder session
session_01G5EqV95Wi7yHJ5Hgy2giaY, 22 Oct 2026. Research note only: no code was changed. Labels: **strong evidence**
(a file and line, a quoted primary source or a measured run), **some evidence** (a secondary source), **reasoning
only**.

## Answer in four lines

1. Our code models **one-expiry, options-only, index-only** positions. It has **no futures** (no futures charges, no
   futures STT, no futures margin rows) and **no second expiry** (a `Leg` has no expiry field). **[strong evidence:
   the files below]**
2. So calendars and diagonals cannot be valued, capped or margined by the current code. Response 327 item 5 ("calendars
   and diagonals wait for a verified payoff and margin model") stays in force. **[strong evidence]**
3. **A long-put calendar's worst case is not its debit.** At NIFTY 22,811, lot 65, the 22,800 put calendar (sell the
   28-day, buy the 63-day) costs about Rs 6,435 but can lose about **Rs 15,644 at mid prices**, 2.4 times the debit,
   before any bid discount. Above the Rs 10,000 cap. **[reasoning only: Black-Scholes arithmetic, inputs stated]**
4. One NIFTY futures lot is Rs 14.8 lakh of exposure: a 1% move is Rs 14,827, a 5.9% gap Rs 87,480. A round trip
   costs about **Rs 886 (13.6 points)** in charges, 60% of it STT. **[strong evidence for the arithmetic; charge rates labelled below]**

## 1. What our code has

| Part | What it does | Where | Limit for the school |
|---|---|---|---|
| Charges | One options order: brokerage Rs 20, STT 0.15% on sold premium, exchange 0.03503%, SEBI Rs 10/crore, IPFT Rs 50/crore, stamp 0.003% on buys, GST 18%; settlement charges for an exercised leg (STT 0.15% on intrinsic) | `fno/costs.py:23-56`, `config.yaml:27-35` | Options premium only. No futures rates (STT, exchange charge, stamp and IPFT all differ for futures). |
| Legs | `Leg(strike, kind, side)` | `fno/research_engine/structures.py:34-41` | No expiry, no instrument type: a future or a second expiry cannot be expressed. |
| Maximum loss | Terminal payoff over every strike at one expiry, plus entry charges, pads (Rs 1 a unit each way) and worst exit charges | `fno/research_engine/cycle_costs.py:63-76` | Assumes every leg expires together and settles at intrinsic. Wrong for a calendar (the far leg is still alive and priced). |
| Naked-short guard | Refuses more legs sold than bought per option type | `structures.py` `require_covered` | A put calendar passes it (one sold, one bought) although its loss is not fixed by the strikes. |
| SPAN margin | Scanning risk of a one-expiry structure from NSE Clearing's SPAN file; "for one expiry there is no calendar-spread charge" | `fno/nse_margins/calculator.py:1-11`, `span_file.py:12-16` | The file holds futures (`futPf`) and every expiry, but the calculator refuses anything else; no inter-month spread charge is read. |
| Exposure margin | 2% of notional per short index option, 3% if more than 10% OTM | `fno/constants.py:316-317` | Line 318: "beyond 9 months (5%) and on expiry day (+2%) NSE's rule differs: not modelled". No futures ELM. |
| C2 margin rows | `structure, width, scan, nov, exposure` per lot | `fno/risk/margins.py:1-28` | Keyed by structure code and width: no expiry pair, no future. |

## 2. What is missing (each needs a story before any futures, calendar or diagonal driver)

1. **Futures charges** per order (rates in section 4).
2. **Futures margin**: SPAN scanning risk from `futPf` plus the index-futures ELM; mark-to-market every day (a futures
   loss is paid in cash each evening, unlike an option's premium).
3. **A leg with an expiry and an instrument type** (option or future), and a maximum loss that values the far leg when
   the near leg settles.
4. **Calendar worst case**, section 3: European far puts can be worth less than intrinsic, and the exit is at the bid.
5. **Expiry-day margin**: the short near leg loses its calendar-spread offset on its own expiry day and pays the extra
   2% ELM there (probe 4 cites the SEBI circular). The cash for that day must be inside the trade's funds.
6. **Stock calendars**: a stock near leg that ends in the money is physically settled (probe 4): a delivery obligation
   of the whole lot, not a cash difference. Stock calendars and diagonals stay out until that is modelled.

## 3. Calendar and diagonal worked examples

Inputs **[reasoning only]**: NIFTY 22,811 (21 Oct close, response 327), lot 65, risk-free 6.5% (`config.yaml`
`risk_free_rate`), one flat implied volatility of 13% for both expiries, near leg 28 days, far leg 63 days (35 days
between them), Black-Scholes European prices, no dividends. Script:
the scratchpad's `calendar_math.py` (not in the repository; the formulas are below so anyone can redo them).

**Why puts are the trap [strong evidence: no-arbitrage bounds of European options].** NIFTY options are European. A
European put's lower bound is `K e^(-rT) - S`, which is **below** its intrinsic `K - S` by `K (1 - e^(-rT))`. When the
near short put settles deep in the money at intrinsic, the far long put can be worth less than the intrinsic just paid.
A European call's lower bound `S - K e^(-rT)` is **above** intrinsic, so a call calendar's worst case is its debit.

`K (1 - e^(-rT))` for K 22,800, r 6.5%, T 35 days = **141.7 points = Rs 9,208 a lot**.

### Put calendar, 22,800: sell 28-day put at 268.3, buy 63-day put at 367.3

Debit 99.0 points = **Rs 6,435**.

| NIFTY at near expiry | Far put left | Near settles at | P&L points | P&L rupees |
|---|---|---|---|---|
| 16,000 | 6,658.3 | 6,800 | -240.7 | **-15,644** |
| 20,000 | 2,658.6 | 2,800 | -240.4 | -15,629 |
| 21,500 | 1,198.5 | 1,300 | -200.5 | -13,034 |
| 22,000 | 779.8 | 800 | -119.2 | -7,746 |
| 22,800 | 298.5 | 0 | +199.5 | +12,970 |
| 23,600 | 75.9 | 0 | -23.1 | -1,504 |
| 30,000 | 0.0 | 0 | -99.0 | -6,435 |

Worst case at mid prices = debit + `K (1 - e^(-rT))` = 99.0 + 141.7 = 240.7 points = **Rs 15,644**. Then add:
- **the exit at the bid**: a deep in-the-money far put is thinly quoted; every 10 points below fair is Rs 650 more;
- **a volatility fall** on the far leg, which this flat-13% table ignores;
- entry and exit charges and the Rs 1 pads (`cycle_costs.py`), and settlement STT on the near leg's intrinsic
  (that STT is the buyer's; as the seller of the near put we pay none, but our far leg's sale at the bid pays 0.15%).

### Call calendar, 22,800: sell 28-day call at 392.7, buy 63-day call at 632.7

Debit 240.0 points = Rs 15,598 (already above the Rs 10,000 cap at this IV). The worst case at mid prices is the debit
itself: -240.0 points at 16,000, -98.3 at 30,000 (the far call keeps 141.7 points of carry above intrinsic). Exit at
the bid still makes it worse than the debit.

### Diagonal put: sell 28-day 22,800 put at 268.3, buy 63-day 22,600 put at 289.5

Debit 21.2 points = Rs 1,380. Worst case = debit + (22,800 - 22,600) + 22,600 x (1 - e^(-0.065 x 35/365)) = 21.2 +
200 + 140.5 = **361.7 points = Rs 23,507**, 17 times the debit. A cheap-looking diagonal hides the strike gap.

**What the model must do [reasoning only, from the above]:** value the far leg at the near expiry with (a) the
no-arbitrage lower bound, not intrinsic, as the floor of its worth; (b) a bid haircut from measured spreads by
moneyness and days left; (c) a volatility shock; and take the worst over the price grid. The cap then uses that, never
the debit.

## 4. Futures worked example

### Charge rates for futures (in force 22 Oct 2026)

| Charge | Rate | Source | Label |
|---|---|---|---|
| STT | **0.05% of the sell side** (0.02% up to 31 Mar 2026) | NSE circular NSE/FATAX/73524, 31 Mar 2026, item (c): "Sale of a futures in securities has been revised to 0.05% (upto March 31, 2026 – 0.02%)." https://nsearchives.nseindia.com/content/circulars/FATAX73524.pdf | strong |
| NSE transaction charge + IPFT | **Rs 183 per crore each side** (Rs 182.99 + Rs 0.01 IPFT from 1 Mar 2026; was Rs 173 + Rs 10) | NSE circular NSE/FA/73061, 27 Feb 2026, table row "Equity Futures ... Rs. 183 each side"; "applicable with effect from March 1, 2026." https://nsearchives.nseindia.com/content/circulars/FA73061.pdf | strong |
| SEBI turnover fee | Rs 10 per crore, both sides | Groww https://groww.in/pricing/futures-and-options ("0.0001%"); Zerodha https://zerodha.com/charges/ | some |
| Stamp duty | 0.002%, buy side | Groww and Zerodha pages above | some |
| Brokerage | Rs 20 per executed order | Groww: "Futures & Options Brokerage ... 20 per executed order" | strong (Groww's own page) |
| GST | 18% on brokerage, exchange charge, IPFT and SEBI fee | Groww pricing page | strong |

The same NSE circular moved the **options** split to Rs 3,552.99 + Rs 0.01 IPFT per crore of premium. Our
`config.yaml:31-33` still uses the old split (0.03503% + Rs 50/crore); the **total is the same Rs 3,553 per crore**,
so our options costs are unchanged to the rupee. Only the labels are stale. **[strong evidence: circular table row
"Equity Options ... Rs. 3,553"]**

### One NIFTY futures lot at 22,811, bought and later sold at the same price [arithmetic on the rates above]

Notional 22,811 x 65 = **Rs 14,82,715** (0.148 crore).

| Item | Rupees |
|---|---|
| STT, 0.05% of the sell | 741.36 |
| NSE charge + IPFT, Rs 183/crore x 2 sides | 54.27 |
| SEBI fee, Rs 10/crore x 2 | 2.97 |
| Stamp, 0.002% of the buy | 29.65 |
| Brokerage, 2 orders | 40.00 |
| GST, 18% of brokerage + NSE + SEBI | 17.50 |
| **Round trip** | **885.75 = 13.6 NIFTY points** |

(A research agent's draft gave about Rs 235 here; it took 0.05% of Rs 16.25 lakh as Rs 81.25 instead of Rs 812.50.
Rejected after re-computing.)

### Moves, gaps and margin [arithmetic strong; margin level some evidence]

| | Rupees per lot |
|---|---|
| 1% move | 14,827 |
| 5.9% gap (response 327) | 87,480 |
| Initial margin, about 11.3% of notional (SPAN about 9.3%, ELM 2%) | about 1,67,500 (SPAN about 1,37,900 + ELM 29,654) |

- ELM: "Index Derivatives 2% of the notional value | Stock Derivatives 3.5% of the notional value"
  (https://www.nseclearing.in/risk-management/equity-derivatives/margins). **[strong]**
- SPAN price scan for index derivatives: "Six standard deviations (6 sigma) scaled up by √2 subject to 9.3% of
  underlying price" (NSE SPAN parameters page, updated 4 Jul 2024). **[strong, but the page is old]**
- About 11.3% in total: Zerodha's public margin feed showed NIFTY April-June 2026 futures at 11.32-11.34% of notional.
  **[some evidence: secondary, not today's]** Today's figure can be read exactly from the SPAN file's `futPf`, which
  our parser already loads (`fno/nse_margins/span_file.py:4`). A futures story should do that, not use 11.3%.
- **The margin does not cap the loss.** A 5.9% gap costs Rs 87,480, half the margin; a day beyond 9.3%, such as NIFTY's fall of about
  13% on 23 Mar 2020 [some evidence: widely reported close-to-close], would pass through the whole margin. A future has no maximum loss: the owner's futures policy
  (response 327, section 5, item 2) must set a stress loss per lot, not lean on a stop.

### Calendar spread margin rules the model must carry [strong evidence: quoted]

- SPAN calendar-spread charge: "Index Derivatives 1.75% of the far month contract | Stock Derivatives 2.2% of the far
  month contract ... A calendar spread position will be granted calendar spread treatment till the expiry of the near
  month contract." (NSE SPAN parameters page, 4 Jul 2024.)
- Futures calendar ELM: "extreme loss margin is levied on one third of the value of the open position of the far month
  futures contract." (NSE Clearing margins page.)
- **Expiry day, index derivatives:** "the benefit of offsetting positions across different expiries ('calendar spread')
  shall not be available on the day of expiry for contracts expiring on that day." SEBI circular
  SEBI/HO/MRD/TPD-1/P/CIR/2024/132, 1 Oct 2024, para 5.2.1, effective 1 Feb 2025 (para 5.2.4).
  https://www.sebi.gov.in/sebi_data/attachdocs/oct-2024/1727786261636.pdf
- **Expiry day, single stocks:** the same removal, SEBI circular HO/47/15/11(2)2025-MRD-TPD1/I/4226/2026, 5 Feb 2026,
  "effective from three months from the date of the circular" (about 5 May 2026).
  https://www.sebi.gov.in/sebi_data/attachdocs/feb-2026/1770288869049.pdf
- **Expiry day, short index options:** "an additional extreme loss margin of 2% shall be levied on short index options
  contracts" (NSE Clearing margins page; SEBI 2024/132). Probe 4 has the details.

So on the near leg's expiry day the calendar's short leg is margined as a naked short option, plus 2% of notional
extra ELM: for one NIFTY lot that is at least Rs 29,654 + Rs 29,654 of ELM alone, before SPAN. A calendar held into
the near expiry needs that cash on that day.

### Lot size [strong evidence]

NIFTY 75 -> 65, BANKNIFTY 35 -> 30, FINNIFTY 65 -> 60, MIDCPNIFTY 140 -> 120: NSE circular NSE/FAOP/70616 (Ref.
176/2025), 3 Oct 2025, effective from the January 2026 contracts.
https://nsearchives.nseindia.com/content/circulars/FAOP70616.pdf. No later 2026 revision found (not proven absent):
use the dated lot from NSE's contract file, as P0b's record fields already require.

## Not verified

- Today's NIFTY futures SPAN (read from the SPAN file in the futures story).
- SEBI's own turnover-fee schedule and the Stamp Act schedule (broker pages only).
- Any NSE charge change after 1 Mar 2026.
- The flat 13% volatility in section 3: real far-month IV and its fall on a big move change the numbers; the put bound
  (debit + `K (1 - e^(-rT))`) does not depend on volatility.

